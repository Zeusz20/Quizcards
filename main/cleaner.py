import os
import threading

from django.conf import settings
from .models import Card

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
    # validate datetime parameters
    if not 1 <= day <= 7:
        raise ValueError(day)
    if not 0 <= hour <= 24:
        raise ValueError(hour)
    if not 0 <= minute <= 59:
        raise ValueError(minute)

    def task():
        from datetime import datetime
        from time import sleep

        while True:
            now = datetime.now()
            current_day = (now.date().isoweekday() == day)
            current_time = (now.hour == hour and now.minute == minute)

            if current_day and current_time:
                file_cleanup()
            sleep(60)   # wake up every minute

    threads = list(
        # get the names of running threads
        map(lambda thread: thread.name, threading.enumerate())
    )

    if CLEANUP_THREAD_NAME not in threads:
        cleanup_thread = threading.Thread(target=task, name=CLEANUP_THREAD_NAME)
        cleanup_thread.start()
        cleanup_thread.join()
