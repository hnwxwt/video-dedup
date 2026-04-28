"""
核心业务逻辑包 - 扫描器模块
"""
from .scanner import scan_worker

__all__ = [
    'scan_worker',
]

"""
核心业务逻辑包 - 视频扫描、处理、比对
"""
from .state import ScanState, reset_state
from .video_processor import (
    get_video_info,
    normalize_frame,
    process_video_optimized,
    process_video_safe_optimized,
    process_video,
    process_video_safe,
    process_video_high_precision,
)
from .comparator import (
    find_duplicate_groups,
    find_duplicate_groups_safe,
    find_duplicate_groups_high_precision,
    calc_similar_score,
    calculate_high_precision_similarity,
    batch_process_videos,
    batch_process_with_callback,
)

__all__ = [
    # 状态管理
    'ScanState',
    'reset_state',
    
    # 视频处理
    'get_video_info',
    'normalize_frame',
    'process_video_optimized',
    'process_video_safe_optimized',
    'process_video',
    'process_video_safe',
    'process_video_high_precision',
    
    # 相似度比对
    'find_duplicate_groups',
    'find_duplicate_groups_safe',
    'find_duplicate_groups_high_precision',
    'calc_similar_score',
    'calculate_high_precision_similarity',
    'batch_process_videos',
    'batch_process_with_callback',
]
