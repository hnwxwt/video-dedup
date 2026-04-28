"""
扫描状态管理模块
"""


class ScanState:
    """全局扫描状态（线程安全）"""
    STOP = False
    PAUSE = False


def reset_state():
    """重置扫描状态"""
    ScanState.STOP = False
    ScanState.PAUSE = False
