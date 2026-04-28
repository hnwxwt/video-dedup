"""
视频处理模块 - 负责帧提取、哈希计算、信息获取
"""
import os
import cv2
import imagehash
from PIL import Image, ImageFilter
import numpy as np
from config import *
from .state import ScanState


def get_video_info(video_path):
    """获取视频基本信息
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        dict: 视频信息字典（分辨率、FPS、时长等）
    """
    info = {}
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return info
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        info['resolution'] = f"{width}x{height}"
        info['fps'] = f"{fps:.2f}"
        info['duration'] = f"{int(duration // 60)}:{int(duration % 60):02d}"
        info['frames'] = str(total_frames)
        
        # 文件大小
        file_size = os.path.getsize(video_path)
        if file_size < 1024 * 1024:
            info['size'] = f"{file_size / 1024:.1f} KB"
        elif file_size < 1024 * 1024 * 1024:
            info['size'] = f"{file_size / (1024 * 1024):.1f} MB"
        else:
            info['size'] = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
        
        # 码率
        bitrate = file_size * 8 / duration if duration > 0 else 0
        info['bitrate'] = f"{bitrate/1000:.0f} kbps"
        cap.release()
    except:
        pass
    return info


def normalize_frame(img_pil, enable_rotate, enable_resize):
    """标准化视频帧（旋转+裁剪+缩放）
    
    Args:
        img_pil: PIL图像对象
        enable_rotate: 是否自动旋转竖屏视频
        enable_resize: 是否统一分辨率
    
    Returns:
        PIL.Image: 标准化后的图像
    """
    img = img_pil.copy()
    if enable_rotate:
        w, h = img.size
        if w > h:
            img = img.rotate(90, expand=True)
    if enable_resize:
        tar_ratio = STANDARD_W / STANDARD_H
        cur_w, cur_h = img.size
        cur_ratio = cur_w / cur_h
        if cur_ratio > tar_ratio:
            new_w = int(cur_h * tar_ratio)
            offset = (cur_w - new_w) // 2
            img = img.crop((offset, 0, offset + new_w, cur_h))
        else:
            new_h = int(cur_w / tar_ratio)
            offset = (cur_h - new_h) // 2
            img = img.crop((0, offset, cur_w, offset + new_h))
        img = img.resize((STANDARD_W, STANDARD_H), Image.Resampling.LANCZOS)
    return img


def process_video_optimized(video_path, enable_rotate, enable_resize):
    """优化的精确模式：使用OpenCV直接处理，减少库转换开销
    
    优化点：
    1. 在OpenCV中完成裁剪、缩放、模糊操作
    2. 降低分辨率到32x32（pHash对尺寸不敏感）
    3. 减少BGR→RGB→PIL的转换次数
    
    Args:
        video_path: 视频文件路径
        enable_rotate: 是否自动旋转
        enable_resize: 是否统一分辨率
    
    Returns:
        tuple: (video_path, hashes, frame_list, video_info) 或 None
    """
    if ScanState.STOP:
        return None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_list = []
        hashes = []
        
        for ratio in CAPTURE_POSITIONS:
            if ScanState.STOP:
                return None
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(1, int(total_frames * ratio)))
            ret, frame = cap.read()
            if not ret:
                frame_list.append(None)
                hashes.append(None)
                continue
            
            # ✅ 直接在OpenCV中处理（避免多次转换）
            # 1. 标准化帧（旋转+裁剪）
            if enable_rotate:
                h, w = frame.shape[:2]
                if w > h:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            
            if enable_resize:
                h, w = frame.shape[:2]
                tar_ratio = STANDARD_W / STANDARD_H
                cur_ratio = w / h
                
                if cur_ratio > tar_ratio:
                    new_w = int(h * tar_ratio)
                    offset = (w - new_w) // 2
                    frame = frame[:, offset:offset+new_w]
                else:
                    new_h = int(w / tar_ratio)
                    offset = (h - new_h) // 2
                    frame = frame[offset:offset+new_h, :]
                
                # ✅ 直接缩放到目标尺寸
                frame = cv2.resize(frame, (STANDARD_W, STANDARD_H), interpolation=cv2.INTER_LANCZOS4)
            
            # 2. BGR转RGB（仅在需要时）
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 3. 转换为PIL进行pHash计算（必须步骤）
            pil_img = Image.fromarray(frame_rgb)
            
            # 保存预览图
            frame_list.append(pil_img.copy())
            
            # 4. 计算哈希
            hashes.append(imagehash.phash(pil_img))
        
        cap.release()
        video_info = get_video_info(video_path)
        return (video_path, hashes, frame_list, video_info)
    except Exception as e:
        print(f"处理视频失败 {video_path}: {e}")
        return None


