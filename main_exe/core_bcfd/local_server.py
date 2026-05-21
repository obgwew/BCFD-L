# bot_runner.py — النسخة المعدلة

import discord
from discord.ext import commands
import json
import os
import asyncio
import threading
from main_exe.core_bcfd.FDScript import run_script, set_vars_dir


# ══════════════════════════════════════════════════════════════
#  PrefixManager — يقرأ مباشرة من bot_commands/
# ══════════════════════════════════════════════════════════════

class PrefixManager:
    def __init__(self):
        self._bot_commands_dir = ''   # يُضبط عند start_bot

    def set_bot_dir(self, bot_dir: str):
        """
        bot_dir = app_data/{bot_name}/bot_files
        bot_commands = app_data/{bot_name}/bot_commands
        """
        bot_root = os.path.dirname(os.path.abspath(bot_dir))
        self._bot_commands_dir = os.path.join(bot_root, 'bot_commands')

    def _load_commands(self) -> list[dict]:
        """
        يقرأ جميع ملفات .py في bot_commands/
        كل ملف يبدأ بـ:  #PREFIX:<prefix_value>
        """
        if not os.path.isdir(self._bot_commands_dir):
            return []

        cmds = []
        for fname in os.listdir(self._bot_commands_dir):
            if not fname.endswith('.py'):
                continue
            path = os.path.join(self._bot_commands_dir, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    raw = f.read()
            except Exception:
                continue

            prefix  = ''
            content = raw
            if raw.startswith('#PREFIX:'):
                nl      = raw.find('\n')
                prefix  = raw[8:nl].strip() if nl != -1 else raw[8:].strip()
                content = raw[nl + 1:] if nl != -1 else ''

            if prefix:
                cmds.append({'prefix': prefix, 'content': content, 'file': fname})

        return cmds

    def get_script_by_message(self, content: str) -> str | None:
        """
        يرجع نص FDScript إذا تطابق الـ prefix
        يُعيد None إذا لم يتطابق أي أمر
        """
        content = content.strip()
        for cmd in self._load_commands():
            if content.startswith(cmd['prefix']):
                return cmd['content']
        return None


prefix_manager = PrefixManager()

_client:  discord.Client | None = None
_loop:    asyncio.AbstractEventLoop | None = None
_thread:  threading.Thread | None = None
_lock     = threading.Lock()
_stopping = False


def _make_bot() -> commands.Bot:
    bot = commands.Bot(
        command_prefix='!',
        intents=discord.Intents.all(),
        help_command=None,
    )

    @bot.event
    async def on_ready():
        print(f'[Bot] {bot.user} متصل وجاهز!')

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        # ── البحث عن أمر مطابق في bot_commands/ ──────────────────
        script_text = prefix_manager.get_script_by_message(message.content)
        if script_text is not None:
            try:
                await run_script(message, bot, script_text)
            except Exception as e:
                print(f"[Bot] خطأ في تنفيذ السكربت: {e}")
            return   # لا تكمل لـ process_commands

        await bot.process_commands(message)

    return bot


def _get_token(bot_dir: str) -> str:
    try:
        config_path = os.path.join(bot_dir, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('token', '')
    except Exception as e:
        print(f"[Bot] خطأ في قراءة config.json: {e}")
        return ''


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
        print(f"[Bot] خطأ: {e}")
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        except Exception:
            pass
        loop.close()
        with _lock:
            _stopping = False


def start_bot(bot_dir: str) -> bool:
    global _client, _thread, _stopping

    if _stopping:
        print("[Bot] لا يزال يتوقف...")
        return False

    if _client and not _client.is_closed():
        print("[Bot] يعمل مسبقاً")
        return False

    token = _get_token(bot_dir)
    if not token:
        print("[Bot] لا يوجد توكن في config.json")
        return False

    # ── ربط PrefixManager بـ bot_dir ──────────────────────────
    prefix_manager.set_bot_dir(bot_dir)

    bot_root = os.path.dirname(os.path.abspath(bot_dir))
    set_vars_dir(os.path.join(bot_root, 'bot_vars'))

    _client = _make_bot()
    _thread = threading.Thread(target=_runner, args=(token,), daemon=True)
    _thread.start()
    print("[Bot] ▶ تم التشغيل")
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
            print(f"[Bot] خطأ في الإيقاف: {e}")
    print("[Bot] ■ تم الإيقاف")


def restart_bot(bot_dir: str) -> bool:
    stop_bot()
    if _thread and _thread.is_alive():
        _thread.join(timeout=6)
    return start_bot(bot_dir)


def is_running() -> bool:
    return bool(_client and not _client.is_closed())