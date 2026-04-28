"""
视频相似度比对模块 - 负责去重算法、评分计算
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter
import imagehash
from config import *


def find_duplicate_groups(video_data, hash_limit):
    """精确模式：逐帧严格比对
    
    Args:
        video_data: 视频数据字典 {path: (hash_list, frame_list, info)}
        hash_limit: 哈希距离阈值
    
    Returns:
        list: 重复视频组列表，每组为排序后的tuple
    """
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


def calc_similar_score(hash_list1, hash_list2):
    """多帧两两比对，计算平均汉明距离
    
    Args:
        hash_list1: 第一个视频的哈希列表
        hash_list2: 第二个视频的哈希列表
    
    Returns:
        float: 平均汉明距离（越低越相似）
    """
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
    """抗水印模式：多帧投票平均距离判定
    
    Args:
        video_data: 视频数据字典 {path: (hash_list, frame_list, info)}
        threshold: 相似度阈值
    
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
    """计算颜色直方图特征
    
    Args:
        img_pil: PIL图像对象
        bins: 直方图bin数量
    
    Returns:
        np.ndarray: 归一化的RGB直方图
    """
    img_array = np.array(img_pil)
    hist_r = np.histogram(img_array[:, :, 0], bins=bins, range=(0, 256))[0]
    hist_g = np.histogram(img_array[:, :, 1], bins=bins, range=(0, 256))[0]
    hist_b = np.histogram(img_array[:, :, 2], bins=bins, range=(0, 256))[0]
    
    # 归一化
    hist = np.concatenate([hist_r, hist_g, hist_b])
    hist = hist / (hist.sum() + 1e-10)
    return hist


def calculate_histogram_distance(hist1, hist2):
    """计算两个直方图的卡方距离
    
    Args:
        hist1: 第一个直方图
        hist2: 第二个直方图
    
    Returns:
        float: 卡方距离
    """
    distance = cv2.compareHist(hist1.astype(np.float32), 
                               hist2.astype(np.float32), 
                               cv2.HISTCMP_CHISQR)
    return distance


def calculate_ssim_similarity(img1_pil, img2_pil):
    """计算结构相似性（SSIM）
    
    Args:
        img1_pil: 第一个PIL图像
        img2_pil: 第二个PIL图像
    
    Returns:
        float: SSIM值（0-1，越高越相似）
    """
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
    from .video_processor import process_video_optimized, process_video_safe_optimized, process_video_high_precision
    
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
    from .video_processor import process_video_optimized, process_video_safe_optimized, process_video_high_precision
    
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
