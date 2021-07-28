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
cleaner.start_cleanup_thread(3, 15, 42)
