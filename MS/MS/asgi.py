"""
ASGI config for MS project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns  # Импортируем маршруты для WebSocket

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MS.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Для обработки HTTP-трафика
    "websocket": AuthMiddlewareStack(  # Для WebSocket соединений с поддержкой аутентификации
        URLRouter(
            websocket_urlpatterns  # Подключаем маршруты для WebSocket
        )
    ),
})