#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.utils import get_color_from_hex
from kivy.metrics import dp

class AppConfig:
    """إعدادات التطبيق العامة"""
    
    # الألوان
    COLORS = {
        'primary': '#4A90E2',
        'success': '#27AE60', 
        'warning': '#F39C12',
        'danger': '#E74C3C',
        'secondary': '#95A5A6',
        'info': '#9B59B6',
        'background': '#ECF0F1',
        'text_primary': '#2C3E50',
        'text_secondary': '#34495E',
        'text_muted': '#7F8C8D',
        'white': '#FFFFFF',
        'input_bg': '#F8F9FA',
        'editor_bg': '#2C3E50',
        'editor_text': '#ECF0F1',
        'separator': '#BDC3C7'
    }
    
    # الأحجام
    SIZES = {
        'button_height': dp(50),
        'input_height': dp(50), 
        'toolbar_height': dp(60),
        'font_size': dp(16),
        'title_font_size': dp(20),
        'large_title_font_size': dp(24),
        'editor_font_size': dp(14),
        'padding': dp(10),
        'spacing': dp(10),
        'large_spacing': dp(15),
        'xl_spacing': dp(20),
        'line_numbers_width': dp(50)
    }
    
    @classmethod
    def get_color(cls, color_name):
        """الحصول على لون بالاسم"""
        return get_color_from_hex(cls.COLORS.get(color_name, '#000000'))
    
    @classmethod
    def get_size(cls, size_name):
        """الحصول على حجم بالاسم"""
        return cls.SIZES.get(size_name, dp(10))
