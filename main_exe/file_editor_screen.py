#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.metrics import dp
from config import AppConfig
from translations import Translations
from widgets import CustomButton, CustomTextInput, CodeEditor, PopupHelper

class FileEditorScreen(Screen):
    """شاشة محرر الملفات"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'editor'
        self.current_file = None
        self.build_ui()
    
    def build_ui(self):
        """بناء واجهة المحرر"""
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
            size_hint_x=0.15
        )
        back_btn.bind(on_press=lambda x: self.app_instance.switch_screen('main'))
        
        self.filename_input = CustomTextInput(
            hint_text=Translations.get('enter_file_name', self.app_instance.language),
            size_hint_x=0.35
        )
        
        # حقل البادئة المخصصة
        self.prefix_input = CustomTextInput(
            hint_text=Translations.get('enter_prefix', self.app_instance.language),
            size_hint_x=0.2
        )
        
        # زر لإدراج template للمكتبة
        template_btn = CustomButton(
            text="Test Command's",
            size_hint_x=0.15,
            background_color=AppConfig.get_color('info')
        )
        template_btn.bind(on_press=self.insert_yellow_template)
        
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
        
        # محرر الكود
        editor_layout = BoxLayout(orientation='horizontal')
        
        # منطقة أرقام الأسطر
        self.line_numbers = Label(
            text='1\n',
            size_hint_x=None,
            width=AppConfig.get_size('line_numbers_width'),
            halign='right',
            valign='top',
            color=AppConfig.get_color('text_muted')
        )
        self.line_numbers.bind(texture_size=self.update_label_height)
        
        # محرر النص
        self.code_editor = CodeEditor()
        self.code_editor.bind(text=self.update_line_numbers)
        
        editor_layout.add_widget(self.line_numbers)
        editor_layout.add_widget(self.code_editor)
        
        layout.add_widget(editor_layout)
        
        self.add_widget(layout)
    
    def insert_yellow_template(self, instance):
        """إدراج template مكتبة Y-ellow مع أمثلة"""
        yellow_template = '''"""
