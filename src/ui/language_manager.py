"""
语言管理模块 - 负责语言偏好保存、加载和UI刷新
"""
import os
from .translations import current_language, set_language


def save_language_preference(lang):
    """保存语言偏好到配置文件
    
    Args:
        lang: 语言代码 ('zh' 或 'en')
    """
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'language_config.txt')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(lang)
    except Exception as e:
        print(f"保存语言配置失败: {e}")


def load_language_preference():
    """从配置文件加载语言偏好"""
    global current_language
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'language_config.txt')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                lang = f.read().strip()
                if lang in ['zh', 'en']:
                    set_language(lang)
    except Exception as e:
        print(f"加载语言配置失败: {e}")


def refresh_ui_language(app, settings_win=None):
    """刷新界面语言（当切换语言时调用）
    
    Args:
        app: 主应用对象
        settings_win: 设置窗口对象（可选）
    """
    # 如果设置窗口打开，先关闭它
    if settings_win and settings_win.winfo_exists():
        settings_win.destroy()
    
    # 重新创建主界面
    # 注意：由于tkinter的限制，完全动态刷新比较复杂
    # 这里我们主要通过重新打开设置窗口来展示新语言
    # 如果需要完整刷新主界面，建议重启应用
    
    # 在主界面上显示提示
    app.log("⚠️ 语言已切换。部分界面文本需要重启应用才能完全生效。")
    app.log("💡 Language changed. Some UI text requires restart to take full effect.")
