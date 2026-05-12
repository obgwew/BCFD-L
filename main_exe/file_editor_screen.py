#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from main_exe.config import AppConfig
from main_exe.translations import Translations
from main_exe.widgets import CustomButton, CustomTextInput, CodeEditor, PopupHelper

class FileEditorScreen(Screen):
    """شاشة محرر الملفات المحدثة"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'editor'
        self.current_file = None
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(
            orientation='vertical', 
            padding=AppConfig.get_size('padding'), 
            spacing=AppConfig.get_size('padding')
        )
        
        toolbar = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=AppConfig.get_size('toolbar_height')
        )
        
        back_btn = CustomButton(
            text=Translations.get('back', self.app_instance.language),
            size_hint_x=0.15
        )
        back_btn.bind(on_press=lambda x: self.app_instance.switch_screen('main'))
        
        self.filename_input = CustomTextInput(
            hint_text=Translations.get('enter_file_name', self.app_instance.language),
            size_hint_x=0.35
        )
        
        self.prefix_input = CustomTextInput(
            hint_text=Translations.get('enter_prefix', self.app_instance.language),
            size_hint_x=0.2
        )
        
        template_btn = CustomButton(
            text="FD Template",
            size_hint_x=0.15,
            background_color=AppConfig.get_color('info')
        )
        template_btn.bind(on_press=self.insert_template)
        
        run_btn = CustomButton(
            text=Translations.get('run', self.app_instance.language),
            size_hint_x=0.15,
            background_color=AppConfig.get_color('success')
        )
        run_btn.bind(on_press=self.save_and_run)
        
        toolbar.add_widget(back_btn)
        toolbar.add_widget(self.filename_input)
        toolbar.add_widget(self.prefix_input)
        toolbar.add_widget(template_btn)
        toolbar.add_widget(run_btn)
        
        layout.add_widget(toolbar)
        
        editor_layout = BoxLayout(orientation='horizontal')
        self.line_numbers = Label(
            text='1\n',
            size_hint_x=None,
            width=AppConfig.get_size('line_numbers_width'),
            halign='right',
            valign='top',
            color=AppConfig.get_color('text_muted')
        )
        
        self.code_editor = CodeEditor()
        self.code_editor.bind(text=self.update_line_numbers)
        
        editor_layout.add_widget(self.line_numbers)
        editor_layout.add_widget(self.code_editor)
        layout.add_widget(editor_layout)
        self.add_widget(layout)
    
    def insert_template(self, instance):
        template = '''# مثال على FDScript المطور
$var[name; $authorName]
$sendMessage[أهلاً بك $var[name] في الخادم!]
$if[$authorID == 123456789]
  $sendMessage[أنت المطور الخاص بي!]
$endif'''
        return template


    def update_line_numbers(self, instance, text):
        lines = text.split('\n')
        self.line_numbers.text = '\n'.join(str(i) for i in range(1, len(lines) + 1))
    
    def save_and_run(self, instance):
        filename = self.filename_input.text.strip()
        if not filename: return
        
        if not filename.endswith('.py'): filename += '.py'
        
        user_content = self.code_editor.text.strip()
        prefix = self.prefix_input.text.strip()
        
        try:
            if prefix:
                self.app_instance.data_manager.set_file_prefix(filename, prefix)
            
            self.app_instance.data_manager.save_file(filename, user_content)
            
            # حفظ التوكن
            bot_token = self.app_instance.data_manager.config.get('bot_token', '')
            if bot_token:
                with open("bot_token.txt", "w", encoding="utf-8") as f:
                    f.write(bot_token)
            
            PopupHelper.show_popup(
                Translations.get('success', self.app_instance.language), 
                f"تم حفظ الملف: {filename}",
                self.app_instance.language
            )
            Clock.schedule_once(lambda dt: self.app_instance.switch_screen('main'), 2)
            
        except Exception as e:
            PopupHelper.show_popup("Error", str(e), self.app_instance.language)
    
    def load_file(self, filename):
        self.current_file = filename
        self.filename_input.text = filename
        self.prefix_input.text = self.app_instance.data_manager.get_file_prefix(filename)
        self.code_editor.text = self.app_instance.data_manager.load_file(filename)
