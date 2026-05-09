# python "c:\coding\BCBD\main.py"
# -*- coding: utf-8 -*-

import os
import json
import threading
import re  
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
import kivy.uix.textinput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.actionbar import ActionBar, ActionView, ActionPrevious, ActionButton
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.clock import Clock
import main_exe.local_server 
import logging
logging.getLogger('discord').setLevel(logging.INFO)
# … بقية الاستيرادات …


class Translations:
    """إدارة الترجمات للتطبيق"""
    
    translations = {
        'ar': {
            'main_title': 'إدارة الملفات والبوتات',
            'create_file': 'إنشاء ملف جديد',
            'bot_token': 'توكن البوت',
            'start_server': 'تشغيل السيرفر المحلي',
            'stop_server': 'إيقاف السيرفر',
            'files_list': 'قائمة الملفات',
            'variables': 'المتغيرات',
            'settings': 'الإعدادات',
            'back': 'رجوع',
            'save': 'حفظ',
            'run': 'تشغيل',
            'file_name': 'اسم الملف',
            'file_content': 'محتوى الملف',
            'variable_name': 'اسم المتغير',
            'variable_value': 'قيمة المتغير',
            'add_variable': 'إضافة متغير',
            'no_files': 'لا توجد ملفات',
            'no_variables': 'لا توجد متغيرات',
            'enter_token': 'أدخل توكن البوت',
            'server_status': 'حالة السيرفر',
            'running': 'يعمل',
            'stopped': 'متوقف',
            'edit': 'تعديل',
            'delete': 'حذف',
            'new_file': 'ملف جديد',
            'language': 'اللغة',
            'arabic': 'العربية',
            'english': 'English',
            'confirm': 'تأكيد',
            'cancel': 'إلغاء',
            'success': 'تم بنجاح',
            'error': 'خطأ',
            'file_saved': 'تم حفظ الملف',
            'variable_added': 'تم إضافة المتغير',
            'enter_file_name': 'أدخل اسم الملف',
            'enter_variable_name': 'أدخل اسم المتغير',
            'file_prefix': 'بادئة الملف',
            'enter_prefix': 'أدخل البادئة (مثل: !test)',
            'prefix': 'البادئة',
            'edit_prefix': 'تعديل البادئة',
            'prefix_updated': 'تم تحديث البادئة'
        },
        'en': {
            'main_title': 'BCFD',
            'create_file': 'Create New File',
            'bot_token': 'Bot Token',
            'start_server': 'Run Server',
            'stop_server': 'Stop Server',
            'files_list': 'Files List',
            'variables': 'Variables',
            'settings': 'Settings',
            'back': 'Back',
            'save': 'Save',
            'run': 'Save & out',
            'file_name': 'File Name',
            'file_content': 'File Content',
            'variable_name': 'Variable Name',
            'variable_value': 'Variable Value',
            'add_variable': 'Add Variable',
            'no_files': 'No Files',
            'no_variables': 'No Variables',
            'enter_token': 'Enter Bot Token',
            'server_status': 'Server Status',
            'running': 'Running',
            'stopped': 'Stopped',
            'edit': 'Edit',
            'delete': 'Delete',
            'new_file': 'New File',
            'language': 'Language',
            'arabic': 'ar',
            'english': 'English',
            'confirm': 'Confirm',
            'cancel': 'Cancel',
            'success': 'Success',
            'error': 'Error',
            'file_saved': 'File Saved',
            'variable_added': 'Variable Added',
            'enter_file_name': 'Enter File Name',
            'enter_variable_name': 'Enter Variable Name',
            'file_prefix': 'File Prefix',
            'enter_prefix': 'Enter prefix (e.g: !test)',
            'prefix': 'Prefix',
            'edit_prefix': 'Edit Prefix',
            'prefix_updated': 'Prefix Updated'
        }
    }
    
    @staticmethod
    def get(key, lang='en'):
        return Translations.translations.get(lang, {}).get(key, key)


