"""
视频缓存系统 - 公共API导出（兼容层）

注意: 此模块从根目录的 video_cache.py 导入所有内容
实际实现在 ../../video_cache.py，此处仅为路径统一
"""
import sys
import os

# 将项目根目录添加到路径
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

# 从根目录的 video_cache 模块导入所有内容
from video_cache import (
    # 核心API
    get_cached_video,
    save_video_cache,
    clear_video_cache,
    flush_cache,
    reset_memory_cache,
    set_current_scan_dir,
    set_log_callback,
    
    # 配置常量
    CACHE_SHARD_SIZE,
    ENABLE_COMPRESSION,
    SAVE_INTERVAL,
    MAX_MEMORY_MB,
    
    # 预加载功能
    start_prefetch_thread,
    stop_prefetch_thread,
    prefetch_next_video,
    
    # 统计信息
    CacheStats,
    get_cache_stats,
    get_cache_stats_summary,
    
    # 内存管理
    check_memory_usage,
)

__all__ = [
    # 核心API
    'get_cached_video',
    'save_video_cache',
    'clear_video_cache',
    'flush_cache',
    'reset_memory_cache',
    'set_current_scan_dir',
    'set_log_callback',
    
    # 配置常量
    'CACHE_SHARD_SIZE',
    'ENABLE_COMPRESSION',
    'SAVE_INTERVAL',
    'MAX_MEMORY_MB',
    
    # 预加载功能
    'start_prefetch_thread',
    'stop_prefetch_thread',
    'prefetch_next_video',
    
    # 统计信息
    'CacheStats',
    'get_cache_stats',
    'get_cache_stats_summary',
    
    # 内存管理
    'check_memory_usage',
]
