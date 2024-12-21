"""
ASGI configuration for Medical Research Platform.

This module configures Django's ASGI interface for production deployment,
enabling asynchronous request handling and WebSocket support.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application  # django 4.2+

# Configure Django's settings module to use production settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Initialize Django ASGI application
# This creates an ASGI callable that can handle:
# - HTTP requests (both sync and async)
# - WebSocket connections for real-time protocol updates
# - Other ASGI protocol types
application = get_asgi_application()

# The application object should be used by ASGI servers like Uvicorn
# with the following recommended settings in production:
#
# uvicorn config.asgi:application \
#     --host 0.0.0.0 \
#     --port 8000 \
#     --workers $(nproc) \
#     --timeout 30 \
#     --backlog 2048 \
#     --log-level info \
#     --proxy-headers \
#     --forwarded-allow-ips='*' \
#     --ssl-keyfile=/path/to/key.pem \
#     --ssl-certfile=/path/to/cert.pem