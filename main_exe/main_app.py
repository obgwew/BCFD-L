#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
import re  
import webbrowser
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
import logging
logging.getLogger('discord').setLevel(logging.INFO)

# استيراد الملفات المنفصلة
from config import AppConfig
from translations import Translations
from data_manager import DataManager
from main_screen import MainScreen
from file_editor_screen import FileEditorScreen
from files_list_screen import FilesListScreen
from variables_screen import VariablesScreen

# استيراد السيرفر المحلي
try:
    from local_server import start_bot, stop_bot
except ImportError:
    def start_bot():
        print("local_server module not found")
    
    def stop_bot():
        print("local_server module not found")


class BilingualApp(App):
    """التطبيق الرئيسي"""
    
    def build(self):
        """بناء التطبيق"""
        # تعيين لون الخلفية
        Window.clearcolor = AppConfig.get_color('background')
        
        # إنشاء مدير البيانات
        self.data_manager = DataManager()
        self.language = self.data_manager.config.get('language', 'en')
        
        # إنشاء مدير الشاشات
        self.screen_manager = ScreenManager()
        
        # إضافة الشاشات
        self.screen_manager.add_widget(MainScreen(self))
        self.screen_manager.add_widget(FileEditorScreen(self))
        self.screen_manager.add_widget(FilesListScreen(self))
        self.screen_manager.add_widget(VariablesScreen(self))
        
        # تعيين الشاشة الافتراضية
        self.screen_manager.current = 'main'
        
        return self.screen_manager
    
    def switch_screen(self, screen_name):
        """تبديل الشاشات"""
        self.screen_manager.current = screen_name
        
        # تحديث قائمة الملفات عند الانتقال إليها
        if screen_name == 'files':
            files_screen = self.screen_manager.get_screen('files')
            files_screen.refresh_files_list()
        elif screen_name == 'variables':
            variables_screen = self.screen_manager.get_screen('variables')
            variables_screen.refresh_variables_list()
    
    def toggle_language(self):
        """تبديل اللغة"""
        self.language = 'en' if self.language == 'ar' else 'ar'
        self.data_manager.config['language'] = self.language
        self.data_manager.save_config()
        
        # تحديث جميع الشاشات
        for screen in self.screen_manager.screens:
            if hasattr(screen, 'refresh_ui'):
                screen.refresh_ui()
    
    def on_pause(self):
        """عند إيقاف التطبيق مؤقتاً (مهم للأندرويد)"""
        return True
    
    def on_resume(self):
        """عند استئناف التطبيق"""
        pass


# ملف منفصل للإعدادات (buildozer.spec)
BUILDOZER_SPEC = '''
[app]
title = File & Bot Manager
package.name = filebotmanager
package.domain = com.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3,kivy

[buildozer]
log_level = 2

[app]
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

[buildozer]
android.arch = arm64-v8a,armeabi-v7a
'''

if __name__ == '__main__':
    # تشغيل التطبيق
    BilingualApp().run()