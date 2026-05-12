import discord
from discord.ext import commands
import json
import os
import asyncio
import threading
import logging
from main_exe.FDScript import run_script

class PrefixManager:
    def __init__(self):
        self.prefixes_file = "app_data/prefixes.json"
        self.files_dir = "app_data/files"
        self.prefixes = self.load_prefixes()

    def load_prefixes(self):
        if os.path.exists(self.prefixes_file):
            try:
                with open(self.prefixes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def get_file_by_message(self, content):
        self.prefixes = self.load_prefixes()
        content = content.strip()
        for filename, prefix in self.prefixes.items():
            if content.startswith(prefix):
                return filename
        return None

prefix_manager = PrefixManager()

async def get_prefix(bot, message):
    return "!"

c = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all(), help_command=None)

@c.event
async def on_ready():
    print(f'{c.user} متصل وجاهز!')

@c.event
async def on_message(message):
    if message.author.bot:
        return
    matched_file = prefix_manager.get_file_by_message(message.content)
    if matched_file:
        file_path = os.path.join(prefix_manager.files_dir, matched_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    script_text = f.read()
                await run_script(message, c, script_text)
                return
            except Exception as e:
                print(f"Error executing {matched_file}: {e}")
    await c.process_commands(message)


_client: discord.Client | None = None
_loop:   asyncio.AbstractEventLoop | None = None
_thread: threading.Thread | None = None
_lock    = threading.Lock()
_stopping = False

def _get_token() -> str:
    try:
        with open("bot_token.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def _runner(token: str) -> None:
    global _loop, _stopping
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with _lock:
        _loop = loop
    try:
        loop.run_until_complete(_client.start(token))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        except Exception:
            pass
        loop.close()
        with _lock:
            _stopping = False

def start_bot() -> bool:
    global _client, _thread, _stopping
    if _stopping:
        return False
    if _client and not _client.is_closed():
        return False
    token = _get_token()
    if not token:
        return False
    _client = c
    _thread = threading.Thread(target=_runner, args=(token,), daemon=True)
    _thread.start()
    return True

def stop_bot() -> None:
    global _stopping
    if _stopping:
        return
    if _client is None or _client.is_closed():
        return
    _stopping = True
    if _loop and _loop.is_running():
        future = asyncio.run_coroutine_threadsafe(_client.close(), _loop)
        try:
            future.result(timeout=5)
        except Exception as e:
            print(f"Error closing bot: {e}")

def restart_bot() -> bool:
    stop_bot()
    if _thread and _thread.is_alive():
        _thread.join(timeout=6)
    return start_bot()

def is_running() -> bool:
    return bool(_client and not _client.is_closed())
