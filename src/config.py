"""
全局配置模块 - 定义所有常量配置

职责:
- 视频格式支持
- 线程数配置
- 哈希阈值范围
- 高精度模式参数
- 用户提示信息
"""

# ========== 基础配置 ==========
VIDEO_FORMATS = (".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".mpg", ".mpeg")
CAPTURE_POSITIONS = [0.2, 0.5, 0.8]

DEFAULT_THUMB_W = 220
DEFAULT_THUMB_H = 280

# ========== 线程配置 ==========
MIN_THREAD = 4
MAX_THREAD = 20
DEFAULT_THREAD = 8

# ========== 精确模式配置 ==========
MIN_HASH_LIMIT = 5
MAX_HASH_LIMIT = 15
DEFAULT_HASH_LIMIT = 8

# ========== 抗水印模式配置 ==========
MIN_HASH_LIMIT_SAFE = 12
MAX_HASH_LIMIT_SAFE = 24
DEFAULT_HASH_LIMIT_SAFE = 16
CUT_RATIO = 0.15  # 中心裁剪比例

STANDARD_W = 360
STANDARD_H = 640

# ========== 进度保存 ==========
SAVE_PROGRESS_PATH = "scan_progress.json"

# ========== 高精度模式配置 ==========
HIGH_PRECISION_SAMPLE_COUNT = 10  # 采样帧数量
HIGH_PRECISION_SSIM_THRESHOLD = 0.95  # SSIM 相似度阈值
HIGH_PRECISION_WEIGHT_PHASH = 0.3  # pHash 权重
HIGH_PRECISION_WEIGHT_AHASH = 0.2  # aHash 权重
HIGH_PRECISION_WEIGHT_DHASH = 0.2  # dHash 权重
HIGH_PRECISION_WEIGHT_COLOR = 0.15  # 颜色直方图权重
HIGH_PRECISION_WEIGHT_SSIM = 0.15  # SSIM 权重

# 高精度模式线程数限制（避免内存溢出）
HIGH_PRECISION_MAX_THREADS = 4  # 最大线程数
HIGH_PRECISION_DEFAULT_THREADS = 2  # 默认线程数

# ========== 用户提示信息 ==========
CPU_THREAD_HINT = """【线程数选择参考 · 根据自己CPU选择】
1. 双核/老旧低压CPU： 2～3 线程（最稳不卡顿）
2. 四核4线程（i3-8100等）： 4～6 线程（均衡稳定）
3. 六核/八核主流CPU： 8～12 线程（日常全速）
4. 十核及以上高性能CPU：12～16 线程（极速扫描）"""

HASH_LIMIT_HINT = """【哈希相似度阈值推荐-精确模式】
严格精准防误判：5～7
日常通用平衡：8（默认）
适度放宽提召回：9～11
宽松模式查更多：12～15"""

HASH_LIMIT_SAFE_HINT = """【哈希相似度阈值推荐-抗水印模式】
严格精准防误判：12～14
日常通用平衡：16（默认）
适度放宽提召回：17～19
宽松模式查更多：20～24"""

# 抗水印模式采样率
SAFE_SAMPLE_RATES = [0.15, 0.3, 0.45, 0.6, 0.75, 0.9]
