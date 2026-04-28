"""
国际化翻译字典模块

包含所有UI文本的中英文翻译
"""

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
    """设置当前语言
    
    Args:
        lang: 语言代码 ('zh' 或 'en')
    """
    global current_language
    if lang in TRANSLATIONS:
        current_language = lang


def get_text(key):
    """获取翻译文本
    
    Args:
        key: 翻译键
    
    Returns:
        str: 翻译后的文本
    """
    return TRANSLATIONS.get(current_language, TRANSLATIONS['zh']).get(key, key)
