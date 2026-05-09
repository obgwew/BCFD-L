#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.metrics import dp
from config import AppConfig
from translations import Translations
from widgets import CustomButton, PrefixEditPopup

class FilesListScreen(Screen):
    """شاشة قائمة الملفات"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'files'
        self.build_ui()
    
    def build_ui(self):
        """بناء واجهة قائمة الملفات"""
        layout = BoxLayout(
            orientation='vertical', 
            padding=AppConfig.get_size('padding'), 
            spacing=AppConfig.get_size('padding')
        )
        
        # شريط الأدوات العلوي
        toolbar = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=AppConfig.get_size('toolbar_height')
        )
        
        back_btn = CustomButton(
            text=Translations.get('back', self.app_instance.language),
            size_hint_x=0.3
        )
        back_btn.bind(on_press=lambda x: self.app_instance.switch_screen('main'))
        
        title_label = Label(
            text=Translations.get('files_list', self.app_instance.language),
            font_size=AppConfig.get_size('title_font_size'),
            color=AppConfig.get_color('text_primary')
        )
        
        toolbar.add_widget(back_btn)
        toolbar.add_widget(title_label)
        
        layout.add_widget(toolbar)
        
        # قائمة الملفات
        scroll = ScrollView()
        self.files_layout = GridLayout(
            cols=1, 
            spacing=AppConfig.get_size('padding'), 
            size_hint_y=None
        )
        self.files_layout.bind(minimum_height=self.files_layout.setter('height'))
        
        scroll.add_widget(self.files_layout)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        
        # تحميل قائمة الملفات
        self.refresh_files_list()
    
    def refresh_files_list(self):
        """تحديث قائمة الملفات"""
        self.files_layout.clear_widgets()
        
        files = self.app_instance.data_manager.get_file_list()
        
        if not files:
            no_files_label = Label(
                text=Translations.get('no_files', self.app_instance.language),
                color=AppConfig.get_color('text_muted'),
                size_hint_y=None,
                height=AppConfig.get_size('button_height')
            )
            self.files_layout.add_widget(no_files_label)
        else:
            for filename in files:
                file_layout = BoxLayout(
                    orientation='vertical', 
                    size_hint_y=None, 
                    height=dp(120), 
                    spacing=dp(5)
                )
                
                # الصف الأول: اسم الملف والأزرار
                first_row = BoxLayout(
                    orientation='horizontal', 
                    size_hint_y=None, 
                    height=AppConfig.get_size('toolbar_height')
                )
                
                file_label = Label(
                    text=filename,
                    color=AppConfig.get_color('text_primary'),
                    text_size=(None, None),
                    halign='left',
                    font_size=AppConfig.get_size('font_size')
                )
                                
                edit_btn = CustomButton(
                    text=Translations.get('edit', self.app_instance.language),
                    size_hint_x=0.15,
                    background_color=AppConfig.get_color('warning')
                )
                edit_btn.bind(on_press=lambda x, f=filename: self.edit_file(f))
                
                delete_btn = CustomButton(
                    text=Translations.get('delete', self.app_instance.language),
                    size_hint_x=0.15,
                    background_color=AppConfig.get_color('danger')
                )
                delete_btn.bind(on_press=lambda x, f=filename: self.delete_file(f))
                
                first_row.add_widget(file_label)
                first_row.add_widget(edit_btn)
                first_row.add_widget(delete_btn)
                
                # الصف الثاني: البادئة وزر التعديل
                second_row = BoxLayout(
                    orientation='horizontal', 
                    size_hint_y=None, 
                    height=AppConfig.get_size('button_height')
                )
                
                prefix = self.app_instance.data_manager.get_file_prefix(filename)
                prefix_text = (
                    f"{Translations.get('prefix', self.app_instance.language)}: {prefix}" 
                    if prefix 
                    else f"{Translations.get('prefix', self.app_instance.language)}: {Translations.get('no_files', self.app_instance.language).lower()}"
                )
                
                prefix_label = Label(
                    text=prefix_text,
                    color=AppConfig.get_color('text_muted') if not prefix else AppConfig.get_color('success'),
                    text_size=(None, None),
                    halign='left',
                    font_size=dp(14)
                )
                
                prefix_edit_btn = CustomButton(
                    text=Translations.get('edit_prefix', self.app_instance.language),
                    size_hint_x=0.3,
                    background_color=AppConfig.get_color('info'),
                    height=dp(40)
                )
                prefix_edit_btn.bind(on_press=lambda x, f=filename: self.edit_prefix(f))
                
                second_row.add_widget(prefix_label)
                second_row.add_widget(prefix_edit_btn)
                
                file_layout.add_widget(first_row)
                file_layout.add_widget(second_row)
                
                # إضافة خط فاصل
                separator = Label(
                    text='─' * 50,
                    color=AppConfig.get_color('separator'),
                    size_hint_y=None,
                    height=AppConfig.get_size('padding')
                )
                file_layout.add_widget(separator)
                
                self.files_layout.add_widget(file_layout)
    
    def edit_file(self, filename):
        """تعديل ملف"""
        editor_screen = self.app_instance.screen_manager.get_screen('editor')
        editor_screen.load_file(filename)
        self.app_instance.switch_screen('editor')
    
    def delete_file(self, filename):
        """حذف ملف"""
        self.app_instance.data_manager.delete_file(filename)
        self.refresh_files_list()
    
    def edit_prefix(self, filename):
        """تعديل بادئة الملف"""
        current_prefix = self.app_instance.data_manager.get_file_prefix(filename)
        popup = PrefixEditPopup(
            self.app_instance, 
            filename, 
            current_prefix, 
            callback=self.refresh_files_list
        )
        popup.open()
