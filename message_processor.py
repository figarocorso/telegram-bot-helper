from telegram_bot_helper.api import CommandMessage

from random import randrange

import itertools
import json


class MessageProcessor():
    def __init__(self, job_descriptions_file):
        with open(job_descriptions_file, 'r') as f:
            self.jobs = json.load(f)

        # TODO Check jobs integrity and lower key fields
        commands = [map(unicode.lower, x['keywords']) for x in self.jobs
                    if self._job_is_command(x)]
        self.available_commands = list(itertools.chain(*commands))

    def _job_is_command(self, job):
        return job['message_type'] == 'command'

    def get_answer(self, message):
        if self._is_valid_command(message):
            return self._command_answer(message)
        return ''

    def _is_valid_command(self, message):
        return isinstance(message, CommandMessage) and \
            message.command in self.available_commands

    def _command_answer(self, message):
        job = self._get_command_job(message.command)
        return getattr(self, "_%s_result" % job['job'].lower())(job)

    def _get_command_job(self, command):
        return [job for job in self.jobs
                if command in job['keywords']][0]

    # Job processors
    def _random_phrase_result(self, job):
        return job['data'][randrange(len(job['data']))]

    def _phrase_result(self, job):
        return job['data']
