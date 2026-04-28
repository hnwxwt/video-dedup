import json
import os
import base64
import hashlib
import gzip
import time
import gc
import threading
from io import BytesIO
from collections import OrderedDict
from typing import Dict, Optional, Tuple, List, Any, Set

"""
视频缓存系统 - 智能分片存储与增量保存

架构设计:
- 分片存储: 按项目隔离，每个项目独立目录
- 增量保存: 只保存变化的分片，减少I/O
- 懒加载: 按需读取分片，启动秒开
- 预加载: 后台线程异步预取下一个视频

性能优化:
- 压缩存储: gzip压缩节省50%空间
- 内存缓存: 全局单例避免重复加载
- 智能清理: LRU策略淘汰冷数据
- 完整性校验: MD5校验和检测损坏

使用方式:
    from video_cache import get_cached_video, save_video_cache
    # 或（新代码推荐）
    from src.utils.video_cache import get_cached_video, save_video_cache
"""
import os
import base64
import hashlib
import gzip
import time
import gc
import threading
from io import BytesIO
from collections import OrderedDict
from typing import Dict, Optional, Tuple, List, Any, Set

# ========== 分片缓存配置 ==========
CACHE_SHARD_SIZE = 500  # 每个分片包含的视频数量（从1000降低到500，减少分片数）
CACHE_DIR = "video_cache_shards"  # 分片缓存目录
ENABLE_COMPRESSION = True  # 启用gzip压缩（节省50%空间）

# ========== 增量保存配置 ==========
SAVE_INTERVAL = 100  # 每处理100个视频自动保存一次（从50增加到100，减少I/O次数）
_processed_count = 0  # 已处理视频计数

# ========== LRU缓存配置 ==========
MAX_MEMORY_MB = 500  # 最大内存占用（MB）

# 内存缓存（全局单例）
_memory_cache: Optional[Dict[str, Any]] = None  # None表示未初始化
_memory_cache_hp: Optional[Dict[str, Any]] = None  # 高精度模式独立缓存
_cache_dirty = False
_cache_dirty_hp = False
_loaded_shards: Set[str] = set()  # 已加载的分片集合
_current_scan_dir: Optional[str] = None  # 当前扫描目录
_log_callback = None  # 日志回调函数

# ========== 预加载配置 ==========
PREFETCH_QUEUE_SIZE = 5  # 预加载队列大小
_prefetch_queue = None  # 延迟初始化
_prefetch_thread = None
_prefetch_stop_event = None

def _init_prefetch_queue():
    """初始化预加载队列（延迟初始化，避免循环导入）"""
    global _prefetch_queue, _prefetch_stop_event
    if _prefetch_queue is None:
        from queue import Queue
        import threading
        _prefetch_queue = Queue(maxsize=PREFETCH_QUEUE_SIZE)
        _prefetch_stop_event = threading.Event()

def _prefetch_worker():
    """后台预加载线程"""
    while not _prefetch_stop_event.is_set():
        try:
            from queue import Empty
            video_path, is_high_precision = _prefetch_queue.get(timeout=1)
            _ensure_shard_loaded(video_path, is_high_precision)
            _prefetch_queue.task_done()
        except Empty:
            continue
        except Exception as e:
            _log_message(f"[WARNING] 预加载失败: {e}")

def start_prefetch_thread():
    """启动预加载线程"""
    global _prefetch_thread
    _init_prefetch_queue()
    
    if _prefetch_thread is None or not _prefetch_thread.is_alive():
        _prefetch_stop_event.clear()
        _prefetch_thread = threading.Thread(target=_prefetch_worker, daemon=True)
        _prefetch_thread.start()
        _log_message("[INFO] 预加载线程已启动")

def stop_prefetch_thread():
    """停止预加载线程"""
    global _prefetch_thread
    if _prefetch_stop_event:
        _prefetch_stop_event.set()
    
    if _prefetch_thread and _prefetch_thread.is_alive():
        _prefetch_thread.join(timeout=2)
    _log_message("[INFO] 预加载线程已停止")

def prefetch_next_video(video_path, is_high_precision=False):
    """预加载下一个视频的缓存（非阻塞）"""
    _init_prefetch_queue()
    
    try:
        _prefetch_queue.put_nowait((video_path, is_high_precision))
    except:
        pass  # 队列满则忽略

# ========== 智能缓存管理器 ==========
class SmartCacheManager:
    """智能缓存管理器（热/温/冷数据分级）"""
    
    def __init__(self):
        self.hot_shards = set()      # 热数据：最近10次访问
        self.warm_shards = set()     # 温数据：最近100次访问
        self.access_count = {}       # 访问计数器
        self.last_access_time = {}   # 最后访问时间
    
    def record_access(self, shard_path):
        """记录分片访问"""
        import time
        
        # 更新访问计数
        self.access_count[shard_path] = self.access_count.get(shard_path, 0) + 1
        self.last_access_time[shard_path] = time.time()
        
        # 分类管理
        count = self.access_count[shard_path]
        
        if count > 10:
            self.hot_shards.add(shard_path)
            self.warm_shards.discard(shard_path)
        elif count > 3:
            self.warm_shards.add(shard_path)
            self.hot_shards.discard(shard_path)
    
    def get_eviction_candidates(self, keep_count=5):
        """获取淘汰候选分片"""
        all_loaded = list(_loaded_shards)
        
        # 优先级：热 > 温 > 冷
        protected = self.hot_shards | self.warm_shards
        
        # 保留最近访问的keep_count个分片
        recent = sorted(
            all_loaded, 
            key=lambda x: self.last_access_time.get(x, 0),
            reverse=True
        )[:keep_count]
        
        protected.update(recent)
        
        # 返回可淘汰的分片
        candidates = [s for s in all_loaded if s not in protected]
        return candidates

