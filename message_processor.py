from telegram_bot_helper.api import CommandMessage, UserMessage

from random import randrange

import json


class BadJob(Exception):
    pass


class Job():
    available_types = ['user_message', 'command']
    available_jobs = ['phrase', 'random_phrase']

    def __init__(self, raw_job):
        self.raw_job = raw_job
        for field in ['keywords', 'message_type', 'job_action', 'data']:
            self.__dict__[field] = getattr(self, "_extract_%s" % field)()

    def _extract_keywords(self):
        keywords = self.raw_job.get('keywords', [])
        keywords = keywords if isinstance(keywords, list) else [keywords]
        return [keyword.lower() for keyword in keywords]

    def _extract_message_type(self):
        message_type = self.raw_job.get('message_type', '').lower()
        if message_type not in self.available_types:
            raise BadJob("Message type %s not available" % message_type)
        return message_type

    def _extract_job_action(self):
        job_action = self.raw_job.get('job_action', '').lower()
        if job_action not in self.available_jobs:
            raise BadJob("Job %s not available" % job_action)
        return job_action

    def _extract_data(self):
        data = self.raw_job.get('data', "")
        return data

    def matches(self, message):
        if isinstance(message, CommandMessage):
            return self._command_match(message.command)
        elif isinstance(message, UserMessage):
            return self._user_text_match(message.text)
        return False

    def _command_match(self, command):
        return command in self.keywords

    def _user_text_match(self, text):
        for word in self.keywords:
            if word.lower() not in text.lower():
                return False
        return True

    def result(self):
        if self.job_action == 'random_phrase':
            return self.data[randrange(len(self.data))]
        elif self.job_action == 'phrase':
            return self.data
        return ''


class MessageProcessor():
    def __init__(self, job_descriptions_file):
        with open(job_descriptions_file, 'r') as f:
            raw_jobs = json.load(f)

        self.jobs = [Job(job) for job in raw_jobs]

    def get_answer(self, message):
        jobs = self._find_matching_jobs(message)
        return jobs[0].result() if len(jobs) else ''

    def _find_matching_jobs(self, message):
        return [job for job in self.jobs if job.matches(message)]
