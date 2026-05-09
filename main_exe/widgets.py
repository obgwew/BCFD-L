#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from config import AppConfig
from translations import Translations

class CustomButton(Button):
    """زر مخصص مع تصميم محسن"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = AppConfig.get_color('primary')
        self.color = AppConfig.get_color('white')
        self.font_size = AppConfig.get_size('font_size')
        self.size_hint_y = None
        self.height = AppConfig.get_size('button_height')

class CustomTextInput(TextInput):
    """حقل نص مخصص"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = AppConfig.get_color('input_bg')
        self.foreground_color = AppConfig.get_color('text_primary')
        self.cursor_color = AppConfig.get_color('primary')
        self.font_size = AppConfig.get_size('font_size')
        self.multiline = kwargs.get('multiline', False)
        if not self.multiline:
            self.size_hint_y = None
            self.height = AppConfig.get_size('input_height')

class CodeEditor(TextInput):
    """محرر الأكواد مع أرقام الأسطر"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = True
        self.background_color = AppConfig.get_color('editor_bg')
        self.foreground_color = AppConfig.get_color('editor_text')
        self.cursor_color = AppConfig.get_color('primary')
        self.font_size = AppConfig.get_size('editor_font_size')
        self.padding = [AppConfig.get_size('padding'), AppConfig.get_size('padding')]
        
        # ربط الأحداث
        self.bind(text=self.on_text_change)
    
    def on_text_change(self, instance, text):
        """تحديث أرقام الأسطر عند تغيير النص"""
        pass  # يمكن إضافة منطق أرقام الأسطر هنا

class PrefixEditPopup(Popup):
    """نافذة منبثقة لتعديل البادئة"""
    
    def __init__(self, app_instance, filename, current_prefix='', callback=None, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.filename = filename
        self.callback = callback
        
        self.title = Translations.get('edit_prefix', app_instance.language)
        self.size_hint = (0.8, 0.4)
        self.auto_dismiss = True
        
        # بناء المحتوى
        content_layout = BoxLayout(
            orientation='vertical', 
            padding=AppConfig.get_size('xl_spacing'), 
            spacing=AppConfig.get_size('large_spacing')
        )
        
        # عنوان
        title_label = Label(
            text=f"{Translations.get('file_prefix', app_instance.language)}: {filename}",
            size_hint_y=None,
            height=dp(40),
            color=AppConfig.get_color('text_primary')
        )
        content_layout.add_widget(title_label)
        
        # حقل إدخال البادئة
        self.prefix_input = CustomTextInput(
            text=current_prefix,
            hint_text=Translations.get('enter_prefix', app_instance.language),
            size_hint_y=None,
            height=AppConfig.get_size('input_height')
        )
        content_layout.add_widget(self.prefix_input)
        
        # أزرار التحكم
        buttons_layout = BoxLayout(
            orientation='horizontal', 
            spacing=AppConfig.get_size('padding'), 
            size_hint_y=None, 
            height=AppConfig.get_size('button_height')
        )
        
        cancel_btn = CustomButton(
            text=Translations.get('cancel', app_instance.language),
            background_color=AppConfig.get_color('secondary')
        )
        cancel_btn.bind(on_press=self.dismiss)
        
        save_btn = CustomButton(
            text=Translations.get('save', app_instance.language),
            background_color=AppConfig.get_color('success')
        )
        save_btn.bind(on_press=self.save_prefix)
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(save_btn)
        content_layout.add_widget(buttons_layout)
        
        self.content = content_layout
    
    def save_prefix(self, instance):
        """حفظ البادئة"""
        prefix = self.prefix_input.text.strip()
        self.app_instance.data_manager.set_file_prefix(self.filename, prefix)
        
        if self.callback:
            self.callback()
        
        # عرض رسالة نجاح
        self.show_success_message()
        self.dismiss()
    
    def show_success_message(self):
        """عرض رسالة نجاح"""
        success_layout = BoxLayout(
            orientation='vertical', 
            padding=AppConfig.get_size('xl_spacing'), 
            spacing=AppConfig.get_size('large_spacing')
        )
        
        message_label = Label(
            text=Translations.get('prefix_updated', self.app_instance.language),
            color=AppConfig.get_color('success')
        )
        success_layout.add_widget(message_label)
        
        ok_btn = CustomButton(text=Translations.get('confirm', self.app_instance.language))
        success_layout.add_widget(ok_btn)
        
        success_popup = Popup(
            title=Translations.get('success', self.app_instance.language),
            content=success_layout,
            size_hint=(0.6, 0.3),
            auto_dismiss=True
        )
        
        ok_btn.bind(on_press=success_popup.dismiss)
        success_popup.open()

class PopupHelper:
    """مساعد لإنشاء النوافذ المنبثقة"""
    
    @staticmethod
    def show_popup(title, message, language='en'):
        """عرض رسالة منبثقة"""
        popup_layout = BoxLayout(
            orientation='vertical', 
            padding=AppConfig.get_size('xl_spacing'), 
            spacing=AppConfig.get_size('xl_spacing')
        )
        
        popup_layout.add_widget(Label(
            text=message, 
            text_size=(dp(300), None), 
            halign='center'
        ))
        
        close_btn = CustomButton(text=Translations.get('confirm', language))
        popup_layout.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=popup_layout,
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
