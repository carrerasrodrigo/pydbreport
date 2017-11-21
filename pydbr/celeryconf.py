from __future__ import absolute_import

from celery import Celery
from celery.schedules import crontab


def setup_celery(conf, method, xml_list):
    app = Celery('Pydbr')

    @app.task(serializer='pickle')
    def execute(conf, xml):
        method(conf, xml)

    @app.on_after_configure.connect
    def setup_periodic_tasks(sender, **kwargs):
        for xml in xml_list:
            if xml.find("cron") is None:
                continue
            cron = crontab(*xml.find("cron").text.split())

            sender.add_periodic_task(
                cron,
                execute.s(conf, xml),
            )
    argv = [
        'worker',
        '--loglevel=INFO',
        '--beat'
    ]
    app.conf.broker_url = conf.beat_broker_config
    app.conf.beat_max_loop_interval = 30
    app.conf.accept_content = ['pickle']
    app.worker_main(argv)
