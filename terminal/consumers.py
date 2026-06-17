import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

logger = logging.getLogger('terminal')


class TerminalConsumer(AsyncWebsocketConsumer):
    """WebSocket orqali terminal"""

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = f'terminal_{self.user.id}'
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': f'🔗 ShadowShell Terminal connected. Welcome, {self.user.username}!',
            'prompt': f'{self.user.username}@shadowshell:~$ ',
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get('command', '').strip()

            if not command:
                return

            if len(command) > 5000:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Buyruq juda uzun.',
                }))
                return

            # Kodni bajarish
            from .sandbox import execute_in_sandbox
            result = execute_in_sandbox(command, timeout=15)

            await self.send(text_data=json.dumps({
                'type': 'output',
                'output': result['output'],
                'error': result.get('error', ''),
                'status': result['status'],
                'prompt': f'{self.user.username}@shadowshell:~$ ',
            }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Noto\'g\'ri format.',
            }))
        except Exception as e:
            logger.error(f'Terminal consumer error: {e}')
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Ichki xatolik yuz berdi.',
            }))