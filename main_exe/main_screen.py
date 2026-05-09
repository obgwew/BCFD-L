#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.metrics import dp
from config import AppConfig
from translations import Translations
from widgets import CustomButton, CustomTextInput
from local_server import start_bot, stop_bot

class MainScreen(Screen):
    """الشاشة الرئيسية"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'main'
        self.build_ui()
    
    def build_ui(self):
        """بناء واجهة المستخدم الرئيسية"""
        main_layout = BoxLayout(
            orientation='vertical', 
            padding=dp(90), 
            spacing=AppConfig.get_size('large_spacing')
        )
        
        # شريط العنوان
        title_bar = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=AppConfig.get_size('toolbar_height')
        )
        
        # العنوان
        title_label = Label(
            text=Translations.get('main_title', self.app_instance.language),
            font_size=AppConfig.get_size('large_title_font_size'),
            color=AppConfig.get_color('text_primary'),
            halign='center'
        )
        title_bar.add_widget(title_label)
        
        main_layout.add_widget(title_bar)
        
        # منطقة إدخال توكن البوت
        token_layout = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=AppConfig.get_size('toolbar_height')
        )
        
        self.token_input = CustomTextInput(
            hint_text=Translations.get('enter_token', self.app_instance.language),
            text=self.app_instance.data_manager.config.get('bot_token', ''),
            size_hint_x=0.7
        )
        self.token_input.bind(text=self.on_token_change) 
        
        token_btn = CustomButton(
            text=Translations.get('bot_token', self.app_instance.language),
            size_hint_x=0.3
        )
        
        token_layout.add_widget(self.token_input)
        token_layout.add_widget(token_btn)
        main_layout.add_widget(token_layout)
        
        # حالة السيرفر
        server_layout = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=AppConfig.get_size('toolbar_height')
        )
        
        self.server_status_label = Label(
            text=f"{Translations.get('server_status', self.app_instance.language)}: {Translations.get('stopped', self.app_instance.language)}",
            color=AppConfig.get_color('danger')
        )
        
        self.server_btn = CustomButton(
            text=Translations.get('start_server', self.app_instance.language),
            size_hint_x=0.5
        )
        self.server_btn.bind(on_press=self.toggle_server)
        
        server_layout.add_widget(self.server_status_label)
        server_layout.add_widget(self.server_btn)
        main_layout.add_widget(server_layout)
        
        # أزرار التنقل الرئيسية
        nav_layout = GridLayout(
            cols=2, 
            spacing=AppConfig.get_size('large_spacing'), 
            size_hint_y=None, 
            height=dp(120)
        )
        
        files_btn = CustomButton(text=Translations.get('files_list', self.app_instance.language))
        files_btn.bind(on_press=lambda x: self.app_instance.switch_screen('files'))
        
        variables_btn = CustomButton(text=Translations.get('variables', self.app_instance.language))
        variables_btn.bind(on_press=lambda x: self.app_instance.switch_screen('variables'))
        
        nav_layout.add_widget(files_btn)
        nav_layout.add_widget(variables_btn)
        main_layout.add_widget(nav_layout)
        
        # زر الإضافة العائم
        float_layout = FloatLayout()
        
        add_btn = Button(
            text='+',
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            pos_hint={'center_x': 0.5, 'y': 0.05},
            background_color=AppConfig.get_color('success'),
            font_size=dp(30),
            background_normal=''
        )
        add_btn.bind(on_press=self.create_new_file)
        
        float_layout.add_widget(main_layout)
        float_layout.add_widget(add_btn)
        
        self.add_widget(float_layout)
    
    def on_token_change(self, instance, text):
        """عند تغيير توكن البوت"""
        self.app_instance.data_manager.config['bot_token'] = text
        self.app_instance.data_manager.save_config()
        
        # حفظ التوكن في ملف منفصل
        try:
            with open("bot_token.txt", "w", encoding="utf-8") as f:
                f.write(text.strip())
        except Exception as e:
            print(f"خطأ في حفظ التوكن: {e}")
    
    def toggle_server(self, instance):
        """تبديل حالة السيرفر"""
        running = self.app_instance.data_manager.config.get('server_running', False)
        if running:
            self.stop_server(instance)
        else:
            self.start_server(instance)
    
    def start_server(self, instance):
        """تستدعى عند الضغط على زر تشغيل البوت"""
        # تحديث الحالة في Config وUI
        self.app_instance.data_manager.config['server_running'] = True
        self.app_instance.data_manager.save_config()
        
        self.server_status_label.text = (
            f"{Translations.get('server_status', self.app_instance.language)}: "
            f"{Translations.get('running', self.app_instance.language)}"
        )
        self.server_status_label.color = AppConfig.get_color('success')
        self.server_btn.text = Translations.get('stop_server', self.app_instance.language)

        # استدعاء دالة تشغيل البوت
        try:
            from local_server import start_bot
            start_bot()
        except ImportError:
            print("local_server module not found")

    def stop_server(self, instance):
        """تستدعى عند الضغط على زر إيقاف البوت"""
        # تحديث الحالة في Config وUI
        self.app_instance.data_manager.config['server_running'] = False
        self.app_instance.data_manager.save_config()
        
        self.server_status_label.text = (
            f"{Translations.get('server_status', self.app_instance.language)}: "
            f"{Translations.get('stopped', self.app_instance.language)}"
        )
        self.server_status_label.color = AppConfig.get_color('danger')
        self.server_btn.text = Translations.get('start_server', self.app_instance.language)

        # استدعاء دالة إيقاف البوت
        try:
            from local_server import stop_bot
            stop_bot()
        except ImportError:
            print("local_server module not found")
    
    def create_new_file(self, instance):
        """إنشاء ملف جديد"""
        self.app_instance.switch_screen('editor')
    
    def refresh_ui(self):
        """تحديث واجهة المستخدم"""
        self.clear_widgets()
        self.build_ui()