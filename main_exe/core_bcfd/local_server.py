# -*- coding: utf-8 -*-
# main_exe/core_bcfd/local_server.py 

import discord
from discord.ext import commands
import json
import os
import asyncio
import threading
import time
from main_exe.core_bcfd.FDScript import run_script, set_vars_dir, set_bot_start_time

# ══════════════════════════════════════════════════════════════
#  PrefixManager 
# ══════════════════════════════════════════════════════════════

class PrefixManager:
    def __init__(self):
        self._bot_commands_dir = ''
        self._bot_events_dir = ''  

    def set_bot_dir(self, bot_dir: str):
        abs_dir = os.path.abspath(bot_dir)
        if os.path.basename(abs_dir).lower() == 'bot_files':
            bot_root = os.path.dirname(abs_dir)
        else:
            bot_root = abs_dir
        self._bot_commands_dir = os.path.join(bot_root, 'bot_commands')
        self._bot_events_dir = os.path.join(bot_root, 'bot_events') 

    def get_event_script(self, event_name: str) -> str | None:
        if not os.path.isdir(self._bot_events_dir):
            return None

        for fname in os.listdir(self._bot_events_dir):
            fpath = os.path.join(self._bot_events_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    continue
                    
                first_line = content.split('\n')[0].strip().replace(" ", "").upper()
                if first_line.startswith("#PREFIX:"):
                    prefix_part = first_line.replace("#PREFIX:", "").split('[')[0]
                    if prefix_part == event_name.upper():
                        return content
            except Exception:
                pass
        return None

    def get_script_by_message(self, message_content: str) -> str | None:
        """فحص الأوامر العادية ذات البادئة الثابتة من مجلد bot_commands"""
        if not os.path.isdir(self._bot_commands_dir):
            return None

        for fname in os.listdir(self._bot_commands_dir):
            fpath = os.path.join(self._bot_commands_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    continue
                
                first_line = content.split('\n')[0].strip()
                if first_line.upper().startswith("#PREFIX:"):
                    prefix = first_line.split(":", 1)[1].strip()
                    if message_content.strip().startswith(prefix):
                        return content
            except Exception:
                pass
        return None


# ─────────────────────────────────────────────────────────────
#  إعدادات المتغيرات العامة للبوت
# ─────────────────────────────────────────────────────────────

_client = None
_thread = None
_loop = None
_stopping = False
prefix_manager = PrefixManager()


def _get_token(bot_dir: str) -> str:
    possible_paths = [
        # 1. المسار المباشر (كما كان)
        os.path.join(bot_dir, 'config.json'),
        
        # 2. داخل مجلد bot_files (الحالة الصحيحة عندك)
        os.path.join(bot_dir, 'bot_files', 'config.json'),
        
        # 3. في المجلد الأب (احتياطي)
        os.path.join(os.path.dirname(bot_dir), 'config.json'),
        
        # 4. في المجلد الأب + bot_files
        os.path.join(os.path.dirname(bot_dir), 'bot_files', 'config.json'),
    ]

    print(f"[DEBUG] bot_dir المستلم: {bot_dir}")

    for path in possible_paths:
        print(f"[DEBUG] جاري البحث في: {path}")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                
                token = data.get('token') or data.get('TOKEN') or data.get('bot_token')
                if token:
                    print(f"[DEBUG] ✅ تم العثور على التوكن في: {path}")
                    return str(token)
                else:
                    print(f"[DEBUG] الملف موجود لكن لا يحتوي على 'token'")
            except Exception as e:
                print(f"[ERROR] خطأ في قراءة {path}: {e}")

    print("[Bot] ❌ لم يتم العثور على config.json في أي مسار متوقع")
    return ''


# ══════════════════════════════════════════════════════════════
#  بناء البوت وربط الأحداث المستقلة (event_FDScripts)
# ══════════════════════════════════════════════════════════════

def _make_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"[Bot] تم تسجيل الدخول بنجاح كـ: {bot.user}")
        set_bot_start_time(time.time())

    # ── 1. حدث دخول الأعضاء ($onJoined) ──
    @bot.event
    async def on_member_join(member):
        script_text = prefix_manager.get_event_script("$onJoined")
        if script_text:
            try:
                from main_exe.core_bcfd.event_FDScripts.onJoined import handle_event
                await handle_event(member, bot, script_text)
            except Exception as e:
                print(f"[Bot] خطأ في تنفيذ حدث $onJoined: {e}")

    # ── 2. حدث خروج الأعضاء ($onLeave) ──
    @bot.event
    async def on_member_remove(member):
        script_text = prefix_manager.get_event_script("$onLeave")
        if script_text:
            try:
                from main_exe.core_bcfd.event_FDScripts.onLeave import handle_event
                await handle_event(member, bot, script_text)
            except Exception as e:
                print(f"[Bot] خطأ في تنفيذ حدث $onLeave: {e}")

    # ── 3. حدث معالجة الرسائل والردود الشات ──
    @bot.event
    async def on_message(message):
        # تجاهل رسائل البوتات تماماً لتجنب الحلقات اللانهائية
        if message.author.bot:
            return

        # أ. تشغيل حدث الرد الدائم ($alwaysReply) أولاً مع كل رسالة جديدة
        always_script = prefix_manager.get_event_script("$alwaysReply")
        if always_script:
            try:
                from main_exe.core_bcfd.event_FDScripts.alwaysReply import handle_event as handle_always_reply
                await handle_always_reply(message, bot, always_script)
            except Exception as e:
                print(f"[Bot] خطأ في تنفيذ حدث $alwaysReply: {e}")

        # ب. فحص الأوامر العادية المكتوبة ببادئة مخصصة وتشغيلها
        script_text = prefix_manager.get_script_by_message(message.content)
        if script_text is not None:
            try:
                await run_script(message, bot, script_text)
            except Exception as e:
                print(f"[Bot] خطأ في تنفيذ السكربت: {e}")
            return

        await bot.process_commands(message)

    return bot


# ══════════════════════════════════════════════════════════════
#  دوال تشغيل وإيقاف البوت عبر خيوط المعالجة (Threading)
# ══════════════════════════════════════════════════════════════

def _runner(token: str):
    global _loop, _client, _stopping
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    
    try:
        _loop.run_until_complete(_client.start(token))
    except Exception as e:
        print(f"[Bot] خطأ أثناء التشغيل: {e}")
    finally:
        _stopping = False
        _client = None


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

    # ربط المسارات بـ PrefixManager
    prefix_manager.set_bot_dir(bot_dir)

    bot_root = os.path.dirname(os.path.abspath(bot_dir))
    if os.path.basename(bot_root).lower() == 'bot_files':
        set_vars_dir(os.path.join(os.path.dirname(bot_root), 'bot_vars'))
    else:
        set_vars_dir(os.path.join(bot_root, 'bot_vars'))

    _client = _make_bot()
    _thread = threading.Thread(target=_runner, args=(token,), daemon=True)
    _thread.start()
    print("[Bot] تم التشغيل بنجاح")
    return True


def stop_bot() -> None:
    global _stopping
    if _stopping:
        return
    if _client is None or _client.is_closed():
        return
    _stopping = True
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_client.close(), _loop)