import json
import os
import imagehash
from PIL import Image
from config import SAVE_PROGRESS_PATH

def save_progress(scan_path, scan_subdir, finished_idx, video_list, video_data):
    # 将 ImageHash 转换为字符串，Image 转换为字符串（base64）
    import base64
    from io import BytesIO

    def serialize_video_data(video_data):
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
    if not os.path.exists(SAVE_PROGRESS_PATH):
        return None
    with open(SAVE_PROGRESS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)