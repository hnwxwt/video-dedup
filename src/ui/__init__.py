"""
UI模块 - 用户界面组件

包含主窗口、设置窗口、国际化等功能
"""
from .translations import TRANSLATIONS, current_language, set_language, get_text
from .language_manager import save_language_preference, load_language_preference, refresh_ui_language
from .settings_window import open_settings_window, toggle_single_hint
from .main_window import create_ui

__all__ = [
    # 翻译相关
    'TRANSLATIONS',
    'current_language',
    'set_language',
    'get_text',
    
    # 语言管理
    'save_language_preference',
    'load_language_preference',
    'refresh_ui_language',
    
    # 设置窗口
    'open_settings_window',
    'toggle_single_hint',
    
    # 主窗口
    'create_ui',
]