class DataManager:
    """إدارة البيانات والملفات"""
    
    def __init__(self):
        self.data_dir = "app_data"
        self.files_dir = os.path.join(self.data_dir, "files")
        self.config_file = os.path.join(self.data_dir, "config.json")
        self.variables_file = os.path.join(self.data_dir, "variables.json")
        self.prefixes_file = os.path.join(self.data_dir, "prefixes.json")
        
        # إنشاء المجلدات إذا لم تكن موجودة
        os.makedirs(self.files_dir, exist_ok=True)
        
        self.config = self.load_config()
        self.variables = self.load_variables()
        self.prefixes = self.load_prefixes()
    
    def load_config(self):
        """تحميل إعدادات التطبيق"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'language': 'en',
            'bot_token': '',
            'server_running': False
        }
    
    def save_config(self):
        """حفظ إعدادات التطبيق"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def load_variables(self):
        """تحميل المتغيرات"""
        if os.path.exists(self.variables_file):
            try:
                with open(self.variables_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_variables(self):
        """حفظ المتغيرات"""
        with open(self.variables_file, 'w', encoding='utf-8') as f:
            json.dump(self.variables, f, ensure_ascii=False, indent=2)
    
    def load_prefixes(self):
        """تحميل البادئات المخصصة للملفات"""
        if os.path.exists(self.prefixes_file):
            try:
                with open(self.prefixes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_prefixes(self):
        """حفظ البادئات المخصصة للملفات"""
        try:
            # التأكد من وجود المجلد
            os.makedirs(os.path.dirname(self.prefixes_file), exist_ok=True)
            
            with open(self.prefixes_file, 'w', encoding='utf-8') as f:
                json.dump(self.prefixes, f, ensure_ascii=False, indent=2)
            print(f"تم حفظ البادئات في: {self.prefixes_file}")
            return True
        except Exception as e:
            print(f"خطأ في حفظ البادئات: {e}")
            return False
    
    def set_file_prefix(self, filename, prefix):
        """تعيين بادئة مخصصة لملف"""
        try:
            self.prefixes[filename] = prefix.strip()
            self.save_prefixes()
            print(f"تم حفظ البادئة '{prefix}' للملف '{filename}'")
            return True
        except Exception as e:
            print(f"خطأ في حفظ البادئة: {e}")
            return False
    
    def get_file_prefix(self, filename):
        """الحصول على بادئة الملف"""
        return self.prefixes.get(filename, '')
    
    def save_file(self, filename, content):
        """حفظ ملف"""
        try:
            filepath = os.path.join(self.files_dir, filename)
            print(f"محاولة حفظ الملف في: {filepath}")
            
            # التأكد من وجود المجلد
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"تم حفظ الملف بنجاح: {filepath}")
            return True
        except Exception as e:
            print(f"خطأ في حفظ الملف: {e}")
            return False
    
    def load_file(self, filename):
        """تحميل ملف"""
        filepath = os.path.join(self.files_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def get_file_list(self):
        """الحصول على قائمة الملفات"""
        if os.path.exists(self.files_dir):
            return [f for f in os.listdir(self.files_dir) if os.path.isfile(os.path.join(self.files_dir, f))]
        return []
    
    def delete_file(self, filename):
        """حذف ملف وبادئته"""
        filepath = os.path.join(self.files_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # حذف البادئة المرتبطة بالملف
        if filename in self.prefixes:
            del self.prefixes[filename]
            self.save_prefixes()


class CustomButton(Button):
    """زر مخصص مع تصميم محسن"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = get_color_from_hex('#4A90E2')
        self.color = get_color_from_hex('#FFFFFF')
        self.font_size = dp(16)
        self.size_hint_y = None
        self.height = dp(50)


class CustomTextInput(kivy.uix.textinput.TextInput):
    """حقل نص مخصص"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = get_color_from_hex('#F8F9FA')
        self.foreground_color = get_color_from_hex('#2C3E50')
        self.cursor_color = get_color_from_hex('#4A90E2')
        self.font_size = dp(16)
        self.multiline = kwargs.get('multiline', False)
        if not self.multiline:
            self.size_hint_y = None
            self.height = dp(50)


class CodeEditor(kivy.uix.textinput.TextInput):
    """محرر الأكواد مع أرقام الأسطر"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = True
        self.background_color = get_color_from_hex('#2C3E50')
        self.foreground_color = get_color_from_hex('#ECF0F1')
        self.cursor_color = get_color_from_hex('#4A90E2')
        self.font_size = dp(14)
        self.padding = [dp(10), dp(10)]
        
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
        content_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # عنوان
        title_label = Label(
            text=f"{Translations.get('file_prefix', app_instance.language)}: {filename}",
            size_hint_y=None,
            height=dp(40),
            color=get_color_from_hex('#2C3E50')
        )
        content_layout.add_widget(title_label)
        #Add
        # حقل إدخال البادئة
        self.prefix_input = CustomTextInput(
            text=current_prefix,
            hint_text=Translations.get('enter_prefix', app_instance.language),
            size_hint_y=None,
            height=dp(50)
        )
        content_layout.add_widget(self.prefix_input)
        
        # أزرار التحكم
        buttons_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        
        cancel_btn = CustomButton(
            text=Translations.get('cancel', app_instance.language),
            background_color=get_color_from_hex('#95A5A6')
        )
        cancel_btn.bind(on_press=self.dismiss)
        
        save_btn = CustomButton(
            text=Translations.get('save', app_instance.language),
            background_color=get_color_from_hex('#27AE60')
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
        success_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        message_label = Label(
            text=Translations.get('prefix_updated', self.app_instance.language),
            color=get_color_from_hex('#27AE60')
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


class MainScreen(Screen):
    """الشاشة الرئيسية"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'main'
        self.build_ui()
    
    def build_ui(self):
        """بناء واجهة المستخدم الرئيسية"""
        main_layout = BoxLayout(orientation='vertical', padding=dp(90), spacing=dp(15))
        
        # شريط العنوان
        title_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
        # العنوان
        title_label = Label(
            text=Translations.get('main_title', self.app_instance.language),
            font_size=dp(24),
            color=get_color_from_hex('#2C3E50'),
            halign='center'
        )
        title_bar.add_widget(title_label)
        
        main_layout.add_widget(title_bar)
        
        # منطقة إدخال توكن البوت
        token_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
        self.token_input = CustomTextInput(
            hint_text=Translations.get('enter_token', self.app_instance.language),
            text=self.app_instance.data_manager.config.get('bot_token', ''),
            size_hint_x=0.7
        )
        self.token_input.bind(text=self.on_token_change) 
        
        self.server_btn = CustomButton(
            text=Translations.get('start_server', self.app_instance.language),
            size_hint_x=0.5
        )
        self.server_btn.bind(on_press=self.toggle_server)

        token_btn = CustomButton(
            text=Translations.get('bot_token', self.app_instance.language),
            size_hint_x=0.3
        )
        
        token_layout.add_widget(self.token_input)
        token_layout.add_widget(token_btn)
        main_layout.add_widget(token_layout)
        
        # حالة السيرفر
        server_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
        self.server_status_label = Label(
            text=f"{Translations.get('server_status', self.app_instance.language)}: {Translations.get('stopped', self.app_instance.language)}",
            color=get_color_from_hex('#E74C3C')
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
        nav_layout = GridLayout(cols=2, spacing=dp(15), size_hint_y=None, height=dp(120))
        
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
            background_color=get_color_from_hex('#27AE60'),
            font_size=dp(30),
            background_normal=''
        )
        add_btn.bind(on_press=self.create_new_file)
        
        float_layout.add_widget(main_layout)
        float_layout.add_widget(add_btn)
        
        self.add_widget(float_layout)

    def toggle_language(self, instance):
        """تبديل اللغة"""
        self.app_instance.toggle_language()
        self.refresh_ui()
    
    def on_token_change(self, instance, text):
        """عند تغيير توكن البوت"""
        self.app_instance.data_manager.config['bot_token'] = text
        self.app_instance.data_manager.save_config()
        #print
        # حفظ التوكن في ملف منفصل
        try:
            with open("bot_token.txt", "w", encoding="utf-8") as f:
                f.write(text.strip())
        except Exception as e:
            print(f"خطأ في حفظ التوكن: {e}")

    def toggle_server(self, instance):
        running = self.app_instance.data_manager.config.get('server_running', False)
        if running:
            self.stop_server(instance)
        else:
            self.start_server(instance)

    def start_server(self, instance):
        """تُستدعى عند الضغط على زر تشغيل البوت"""
        # تحديث الحالة في Config وUI
        self.app_instance.data_manager.config['server_running'] = True
        self.app_instance.data_manager.save_config()
        self.server_status_label.text = (
            f"{Translations.get('server_status', self.app_instance.language)}: "
            f"{Translations.get('running', self.app_instance.language)}"
        )
        self.server_status_label.color = get_color_from_hex('#27AE60')
        self.server_btn.text = Translations.get('stop_server', self.app_instance.language)

        # استدعاء دالة تشغيل البوت
        main_exe.local_server.start_bot()

    def stop_server(self, instance):
        """تُستدعى عند الضغط على زر إيقاف البوت"""
        # تحديث الحالة في Config وUI
        self.app_instance.data_manager.config['server_running'] = False
        self.app_instance.data_manager.save_config()
        self.server_status_label.text = (
            f"{Translations.get('server_status', self.app_instance.language)}: "
            f"{Translations.get('stopped', self.app_instance.language)}"
        )
        self.server_status_label.color = get_color_from_hex('#E74C3C')
        self.server_btn.text = Translations.get('start_server', self.app_instance.language)

        # استدعاء دالة إيقاف البوت
        main_exe.local_server.stop_bot()

    
    def create_new_file(self, instance):
        """إنشاء ملف جديد"""
        self.app_instance.switch_screen('editor')
    
    def refresh_ui(self):
        """تحديث واجهة المستخدم"""
        self.clear_widgets()
        self.build_ui()


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
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # شريط الأدوات العلوي
        toolbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
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
            background_color=get_color_from_hex('#9B59B6')
        )
        template_btn.bind(on_press=self.insert_yellow_template)
        
        run_btn = CustomButton(
            text=Translations.get('run', self.app_instance.language),
            size_hint_x=0.15,
            background_color=get_color_from_hex('#27AE60')
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
            width=dp(50),
            halign='right',
            valign='top',
            color=get_color_from_hex('#7F8C8D')
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
- info.py with the prefix !info'''
        
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
                    # إضافة السطر كاملاً إذا وُجد أمر Y-ellow
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
            self.show_popup(Translations.get('error', self.app_instance.language), 
                           Translations.get('enter_file_name', self.app_instance.language))
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
            
            self.show_popup(Translations.get('success', self.app_instance.language), success_message)
            print("تم عرض رسالة النجاح")
            
            # العودة للشاشة الرئيسية بعد ثانيتين
            Clock.schedule_once(lambda dt: self.app_instance.switch_screen('main'), 2)
            
        except Exception as e:
            error_message = f"خطأ في الحفظ: {str(e)}"
            print(error_message)
            self.show_popup(Translations.get('error', self.app_instance.language), error_message)
    
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
    
    def show_popup(self, title, message):
        """عرض رسالة منبثقة"""
        popup_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        popup_layout.add_widget(Label(text=message, text_size=(dp(300), None), halign='center'))
        
        close_btn = CustomButton(text=Translations.get('confirm', self.app_instance.language))
        popup_layout.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=popup_layout,
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class FilesListScreen(Screen):
    """شاشة قائمة الملفات"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'files'
        self.build_ui()
    
    def build_ui(self):
        """بناء واجهة قائمة الملفات"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # شريط الأدوات العلوي
        toolbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
        back_btn = CustomButton(
            text=Translations.get('back', self.app_instance.language),
            size_hint_x=0.3
        )
        back_btn.bind(on_press=lambda x: self.app_instance.switch_screen('main'))
        
        title_label = Label(
            text=Translations.get('files_list', self.app_instance.language),
            font_size=dp(20),
            color=get_color_from_hex('#2C3E50')
        )
        
        toolbar.add_widget(back_btn)
        toolbar.add_widget(title_label)
        
        layout.add_widget(toolbar)
        
        # قائمة الملفات
        scroll = ScrollView()
        self.files_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
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
                color=get_color_from_hex('#7F8C8D'),
                size_hint_y=None,
                height=dp(50)
            )
            self.files_layout.add_widget(no_files_label)
        else:
            for filename in files:
                file_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), spacing=dp(5))
                
                # الصف الأول: اسم الملف والأزرار
                first_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
                
                file_label = Label(
                    text=filename,
                    color=get_color_from_hex('#2C3E50'),
                    text_size=(None, None),
                    halign='left',
                    font_size=dp(16)
                )
                                
                edit_btn = CustomButton(
                    text=Translations.get('edit', self.app_instance.language),
                    size_hint_x=0.15,
                    background_color=get_color_from_hex('#F39C12')
                )
                edit_btn.bind(on_press=lambda x, f=filename: self.edit_file(f))
                
                delete_btn = CustomButton(
                    text=Translations.get('delete', self.app_instance.language),
                    size_hint_x=0.15,
                    background_color=get_color_from_hex('#E74C3C')
                )
                delete_btn.bind(on_press=lambda x, f=filename: self.delete_file(f))
                
                first_row.add_widget(file_label)
                first_row.add_widget(edit_btn)
                first_row.add_widget(delete_btn)
                
                # الصف الثاني: البادئة وزر التعديل
                second_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
                
                prefix = self.app_instance.data_manager.get_file_prefix(filename)
                prefix_text = f"{Translations.get('prefix', self.app_instance.language)}: {prefix}" if prefix else f"{Translations.get('prefix', self.app_instance.language)}: {Translations.get('no_files', self.app_instance.language).lower()}"
                
                prefix_label = Label(
                    text=prefix_text,
                    color=get_color_from_hex('#7F8C8D') if not prefix else get_color_from_hex('#27AE60'),
                    text_size=(None, None),
                    halign='left',
                    font_size=dp(14)
                )
                
                prefix_edit_btn = CustomButton(
                    text=Translations.get('edit_prefix', self.app_instance.language),
                    size_hint_x=0.3,
                    background_color=get_color_from_hex('#9B59B6'),
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
                    color=get_color_from_hex('#BDC3C7'),
                    size_hint_y=None,
                    height=dp(10)
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


class VariablesScreen(Screen):
    """شاشة إدارة المتغيرات"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'variables'
        self.build_ui()
    
    def build_ui(self):
        """بناء واجهة إدارة المتغيرات"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # شريط الأدوات العلوي
        toolbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
        back_btn = CustomButton(
            text=Translations.get('back', self.app_instance.language),
            size_hint_x=0.3
        )
        back_btn.bind(on_press=lambda x: self.app_instance.switch_screen('main'))
        
        title_label = Label(
            text=Translations.get('variables', self.app_instance.language),
            font_size=dp(20),
            color=get_color_from_hex('#2C3E50')
        )
        
        toolbar.add_widget(back_btn)
        toolbar.add_widget(title_label)
        
        layout.add_widget(toolbar)
        
        # منطقة إضافة متغير جديد
        add_var_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(140), spacing=dp(10))
        
        var_inputs_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
        self.var_name_input = CustomTextInput(
            hint_text=Translations.get('variable_name', self.app_instance.language),
            size_hint_x=0.5
        )
        
        self.var_value_input = CustomTextInput(
            hint_text=Translations.get('variable_value', self.app_instance.language),
            size_hint_x=0.5
        )
        
        var_inputs_layout.add_widget(self.var_name_input)
        var_inputs_layout.add_widget(self.var_value_input)
        
        add_btn = CustomButton(
            text=Translations.get('add_variable', self.app_instance.language),
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#27AE60')
        )
        add_btn.bind(on_press=self.add_variable)
        
        add_var_layout.add_widget(var_inputs_layout)
        add_var_layout.add_widget(add_btn)
        
        layout.add_widget(add_var_layout)
        
        # قائمة المتغيرات
        scroll = ScrollView()
        self.variables_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.variables_layout.bind(minimum_height=self.variables_layout.setter('height'))
        
        scroll.add_widget(self.variables_layout)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        
        # تحميل قائمة المتغيرات
        self.refresh_variables_list()
    
    def add_variable(self, instance):
        """إضافة متغير جديد"""
        name = self.var_name_input.text.strip()
        value = self.var_value_input.text.strip()
        
        if not name:
            self.show_popup(Translations.get('error', self.app_instance.language), 
                           Translations.get('enter_variable_name', self.app_instance.language))
            return
        
        self.app_instance.data_manager.variables[name] = value
        self.app_instance.data_manager.save_variables()
        
        # مسح الحقول
        self.var_name_input.text = ''
        self.var_value_input.text = ''
        
        # تحديث القائمة
        self.refresh_variables_list()
        
        self.show_popup(Translations.get('success', self.app_instance.language), 
                       Translations.get('variable_added', self.app_instance.language))
    
    def refresh_variables_list(self):
        """تحديث قائمة المتغيرات"""
        self.variables_layout.clear_widgets()
        
        variables = self.app_instance.data_manager.variables
        
        if not variables:
            no_vars_label = Label(
                text=Translations.get('no_variables', self.app_instance.language),
                color=get_color_from_hex('#7F8C8D'),
                size_hint_y=None,
                height=dp(50)
            )
            self.variables_layout.add_widget(no_vars_label)
        else:
            for name, value in variables.items():
                var_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
                
                name_label = Label(
                    text=f"{name}:",
                    color=get_color_from_hex('#2C3E50'),
                    size_hint_x=0.3,
                    text_size=(None, None),
                    halign='left'
                )
                
                value_label = Label(
                    text=str(value),
                    color=get_color_from_hex('#34495E'),
                    text_size=(None, None),
                    halign='left'
                )
                
                delete_btn = CustomButton(
                    text=Translations.get('delete', self.app_instance.language),
                    size_hint_x=0.2,
                    background_color=get_color_from_hex('#E74C3C')
                )
                delete_btn.bind(on_press=lambda x, n=name: self.delete_variable(n))
                
                var_layout.add_widget(name_label)
                var_layout.add_widget(value_label)
                var_layout.add_widget(delete_btn)
                
                self.variables_layout.add_widget(var_layout)
    
    def delete_variable(self, name):
        """حذف متغير"""
        if name in self.app_instance.data_manager.variables:
            del self.app_instance.data_manager.variables[name]
            self.app_instance.data_manager.save_variables()
            self.refresh_variables_list()
    
    def show_popup(self, title, message):
        """عرض رسالة منبثقة"""
        popup_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        popup_layout.add_widget(Label(text=message, text_size=(dp(300), None), halign='center'))
        
        close_btn = CustomButton(text=Translations.get('confirm', self.app_instance.language))
        popup_layout.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=popup_layout,
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class BilingualApp(App):
    """التطبيق الرئيسي"""
    
    def build(self):
        """بناء التطبيق"""
        # تعيين لون الخلفية
        Window.clearcolor = get_color_from_hex('#ECF0F1')
        
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
    #MainScreen.build_ui
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
    
#toggle_server
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
    