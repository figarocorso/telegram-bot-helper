from time import sleep
import requests


class InvalidMessage(Exception):
    pass


class Message():
    @staticmethod
    def from_raw(raw_message, bot_name):
        message = raw_message.get('message', {})
        if Message.is_join_message(message):
            return JoinMessage(raw_message, bot_name)
        if Message.is_left_message(message):
            return LeftMessage(raw_message, bot_name)
        if Message.is_command_message(message):
            return CommandMessage(raw_message, bot_name)
        if Message.is_user_message(message):
            return UserMessage(raw_message, bot_name)

        return Message(raw_message, bot_name)

    @staticmethod
    def is_join_message(message):
        return 'new_chat_participant' in message.keys()

    @staticmethod
    def is_left_message(message):
        return 'left_chat_participant' in message.keys()

    @staticmethod
    def is_command_message(message):
        return 'text' in message.keys() and len(message['text']) and \
            message['text'][0] == '/'

    @staticmethod
    def is_user_message(message):
        return 'text' in message.keys()

    def __init__(self, raw, bot_name):
        self.update_id = raw.get('update_id', 0)
        self.raw_message = raw.get('message', {})
        self.bot_name = bot_name

    @property
    def id(self):
        return self.raw_message.get('message_id', 0)

    @property
    def date(self):
        return self.raw_message.get('date', 0)

    @property
    def chat_id(self):
        return self.raw_message.get('chat', {}).get('id', 0)

    @property
    def chat_title(self):
        return self.raw_message.get('chat', {}).get('title', '')

    @property
    def from_id(self):
        return self.raw_message.get('from', {}).get('id', 0)

    @property
    def from_username(self):
        return self.raw_message.get('from', {}).get('username', '')

    @property
    def from_name(self):
        message_from = self.raw_message.get('from', {})
        return message_from.get('first_name', '') + " " + \
            message_from.get('last_name', '')

    def is_group_chat(self):
        return self.chat_id < 0


class JoinMessage(Message):
    @property
    def subject_id(self):
        return self.raw_message.get('new_chat_participant', {}).\
            get('id', 0)

    @property
    def subject_username(self):
        return self.raw_message.get('new_chat_participant', {}).\
            get('username', 0)


class LeftMessage(Message):
    @property
    def subject_id(self):
        return self.raw_message.get('left_chat_participant', {}).\
            get('id', 0)

    @property
    def subject_username(self):
        return self.raw_message.get('left_chat_participant', {}).\
            get('username', 0)


class CommandMessage(Message):
    @property
    def command(self):
        text = self.raw_message.get('text', '').lower().split()

        if not len(text):
            return ''

        if self._is_direct_command(text[0]):
            if not self._is_direct_command_to_us(text[0]):
                return ''

        return self._extract_command(text[0])

    def _is_direct_command(self, command):
        return '@' in command

    def _is_direct_command_to_us(self, command):
        return self.bot_name == command.split('@')[1]

    def _extract_command(self, command):
        return command[1:].split('@')[0]

    @property
    def arguments(self):
        text = self.raw_message.get('text', '').split()
        return text[1:] if len(text) else []


class UserMessage(Message):
    @property
    def text(self):
        return self.raw_message.get('text', '').lower()

    @property
    def original_text(self):
        return self.raw_message.get('text', '')


class AnswerMessage():
    method_correlation = {
        'text': 'sendMessage',
        'audio': 'sendAudio',
        'photo': 'sendPhoto',
    }

    def __init__(self, data, message_type='text'):
        self.message_type = message_type.lower()
        if self.message_type not in self.method_correlation.keys():
            raise InvalidMessage("Wrong answer message type %s" % message_type)

        self.data = {message_type: data}

    def set_destination_chat(self, chat_id):
        self.data['chat_id'] = chat_id

    def in_reply_to(self, message):
        self.data['chat_id'] = message.chat_id

    @property
    def method(self):
        return self.method_correlation.get(self.message_type, 'sendMessage')

    @property
    def data(self):
        return self.data


class TelegramAPIHelper():
    def __init__(self, token, bot_name):
        self.last_update_id = 0
        self.url = "https://api.telegram.org/bot%s/" % token
        self.bot_name = bot_name.lower()

    def get_new_messages(self, mark_as_read=True):
        data = self._get_data(mark_as_read)
        self.raw_messages = data.get('result', [])
        self.messages = self._parse_raw_messages()

        return self.messages

    def update_offset(self):
        if not len(self.messages):
            return
        self.last_update_id = self.messages[-1].update_id

    def send_message(self, data, method='sendMessage', tries=5):
        success = False
        while not success and tries > 0:
            success = self._send_post_request(method, data)
            tries -= 1
            sleep(1)

    def send_answer(self, answer):
        self.send_message(answer.data, answer.method)

    def reply(self, message, answer):
        answer.in_reply_to(message)
        self.send_answer(answer)

    def _get_data(self, mark_as_read):
        timeout = 12 * 60 * 60
        params = {'offset': self.last_update_id + 1, 'timeout': timeout}
        params = params if mark_as_read else {}
        try:
            response = requests.get(self.url + "getUpdates",
                                    params=params,
                                    timeout=timeout)
        except requests.exceptions.ConnectionError:
            return {}
        except requests.exceptions.Timeout:
            return {}

        if not response.ok:
            return {}

        return response.json()

    def _parse_raw_messages(self):
        messages = []
        for raw_message in self.raw_messages:
            message = Message.from_raw(raw_message, self.bot_name)
            messages.append(message)

        return messages

    def _send_post_request(self, method, data):
        try:
            response = requests.post("%s%s" % (self.url, method),
                                     data=data)
            return response.ok
        except requests.exceptions.ConnectionError:
            return False
