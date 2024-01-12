import logging
import os
import pathlib
from celery.signals import worker_ready, setup_logging, worker_shutdown, task_postrun
from logging.handlers import RotatingFileHandler

import kombu
from celery import Celery
from dotenv import load_dotenv

APP_PATH = pathlib.Path(__file__).parent.parent

env_path = APP_PATH.parent.parent / '.env'

assert env_path.is_file(), env_path

load_dotenv(env_path)

broker_url = os.getenv('CELERY_BROKER')
imports = ('src.celery_application.tasks',)
celery_app = Celery(
    broker=broker_url,
    include=imports,
    broker_connection_retry=True,
    broker_api_url=os.getenv('CELERY_BROKER_API_URL', None),
    task_reject_on_worker_lost=True,
    event_queue_prefix=f"{os.getenv('celeryev')}event_queue_"
)

celery_app.conf.task_queues = (
    kombu.Queue(name='default_q'),
    kombu.Queue(name='cold_start_q'),
    kombu.Queue(name='health_check_q'),
)

log_file = os.getenv('CELERY_LOG_PATH', './celery.log')

log_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024 * 100, backupCount=5)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
celery_app.log.get_default_logger().addHandler(log_handler)

celery_app.conf.task_default_exchange = 'default_q'


celery_app.conf.beat_schedule = {
    'check-servers-health': {
        'task': 'health_check',
        'schedule': 60.0,
        'args': []
    }
}


@setup_logging.connect
def on_celery_setup_logging(**kwargs):
    celery_app.log.get_default_logger().info('STARTED UP NEW NODE')
