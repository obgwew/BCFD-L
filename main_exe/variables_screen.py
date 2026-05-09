#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from config import AppConfig
from translations import Translations
from widgets import CustomButton, CustomTextInput, PopupHelper
from kivy.metrics import dp

class VariablesScreen(Screen):
    """شاشة إدارة المتغيرات"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'variables'
        self.build_ui()
    
    def build_ui(self):
        """بناء واجهة إدارة المتغيرات"""
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
            text=Translations.get('variables', self.app_instance.language),
            font_size=AppConfig.get_size('title_font_size'),
            color=AppConfig.get_color('text_primary')
        )
        
        toolbar.add_widget(back_btn)
        toolbar.add_widget(title_label)
        
        layout.add_widget(toolbar)
        
        # منطقة إضافة متغير جديد
        add_var_layout = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            height=dp(140), 
            spacing=AppConfig.get_size('padding')
        )
        
        var_inputs_layout = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=AppConfig.get_size('toolbar_height')
        )
        
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
            height=AppConfig.get_size('button_height'),
            background_color=AppConfig.get_color('success')
        )
        add_btn.bind(on_press=self.add_variable)
        
        add_var_layout.add_widget(var_inputs_layout)
        add_var_layout.add_widget(add_btn)
        
        layout.add_widget(add_var_layout)
        
        # قائمة المتغيرات
        scroll = ScrollView()
        self.variables_layout = GridLayout(
            cols=1, 
            spacing=AppConfig.get_size('padding'), 
            size_hint_y=None
        )
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
            PopupHelper.show_popup(
                Translations.get('error', self.app_instance.language), 
                Translations.get('enter_variable_name', self.app_instance.language),
                self.app_instance.language
            )
            return
        
        self.app_instance.data_manager.variables[name] = value
        self.app_instance.data_manager.save_variables()
        
        # مسح الحقول
        self.var_name_input.text = ''
        self.var_value_input.text = ''
        
        # تحديث القائمة
        self.refresh_variables_list()
        
        PopupHelper.show_popup(
            Translations.get('success', self.app_instance.language), 
            Translations.get('variable_added', self.app_instance.language),
            self.app_instance.language
        )
    
    def refresh_variables_list(self):
        """تحديث قائمة المتغيرات"""
        self.variables_layout.clear_widgets()
        
        variables = self.app_instance.data_manager.variables
        
        if not variables:
            no_vars_label = Label(
                text=Translations.get('no_variables', self.app_instance.language),
                color=AppConfig.get_color('text_muted'),
                size_hint_y=None,
                height=AppConfig.get_size('button_height')
            )
            self.variables_layout.add_widget(no_vars_label)
        else:
            for name, value in variables.items():
                var_layout = BoxLayout(
                    orientation='horizontal', 
                    size_hint_y=None, 
                    height=AppConfig.get_size('toolbar_height')
                )
                
                name_label = Label(
                    text=f"{name}:",
                    color=AppConfig.get_color('text_primary'),
                    size_hint_x=0.3,
                    text_size=(None, None),
                    halign='left'
                )
                
                value_label = Label(
                    text=str(value),
                    color=AppConfig.get_color('text_secondary'),
                    text_size=(None, None),
                    halign='left'
                )
                
                delete_btn = CustomButton(
                    text=Translations.get('delete', self.app_instance.language),
                    size_hint_x=0.2,
                    background_color=AppConfig.get_color('danger')
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
