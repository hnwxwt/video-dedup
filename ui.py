import os
import tkinter as tk
from tkinter import ttk, font
from config import (
    MIN_THREAD, MAX_THREAD, DEFAULT_THREAD,
    MIN_HASH_LIMIT, MAX_HASH_LIMIT, DEFAULT_HASH_LIMIT,
    MIN_HASH_LIMIT_SAFE, MAX_HASH_LIMIT_SAFE, DEFAULT_HASH_LIMIT_SAFE,
    CPU_THREAD_HINT, HASH_LIMIT_HINT, HASH_LIMIT_SAFE_HINT
)

# ========== 国际化翻译字典 ==========
TRANSLATIONS = {
    'zh': {
        # 设置窗口标题
        'settings_title': '⚙️ 设置',
        
        # 基础选项
        'basic_options': '⚙️ 基础选项',
        'multi_thread': '多线程加速',
        'auto_rotate': '自动旋转竖屏',
        'unified_resolution': '统一分辨率比较',
        
        # 预览设置
        'preview_settings': '🖼️ 预览设置',
        'thumbnail_size': '缩略图尺寸：',
        
        # 进度管理
        'progress_management': '📦 进度管理',
        'export_progress': '💾 导出进度备份',
        'import_progress': '📂 导入进度备份',
        
        # 缓存管理
        'cache_management': '🗃️ 缓存管理',
        'cache_info': '[INFO] 精确模式和抗水印模式共用同一缓存\n[INFO] 高精度模式使用独立缓存',
        'clear_precise_cache': '🗑️ 清空精确+抗水印缓存',
        'clear_high_precision_cache': '🗑️ 清空高精度缓存',
        'clear_all_cache': '🗑️ 清空所有缓存',
        
        # 语言设置
        'language': '🌐 语言设置',
        'language_cn': '中文',
        'language_en': 'English',
        
        # 关闭按钮
        'close': '关闭',
        
        # 主界面
        'video_directory': '📁 视频目录',
        'browse': '浏览',
        'include_subfolders': '包含子文件夹',
        'current_folder_only': '仅当前文件夹',
        
        'comparison_mode': '🔍 比对模式',
        'precise_mode_tab': '精确模式（无水印）',
        'safe_mode_tab': '抗水印模式（有字幕）',
        'high_precision_mode_tab': '高精度模式（最准确）',
        
        'thread_count': '线程数：',
        'hash_similarity_threshold': '哈希相似度阈值：',
        'avg_hamming_distance_threshold': '平均汉明距离阈值：',
        'similarity_threshold_recommended': '相似度阈值（推荐3-8）：',
        
        'view_precise_help': '❓ 查看精确模式说明',
        'hide_help': '❌ 隐藏说明',
        'view_safe_help': '❓ 查看抗水印模式说明',
        'view_hp_help': '❓ 查看高精度模式说明',
        
        'settings_button': '⚙️ 设置',
        
        'operations': '📋 操作',
        'start_scan': '▶ 开始扫描',
        'pause': '⏸ 暂停',
        'stop': '⏹ 停止',
        
        'run_log': '📜 运行日志',
        
        'duplicate_preview': '重复视频预览',
        'similarity_filter': '相似度≤：',
        'filter': '筛选',
        'reset': '重置',
        
        'min_file_size': '最小文件',
        'min_resolution': '最低分辨率',
        'one_click_select': '🎯 一键选择',
        
        'delete_selected': '🗑️ 删除选中文件到回收站',
    },
    'en': {
        # Settings window title
        'settings_title': '⚙️ Settings',
        
        # Basic options
        'basic_options': '⚙️ Basic Options',
        'multi_thread': 'Multi-threading',
        'auto_rotate': 'Auto Rotate Portrait',
        'unified_resolution': 'Unified Resolution',
        
        # Preview settings
        'preview_settings': '🖼️ Preview Settings',
        'thumbnail_size': 'Thumbnail Size:',
        
        # Progress management
        'progress_management': '📦 Progress Management',
        'export_progress': '💾 Export Progress Backup',
        'import_progress': '📂 Import Progress Backup',
        
        # Cache management
        'cache_management': '🗃️ Cache Management',
        'cache_info': '[INFO] Precise mode and Anti-watermark mode share the same cache\n[INFO] High Precision mode uses independent cache',
        'clear_precise_cache': '🗑️ Clear Precise + Anti-watermark Cache',
        'clear_high_precision_cache': '🗑️ Clear High Precision Cache',
        'clear_all_cache': '🗑️ Clear All Cache',
        
        # Language settings
        'language': '🌐 Language',
        'language_cn': '中文',
        'language_en': 'English',
        
        # Close button
        'close': 'Close',
        
        # Main interface
        'video_directory': '📁 Video Directory',
        'browse': 'Browse',
        'include_subfolders': 'Include Subfolders',
        'current_folder_only': 'Current Folder Only',
        
        'comparison_mode': '🔍 Comparison Mode',
        'precise_mode_tab': 'Precise Mode (No Watermark)',
        'safe_mode_tab': 'Anti-watermark Mode (With Subtitles)',
        'high_precision_mode_tab': 'High Precision Mode (Most Accurate)',
        
        'thread_count': 'Thread Count:',
        'hash_similarity_threshold': 'Hash Similarity Threshold:',
        'avg_hamming_distance_threshold': 'Avg Hamming Distance Threshold:',
        'similarity_threshold_recommended': 'Similarity Threshold (Recommended 3-8):',
        
        'view_precise_help': '❓ View Precise Mode Help',
        'hide_help': '❌ Hide Help',
        'view_safe_help': '❓ View Anti-watermark Mode Help',
        'view_hp_help': '❓ View High Precision Mode Help',
        
        'settings_button': '⚙️ Settings',
        
        'operations': '📋 Operations',
        'start_scan': '▶ Start Scan',
        'pause': '⏸ Pause',
        'stop': '⏹ Stop',
        
        'run_log': '📜 Run Log',
        
        'duplicate_preview': 'Duplicate Video Preview',
        'similarity_filter': 'Similarity ≤:',
        'filter': 'Filter',
        'reset': 'Reset',
        
        'min_file_size': 'Min File Size',
        'min_resolution': 'Min Resolution',
        'one_click_select': '🎯 One-Click Select',
        
        'delete_selected': '🗑️ Delete Selected to Recycle Bin',
    }
}

