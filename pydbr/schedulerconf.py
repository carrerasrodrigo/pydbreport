from __future__ import absolute_import

import logging
import time

from croniter import croniter
from datetime import datetime
import pytz

logger = logging.getLogger('pydbr')


class Task(object):
    def __init__(self, cron, job, task_name):
        self.event = cron
        self.job = job
        self.next_iter = self.event.get_next(datetime)
        self.task_name = task_name

    def should_execute(self):
        dt = pytz.timezone('UTC').localize(datetime.now())
        return self.next_iter <= dt

    def execute(self):
        logger.info(f'{self.task_name} executing now')
        self.job()
        self.next_iter = self.event.get_next(datetime)
        logger.info(f'{self.task_name} done, next execution {self.next_iter}')


class Scheduler(object):
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def loop(self):
        while True:
            for task in self.tasks:
                if task.should_execute():
                    task.execute()
            time.sleep(60)


def start_loop(conf, method, xml_list):
    tz = pytz.timezone('UTC')
    base = tz.localize(datetime.now())

    logger.info('starting pydbr scheduler')
    scheduler = Scheduler()
    for xml in xml_list:
        subject = xml.find('subject').text
        if xml.find("cron") is None or \
                not croniter.is_valid(xml.find("cron").text):
            logger.warning(f'warning cron ignored {subject}')
            continue

        cron = croniter(xml.find("cron").text, base)

        def execute():
            logger.info(f'running job {subject}')
            method(conf, xml)
            logger.info(f'job done {subject}')

        task = Task(cron, execute, subject)
        logger.info(f'adding task {subject} to scheduler')
        scheduler.add_task(task)

    logger.info('starting pydbr scheduler')
    scheduler.loop()
