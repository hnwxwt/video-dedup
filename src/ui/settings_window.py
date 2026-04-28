"""
设置窗口模块 - 负责设置对话框的创建和管理
"""
import tkinter as tk
from tkinter import ttk
from .translations import get_text, current_language, set_language
from .language_manager import save_language_preference, refresh_ui_language
from config import CPU_THREAD_HINT


def toggle_single_hint(app, hint_type):
    """切换单个提示框的显示/隐藏
    
    Args:
        app: 主应用对象
        hint_type: 提示类型 ("cpu", "hash", "safe")
    """
    if hint_type == "cpu":
        widget = app.hint_cpu_detail
    elif hint_type == "hash":
        widget = app.hint_hash_detail
    else:
        widget = app.hint_safe_detail
    
    if widget.winfo_viewable():
        widget.pack_forget()
    else:
        widget.pack(fill=tk.X, pady=(6, 0))


def open_settings_window(app, parent):
    """打开设置窗口
    
    Args:
        app: 主应用对象
        parent: 父窗口
    """
    settings_win = tk.Toplevel(parent)
    settings_win.title(get_text('settings_title'))
    settings_win.geometry("450x500")
    settings_win.transient(parent)
    settings_win.grab_set()
    
    # 先隐藏窗口，避免闪烁
    settings_win.withdraw()
    
    # 创建可滚动容器
    canvas = tk.Canvas(settings_win, highlightthickness=0)
    scrollbar = ttk.Scrollbar(settings_win, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # 语言设置（放在最顶部）
    lang_frame = ttk.LabelFrame(scrollable_frame, text=get_text('language'), padding=10)
    lang_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
    
    lang_row = ttk.Frame(lang_frame)
    lang_row.pack(fill=tk.X)
    
    app.lang_var = tk.StringVar(value=current_language)
    
    def on_language_change():
        global current_language
        new_lang = app.lang_var.get()
        if new_lang != current_language:
            set_language(new_lang)
            # 保存语言偏好到配置文件
            save_language_preference(new_lang)
            # 刷新界面
            refresh_ui_language(app, settings_win)
    
    ttk.Radiobutton(lang_row, text=get_text('language_cn'), variable=app.lang_var, 
                    value='zh', command=on_language_change).pack(side=tk.LEFT, padx=(0, 20))
    ttk.Radiobutton(lang_row, text=get_text('language_en'), variable=app.lang_var, 
                    value='en', command=on_language_change).pack(side=tk.LEFT)
    
    # 基础选项
    opt_frame = ttk.LabelFrame(scrollable_frame, text=get_text('basic_options'), padding=10)
    opt_frame.pack(fill=tk.X, padx=15, pady=10)
    
    opt_row1 = ttk.Frame(opt_frame)
    opt_row1.pack(fill=tk.X)
    ttk.Checkbutton(opt_row1, text=get_text('multi_thread'), variable=app.use_thread).pack(side=tk.LEFT)
    app.hint_cpu = ttk.Label(opt_row1, text="❓", foreground="#2196F3", cursor="hand2", font=("微软雅黑", 9))
    app.hint_cpu.pack(side=tk.LEFT, padx=(6, 0))
    app.hint_cpu.bind("<Button-1>", lambda e: toggle_single_hint(app, "cpu"))
    
    ttk.Checkbutton(opt_row1, text=get_text('auto_rotate'), variable=app.rotate).pack(side=tk.LEFT, padx=(20, 0))
    
    opt_row2 = ttk.Frame(opt_frame)
    opt_row2.pack(fill=tk.X, pady=(6, 0))
    ttk.Checkbutton(opt_row2, text=get_text('unified_resolution'), variable=app.resize).pack(side=tk.LEFT)

    # CPU提示（可折叠）
    app.hint_cpu_detail = ttk.Label(opt_frame, text=CPU_THREAD_HINT, foreground="#757575",
                                      justify=tk.LEFT, wraplength=380, font=("微软雅黑", 8))
    app.hint_cpu_detail.pack_forget()  # 默认隐藏
    
    # 预览设置
    preview_frame = ttk.LabelFrame(scrollable_frame, text=get_text('preview_settings'), padding=10)
    preview_frame.pack(fill=tk.X, padx=15, pady=10)
    
    preview_row = ttk.Frame(preview_frame)
    preview_row.pack()
    ttk.Label(preview_row, text=get_text('thumbnail_size'), font=("微软雅黑", 9)).pack(side=tk.LEFT)
    ttk.Entry(preview_row, textvariable=app.prev_w, width=5, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=3)
    ttk.Label(preview_row, text="×", font=("微软雅黑", 9)).pack(side=tk.LEFT)
    ttk.Entry(preview_row, textvariable=app.prev_h, width=5, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=3)
    
    # 进度管理
    progress_frame = ttk.LabelFrame(scrollable_frame, text=get_text('progress_management'), padding=10)
    progress_frame.pack(fill=tk.X, padx=15, pady=10)
    
    progress_row = ttk.Frame(progress_frame)
    progress_row.pack(fill=tk.X)
    app.btn_save = ttk.Button(progress_row, text=get_text('export_progress'), command=app.save_progress, state=tk.DISABLED, style="Secondary.TButton")
    app.btn_save.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    app.btn_load = ttk.Button(progress_row, text=get_text('import_progress'), command=app.load_progress, style="Secondary.TButton")
    app.btn_load.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    # 缓存管理
    cache_frame = ttk.LabelFrame(scrollable_frame, text=get_text('cache_management'), padding=10)
    cache_frame.pack(fill=tk.X, padx=15, pady=10)
    
    # 缓存提示
    cache_tip = ttk.Label(cache_frame, 
                          text=get_text('cache_info'), 
                          foreground="#2196F3", font=("微软雅黑", 8), justify=tk.LEFT)
    cache_tip.pack(pady=(0, 8))
    
    # 清空缓存按钮
    cache_btn_row1 = ttk.Frame(cache_frame)
    cache_btn_row1.pack(fill=tk.X)
    ttk.Button(cache_btn_row1, text=get_text('clear_precise_cache'), 
               command=lambda: app.clear_cache(mode="precise"),
               style="Secondary.TButton").pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
    ttk.Button(cache_btn_row1, text=get_text('clear_high_precision_cache'), 
               command=lambda: app.clear_cache(mode="high_precision"),
               style="Secondary.TButton").pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
    
    cache_btn_row2 = ttk.Frame(cache_frame)
    cache_btn_row2.pack(fill=tk.X, pady=(6, 0))
    ttk.Button(cache_btn_row2, text=get_text('clear_all_cache'), 
               command=lambda: app.clear_cache(mode="all"),
               style="Secondary.TButton").pack(fill=tk.X)
    
    # 关闭按钮
    close_frame = ttk.Frame(scrollable_frame)
    close_frame.pack(fill=tk.X, padx=15, pady=(10, 15))
    ttk.Button(close_frame, text=get_text('close'), command=settings_win.destroy).pack(fill=tk.X)
    
    # 布局滚动容器
    canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(15, 0))
    scrollbar.pack(side="right", fill="y", pady=(15, 0))
    
    # 居中显示并显示窗口
    settings_win.update_idletasks()
    width = settings_win.winfo_width()
    height = settings_win.winfo_height()
    x = (settings_win.winfo_screenwidth() // 2) - (width // 2)
    y = (settings_win.winfo_screenheight() // 2) - (height // 2)
    settings_win.geometry(f'{width}x{height}+{x}+{y}')
    
    settings_win.deiconify()
