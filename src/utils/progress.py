"""
进度管理模块 - 负责扫描进度的保存和加载
"""
import json
import os
import base64
from io import BytesIO
from config import SAVE_PROGRESS_PATH


def save_progress(scan_path, scan_subdir, finished_idx, video_list, video_data):
    """保存扫描进度到文件
    
    Args:
        scan_path: 扫描路径
        scan_subdir: 是否包含子文件夹
        finished_idx: 已完成索引
        video_list: 视频列表
        video_data: 视频数据字典 {path: (hashes, frames, info)}
    """
    def serialize_video_data(video_data):
        """序列化视频数据（将ImageHash和PIL Image转换为可JSON序列化的格式）"""
        result = {}
        for k, v in video_data.items():
            hashes, frames, info = v
            # hashes: ImageHash 列表 -> 字符串列表
            hash_list = [str(h) if h is not None else None for h in hashes]
            # frames: PIL Image 列表 -> base64 字符串列表
            frame_list = []
            for img in frames:
                if img is not None:
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    frame_list.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
                else:
                    frame_list.append(None)
            result[k] = [hash_list, frame_list, info]
        return result

    data = {
        "scan_path": scan_path,
        "scan_subdir": scan_subdir,
        "finished_idx": finished_idx,
        "video_list": video_list,
        "video_data": serialize_video_data(video_data)
    }
    with open(SAVE_PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_progress():
    """从文件加载扫描进度
    
    Returns:
        dict: 进度数据，如果文件不存在则返回None
    """
    if not os.path.exists(SAVE_PROGRESS_PATH):
        return None
    with open(SAVE_PROGRESS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