_smart_cache = SmartCacheManager()

# ========== 统计信息 ==========
class CacheStats:
    """缓存统计信息"""
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.shards_loaded = 0
        self.total_load_time = 0.0
        self.start_time = time.time()
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    @property
    def hit_rate(self):
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_summary(self):
        elapsed = time.time() - self.start_time
        return (
            f"缓存统计:\n"
            f"  命中率: {self.hit_rate:.1%}\n"
            f"  命中次数: {self.hits}\n"
            f"  未命中次数: {self.misses}\n"
            f"  已加载分片: {self.shards_loaded}\n"
            f"  运行时间: {elapsed:.1f}秒"
        )

_cache_stats = CacheStats()

def set_log_callback(callback):
    """设置日志回调函数，用于将缓存日志输出到UI
    
    Args:
        callback: 日志回调函数，接收一个字符串参数
    """
    global _log_callback
    _log_callback = callback

def set_current_scan_dir(scan_dir):
    """设置当前扫描目录，用于缓存隔离
    
    Args:
        scan_dir: 扫描根目录路径
    """
    global _current_scan_dir
    if scan_dir:
        _current_scan_dir = os.path.abspath(scan_dir)
        _log_message(f"[INFO] 缓存目录已设置为: {_get_cache_dir(False)}")

def _log_message(msg):
    """内部日志函数，优先使用回调，否则使用print"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    
    if _log_callback:
        try:
            _log_callback(formatted_msg)
        except:
            pass
    else:
        print(formatted_msg)

def check_memory_usage():
    """检查内存使用情况，超过阈值时自动清理"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > MAX_MEMORY_MB * 1.5:  # 超过阈值的1.5倍
            _log_message(f"[WARNING] 内存使用过高: {memory_mb:.0f}MB，执行垃圾回收...")
            gc.collect()
            
            # 如果仍然过高，清理旧分片
            if memory_mb > MAX_MEMORY_MB * 2:
                _log_message("[WARNING] 内存严重不足，清理旧缓存...")
                _evict_old_shards()
    except ImportError:
        # psutil未安装，跳过内存监控
        pass
    except Exception as e:
        _log_message(f"[WARNING] 内存监控失败: {e}")

def _evict_old_shards():
    """智能清理旧分片（基于热/温/冷分级）"""
    candidates = _smart_cache.get_eviction_candidates(keep_count=5)
    
    if not candidates:
        return
    
    removed_count = 0
    for shard_path in candidates:
        _loaded_shards.discard(shard_path)
        removed_count += 1
    
    if removed_count > 0:
        _log_message(f"[INFO] 智能清理 {removed_count} 个冷分片")
        gc.collect()

def _get_cache_dir(is_high_precision=False, scan_dir=None):
    """获取分片缓存目录（按扫描目录隔离）
    
    Args:
        is_high_precision: 是否为高精度模式
        scan_dir: 扫描根目录，如果为None则使用全局默认目录
    
    Returns:
        str: 缓存目录路径
    """
    global _current_scan_dir
    
    # 如果未指定scan_dir，使用当前扫描目录
    if scan_dir is None:
        scan_dir = _current_scan_dir
    
    # 基础目录
    base_dir = CACHE_DIR
    
    # 如果有扫描目录，创建子目录（使用目录名的哈希值避免路径过长）
    if scan_dir:
        # 规范化路径
        scan_dir = os.path.abspath(scan_dir)
        # 使用目录名的MD5哈希作为子目录名（避免特殊字符和路径过长问题）
        dir_hash = hashlib.md5(scan_dir.encode('utf-8')).hexdigest()[:12]
        # 同时保留可读的目录名（截断）
        dir_name = os.path.basename(scan_dir)
        if len(dir_name) > 20:
            dir_name = dir_name[:20]
        subdir_name = f"{dir_name}_{dir_hash}"
        base_dir = os.path.join(CACHE_DIR, "projects", subdir_name)
    
    # 模式子目录
    if is_high_precision:
        return os.path.join(base_dir, "high_precision")
    else:
        return os.path.join(base_dir, "normal")

def _get_shard_path(video_path, is_high_precision=False):
    """根据视频路径计算分片文件路径（自动使用扫描目录隔离）
    
    Args:
        video_path: 视频文件路径
        is_high_precision: 是否为高精度模式
    
    Returns:
        tuple: (分片文件路径, 分片ID)
    """
    global _current_scan_dir
    
    # 从视频路径推断扫描根目录
    scan_dir = _current_scan_dir
    if not scan_dir and video_path:
        # 如果未设置全局扫描目录，尝试从视频路径推断
        abs_video_path = os.path.abspath(video_path)
        # 向上查找包含多个视频的父目录作为根目录
        parent_dir = os.path.dirname(abs_video_path)
        # 简单策略：使用视频所在的第一层父目录
        scan_dir = parent_dir
    
    cache_dir = _get_cache_dir(is_high_precision, scan_dir)
    
    # 使用文件路径的哈希值确定分片
    path_hash = hashlib.md5(os.path.abspath(video_path).encode('utf-8')).hexdigest()
    shard_id = int(path_hash[:8], 16) % CACHE_SHARD_SIZE
    
    # 确保目录存在
    os.makedirs(cache_dir, exist_ok=True)
    
    # 如果启用压缩，返回.gz后缀
    if ENABLE_COMPRESSION:
        return os.path.join(cache_dir, f"shard_{shard_id}.json.gz"), shard_id
    else:
        return os.path.join(cache_dir, f"shard_{shard_id}.json"), shard_id