# 当前语言（默认中文）
current_language = 'zh'

def set_language(lang):
    """设置当前语言"""
    global current_language
    if lang in ['zh', 'en']:
        current_language = lang

def get_text(key):
    """获取翻译文本"""
    return TRANSLATIONS.get(current_language, TRANSLATIONS['zh']).get(key, key)

def toggle_single_hint(app, hint_type):
    """切换单个提示的显示/隐藏"""
    if hint_type == "cpu":
        if app.hint_cpu_detail.winfo_viewable():
            app.hint_cpu_detail.pack_forget()
            app.hint_cpu.config(text="❓")
        else:
            app.hint_cpu_detail.pack(pady=(5, 0), anchor=tk.W)
            app.hint_cpu.config(text="❌")

def open_settings_window(app, parent):
    """打开设置窗口"""
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
    settings_win.deiconify()  # 显示窗口

def create_ui(root, app):
    # ========== 配置样式 ==========
    style = ttk.Style()
    
    # 自定义进度条样式
    style.configure("Custom.Horizontal.TProgressbar", 
                   thickness=10,
                   background="#4CAF50",
                   troughcolor="#E0E0E0")
    
    # 自定义按钮样式
    style.configure("Primary.TButton",
                   padding=(15, 8),
                   font=("Arial", 10, "bold"))
    
    style.configure("Secondary.TButton",
                   padding=(10, 6),
                   font=("Arial", 9))
    
    # 自定义LabelFrame样式
    style.configure("Card.TLabelframe",
                   padding=12,
                   borderwidth=1,
                   relief="solid")
    
    style.configure("Card.TLabelframe.Label",
                   font=("Arial", 10, "bold"),
                   foreground="#333333")

    # ========== 主分栏（两栏布局） ==========
    main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # 左侧面板（固定宽度）
    left_panel = ttk.Frame(main_paned, width=450)
    left_panel.pack_propagate(False)
    main_paned.add(left_panel, weight=0)

    # 右侧面板（预览区域，可扩展）
    right_panel = ttk.Frame(main_paned)
    main_paned.add(right_panel, weight=1)

    # ========== 底部进度条 ==========
    bottom_bar = ttk.Frame(root, padding=(15, 8, 15, 10))
    bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    app.progress_bar = ttk.Progressbar(bottom_bar, style="Custom.Horizontal.TProgressbar")
    app.progress_bar.pack(fill=tk.X)
    
    # 比对进度条（默认隐藏）
    app.compare_progress_bar = ttk.Progressbar(bottom_bar, style="Custom.Horizontal.TProgressbar")
    app.compare_progress_bar.pack(fill=tk.X)
    app.compare_progress_bar.pack_forget()  # 初始隐藏

    # ========== 左侧：设置区域 ==========
    # 目录选择
    dir_frame = ttk.LabelFrame(left_panel, text=get_text('video_directory'), padding=10, style="Card.TLabelframe")
    dir_frame.pack(fill=tk.X, pady=(0, 6))
    
    path_row = ttk.Frame(dir_frame)
    path_row.pack(fill=tk.X)
    ttk.Entry(path_row, textvariable=app.scan_path, width=35, font=("Arial", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
    ttk.Button(path_row, text=get_text('browse'), command=app.select_folder, width=7, style="Secondary.TButton").pack(side=tk.LEFT)

    range_frame = ttk.Frame(dir_frame)
    range_frame.pack(fill=tk.X, pady=(8, 0))
    ttk.Radiobutton(range_frame, text=get_text('include_subfolders'), variable=app.scan_subdir, value=1).pack(side=tk.LEFT, padx=(0, 18))
    ttk.Radiobutton(range_frame, text=get_text('current_folder_only'), variable=app.scan_subdir, value=0).pack(side=tk.LEFT)

    # 比对模式 - 减少内边距
    mode_frame = ttk.LabelFrame(left_panel, text=get_text('comparison_mode'), padding=8, style="Card.TLabelframe")
    mode_frame.pack(fill=tk.X, pady=6)

    mode_notebook = ttk.Notebook(mode_frame)
    mode_notebook.pack(fill=tk.X)

    # 精确模式
    precise_frame = ttk.Frame(mode_notebook, padding=8)
    mode_notebook.add(precise_frame, text=get_text('precise_mode_tab'))

    ttk.Label(precise_frame, text=get_text('thread_count'), font=("微软雅黑", 9)).pack(anchor=tk.W)
    thread_row_precise = ttk.Frame(precise_frame)
    thread_row_precise.pack(fill=tk.X, pady=(2, 8))
    app.thread_slider = ttk.Scale(thread_row_precise, from_=MIN_THREAD, to=MAX_THREAD, 
                                   orient=tk.HORIZONTAL, variable=app.thread_cnt,
                                   command=lambda v: app.thread_cnt.set(int(float(v))))
    app.thread_slider.set(DEFAULT_THREAD)
    app.thread_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(thread_row_precise, textvariable=app.thread_cnt, width=3, font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)

    ttk.Label(precise_frame, text=get_text('hash_similarity_threshold'), font=("微软雅黑", 9)).pack(anchor=tk.W)
    hash_row_precise = ttk.Frame(precise_frame)
    hash_row_precise.pack(fill=tk.X, pady=(2, 6))
    app.hash_slider = ttk.Scale(hash_row_precise, from_=MIN_HASH_LIMIT, to=MAX_HASH_LIMIT,
                                 orient=tk.HORIZONTAL, variable=app.hash_val,
                                 command=lambda v: app.hash_val.set(int(float(v))))
    app.hash_slider.set(DEFAULT_HASH_LIMIT)
    app.hash_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(hash_row_precise, textvariable=app.hash_val, width=3, font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)

    # 帮助按钮行
    help_btn_frame_precise = ttk.Frame(precise_frame)
    help_btn_frame_precise.pack(anchor=tk.W, pady=(6, 0))
    app.precise_help_btn = ttk.Label(help_btn_frame_precise, text=get_text('view_precise_help'), foreground="#2196F3", 
                                      cursor="hand2", font=("微软雅黑", 9, "underline"))
    app.precise_help_btn.pack(side=tk.LEFT)

    app.hint_precise = ttk.Label(precise_frame, text=HASH_LIMIT_HINT, foreground="#757575",
                                  justify=tk.LEFT, wraplength=400, font=("Arial", 8))
    app.hint_precise.pack_forget()  # 默认隐藏
    
    # 点击帮助按钮显示/隐藏说明
    def toggle_precise_help(event=None):
        if app.hint_precise.winfo_viewable():
            app.hint_precise.pack_forget()
            app.precise_help_btn.config(text=get_text('view_precise_help'))
        else:
            app.hint_precise.pack(pady=(6, 0), anchor=tk.W)
            app.precise_help_btn.config(text=get_text('hide_help'))
    
    app.precise_help_btn.bind("<Button-1>", toggle_precise_help)

    # 抗水印模式
    safe_frame = ttk.Frame(mode_notebook, padding=8)
    mode_notebook.add(safe_frame, text=get_text('safe_mode_tab'))

    ttk.Label(safe_frame, text=get_text('thread_count'), font=("微软雅黑", 9)).pack(anchor=tk.W)
    thread_row_safe = ttk.Frame(safe_frame)
    thread_row_safe.pack(fill=tk.X, pady=(2, 8))
    app.thread_slider_safe = ttk.Scale(thread_row_safe, from_=MIN_THREAD, to=MAX_THREAD,
                                        orient=tk.HORIZONTAL, variable=app.thread_cnt,
                                        command=lambda v: app.thread_cnt.set(int(float(v))))
    app.thread_slider_safe.set(DEFAULT_THREAD)
    app.thread_slider_safe.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(thread_row_safe, textvariable=app.thread_cnt, width=3, font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)

    ttk.Label(safe_frame, text=get_text('avg_hamming_distance_threshold'), font=("微软雅黑", 9)).pack(anchor=tk.W)
    hash_row_safe = ttk.Frame(safe_frame)
    hash_row_safe.pack(fill=tk.X, pady=(2, 6))
    app.hash_slider_safe = ttk.Scale(hash_row_safe, from_=MIN_HASH_LIMIT_SAFE, to=MAX_HASH_LIMIT_SAFE,
                                      orient=tk.HORIZONTAL, variable=app.hash_val,
                                      command=lambda v: app.hash_val.set(int(float(v))))
    app.hash_slider_safe.set(DEFAULT_HASH_LIMIT_SAFE)
    app.hash_slider_safe.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(hash_row_safe, textvariable=app.hash_val, width=3, font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)

    # 帮助按钮行
    help_btn_frame_safe = ttk.Frame(safe_frame)
    help_btn_frame_safe.pack(anchor=tk.W, pady=(6, 0))
    app.safe_help_btn = ttk.Label(help_btn_frame_safe, text=get_text('view_safe_help'), foreground="#2196F3", 
                                   cursor="hand2", font=("微软雅黑", 9, "underline"))
    app.safe_help_btn.pack(side=tk.LEFT)

    app.hint_safe = ttk.Label(safe_frame, text=HASH_LIMIT_SAFE_HINT, foreground="#757575",
                               justify=tk.LEFT, wraplength=400, font=("Arial", 8))
    app.hint_safe.pack_forget()  # 默认隐藏
    
    # 点击帮助按钮显示/隐藏说明
    def toggle_safe_help(event=None):
        if app.hint_safe.winfo_viewable():
            app.hint_safe.pack_forget()
            app.safe_help_btn.config(text=get_text('view_safe_help'))
        else:
            app.hint_safe.pack(pady=(6, 0), anchor=tk.W)
            app.safe_help_btn.config(text=get_text('hide_help'))
    
    app.safe_help_btn.bind("<Button-1>", toggle_safe_help)
    
    # 高精度模式
    high_precision_frame = ttk.Frame(mode_notebook, padding=8)
    mode_notebook.add(high_precision_frame, text=get_text('high_precision_mode_tab'))
    
    ttk.Label(high_precision_frame, text=get_text('thread_count'), font=("微软雅黑", 9)).pack(anchor=tk.W)
    thread_row_hp = ttk.Frame(high_precision_frame)
    thread_row_hp.pack(fill=tk.X, pady=(2, 8))
    app.thread_slider_hp = ttk.Scale(thread_row_hp, from_=MIN_THREAD, to=MAX_THREAD,
                                      orient=tk.HORIZONTAL, variable=app.thread_cnt,
                                      command=lambda v: app.thread_cnt.set(int(float(v))))
    app.thread_slider_hp.set(DEFAULT_THREAD)
    app.thread_slider_hp.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(thread_row_hp, textvariable=app.thread_cnt, width=3, font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
    
    ttk.Label(high_precision_frame, text=get_text('similarity_threshold_recommended'), font=("微软雅黑", 9)).pack(anchor=tk.W)
    hash_row_hp = ttk.Frame(high_precision_frame)
    hash_row_hp.pack(fill=tk.X, pady=(2, 6))
    app.hash_slider_hp = ttk.Scale(hash_row_hp, from_=1, to=15,
                                    orient=tk.HORIZONTAL, variable=app.hash_val,
                                    command=lambda v: app.hash_val.set(int(float(v))))
    app.hash_slider_hp.set(5)
    app.hash_slider_hp.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(hash_row_hp, textvariable=app.hash_val, width=3, font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
    
    # 帮助按钮行
    help_btn_frame = ttk.Frame(high_precision_frame)
    help_btn_frame.pack(anchor=tk.W, pady=(6, 0))
    app.hp_help_btn = ttk.Label(help_btn_frame, text=get_text('view_hp_help'), foreground="#2196F3", 
                                 cursor="hand2", font=("微软雅黑", 9, "underline"))
    app.hp_help_btn.pack(side=tk.LEFT)

    hp_hint_text = """【高精度模式说明】
• 多特征融合：pHash + aHash + dHash + 颜色直方图 + SSIM
• 采样帧数：10帧（更全面的比对）
• 适用场景：对精度要求极高，能容忍较慢的扫描速度
• 推荐阈值：3-5（严格），6-8（宽松）
• 注意：速度约为精确模式的3-4倍"""
    
    app.hint_hp = ttk.Label(high_precision_frame, text=hp_hint_text, foreground="#757575",
                             justify=tk.LEFT, wraplength=400, font=("Arial", 8))
    app.hint_hp.pack_forget()  # 默认隐藏
    
    # 点击帮助按钮显示/隐藏说明
    def toggle_hp_help(event=None):
        if app.hint_hp.winfo_viewable():
            app.hint_hp.pack_forget()
            app.hp_help_btn.config(text=get_text('view_hp_help'))
        else:
            app.hint_hp.pack(pady=(6, 0), anchor=tk.W)
            app.hp_help_btn.config(text=get_text('hide_help'))
    
    app.hp_help_btn.bind("<Button-1>", toggle_hp_help)
    
    # 绑定标签页切换
    def on_mode_change(event):
        selected = mode_notebook.index(mode_notebook.select())
        if selected == 0:
            app.mode_safe = False
            app.mode_high_precision = False
            app.hash_slider.set(app.hash_val.get())
        elif selected == 1:
            app.mode_safe = True
            app.mode_high_precision = False
            if app.hash_val.get() < MIN_HASH_LIMIT_SAFE:
                app.hash_slider_safe.set(DEFAULT_HASH_LIMIT_SAFE)
            elif app.hash_val.get() > MAX_HASH_LIMIT_SAFE:
                app.hash_slider_safe.set(app.hash_val.get())
            else:
                app.hash_slider_safe.set(app.hash_val.get())
        else:  # selected == 2
            app.mode_safe = False
            app.mode_high_precision = True
            if app.hash_val.get() > 15:
                app.hash_slider_hp.set(5)

    mode_notebook.bind("<<NotebookTabChanged>>", on_mode_change)

    # 设置按钮（打开设置窗口）
    settings_btn_frame = ttk.Frame(left_panel)
    settings_btn_frame.pack(fill=tk.X, pady=6)
    app.btn_settings = ttk.Button(settings_btn_frame, text=get_text('settings_button'), command=lambda: open_settings_window(app, root), style="Secondary.TButton")
    app.btn_settings.pack(fill=tk.X)

    # 操作按钮 - 紧凑布局
    btn_ops = ttk.LabelFrame(left_panel, text=get_text('operations'), padding=10, style="Card.TLabelframe")
    btn_ops.pack(fill=tk.X, pady=6)
    
    btn_row1 = ttk.Frame(btn_ops)
    btn_row1.pack(fill=tk.X)
    app.btn_start = ttk.Button(btn_row1, text=get_text('start_scan'), command=app.start, style="Primary.TButton")
    app.btn_start.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
    app.btn_pause = ttk.Button(btn_row1, text=get_text('pause'), command=app.pause, state=tk.DISABLED, style="Secondary.TButton")
    app.btn_pause.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
    app.btn_stop = ttk.Button(btn_row1, text=get_text('stop'), command=app.stop, state=tk.DISABLED, style="Secondary.TButton")
    app.btn_stop.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

    # 运行日志 - 占据剩余空间
    log_frame = ttk.LabelFrame(left_panel, text=get_text('run_log'), padding=8, style="Card.TLabelframe")
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
    app.log_text = tk.Text(log_frame, font=("Consolas", 9), bg="#FAFAFA",
                           fg="#333333", insertbackground="#2196F3",
                           selectbackground="#BBDEFB", selectforeground="#000000")
    log_scroll = ttk.Scrollbar(log_frame, command=app.log_text.yview)
    app.log_text.config(yscrollcommand=log_scroll.set)
    log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    app.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # ========== 右侧：预览区域 ==========
    right_header = ttk.Frame(right_panel, padding=(0, 0, 0, 8))
    right_header.pack(fill=tk.X)
    
    ttk.Label(right_header, text=get_text('duplicate_preview'), font=("微软雅黑", 13, "bold"), foreground="#333333").pack(side=tk.LEFT)
    
    # 相似度筛选
    filter_frame = ttk.Frame(right_header)
    filter_frame.pack(side=tk.LEFT, padx=20)
    ttk.Label(filter_frame, text=get_text('similarity_filter'), font=("微软雅黑", 9)).pack(side=tk.LEFT)
    app.sim_filter = ttk.Spinbox(filter_frame, from_=0, to=100, width=5, font=("微软雅黑", 9),
                                   textvariable=app.sim_filter_val)
    app.sim_filter.set("100")
    app.sim_filter.pack(side=tk.LEFT, padx=3)
    ttk.Button(filter_frame, text=get_text('filter'), command=lambda: app.apply_filter(), width=5, style="Secondary.TButton").pack(side=tk.LEFT, padx=4)
    ttk.Button(filter_frame, text=get_text('reset'), command=lambda: app.reset_filter(), width=5, style="Secondary.TButton").pack(side=tk.LEFT, padx=2)

    # 保留策略（一键选择）- 右上角
    select_frame = ttk.Frame(right_header)
    select_frame.pack(side=tk.RIGHT)
    app.select_by_size = tk.BooleanVar(value=False)
    app.select_by_res = tk.BooleanVar(value=False)
    ttk.Checkbutton(select_frame, text=get_text('min_file_size'), variable=app.select_by_size).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Checkbutton(select_frame, text=get_text('min_resolution'), variable=app.select_by_res).pack(side=tk.LEFT, padx=(0, 10))
    app.btn_select = ttk.Button(select_frame, text=get_text('one_click_select'), command=app.select_by_condition, state=tk.DISABLED, style="Primary.TButton")
    app.btn_select.pack(side=tk.LEFT)

    # 预览容器 - 占据剩余空间
    preview_container = ttk.Frame(right_panel)
    preview_container.pack(fill=tk.BOTH, expand=True)
    
    app.canvas = tk.Canvas(preview_container, bg="#FAFAFA", highlightthickness=0)
    scroll_y = ttk.Scrollbar(preview_container, orient=tk.VERTICAL, command=app.canvas.yview)
    app.canvas.config(yscrollcommand=scroll_y.set)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    app.canvas.pack(fill=tk.BOTH, expand=True)
    
    # ✅ 绑定鼠标滚轮事件
    def _on_mousewheel(event):
        app.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    app.canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    # 在canvas中创建frame用于放置预览项
    app.preview_frame = ttk.Frame(app.canvas)
    app.canvas_window = app.canvas.create_window((0, 0), window=app.preview_frame, anchor=tk.NW)
    
    # 绑定滚动事件
    app.preview_frame.bind("<Configure>", lambda e: app.canvas.configure(scrollregion=app.canvas.bbox("all")))
    
    # ✅ 绑定canvas大小变化事件，确保preview_frame宽度跟随canvas
    def on_canvas_configure(event):
        app.canvas.itemconfig(app.canvas_window, width=event.width)
    
    app.canvas.bind("<Configure>", on_canvas_configure)

    # ✅ 绑定canvas大小变化事件，确保preview_frame宽度跟随canvas
    def on_canvas_configure(event):
        app.canvas.itemconfig(app.canvas_window, width=event.width)
    
    app.canvas.bind("<Configure>", on_canvas_configure)

    # ✅ 删除按钮区域（预览底部）
    delete_frame = ttk.Frame(right_panel, padding=(0, 8, 0, 0))
    delete_frame.pack(fill=tk.X)
    
    app.btn_delete = ttk.Button(delete_frame, text=get_text('delete_selected'), command=app.delete_selected, state=tk.DISABLED, style="Primary.TButton")
    app.btn_delete.pack(fill=tk.X, padx=5)

    # 初始化变量
    app.check_vars = []
    app.image_refs = []
    app.current_groups = []
    app.group_scores = {}

def save_language_preference(lang):
    """保存语言偏好到配置文件"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'language_config.txt')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(lang)
    except Exception as e:
        print(f"保存语言配置失败: {e}")

def load_language_preference():
    """从配置文件加载语言偏好"""
    global current_language
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'language_config.txt')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                lang = f.read().strip()
                if lang in ['zh', 'en']:
                    current_language = lang
    except Exception as e:
        print(f"加载语言配置失败: {e}")

def refresh_ui_language(app, settings_win=None):
    """刷新界面语言（当切换语言时调用）"""
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
