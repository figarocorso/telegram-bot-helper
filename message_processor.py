from telegram_bot_helper.api import CommandMessage, UserMessage

from random import randrange

import datetime
import uuid
import json


class BadJob(Exception):
    pass


class JobStatus():
    job_status = {}

    @classmethod
    def decrease_countdown(cls, job_id, minutes, countdown):
        if job_id not in cls.job_status.keys():
            cls._insert_new_job_status(job_id, minutes, countdown)
        else:
            cls.job_status[job_id]['countdown'] -= 1

    @classmethod
    def _insert_new_job_status(cls, job_id, minutes, countdown):
        cls.job_status[job_id] = {
            'countdown': countdown - 1,
            'timeout': minutes,
            'creation': datetime.datetime.now()}

    @classmethod
    def get_countdown(cls, job_id):
        if job_id not in cls.job_status.keys():
            return 0
        return cls.job_status[job_id]['countdown']

    @classmethod
    def clean(cls):
        now = datetime.datetime.now()
        deletions = []
        for key, status in cls.job_status.iteritems():
            if (now - status['creation']).seconds / 60 > status['timeout'] or \
               status['countdown'] <= 0:
                deletions.append(key)

        for key in deletions:
            del(cls.job_status[key])


class Job():
    available_types = ['user_message', 'command', 'repeated_message']
    available_jobs = ['phrase', 'random_phrase']

    def __init__(self, raw_job):
        self.raw_job = raw_job
        for field in ['keywords', 'message_type', 'job_action', 'data',
                      'minutes_timeout', 'countdown', 'job_id']:
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
        return self.raw_job.get('data', "")

    def _extract_countdown(self):
        return self.raw_job.get('countdown', 0)

    def _extract_minutes_timeout(self):
        return self.raw_job.get('minutes_timeout', 0)

    def _extract_job_id(self):
        return self.raw_job.get('job_id', str(uuid.uuid1()))

    def matches(self, message):
        if self.message_type == 'command' and \
           isinstance(message, CommandMessage):
            return self._command_match(message.command)
        elif (self.message_type == 'user_message' and
              isinstance(message, UserMessage)):
            return self._user_text_match(message.text)
        return False

    def _command_match(self, command):
        return command in self.keywords

    def _user_text_match(self, text):
        for phrase in self.keywords:
            if self._text_contains(text, phrase):
                return True
        return False

    def _text_contains(self, text, phrase):
        string = text.lower()
        needle = phrase.lower()

        exact = len(string) == len(needle)
        begin = string.find("%s " % needle) == 0
        middle = " %s " % needle in string
        end = string.find(" %s" % needle) == (len(string) - (len(needle) + 1))

        return needle in string and (exact or begin or middle or end)

    def should_be_triggered(self):
        if not self.countdown:
            return True

        JobStatus.decrease_countdown(self.job_id, self.minutes_timeout,
                                     self.countdown)
        trigger = JobStatus.get_countdown(self.job_id) <= 0
        JobStatus.clean()

        return trigger

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
        triggered_jobs = [x for x in jobs if x.should_be_triggered()]

        if not len(triggered_jobs):
            return ''
        return triggered_jobs[0].result()

    def _find_matching_jobs(self, message):
        return [job for job in self.jobs if job.matches(message)]
