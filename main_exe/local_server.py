# local_server.py

import discord
from discord.ext import commands
import json
import os
import asyncio
import threading
from pathlib import Path

from main_exe.FDScript import run_script  # استدعاء المفسر من الملف الخارجي

class PrefixManager:
    """مدير البرفكسات المخصصة"""
    def __init__(self):
        self.prefixes_file = "app_data/prefixes.json"
        self.files_dir = "app_data/files"
        self.prefixes = self.load_prefixes()
        self.file_commands = {}
        self.load_file_commands()

    def load_prefixes(self):
        if os.path.exists(self.prefixes_file):
            try:
                with open(self.prefixes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def load_file_commands(self):
        self.file_commands = {}
        for filename, prefix in self.prefixes.items():
            if prefix.strip():
                self.file_commands[prefix.strip()] = filename

    def get_file_by_prefix(self, prefix):
        return self.file_commands.get(prefix)

    def get_all_prefixes(self):
        return list(self.file_commands.keys())

# إنشاء مدير البرفكسات
prefix_manager = PrefixManager()

# دالة لتحديد البرفكس ديناميكياً
async def get_prefix(bot, message):
    prefix_manager.load_prefixes()
    prefix_manager.load_file_commands()
    prefixes = prefix_manager.get_all_prefixes()
    prefixes.append('!')
    return prefixes

# إنشاء البوت مع البرفكس الديناميكي
c = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all(), help_command=None)

@c.event
async def on_ready():
    print(f'{c.user} متصل!')

@c.event
async def on_message(message):
    if message.author.bot:
        return

    prefix_manager.load_prefixes()
    prefix_manager.load_file_commands()

    message_content = message.content
    matched_prefix = None
    matched_file = None

    for prefix in prefix_manager.get_all_prefixes():
        if message_content.startswith(prefix + ' ') or message_content == prefix:
            matched_prefix = prefix
            matched_file = prefix_manager.get_file_by_prefix(prefix)
            break

    if matched_prefix and matched_file:
        try:
            file_path = os.path.join(prefix_manager.files_dir, matched_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                await run_script(message, c, file_content)  # تفسير الأوامر من bcfd
            else:
                await message.channel.send(f"الملف {matched_file} غير موجود!")
        except Exception as e:
            await message.channel.send(f"خطأ في تنفيذ الملف: {str(e)}")

    await c.process_commands(message)

# 🔹 دعم التشغيل والإيقاف الآمن للبوت (مناسب لـ Kivy)
bot_loop   = None
bot_thread = None

def start_bot():
    """
    تشغيل البوت في خيط منفصل مع event loop جديد.
    إذا كان البوت يعمل بالفعل، يتجاهل الطلب.
    """
    global bot_loop, bot_thread

    if bot_thread and bot_thread.is_alive():
        return

    def _run():
        global bot_loop
        bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(bot_loop)

        try:
            with open("bot_token.txt", "r", encoding="utf-8") as f:
                token = f.read().strip()

            bot_loop.run_until_complete(c.start(token))

        except Exception as e:
            print(f"❌ خطأ أثناء تشغيل البوت: {e}")

        finally:
            bot_loop.run_until_complete(bot_loop.shutdown_asyncgens())
            bot_loop.close()

    bot_thread = threading.Thread(target=_run, daemon=True)
    bot_thread.start()

def stop_bot():
    global bot_loop, bot_thread

    if bot_loop:
        async def _close_bot():
            await c.close()

        bot_loop.call_soon_threadsafe(lambda: asyncio.create_task(_close_bot()))

    if bot_thread:
        bot_thread.join()
        bot_thread = None
        bot_loop   = None