from django.urls import re_path
from accounts.consumers import CyberTerminalConsumer  # Biz yozgan yangi consumer

websocket_urlpatterns = [
    # ... agar eski yo'nalishlar bo'lsa turadi, bo'lmasa pastdagini qo'shing:
    path('ws/cyber-terminal/', CyberTerminalConsumer.as_websocket()),
    re_path(r'ws/cyber-terminal/$', CyberTerminalConsumer.as_websocket()),
]