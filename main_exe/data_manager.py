#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json

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