def process_video_safe_optimized(video_path):
    """优化的抗水印模式：使用OpenCV直接处理
    
    优化点：
    1. 在OpenCV中完成裁剪、缩放、模糊
    2. 降低分辨率到32x32
    3. 直接使用灰度图计算pHash
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        tuple: (video_path, hash_list, frame_list, video_info) 或 None
    """
    if ScanState.STOP:
        return None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        hash_list = []
        frame_list = []  # 预览图列表

        for rate in SAFE_SAMPLE_RATES:
            if ScanState.STOP:
                cap.release()
                return None
            frame_idx = int(total_frames * rate)
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_idx - 1))
            ret, frame = cap.read()
            if not ret:
                frame_list.append(None)
                continue
            
            # ✅ 直接在OpenCV中处理
            h, w = frame.shape[:2]
            cut_w = int(w * CUT_RATIO)
            cut_h = int(h * CUT_RATIO)
            
            # 1. 裁剪中心区域
            cropped = frame[cut_h:h-cut_h, cut_w:w-cut_w]
            
            # 2. 缩放到32x32（更小的尺寸，更快）
            resized = cv2.resize(cropped, (32, 32), interpolation=cv2.INTER_AREA)
            
            # 3. 高斯模糊
            blurred = cv2.GaussianBlur(resized, (3, 3), 1)
            
            # 4. 转换为灰度图（pHash只需要灰度）
            gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
            
            # 5. 转换为PIL进行pHash计算
            pil_img = Image.fromarray(gray)
            
            # 保存预览图（彩色）
            preview_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
            preview_pil = Image.fromarray(preview_rgb)
            frame_list.append(preview_pil)
            
            # 6. 计算哈希
            frame_hash = imagehash.phash(pil_img)
            hash_list.append(frame_hash)

        cap.release()
        if not hash_list:
            return None
        video_info = get_video_info(video_path)
        return (video_path, hash_list, frame_list, video_info)
    except Exception as e:
        print(f"处理视频失败 {video_path}: {e}")
        return None


def process_video(video_path, enable_rotate, enable_resize):
    """原始版本（保留兼容性）
    
    Args:
        video_path: 视频文件路径
        enable_rotate: 是否自动旋转
        enable_resize: 是否统一分辨率
    
    Returns:
        tuple: (video_path, hashes, frame_list, video_info) 或 None
    """
    if ScanState.STOP:
        return None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_list = []
        hashes = []
        for ratio in CAPTURE_POSITIONS:
            if ScanState.STOP:
                return None
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(1, int(total_frames * ratio)))
            ret, frame = cap.read()
            if not ret:
                frame_list.append(None)
                hashes.append(None)
                continue
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_raw = Image.fromarray(frame_rgb)
            img_std = normalize_frame(img_raw, enable_rotate, enable_resize)
            frame_list.append(img_std.copy())
            hashes.append(imagehash.phash(img_std))
        cap.release()
        video_info = get_video_info(video_path)
        return (video_path, hashes, frame_list, video_info)
    except:
        return None


def crop_center_region(img, cut_ratio=0.15):
    """裁剪图像中心区域（去除边缘水印）
    
    Args:
        img: PIL图像对象
        cut_ratio: 裁剪比例（默认15%）
    
    Returns:
        PIL.Image: 裁剪后的图像
    """
    w, h = img.size
    cut_w = int(w * cut_ratio)
    cut_h = int(h * cut_ratio)
    return img.crop((cut_w, cut_h, w - cut_w, h - cut_h))


def get_safe_frame_hash(raw_img):
    """计算抗水印模式的帧哈希
    
    Args:
        raw_img: 原始PIL图像
    
    Returns:
        imagehash.ImageHash: 帧哈希值
    """
    cropped = crop_center_region(raw_img)
    resized = cropped.resize((32, 32), Image.Resampling.LANCZOS)
    blurred = resized.filter(ImageFilter.GaussianBlur(radius=1))
    return imagehash.phash(blurred)


def process_video_safe(video_path):
    """抗水印模式处理（原始版本，保留兼容性）
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        tuple: (video_path, hash_list, frame_list, video_info) 或 None
    """
    if ScanState.STOP:
        return None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        hash_list = []
        frame_list = []
        for rate in SAFE_SAMPLE_RATES:
            if ScanState.STOP:
                cap.release()
                return None
            frame_idx = int(total_frames * rate)
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_idx - 1))
            ret, frame = cap.read()
            if not ret:
                frame_list.append(None)
                continue
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_raw = Image.fromarray(frame_rgb)
            frame_list.append(img_raw.copy())
            frame_hash = get_safe_frame_hash(img_raw)
            hash_list.append(frame_hash)
        cap.release()
        if not hash_list:
            return None
        video_info = get_video_info(video_path)
        return (video_path, hash_list, frame_list, video_info)
    except Exception as e:
        print(f"处理视频失败 {video_path}: {e}")
        return None


def process_video_high_precision(video_path):
    """高精度模式处理（提取多维特征）
    
    Args:
        video_path: 视频文件路径
    
    Returns:
        tuple: (video_path, features_dict, frame_list, video_info) 或 None
    """
    from .comparator import calculate_color_histogram
    
    if ScanState.STOP:
        return None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        features_list = []
        frame_list = []
        
        for ratio in CAPTURE_POSITIONS:
            if ScanState.STOP:
                return None
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(1, int(total_frames * ratio)))
            ret, frame = cap.read()
            if not ret:
                frame_list.append(None)
                features_list.append(None)
                continue
            
            # BGR转RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            frame_list.append(pil_img.copy())
            
            # 提取多维特征
            features = {
                'phash': imagehash.phash(pil_img),
                'ahash': imagehash.average_hash(pil_img),
                'dhash': imagehash.dhash(pil_img),
                'histogram': calculate_color_histogram(pil_img)
            }
            features_list.append(features)
        
        cap.release()
        if not features_list:
            return None
        video_info = get_video_info(video_path)
        return (video_path, features_list, frame_list, video_info)
    except Exception as e:
        print(f"处理视频失败 {video_path}: {e}")
        return None
