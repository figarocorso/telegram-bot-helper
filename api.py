from time import sleep
import requests


class TelegramAPIHelper():
    emojis = {
        ':+1:': u'\U0001F44D',
    }

    def __init__(self, token):
        self.last_update_id = 0
        self.url = "https://api.telegram.org/bot%s/" % token

    def get_new_messages(self, mark_as_read=True):
        data = self._get_data(mark_as_read)
        self.raw_messages = data.get('result', [])
        self.messages = self._parse_raw_messages()

        return self.messages

    def update_offset(self):
        if not len(self.messages):
            return
        self.last_update_id = self.messages[-1].get('update_id')

    def send_message(self, chat, message, tries=5):
        success = False
        while not success and tries > 0:
            data = {'chat_id': chat, 'text': message}
            success = self._send_post_request("sendMessage", data)
            tries -= 1
            sleep(1)

    def reply(self, message, text):
        pass

    def _get_data(self, mark_as_read):
        params = {'offset': self.last_update_id + 1} if mark_as_read else {}
        try:
            response = requests.get(self.url + "getUpdates", params=params)
        except requests.exceptions.ConnectionError:
            return {}

        if not response.ok:
            return {}

        return response.json()

    def _parse_raw_messages(self):
        messages = []
        for raw_message in self.raw_messages:
            message = raw_message.get('message', {})
            message['update_id'] = raw_message.get('update_id', 0)
            messages.append(message)

        return messages

    def _send_post_request(self, method, data):
        try:
            response = requests.post("%s%s" % (self.url, method),
                                     data=data)
            return response.ok
        except requests.exceptions.ConnectionError:
            return False
