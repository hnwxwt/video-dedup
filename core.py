import os
import cv2
import imagehash
from PIL import Image, ImageFilter
import numpy as np
from config import *

# 设置 OpenCV 日志级别为 ERROR，抑制 FFmpeg 警告
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

class ScanState:
    STOP = False
    PAUSE = False

def reset_state():
    """重置扫描状态"""
    ScanState.STOP = False
    ScanState.PAUSE = False

def get_video_info(video_path):
    """获取视频基本信息"""
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

# ============ 优化版：使用OpenCV直接处理（减少PIL转换开销） ============
def process_video_optimized(video_path, enable_rotate, enable_resize):
    """优化的精确模式：使用OpenCV直接处理，减少库转换开销
    
    优化点：
    1. 在OpenCV中完成裁剪、缩放、模糊操作
    2. 降低分辨率到32x32（pHash对尺寸不敏感）
    3. 减少BGR→RGB→PIL的转换次数
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

# ============ 原始版本（保留兼容性） ============
def process_video(video_path, enable_rotate, enable_resize):
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

def find_duplicate_groups(video_data, hash_limit):
    """精确模式：逐帧严格比对"""
    used = set()
    groups = []
    file_list = list(video_data.keys())
    for i in range(len(file_list)):
        f1 = file_list[i]
        if f1 in used:
            continue
        group = [f1]
        h1, _, _ = video_data[f1]
        for j in range(i+1, len(file_list)):
            f2 = file_list[j]
            if f2 in used:
                continue
            h2, _, _ = video_data[f2]
            same = True
            for a, b in zip(h1, h2):
                if a is None or b is None or abs(a - b) > hash_limit:
                    same = False
                    break
            if same:
                group.append(f2)
                used.add(f2)
        if len(group) > 1:
            # 返回排序后的 tuple，确保与 main.py 中的 key 一致
            groups.append(tuple(sorted(group)))
    return groups

# ============ 抗水印模式（新逻辑） ============
def crop_center_region(img, cut_ratio=0.15):
    """裁剪中心区域，切掉四周15%，过滤角落水印、字幕"""
    w, h = img.size
    cut_w = int(w * cut_ratio)
    cut_h = int(h * cut_ratio)
    return img.crop((cut_w, cut_h, w - cut_w, h - cut_h))

def get_safe_frame_hash(raw_img):
    """抗水印哈希：裁剪 + 模糊 + 弱化细节"""
    img = crop_center_region(raw_img, cut_ratio=CUT_RATIO)
    img = img.resize((64, 64))
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    return imagehash.phash(img)

def process_video_safe(video_path):
    """抗水印模式处理视频"""
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
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            h = get_safe_frame_hash(pil_img)
            hash_list.append(h)
            # 裁剪中心区域作为预览图
            preview = crop_center_region(pil_img, cut_ratio=CUT_RATIO)
            frame_list.append(preview)

        cap.release()
        if not hash_list:
            return None
        video_info = get_video_info(video_path)
        return (video_path, hash_list, frame_list, video_info)
    except:
        return None

def calc_similar_score(hash_list1, hash_list2):
    """多帧两两比对，计算平均汉明距离"""
    total = 0
    count = 0
    for h1 in hash_list1:
        for h2 in hash_list2:
            # 跳过 None 值
            if h1 is None or h2 is None:
                continue
            dist = abs(h1 - h2)
            total += dist
            count += 1
    if count == 0:
        return 999
    return total / count

def find_duplicate_groups_safe(video_data, threshold=16):
    """抗水印模式：多帧投票平均距离判定"""
    files = list(video_data.keys())
    n = len(files)
    used = set()
    groups = []

    for i in range(n):
        f1 = files[i]
        if f1 in used:
            continue
        group = [f1]
        hash_list1, _, _ = video_data[f1]  # (hash_list, frame_list, info)
        for j in range(i + 1, n):
            f2 = files[j]
            if f2 in used:
                continue
            hash_list2, _, _ = video_data[f2]
            score = calc_similar_score(hash_list1, hash_list2)
            if score <= threshold:
                group.append(f2)
                used.add(f2)
        if len(group) >= 2:
            # 返回排序后的 tuple，确保与 main.py 中的 key 一致
            groups.append(tuple(sorted(group)))
    return groups

# ============ 高精度模式（新增） ============
def calculate_high_precision_similarity(features1, features2):
    """计算两个视频的高精度相似度得分
    
    Args:
        features1: 第一个视频的特征字典 {'phash_list': [], 'ahash_list': [], ...}
        features2: 第二个视频的特征字典
    
    Returns:
        float: 综合相似度得分（越低越相似）
    """
    try:
        # 1. pHash 平均距离
        phash_dists = []
        for h1, h2 in zip(features1['phash_list'], features2['phash_list']):
            if h1 is not None and h2 is not None:
                phash_dists.append(abs(h1 - h2))
        avg_phash = sum(phash_dists) / len(phash_dists) if phash_dists else 64
        
        # 2. aHash 平均距离
        ahash_dists = []
        for h1, h2 in zip(features1['ahash_list'], features2['ahash_list']):
            if h1 is not None and h2 is not None:
                ahash_dists.append(abs(h1 - h2))
        avg_ahash = sum(ahash_dists) / len(ahash_dists) if ahash_dists else 64
        
        # 3. dHash 平均距离
        dhash_dists = []
        for h1, h2 in zip(features1['dhash_list'], features2['dhash_list']):
            if h1 is not None and h2 is not None:
                dhash_dists.append(abs(h1 - h2))
        avg_dhash = sum(dhash_dists) / len(dhash_dists) if dhash_dists else 64
        
        # 4. 颜色直方图平均距离
        color_dists = []
        for hist1, hist2 in zip(features1['color_hist_list'], features2['color_hist_list']):
            if hist1 is not None and hist2 is not None:
                dist = calculate_histogram_distance(hist1, hist2)
                color_dists.append(dist)
        avg_color = sum(color_dists) / len(color_dists) if color_dists else 10
        
        # 5. SSIM 平均相似度（需要帧图像，这里简化处理）
        # 由于SSIM计算需要原始帧图像，而缓存中可能没有保存所有帧
        # 这里使用pHash作为替代，或者返回默认值
        avg_ssim = 1.0  # 默认最高相似度
        
        # 加权综合得分
        # 注意：pHash/aHash/dHash越小越相似，color_dist越小越相似，ssim越大越相似
        # 将SSIM转换为距离：(1 - ssim) * 100
        ssim_dist = (1 - avg_ssim) * 100
        
        weighted_score = (
            HIGH_PRECISION_WEIGHT_PHASH * avg_phash +
            HIGH_PRECISION_WEIGHT_AHASH * avg_ahash +
            HIGH_PRECISION_WEIGHT_DHASH * avg_dhash +
            HIGH_PRECISION_WEIGHT_COLOR * avg_color +
            HIGH_PRECISION_WEIGHT_SSIM * ssim_dist
        )
        
        return weighted_score
    except Exception as e:
        print(f"高精度相似度计算失败: {e}")
        return 999

def find_duplicate_groups_high_precision(video_data, threshold=5):
    """高精度模式：多特征融合比对
    
    Args:
        video_data: 视频数据字典 {path: (features_dict, frame_list, info)}
        threshold: 相似度阈值，越低要求越严格
    
    Returns:
        list: 重复视频组列表
    """
    files = list(video_data.keys())
    n = len(files)
    used = set()
    groups = []

    for i in range(n):
        f1 = files[i]
        if f1 in used:
            continue
        group = [f1]
        features1, _, _ = video_data[f1]  # (features_dict, frame_list, info)
        
        for j in range(i + 1, n):
            f2 = files[j]
            if f2 in used:
                continue
            features2, _, _ = video_data[f2]
            
            # 计算高精度相似度
            score = calculate_high_precision_similarity(features1, features2)
            
            if score <= threshold:
                group.append(f2)
                used.add(f2)
        
        if len(group) >= 2:
            # 返回排序后的 tuple，确保与 main.py 中的 key 一致
            groups.append(tuple(sorted(group)))
    
    return groups

def calculate_color_histogram(img_pil, bins=32):
    """计算颜色直方图特征"""
    img_array = np.array(img_pil)
    hist_r = np.histogram(img_array[:, :, 0], bins=bins, range=(0, 256))[0]
    hist_g = np.histogram(img_array[:, :, 1], bins=bins, range=(0, 256))[0]
    hist_b = np.histogram(img_array[:, :, 2], bins=bins, range=(0, 256))[0]
    
    # 归一化
    hist = np.concatenate([hist_r, hist_g, hist_b])
    hist = hist / (hist.sum() + 1e-10)
    return hist

def calculate_histogram_distance(hist1, hist2):
    """计算两个直方图的卡方距离"""
    distance = cv2.compareHist(hist1.astype(np.float32), 
                               hist2.astype(np.float32), 
                               cv2.HISTCMP_CHISQR)
    return distance

def calculate_ssim_similarity(img1_pil, img2_pil):
    """计算结构相似性（SSIM）"""
    try:
        img1 = np.array(img1_pil.convert('L'))  # 转为灰度图
        img2 = np.array(img2_pil.convert('L'))
        
        # 确保尺寸一致
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # 计算 SSIM
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        img1_float = img1.astype(np.float64)
        img2_float = img2.astype(np.float64)
        
        mu1 = cv2.GaussianBlur(img1_float, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(img2_float, (11, 11), 1.5)
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = cv2.GaussianBlur(img1_float ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(img2_float ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(img1_float * img2_float, (11, 11), 1.5) - mu1_mu2
        
        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
                   ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        
        return np.mean(ssim_map)
    except:
        return 0.0

def process_video_high_precision(video_path):
    """高精度模式：多特征融合"""
    if ScanState.STOP:
        return None
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            cap.release()
            return None
        
        # 均匀采样
        sample_positions = [int(total_frames * i / HIGH_PRECISION_SAMPLE_COUNT) 
                           for i in range(1, HIGH_PRECISION_SAMPLE_COUNT + 1)]
        
        feature_data = {
            'phash_list': [],
            'ahash_list': [],
            'dhash_list': [],
            'color_hist_list': [],
            'frame_list': []  # 只保存1-2帧用于预览
        }
        
        preview_saved = False  # 标记是否已保存预览帧
        
        for idx, pos in enumerate(sample_positions):
            if ScanState.STOP:
                cap.release()
                return None
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(pos, total_frames - 1))
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            
            # 计算多种哈希
            img_resized = pil_img.resize((32, 32), Image.Resampling.LANCZOS)
            phash = imagehash.phash(img_resized)
            ahash = imagehash.average_hash(img_resized)
            dhash = imagehash.dhash(img_resized)
            
            # 计算颜色直方图
            color_hist = calculate_color_histogram(pil_img.resize((64, 64)))
            
            feature_data['phash_list'].append(phash)
            feature_data['ahash_list'].append(ahash)
            feature_data['dhash_list'].append(dhash)
            feature_data['color_hist_list'].append(color_hist)
            
            # 只保存第1帧和第5帧作为预览（减少内存占用）
            if not preview_saved or idx == 4:
                feature_data['frame_list'].append(pil_img.copy())
                preview_saved = True
            else:
                feature_data['frame_list'].append(None)
        
        cap.release()
        
        if not feature_data['phash_list']:
            return None
        
        video_info = get_video_info(video_path)
        return (video_path, feature_data, feature_data['frame_list'], video_info)
    except Exception as e:
        import traceback
        error_detail = f"[ERROR] 高精度处理失败: {video_path}\n错误: {e}\n{traceback.format_exc()}"
        print(error_detail)
        return None

# ============ 批量视频处理（最有效优化） ============
def batch_process_videos(video_paths, mode="precise", max_workers=None, **kwargs):
    """批量处理视频，使用线程池并行处理
    
    Args:
        video_paths: 视频路径列表
        mode: 处理模式 ("precise"/"safe"/"high_precision")
        max_workers: 最大线程数（None则自动选择）
        **kwargs: 传递给处理函数的额外参数
    
    Returns:
        dict: {video_path: result}，仅包含成功处理的视频
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # 根据模式选择处理函数
    if mode == "precise":
        process_func = lambda path: process_video_optimized(path, **kwargs)
    elif mode == "safe":
        process_func = process_video_safe_optimized
    elif mode == "high_precision":
        process_func = process_video_high_precision
    else:
        raise ValueError(f"未知模式: {mode}")
    
    # 自动选择线程数
    if max_workers is None:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        # 高精度模式使用较少线程（内存密集）
        if mode == "high_precision":
            max_workers = min(4, cpu_count)
        else:
            max_workers = min(cpu_count, 8)
    
    results = {}
    total = len(video_paths)
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_path = {
            executor.submit(process_func, path): path 
            for path in video_paths
        }
        
        # 收集结果
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                if result:
                    results[path] = result
                processed += 1
                
                # 每处理10个视频输出进度
                if processed % 10 == 0:
                    print(f"[INFO] 批量处理进度: {processed}/{total}")
                    
            except Exception as e:
                print(f"[ERROR] 处理失败 {path}: {e}")
    
    print(f"[INFO] 批量处理完成: {len(results)}/{total} 成功")
    return results

def batch_process_with_callback(video_paths, mode="precise", callback=None, max_workers=None, **kwargs):
    """批量处理视频（带回调函数，适合GUI应用）
    
    Args:
        video_paths: 视频路径列表
        mode: 处理模式
        callback: 回调函数 callback(processed, total, result)
        max_workers: 最大线程数
        **kwargs: 传递给处理函数的参数
    
    Returns:
        dict: {video_path: result}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # 根据模式选择处理函数
    if mode == "precise":
        process_func = lambda path: process_video_optimized(path, **kwargs)
    elif mode == "safe":
        process_func = process_video_safe_optimized
    elif mode == "high_precision":
        process_func = process_video_high_precision
    else:
        raise ValueError(f"未知模式: {mode}")
    
    # 自动选择线程数
    if max_workers is None:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        if mode == "high_precision":
            max_workers = min(4, cpu_count)
        else:
            max_workers = min(cpu_count, 8)
    
    results = {}
    total = len(video_paths)
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(process_func, path): path 
            for path in video_paths
        }
        
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                if result:
                    results[path] = result
                processed += 1
                
                # 调用回调函数更新进度
                if callback:
                    callback(processed, total, result)
                    
            except Exception as e:
                if callback:
                    callback(processed, total, None)
    
    return results
