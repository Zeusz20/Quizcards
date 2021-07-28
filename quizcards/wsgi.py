"""
WSGI config for quizcards project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from main import cleaner

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizcards.settings')

application = get_wsgi_application()

# run file cleanup every FRI at 17:00
cleaner.start_cleanup_thread(5, 17, 00)
