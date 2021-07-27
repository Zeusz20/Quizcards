import os
import threading

from django.conf import settings
from .models import Card


_CLEANUP_THREAD_NAME = 'FileCleanupThread'


def file_cleanup():
    images = list()

    for card in Card.objects.all():
        images.append(os.path.basename(card.term_image.name))
        images.append(os.path.basename(card.definition_image.name))

    for filename in os.listdir(settings.MEDIA_ROOT):
        if filename not in images:
            file = os.path.join(settings.MEDIA_ROOT, filename)
            os.remove(file)


def schedule_cleanup():
    threads = list(
        # get the names of running threads
        map(lambda thread: thread.name, threading.enumerate())
    )

    if _CLEANUP_THREAD_NAME not in threads:
        cleanup_thread = threading.Thread(target=file_cleanup, daemon=True, name=_CLEANUP_THREAD_NAME)
        cleanup_thread.start()
        cleanup_thread.join()