def _get_shard_index_path(is_high_precision=False):
    """获取分片索引文件路径"""
    cache_dir = _get_cache_dir(is_high_precision)
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "index.json")

def _load_shard_index(is_high_precision=False):
    """加载分片索引"""
    index_path = _get_shard_index_path(is_high_precision)
    try:
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        _log_message(f"[WARNING] 加载分片索引失败: {e}")
    return {}

def _save_shard_index(index, is_high_precision=False):
    """保存分片索引"""
    index_path = _get_shard_index_path(is_high_precision)
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_message(f"[ERROR] 保存分片索引失败: {e}")

def _load_shard(shard_path):
    """加载单个分片文件（支持gzip压缩）"""
    try:
        if os.path.exists(shard_path):
            # 判断是否为压缩文件
            if shard_path.endswith('.gz'):
                with gzip.open(shard_path, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(shard_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
    except Exception as e:
        error_msg = str(e)
        # ✅ 关键修复：如果是压缩文件损坏或JSON格式错误，直接删除
        should_delete = False
        
        # 检查是否为压缩文件损坏
        if "Compressed file ended before" in error_msg or "EOFError" in error_msg:
            should_delete = True
            reason = "压缩文件损坏"
        
        # ✅ 新增：检查是否为JSON解析错误
        elif "Expecting value" in error_msg or "JSONDecodeError" in error_msg:
            should_delete = True
            reason = "JSON格式错误"
        
        if should_delete:
            _log_message(f"[WARNING] 分片文件{reason}，自动删除: {shard_path}")
            try:
                os.remove(shard_path)
                # 同时删除校验和文件
                if os.path.exists(shard_path + '.md5'):
                    os.remove(shard_path + '.md5')
                _log_message(f"[INFO] 已删除损坏的分片文件，下次扫描将重新生成")
            except Exception as del_err:
                _log_message(f"[ERROR] 删除损坏分片失败: {del_err}")
        else:
            _log_message(f"[WARNING] 加载分片失败 {shard_path}: {e}")
    return {}

def _save_shard(shard_path, shard_data):
    """保存单个分片文件（支持gzip压缩）"""
    try:
        # 如果数据为空，删除分片文件
        if not shard_data:
            if os.path.exists(shard_path):
                os.remove(shard_path)
            return
        
        # 根据配置选择压缩或普通保存
        if ENABLE_COMPRESSION:
            # 确保文件名为.gz后缀
            if not shard_path.endswith('.gz'):
                shard_path = shard_path + '.gz'
            
            # 使用动态压缩级别
            compress_level = get_dynamic_compress_level()
            
            with gzip.open(shard_path, 'wt', encoding='utf-8', compresslevel=compress_level) as f:
                json.dump(shard_data, f, ensure_ascii=False, separators=(',', ':'))
        else:
            with open(shard_path, 'w', encoding='utf-8') as f:
                json.dump(shard_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _log_message(f"[ERROR] 保存分片失败 {shard_path}: {e}")

def _save_shard_with_checksum(shard_path, shard_data):
    """保存分片并生成MD5校验和
    
    Args:
        shard_path: 分片文件路径
        shard_data: 分片数据
    """
    # 先保存数据
    _save_shard(shard_path, shard_data)
    
    try:
        # 生成MD5校验和
        with open(shard_path, 'rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        
        # 保存校验和文件
        checksum_path = shard_path + '.md5'
        with open(checksum_path, 'w') as f:
            f.write(md5)
    except Exception as e:
        _log_message(f"[WARNING] 生成校验和失败: {e}")

def _verify_shard_integrity(shard_path):
    """验证分片完整性
    
    Args:
        shard_path: 分片文件路径
    
    Returns:
        bool: 是否通过验证
    """
    checksum_path = shard_path + '.md5'
    
    if not os.path.exists(checksum_path):
        return True  # 无校验和文件，跳过验证
    
    try:
        with open(shard_path, 'rb') as f:
            current_md5 = hashlib.md5(f.read()).hexdigest()
        
        with open(checksum_path, 'r') as f:
            expected_md5 = f.read().strip()
        
        is_valid = current_md5 == expected_md5
        
        if not is_valid:
            _log_message(f"[ERROR] 分片完整性校验失败: {shard_path}")
        
        return is_valid
    except Exception as e:
        _log_message(f"[WARNING] 验证分片完整性失败: {e}")
        return False

def safe_load_shard(shard_path, max_retries=3):
    """安全加载分片，带重试和修复
    
    Args:
        shard_path: 分片文件路径
        max_retries: 最大重试次数
    
    Returns:
        dict: 分片数据，失败返回空字典
    """
    for attempt in range(max_retries):
        try:
            # 验证完整性
            if os.path.exists(shard_path + '.md5'):
                if not _verify_shard_integrity(shard_path):
                    _log_message(f"[WARNING] 分片校验失败，尝试修复: {shard_path}")
                    _repair_shard(shard_path)
                    continue
            
            # 加载数据
            return _load_shard(shard_path)
        
        except Exception as e:
            _log_message(f"[WARNING] 加载分片失败 (尝试 {attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(0.5)  # 等待后重试
            else:
                _log_message(f"[ERROR] 分片加载失败，跳过: {shard_path}")
                return {}
    
    return {}

def _repair_shard(shard_path):
    """尝试修复损坏的分片"""
    backup_path = shard_path + '.backup'
    
    if os.path.exists(backup_path):
        _log_message(f"[INFO] 从备份恢复分片: {shard_path}")
        import shutil
        shutil.copy2(backup_path, shard_path)
    else:
        _log_message(f"[WARNING] 无备份可用，删除损坏分片: {shard_path}")
        if os.path.exists(shard_path):
            os.remove(shard_path)

def _migrate_old_cache(is_high_precision=False):
    """迁移旧版单文件缓存到分片缓存"""
    old_cache_path = VIDEO_CACHE_HIGH_PRECISION_PATH if is_high_precision else VIDEO_CACHE_PATH
    
    if not os.path.exists(old_cache_path):
        return
    
    try:
        _log_message(f"[INFO] 检测到旧版缓存文件，正在迁移到分片缓存...")
        
        with open(old_cache_path, 'r', encoding='utf-8') as f:
            old_cache = json.load(f)
        
        total_videos = len(old_cache)
        _log_message(f"[INFO] 迁移 {total_videos} 个视频缓存...")
        
        # 按分片分组
        shards = {}
        for video_path, data in old_cache.items():
            shard_path, shard_id = _get_shard_path(video_path, is_high_precision)
            if shard_path not in shards:
                shards[shard_path] = {}
            shards[shard_path][video_path] = data
        
        # 保存各个分片
        for shard_path, shard_data in shards.items():
            _save_shard(shard_path, shard_data)
        
        # 更新索引
        index = _load_shard_index(is_high_precision)
        for shard_path in shards.keys():
            shard_name = os.path.basename(shard_path)
            index[shard_name] = len(shards[shard_path])
        _save_shard_index(index, is_high_precision)
        
        # 备份旧文件
        backup_path = old_cache_path + ".backup"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(old_cache_path, backup_path)
        
        _log_message(f"[INFO] 迁移完成！旧缓存已备份为: {backup_path}")
        _log_message(f"[INFO] 分片缓存目录: {_get_cache_dir(is_high_precision)}")
        
    except Exception as e:
        _log_message(f"[ERROR] 迁移缓存失败: {e}")
        _log_message(f"[WARNING] 保留旧缓存文件，请手动处理")

def _initialize_cache(is_high_precision=False):
    """初始化缓存（旧版迁移逻辑已移除）"""
    pass

def _get_memory_cache(is_high_precision=False):
    """获取内存缓存（单例模式）"""
    global _memory_cache, _memory_cache_hp
    
    if is_high_precision:
        if _memory_cache_hp is None:
            _initialize_cache(is_high_precision=True)
            _memory_cache_hp = {}
        return _memory_cache_hp
    else:
        if _memory_cache is None:
            _initialize_cache(is_high_precision=False)
            _memory_cache = {}
        return _memory_cache

def _ensure_shard_loaded(video_path, is_high_precision=False):
    """确保视频所在的分片已加载到内存（懒加载）
    
    Args:
        video_path: 视频文件路径
        is_high_precision: 是否为高精度模式
    
    Returns:
        bool: 是否成功加载
    """
    global _loaded_shards
    
    shard_path, shard_id = _get_shard_path(video_path, is_high_precision)
    
    # 如果该分片已加载，记录访问并返回
    if shard_path in _loaded_shards:
        _smart_cache.record_access(shard_path)
        return True
    
    try:
        start_time = time.time()
        
        # 加载单个分片
        shard_data = _load_shard(shard_path)
        
        # 合并到内存缓存
        cache = _get_memory_cache(is_high_precision)
        cache.update(shard_data)
        
        # 标记为已加载
        _loaded_shards.add(shard_path)
        _cache_stats.shards_loaded += 1
        
        # 记录访问（智能缓存）
        _smart_cache.record_access(shard_path)
        
        # 记录加载时间
        load_time = time.time() - start_time
        _cache_stats.total_load_time += load_time
        
        # 检查内存使用情况
        check_memory_usage()
        
        return True
    except Exception as e:
        _log_message(f"[WARNING] 加载分片失败 {shard_path}: {e}")
        return False

def _load_cache_from_disk(is_high_precision=False):
    """从磁盘加载缓存到内存（主体改为懒加载）"""
    global _memory_cache, _memory_cache_hp
    
    # 懒加载模式下，此处不需要全量加载，只需确保内存字典已初始化
    # 初始化会在 _get_memory_cache 中自动完成
    pass

def save_video_cache_to_disk():
    """将内存缓存批量写入磁盘（分片模式 - 增量保存）"""
    global _cache_dirty, _cache_dirty_hp
    
    # 保存普通模式缓存
    if _cache_dirty and _memory_cache:
        try:
            # ✅ 关键修复：先复制字典快照，避免迭代时被其他线程修改
            cache_snapshot = dict(_memory_cache.items())
            
            # ✅ 加载现有索引，用于判断哪些分片需要更新
            index = _load_shard_index(is_high_precision=False)
            
            # 按分片分组
            shards = {}
            for video_path, data in cache_snapshot.items():
                shard_path, shard_id = _get_shard_path(video_path, is_high_precision=False)
                if shard_path not in shards:
                    shards[shard_path] = {}
                shards[shard_path][video_path] = data
            
            # ✅ 增量保存：只保存有变化的分片
            saved_count = 0
            for shard_path, shard_data in shards.items():
                shard_name = os.path.basename(shard_path)
                
                # 检查分片是否有变化（通过对比视频数量）
                old_count = index.get(shard_name, 0)
                new_count = len(shard_data)
                
                # 如果分片中视频数量增加，说明有新数据需要保存
                if new_count > old_count:
                    _save_shard(shard_path, shard_data)
                    index[shard_name] = new_count
                    saved_count += 1
            
            # 只在有分片被保存时才更新索引文件
            if saved_count > 0:
                _save_shard_index(index, is_high_precision=False)
                _log_message(f"[INFO] 已增量保存普通视频分片缓存: {len(cache_snapshot)} 个视频 ({saved_count} 个分片有更新)")
            else:
                _log_message(f"[INFO] 普通视频缓存无新数据，跳过保存")
            
            _cache_dirty = False
        except Exception as e:
            _log_message(f"[ERROR] 保存普通缓存失败: {e}")
    
    # 保存高精度模式缓存
    if _cache_dirty_hp and _memory_cache_hp:
        try:
            # ✅ 关键修复：先复制字典快照，避免迭代时被其他线程修改
            cache_snapshot = dict(_memory_cache_hp.items())
            
            # ✅ 加载现有索引，用于判断哪些分片需要更新
            index = _load_shard_index(is_high_precision=True)
            
            # 按分片分组
            shards = {}
            for video_path, data in cache_snapshot.items():
                shard_path, shard_id = _get_shard_path(video_path, is_high_precision=True)
                if shard_path not in shards:
                    shards[shard_path] = {}
                shards[shard_path][video_path] = data
            
            # ✅ 增量保存：只保存有变化的分片
            saved_count = 0
            for shard_path, shard_data in shards.items():
                shard_name = os.path.basename(shard_path)
                
                # 检查分片是否有变化
                old_count = index.get(shard_name, 0)
                new_count = len(shard_data)
                
                if new_count > old_count:
                    _save_shard(shard_path, shard_data)
                    index[shard_name] = new_count
                    saved_count += 1
            
            if saved_count > 0:
                _save_shard_index(index, is_high_precision=True)
                _log_message(f"[INFO] 已增量保存高精度视频分片缓存: {len(cache_snapshot)} 个视频 ({saved_count} 个分片有更新)")
            else:
                _log_message(f"[INFO] 高精度视频缓存无新数据，跳过保存")
            
            _cache_dirty_hp = False
        except Exception as e:
            _log_message(f"[ERROR] 保存高精度缓存失败: {e}")

def save_video_cache(video_path, hash_list, frame_list, video_info, is_high_precision=False):
    """保存单个视频的扫描结果到内存缓存（不立即写入磁盘）
    
    Args:
        video_path: 视频文件路径
        hash_list: 哈希列表或特征列表
        frame_list: 帧图像列表
        video_info: 视频信息字典
        is_high_precision: 是否为高精度模式（显式指定）
    """
    global _memory_cache, _memory_cache_hp, _cache_dirty, _cache_dirty_hp
    
    try:
        # 根据模式选择对应的缓存
        cache = _get_memory_cache(is_high_precision)
        
        # 生成缓存键（使用绝对路径）
        cache_key = os.path.abspath(video_path)
        
        # 获取文件信息用于验证（添加Windows长路径支持）
        try:
            # Windows系统：如果路径过长，使用\\?\前缀
            if os.name == 'nt' and len(cache_key) > 260:
                cache_key_for_stat = "\\\\?\\" + cache_key
            else:
                cache_key_for_stat = cache_key
            
            file_stat = os.stat(cache_key_for_stat)
            file_size = file_stat.st_size
            file_mtime = file_stat.st_mtime
        except OSError as e:
            _log_message(f"[WARNING] 无法获取文件信息: {video_path}, 错误: {e}")
            # 如果无法获取文件信息，使用默认值
            file_size = 0
            file_mtime = 0
        
        if is_high_precision:
            # 高精度模式：hash_list 是特征字典列表
            serialized_features_list = []
            for features in hash_list:
                if features is None:
                    serialized_features_list.append(None)
                    continue
                
                serialized_features = {}
                for key, value in features.items():
                    if key == 'frame_list':
                        # 帧列表单独处理
                        continue
                    elif isinstance(value, list):
                        # 哈希列表：转换为字符串
                        serialized_features[key] = [str(h) if h is not None else None for h in value]
                    else:
                        # 单个ImageHash对象：转换为字符串
                        serialized_features[key] = str(value) if value is not None else None
                
                serialized_features_list.append(serialized_features)
            
            # 序列化帧列表
            frame_b64_list = []
            for img in frame_list:
                if img is not None:
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    frame_b64_list.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
                else:
                    frame_b64_list.append(None)
            
            # 保存到内存缓存
            cache[cache_key] = {
                "file_size": file_size,
                "file_mtime": file_mtime,
                "features_list": serialized_features_list,  # 改为 features_list
                "frame_list": frame_b64_list,
                "video_info": video_info
            }
            
            _cache_dirty_hp = True
        else:
            # 传统模式：列表类型
            hash_str_list = [str(h) if h is not None else None for h in hash_list]
            frame_b64_list = []
            for img in frame_list:
                if img is not None:
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    frame_b64_list.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
                else:
                    frame_b64_list.append(None)
            
            # 保存到内存缓存
            cache[cache_key] = {
                "file_size": file_size,
                "file_mtime": file_mtime,
                "hash_list": hash_str_list,
                "frame_list": frame_b64_list,
                "video_info": video_info
            }
            
            _cache_dirty = True
        
        # 增量保存：每处理SAVE_INTERVAL个视频自动保存
        global _processed_count
        _processed_count += 1
        if _processed_count % SAVE_INTERVAL == 0:
            # 异步保存，不阻塞主线程
            threading.Thread(target=save_video_cache_to_disk, daemon=True).start()
            _log_message(f"[INFO] 已自动保存进度: {_processed_count} 个视频")
        
        return True
    except Exception as e:
        _log_message(f"[ERROR] 保存视频缓存失败: {video_path}, 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_cached_video(video_path, is_high_precision=False):
    """获取缓存的视频扫描结果，如果缓存失效则返回None
    
    Args:
        video_path: 视频文件路径
        is_high_precision: 是否为高精度模式（默认False）
    """
    try:
        cache_key = os.path.abspath(video_path)
        
        # 懒加载：确保当前视频所在的分片已加载
        _ensure_shard_loaded(video_path, is_high_precision)
        
        # 根据模式选择对应的缓存
        cache = _get_memory_cache(is_high_precision)
        
        if cache_key not in cache:
            # 缓存未命中
            _cache_stats.record_miss()
            return None
        
        # 缓存命中
        _cache_stats.record_hit()
        
        cached_data = cache[cache_key]
        
        # 验证文件是否变化（添加Windows长路径支持）
        if not os.path.exists(cache_key):
            return None
        
        try:
            # Windows系统：如果路径过长，使用\\?\前缀
            if os.name == 'nt' and len(cache_key) > 260:
                cache_key_for_stat = "\\\\?\\" + cache_key
            else:
                cache_key_for_stat = cache_key
            
            file_stat = os.stat(cache_key_for_stat)
            current_size = file_stat.st_size
            current_mtime = file_stat.st_mtime
        except OSError as e:
            _log_message(f"[WARNING] 无法验证缓存文件: {cache_key}, 错误: {e}")
            # 如果无法获取文件信息，认为缓存失效
            return None
        
        # 如果文件大小或修改时间变化，缓存失效
        if (current_size != cached_data["file_size"] or 
            abs(current_mtime - cached_data["file_mtime"]) > 1):
            _log_message(f"[INFO] {'高精度' if is_high_precision else '普通'}缓存失效: {cache_key}")
            return None
        
        # 反序列化数据
        import imagehash
        from PIL import Image
        
        if is_high_precision:
            # 高精度模式：反序列化特征字典列表
            features_list = []
            serialized_features_list = cached_data.get("features_list", [])
            
            for serialized_features in serialized_features_list:
                if serialized_features is None:
                    features_list.append(None)
                    continue
                
                features = {}
                for key, value in serialized_features.items():
                    if isinstance(value, list):
                        # 哈希列表：从字符串恢复
                        hash_list = []
                        for h_str in value:
                            if h_str is not None:
                                try:
                                    hash_list.append(imagehash.hex_to_hash(h_str))
                                except:
                                    hash_list.append(None)
                            else:
                                hash_list.append(None)
                        features[key] = hash_list
                    else:
                        # 单个ImageHash对象：从字符串恢复
                        if value is not None:
                            try:
                                features[key] = imagehash.hex_to_hash(value)
                            except:
                                features[key] = None
                        else:
                            features[key] = None
                features_list.append(features)
            
            # 反序列化帧列表
            frame_list = []
            for frame_b64 in cached_data.get("frame_list", []):
                if frame_b64 is not None:
                    try:
                        frame_list.append(Image.open(BytesIO(base64.b64decode(frame_b64))))
                    except:
                        frame_list.append(None)
                else:
                    frame_list.append(None)
            
            video_info = cached_data["video_info"]
            
            return (features_list, frame_list, video_info)
        else:
            # 传统模式：列表类型
            hash_list = []
            for h_str in cached_data["hash_list"]:
                if h_str is not None:
                    try:
                        hash_list.append(imagehash.hex_to_hash(h_str))
                    except:
                        hash_list.append(None)
                else:
                    hash_list.append(None)
            
            frame_list = []
            for frame_b64 in cached_data["frame_list"]:
                if frame_b64 is not None:
                    try:
                        frame_list.append(Image.open(BytesIO(base64.b64decode(frame_b64))))
                    except:
                        frame_list.append(None)
                else:
                    frame_list.append(None)
            
            video_info = cached_data["video_info"]
            
            return (hash_list, frame_list, video_info)
    except Exception as e:
        _log_message(f"[ERROR] 读取视频缓存失败: {video_path}, 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def _is_video_in_current_dir(video_path):
    """检查视频是否在当前扫描目录下"""
    if not _current_scan_dir:
        return True  # 未设置目录时，返回True（加载所有）
    
    video_abs = os.path.abspath(video_path)
    return video_abs.startswith(_current_scan_dir)

def _get_related_shards_for_dir(scan_dir, is_high_precision=False):
    """获取与指定目录相关的分片文件列表
    
    Args:
        scan_dir: 扫描目录路径
        is_high_precision: 是否为高精度模式
    
    Returns:
        相关分片文件路径列表
    """
    cache_dir = _get_cache_dir(is_high_precision)
    if not os.path.exists(cache_dir):
        return []
    
    related_shards = []
    index = _load_shard_index(is_high_precision)
    
    # 遍历索引中的所有分片
    for shard_name in index.keys():
        shard_path = os.path.join(cache_dir, shard_name)
        
        # 如果分片文件不存在，跳过
        if not os.path.exists(shard_path):
            continue
        
        # 加载分片数据（临时）
        shard_data = _load_shard(shard_path)
        
        # 检查是否有视频属于当前扫描目录
        has_related = False
        for video_path in shard_data.keys():
            if video_path.startswith(scan_dir):
                has_related = True
                break
        
        if has_related:
            related_shards.append(shard_path)
    
    return related_shards

def warmup_cache_for_directory(scan_dir, is_high_precision=False):
    """为指定目录预热缓存（批量加载相关分片）
    
    Args:
        scan_dir: 扫描目录路径
        is_high_precision: 是否为高精度模式
    """
    _log_message(f"[INFO] 正在预热 {scan_dir} 的缓存...")
    
    # 扫描目录下的所有视频文件
    video_files = []
    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v')
    
    for root, dirs, files in os.walk(scan_dir):
        for f in files:
            if f.lower().endswith(video_extensions):
                video_files.append(os.path.join(root, f))
    
    if not video_files:
        _log_message(f"[INFO] 目录 {scan_dir} 中未找到视频文件")
        return
    
    # 收集相关分片
    related_shards = set()
    for video_path in video_files:
        shard_path, _ = _get_shard_path(video_path, is_high_precision)
        related_shards.add(shard_path)
    
    # 批量加载
    loaded_count = 0
    total_count = len(related_shards)
    
    for i, shard_path in enumerate(related_shards, 1):
        if shard_path not in _loaded_shards:
            try:
                shard_data = _load_shard(shard_path)
                cache = _get_memory_cache(is_high_precision)
                cache.update(shard_data)
                _loaded_shards.add(shard_path)
                _cache_stats.shards_loaded += 1
                loaded_count += 1
                
                # 每加载10个分片输出一次进度
                if loaded_count % 10 == 0:
                    _log_message(f"[INFO] 缓存预热进度: {loaded_count}/{total_count}")
            except Exception as e:
                _log_message(f"[WARNING] 加载分片失败 {shard_path}: {e}")
    
    _log_message(f"[INFO] 缓存预热完成: 加载 {loaded_count}/{total_count} 个分片，共 {len(video_files)} 个视频")

def warmup_cache_parallel(scan_dir, is_high_precision=False, max_workers=4):
    """并行预热缓存（使用线程池）
    
    Args:
        scan_dir: 扫描目录路径
        is_high_precision: 是否为高精度模式
        max_workers: 最大并行线程数
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    _log_message(f"[INFO] 正在并行预热 {scan_dir} 的缓存（{max_workers}线程）...")
    
    # 收集所有相关分片
    related_shards = set()
    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v')
    
    for root, dirs, files in os.walk(scan_dir):
        for f in files:
            if f.lower().endswith(video_extensions):
                video_path = os.path.join(root, f)
                shard_path, _ = _get_shard_path(video_path, is_high_precision)
                related_shards.add(shard_path)
    
    # 过滤未加载的分片
    shards_to_load = [s for s in related_shards if s not in _loaded_shards]
    
    if not shards_to_load:
        _log_message("[INFO] 所有分片已加载，无需预热")
        return
    
    def load_single_shard(shard_path):
        """加载单个分片"""
        try:
            shard_data = _load_shard(shard_path)
            cache = _get_memory_cache(is_high_precision)
            cache.update(shard_data)
            _loaded_shards.add(shard_path)
            _cache_stats.shards_loaded += 1
            return True, shard_path
        except Exception as e:
            return False, str(e)
    
    # 并行加载
    loaded_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_shard = {
            executor.submit(load_single_shard, shard): shard 
            for shard in shards_to_load
        }
        
        for future in as_completed(future_to_shard):
            success, result = future.result()
            if success:
                loaded_count += 1
                if loaded_count % 10 == 0:
                    _log_message(f"[INFO] 已加载 {loaded_count}/{len(shards_to_load)} 个分片")
            else:
                failed_count += 1
                _log_message(f"[WARNING] 加载失败: {result}")
    
    _log_message(f"[INFO] 并行预热完成: {loaded_count} 成功, {failed_count} 失败")

def get_cache_stats():
    """获取缓存统计信息"""
    return _cache_stats.get_summary()


def get_cache_stats_summary():
    """获取缓存统计摘要（别名函数，用于兼容）"""
    return _cache_stats.get_summary()


def reset_cache_stats():
    """重置缓存统计信息"""
    global _cache_stats
    _cache_stats = CacheStats()

def flush_cache():
    """强制将内存缓存刷新到磁盘（别名函数）"""
    save_video_cache_to_disk()

def reset_memory_cache():
    """清空内存缓存（用于重新扫描）"""
    global _memory_cache, _memory_cache_hp, _cache_dirty, _cache_dirty_hp, _loaded_shards
    _memory_cache = None  # 重置为None，下次访问时重新初始化
    _memory_cache_hp = None
    _cache_dirty = False
    _cache_dirty_hp = False
    _loaded_shards.clear()  # 清空已加载分片记录

def clear_video_cache(mode="all"):
    """清空所有视频扫描缓存文件（支持分片缓存）
    
    Args:
        mode: 清除模式 - "precise"(精确), "safe"(抗水印), "high_precision"(高精度), "all"(全部)
    """
    global _memory_cache, _memory_cache_hp, _cache_dirty, _cache_dirty_hp
    
    # 清空内存缓存
    if mode == "all" or mode == "precise" or mode == "safe":
        _memory_cache = {}
        _cache_dirty = False
    
    if mode == "all" or mode == "high_precision":
        _memory_cache_hp = {}
        _cache_dirty_hp = False
    
    # 删除磁盘缓存文件
    try:
        import shutil
        
        # 删除分片缓存目录
        if mode == "all" or mode == "precise" or mode == "safe":
            normal_cache_dir = _get_cache_dir(is_high_precision=False)
            if os.path.exists(normal_cache_dir):
                shutil.rmtree(normal_cache_dir)
                _log_message(f"[INFO] 已删除普通分片缓存目录: {normal_cache_dir}")
        
        if mode == "all" or mode == "high_precision":
            hp_cache_dir = _get_cache_dir(is_high_precision=True)
            if os.path.exists(hp_cache_dir):
                shutil.rmtree(hp_cache_dir)
                _log_message(f"[INFO] 已删除高精度分片缓存目录: {hp_cache_dir}")
        
        return True
    except Exception as e:
        _log_message(f"[ERROR] 清空缓存失败: {e}")
        return False

def calculate_optimal_shard_size():
    """计算最优分片大小（根据平均缓存大小动态调整）
    
    Returns:
        int: 建议的分片大小
    """
    cache = _memory_cache or _memory_cache_hp
    if not cache:
        return CACHE_SHARD_SIZE
    
    try:
        # 计算平均每个视频的缓存大小
        total_size = 0
        sample_count = min(100, len(cache))  # 只采样前100个
        
        for i, (key, value) in enumerate(cache.items()):
            if i >= sample_count:
                break
            total_size += len(json.dumps(value).encode('utf-8'))
        
        avg_size_per_video = total_size / sample_count
        
        # 目标：每个分片约1-2MB
        target_shard_size_bytes = 1.5 * 1024 * 1024  # 1.5MB
        optimal_count = int(target_shard_size_bytes / avg_size_per_video)
        
        # 限制范围在100-5000之间
        optimal_count = max(100, min(5000, optimal_count))
        
        _log_message(f"[INFO] 建议分片大小: {optimal_count}（当前: {CACHE_SHARD_SIZE}）")
        return optimal_count
    except Exception as e:
        _log_message(f"[WARNING] 计算分片大小失败: {e}")
        return CACHE_SHARD_SIZE

def get_dynamic_compress_level():
    """根据CPU负载动态选择压缩级别
    
    Returns:
        int: 压缩级别（1-9）
    """
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        if cpu_percent < 30:
            return 9  # CPU空闲，使用高压缩率
        elif cpu_percent < 70:
            return 6  # 正常负载，平衡模式
        else:
            return 1  # 高负载，快速压缩
    except ImportError:
        # psutil未安装，返回默认值
        return 6
    except Exception:
        return 6

def incremental_compare(new_videos, existing_data, mode="precise"):
    """增量比对：只处理新增或变化的视频
    
    Args:
        new_videos: 新扫描的视频列表 [(path, data), ...]
        existing_data: 已有的视频数据字典 {path: (data, frames, info)}
        mode: 比对模式 (precise/safe/high_precision)
    
    Returns:
        新增的重复组列表 [(new_path, matched_path, score), ...]
    """
    _log_message(f"[INFO] 开始增量比对: {len(new_videos)} 个新视频")
    
    new_groups = []
    threshold_map = {
        "precise": 10,
        "safe": 20,
        "high_precision": 15
    }
    threshold = threshold_map.get(mode, 10)
    
    for new_path, new_data in new_videos:
        best_match = None
        best_score = float('inf')
        
        # 与已有视频比对
        for existing_path, existing_data_tuple in existing_data.items():
            existing_data_item = existing_data_tuple[0]
            
            # 计算相似度
            if isinstance(new_data, dict) and isinstance(existing_data_item, dict):
                from core import calculate_high_precision_similarity
                score = calculate_high_precision_similarity(new_data, existing_data_item)
            else:
                from core import calc_similar_score
                score = calc_similar_score(new_data, existing_data_item)
            
            # 判断是否重复
            if score < threshold and score < best_score:
                best_score = score
                best_match = existing_path
        
        # 如果找到重复，添加到结果
        if best_match:
            new_groups.append((new_path, best_match, best_score))
    
    _log_message(f"[INFO] 增量比对完成: 发现 {len(new_groups)} 组新重复")
    return new_groups

def batch_get_cached_videos(video_paths, is_high_precision=False):
    """批量获取缓存（减少I/O次数）
    
    Args:
        video_paths: 视频路径列表
        is_high_precision: 是否为高精度模式
    
    Returns:
        dict: {video_path: cached_data}，仅包含命中的缓存
    """
    results = {}
    
    # 按分片分组
    shard_groups = {}
    for path in video_paths:
        shard_path, _ = _get_shard_path(path, is_high_precision)
        if shard_path not in shard_groups:
            shard_groups[shard_path] = []
        shard_groups[shard_path].append(path)
    
    # 逐批加载
    for shard_path, paths in shard_groups.items():
        if shard_path not in _loaded_shards:
            shard_data = safe_load_shard(shard_path)  # 使用安全加载
            cache = _get_memory_cache(is_high_precision)
            cache.update(shard_data)
            _loaded_shards.add(shard_path)
            _smart_cache.record_access(shard_path)
        
        # 从内存中获取
        cache = _get_memory_cache(is_high_precision)
        for path in paths:
            cache_key = os.path.abspath(path)
            if cache_key in cache:
                results[path] = cache[cache_key]
    
    return results

def batch_save_video_cache(video_data_list):
    """批量保存视频缓存
    
    Args:
        video_data_list: [(video_path, hash_list, frame_list, video_info), ...]
    """
    for video_path, hash_list, frame_list, video_info in video_data_list:
        save_video_cache(video_path, hash_list, frame_list, video_info)
    
    # 统一保存
    save_video_cache_to_disk()


















