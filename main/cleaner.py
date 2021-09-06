import os
import threading

from django.conf import settings
from .models import Card
from .utils import django_thread, validate_datetime

CLEANUP_THREAD_NAME = 'FileCleanupThread'


def file_cleanup():
    images = list()

    for card in Card.objects.all():
        images.append(os.path.basename(card.term_image.name))
        images.append(os.path.basename(card.definition_image.name))

    for filename in os.listdir(settings.MEDIA_ROOT):
        if filename not in images:
            file = os.path.join(settings.MEDIA_ROOT, filename)
            os.remove(file)


def start_cleanup_thread(day, hour, minute):
    # raises ValueError if datetime is invalid
    validate_datetime(day, hour, minute)

    def task():
        from datetime import datetime
        from time import sleep

        while django_thread().is_alive():
            now = datetime.now()
            current_day = (now.date().isoweekday() == day)
            current_time = (now.hour == hour and now.minute == minute)

            if current_day and current_time:
                file_cleanup()
            sleep(60)   # wake up every minute

    # get the names of running threads
    threads = map(lambda thread: thread.name, threading.enumerate())

    if CLEANUP_THREAD_NAME not in threads:
        cleanup_thread = threading.Thread(target=task, name=CLEANUP_THREAD_NAME, daemon=True)
        cleanup_thread.start()