- You have a file named welcome.py with the prefix !hi
File content:
sendMessage[Welcome to the server!]
reply[Hello and welcome]
- When someone types !hi in Discord:
- The bot searches for the file associated with the prefix !hi
- It finds the file welcome.py
- It executes the commands inside it
- You can create multiple files:
- moderation.py with the prefix !mod
- fun.py with the prefix !fun
- info.py with the prefix !info
"""'''
        
        # إضافة النص إلى المحرر
        current_text = self.code_editor.text
        if current_text.strip():
            self.code_editor.text = current_text + "\n\n" + yellow_template
        else:
            self.code_editor.text = yellow_template
    
    def extract_yellow_commands(self, user_content):
        """استخراج أوامر Y-ellow من محتوى المستخدم"""
        yellow_commands = []
        
        # البحث عن الأوامر المدعومة
        command_patterns = [
            r'\$?sendMessage\[([^\]]+)\]',
            r'\$?reply\[([^\]]+)\]', 
            r'\$?sendDM\[([^\]]+)\]',
            r'\$?mention\[([^\]]+)\]',
            r'\$?embed\[([^\]]+)\]',
            r'\$?log\[([^\]]+)\]',
            r'\$?wait\[([^\]]+)\]',
            r'\$?set\[([^\]]+)\]',
            r'\$?setVar\[([^\]]+)\]',
            r'\$?if\[([^\]]+)\]',
            r'\$?loop\[([^\]]+)\]',
        ]
        
        lines = user_content.split('\n')
        for line in lines:
            line = line.strip()
            # تجاهل التعليقات
            if line.startswith('#') or line.startswith('//'):
                continue
                
            # البحث عن الأوامر
            for pattern in command_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    # إضافة السطر كاملاً إذا وجد أمر Y-ellow
                    clean_line = line.lstrip('$')
                    yellow_commands.append(clean_line)
                    break
        
        return '\n'.join(yellow_commands)
    
    def get_yellow_integrated_content(self, user_content):
        """دمج محتوى المستخدم مع مكتبة Y-ellow"""
        # إرجاع المحتوى كما هو (بدون تعديل)
        # يمكنك إضافة أي معالجة إضافية هنا إذا لزم الأمر
        return user_content.strip()

    def update_line_numbers(self, instance, text):
        """تحديث أرقام الأسطر"""
        lines = text.split('\n')
        line_count = len(lines)
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.text = line_numbers_text
    
    def update_label_height(self, instance, value):
        """ضبط ارتفاع label حسب المحتوى"""
        instance.height = value[1]
        instance.text_size = (instance.width, None)
    
    def save_and_run(self, instance):
        """حفظ الملف مع البادئة المخصصة والعودة للشاشة الرئيسية"""
        filename = self.filename_input.text.strip()
        if not filename:
            PopupHelper.show_popup(
                Translations.get('error', self.app_instance.language), 
                Translations.get('enter_file_name', self.app_instance.language),
                self.app_instance.language
            )
            return
        
        # إضافة امتداد .py إذا لم يكن موجوداً
        if not filename.endswith('.py'):
            filename += '.py'
        
        user_content = self.code_editor.text.strip()
        prefix = self.prefix_input.text.strip()
        
        # التأكد من وجود محتوى للحفظ
        if not user_content:
            user_content = "# ملف فارغ\nprint('Hello World')"
        
        try:
            # حفظ البادئة المخصصة للملف
            if prefix:
                self.app_instance.data_manager.set_file_prefix(filename, prefix)
                print(f"تم حفظ البادئة: {prefix} للملف: {filename}")
            
            # معالجة المحتوى
            final_content = self.get_yellow_integrated_content(user_content)
            
            # حفظ الملف
            self.app_instance.data_manager.save_file(filename, final_content)
            print(f"تم حفظ الملف: {filename}")
            print(f"محتوى الملف: {final_content[:100]}...")
            
            # حفظ التوكن في ملف منفصل
            bot_token = self.app_instance.data_manager.config.get('bot_token', '')
            if bot_token:
                try:
                    with open("bot_token.txt", "w", encoding="utf-8") as f:
                        f.write(bot_token)
                    print("تم حفظ التوكن")
                except Exception as e:
                    print(f"خطأ في حفظ التوكن: {e}")
            
            # إعداد رسالة النجاح
            success_message = f"{Translations.get('file_saved', self.app_instance.language)}: {filename}\n"
            if prefix:
                success_message += f"{Translations.get('prefix', self.app_instance.language)}: {prefix}\n"
            success_message += "تم الحفظ بنجاح!"
            
            PopupHelper.show_popup(
                Translations.get('success', self.app_instance.language), 
                success_message,
                self.app_instance.language
            )
            print("تم عرض رسالة النجاح")
            
            # العودة للشاشة الرئيسية بعد ثانيتين
            Clock.schedule_once(lambda dt: self.app_instance.switch_screen('main'), 2)
            
        except Exception as e:
            error_message = f"خطأ في الحفظ: {str(e)}"
            print(error_message)
            PopupHelper.show_popup(
                Translations.get('error', self.app_instance.language), 
                error_message,
                self.app_instance.language
            )
    
    def load_file(self, filename):
        """تحميل ملف للتعديل"""
        self.current_file = filename
        self.filename_input.text = filename
        
        # تحميل البادئة المحفوظة
        prefix = self.app_instance.data_manager.get_file_prefix(filename)
        self.prefix_input.text = prefix
        print(f"تم تحميل البادئة: {prefix} للملف: {filename}")
        
        content = self.app_instance.data_manager.load_file(filename)
        print(f"تم تحميل الملف: {filename}, الحجم: {len(content)} حرف")
        
        # عرض المحتوى كما هو
        self.code_editor.text = content
