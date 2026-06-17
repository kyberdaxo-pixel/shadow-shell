# /home/king/shadowshell/shadowshell/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path, re_path

# 1. Atrof-muhit sozlamasini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shadowshell.settings')
django_asgi_app = get_asgi_application()

# 2. Consumer'ni to'g'ridan-to'g'ri import qilish
from accounts.consumers import CyberTerminalConsumer

# 3. .as_websocket() o'rniga .as_asgi() metodini ishlatamiz 🔥
explicit_websocket_urlpatterns = [
    path('ws/cyber-terminal/', CyberTerminalConsumer.as_asgi()),
    re_path(r'^ws/cyber-terminal/?$', CyberTerminalConsumer.as_asgi()),
    re_path(r'ws/cyber-terminal/', CyberTerminalConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(explicit_websocket_urlpatterns)
    ),
})