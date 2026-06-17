import asyncio
import json
import pexpect
from channels.generic.websocket import AsyncWebsocketConsumer

class CyberTerminalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_superuser:
            await self.close()
            return

        await self.accept()
        
        # O'yin statistikasi
        self.command_count = 0
        self.task_1_completed = False
        self.task_2_completed = False

        try:
            self.terminal = pexpect.spawn(
                'docker run -it --rm --net=none alpine sh',
                encoding='utf-8',
                dimensions=(24, 80)
            )
            self.read_task = asyncio.create_task(self.read_from_container())
        except Exception as e:
            await self.close()

    async def disconnect(self, close_code):
        try: self.read_task.cancel()
        except: pass
        try:
            if self.terminal and self.terminal.isalive():
                self.terminal.close(force=True)
        except: pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data or not self.terminal.isalive():
            return

        # Klaviatura kiritishlarini tekshirish
        # Agar foydalanuvchi Enter (tarmoqda \r yoki \n) bossa, demak bitta buyruq yakunlandi
        if text_data in ['\r', '\n']:
            self.command_count += 1
            # Har 15 ta buyruqda yutuq berish mexanizmi
            if self.command_count % 15 == 0:
                await self.send(text_data=json.dumps({
                    "event": "achievement",
                    "title": f"🏆 Terminal Exploit Master v{self.command_count // 15}",
                    "desc": f"{self.command_count} ta buyruqni xavfsiz bajarganingiz uchun!"
                }))

        try:
            self.terminal.send(text_data)
        except Exception:
            pass

    async def read_from_container(self):
        loop = asyncio.get_running_loop()
        while True:
            try:
                data = await loop.run_in_executor(
                    None, 
                    lambda: self.terminal.read_nonblocking(size=2048, timeout=0.05)
                )
                if data:
                    # 1. Matnni to'g'ridan-to'g'ri xterm'ga jo'natamiz
                    await self.send(text_data=json.dumps({"event": "terminal", "data": data}))
                    
                    # 2. 🟢 TOPSHIRIQ №01 TEKSHIRISH: whoami yozilganda root javobi kelsa
                    if "root" in data and not self.task_1_completed:
                        self.task_1_completed = True
                        await self.send(text_data=json.dumps({
                            "event": "task_complete",
                            "task_id": 1,
                            "exp": 150,
                            "next_task_id": 2
                        }))

                    # 3. 🔴 TOPSHIRIQ №02 TEKSHIRISH: rm -rf / qilinganda seans o'lsa yoki xatolik bersa
                    if ("rm: can't remove" in data or "reboot" in data) and not self.task_2_completed:
                        self.task_2_completed = True
                        await self.send(text_data=json.dumps({
                            "event": "task_complete",
                            "task_id": 2,
                            "exp": 300,
                            "next_task_id": null
                        }))

            except pexpect.TIMEOUT:
                await asyncio.sleep(0.01)
                continue
            except (pexpect.EOF, Exception):
                break
        await self.close()