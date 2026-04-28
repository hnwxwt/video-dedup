# 视频去重工具 - 架构说明

## 📁 项目结构

```
video/
├── main.py              # 🚀 唯一入口（UI控制器）
├── config.py            # ⚙️ 兼容层（转发到 src/config.py）
├── video_cache.py       # 💾 缓存系统（1322行，单文件优化版）
│
├── src/                 # 📦 所有业务代码
│   ├── config.py        # ⚙️ 全局配置（常量定义）
│   ├── core/            # 核心业务逻辑
│   │   ├── __init__.py  # 导出公共API
│   │   ├── state.py     # 扫描状态管理（15行）
│   │   ├── video_processor.py  # 视频处理（400行）
│   │   ├── comparator.py       # 相似度比对（320行）
│   │   └── scanner.py          # 扫描工作线程（184行）
│   ├── ui/              # UI层
│   │   ├── __init__.py  # 导出公共API
│   │   ├── translations.py     # 国际化翻译（170行）
│   │   ├── main_window.py      # 主窗口UI（350行）
│   │   ├── settings_window.py  # 设置窗口（150行）
│   │   └── language_manager.py # 语言管理（40行）
│   └── utils/           # 工具层
│       ├── __init__.py  # 导出公共API
│       ├── progress.py  # 进度管理（100行）
│       └── video_cache/ # 缓存系统兼容层（转发到根目录）
│           └── __init__.py
│
├── docs/                # 📚 文档
│   ├── ARCHITECTURE.md  # 架构说明
│   ├── CHANGELOG.md     # 变更日志
│   └── CONTRIBUTING.md  # 贡献指南
│
├── tests/               # 🧪 测试
│   ├── __init__.py
│   └── test_core.py     # 核心模块测试
│
├── .github/             # 🛠️ GitHub配置
│   └── workflows/
│       └── python-app.yml
│
├── assets/              # 🖼️ 资源文件
│
├── build/               # 🏗️ 构建产物
├── dist/                # 📦 发布包
│
├── requirements.txt     # 📦 依赖列表
├── setup.py             # 📦 构建配置
├── LICENSE              # 📄 许可证
├── README.md            # 📖 项目介绍
└── VERSION              # 🏷️ 版本号
```

## 🏗️ 模块职责

### main.py (920行)
- **职责**: UI事件处理、流程控制
- **主要功能**:
  - 启动GUI应用
  - 绑定按钮事件
  - 管理扫描流程（开始/暂停/停止）
  - 调用后端模块

### src/config.py (62行)
- **职责**: 全局配置
- **主要功能**:
  - 定义常量（线程数、阈值、格式等）
  - 提示信息配置

### src/core/ (核心业务逻辑)

#### state.py (15行)
- **职责**: 扫描状态管理
- **内容**: 
  - `ScanState` 类（STOP/PAUSE标志）
  - `reset_state()` 函数

#### video_processor.py (400行)
- **职责**: 视频帧提取与哈希计算
- **主要功能**:
  - `get_video_info()` - 获取视频元信息
  - `normalize_frame()` - 帧标准化（旋转/裁剪/缩放）
  - `process_video_optimized()` - 精确模式处理
  - `process_video_safe_optimized()` - 抗水印模式处理
  - `process_video_high_precision()` - 高精度模式处理

#### comparator.py (320行)
- **职责**: 相似度比对与去重算法
- **主要功能**:
  - `find_duplicate_groups()` - 精确模式去重
  - `find_duplicate_groups_safe()` - 抗水印模式去重
  - `find_duplicate_groups_high_precision()` - 高精度模式去重
  - `calc_similar_score()` - 计算汉明距离
  - `batch_process_videos()` - 批量并行处理

#### scanner.py (184行)
- **职责**: 后台扫描线程
- **主要功能**:
  - 多线程任务分发
  - 缓存检查与加载
  - 进度回调
  - 暂停/停止状态管理

### src/ui/ (UI层)

#### translations.py (170行)
- **职责**: 国际化翻译字典
- **内容**: 
  - `TRANSLATIONS` - 中英文翻译字典
  - `set_language()` / `get_text()` - 翻译函数

#### settings_window.py (150行)
- **职责**: 设置对话框
- **主要功能**:
  - `open_settings_window()` - 创建设置窗口
  - `toggle_single_hint()` - 切换提示框显示

#### main_window.py (350行)
- **职责**: 主界面布局
- **主要功能**:
  - `create_ui()` - 创建主窗口所有组件
  - 两栏布局、进度条、预览区域等

#### language_manager.py (40行)
- **职责**: 语言偏好管理
- **主要功能**:
  - `save_language_preference()` - 保存语言配置
  - `load_language_preference()` - 加载语言配置
  - `refresh_ui_language()` - 刷新UI语言

### src/utils/ (工具模块)

#### progress.py (100行)
- **职责**: 进度管理
- **主要功能**:
  - `save_progress()` - 保存扫描进度
  - `load_progress()` - 加载扫描进度

### video_cache.py (1322行) ⭐保持单文件
- **职责**: 智能缓存系统
- **设计决策**: 保持单文件，原因：
  1. 高度优化的单一职责模块
  2. 内部函数依赖复杂，拆分风险高
  3. 当前结构清晰，易于维护
- **主要功能**:
  - 分片存储（按项目隔离）
  - 增量保存（只保存变化）
  - 懒加载（按需读取）
  - 预加载线程
  - LRU内存清理

## 🔄 数据流

```
用户操作 → main.py事件处理 → src.core业务逻辑 → src.core.scanner后台扫描
                                    ↓
                            video_cache.py缓存读写
                                    ↓
                              结果返回UI显示
```

## 🚀 性能优化

### 缓存系统
- **分片存储**: 每个项目独立目录，避免全量加载
- **增量保存**: 只保存新增/修改的分片，减少I/O
- **懒加载**: 首次访问时加载对应分片，启动秒开
- **预加载**: 后台线程预取下一个视频缓存

### 扫描加速
- **多线程**: 支持4-8线程并发（高精度模式限制4线程）
- **缓存命中**: 优先使用缓存，跳过重复扫描
- **异步IO**: 磁盘操作不阻塞主线程

## 📝 开发指南

### 添加新功能
1. **UI相关** → 修改 `src/ui/` 对应模块
   - 翻译文本 → `translations.py`
   - 设置窗口 → `settings_window.py`
   - 主窗口 → `main_window.py`
   - 语言管理 → `language_manager.py`
2. **状态管理** → 修改 `src/core/state.py`
3. **视频处理** → 修改 `src/core/video_processor.py`
4. **比对算法** → 修改 `src/core/comparator.py`
5. **扫描线程** → 修改 `src/core/scanner.py`
6. **进度管理** → 修改 `src/utils/progress.py`
7. **缓存优化** → 修改 `video_cache.py`
8. **流程控制** → 修改 `main.py`

### 导入规范
```python
# ✅ 推荐方式（新代码）
from src.core import ScanState, process_video_optimized, scan_worker
from src.ui import create_ui, get_text
from src.utils.progress import save_progress, load_progress
from src.utils.video_cache import get_cached_video
from src.config import MIN_THREAD, MAX_THREAD

# ✅ 兼容方式（旧代码仍有效）
from core import ScanState
from ui import create_ui
from progress import save_progress, load_progress
from scanner import scan_worker
from video_cache import get_cached_video
from config import MIN_THREAD, MAX_THREAD
```

### 调试技巧
- 查看日志输出（带时间戳）
- 检查缓存目录结构：`video_cache_shards/projects/`
- 监控内存占用：`check_memory_usage()`

## ⚠️ 注意事项

1. **不要直接修改缓存文件** - 使用提供的API
2. **停止扫描后等待缓存保存完成** - 约几秒
3. **切换项目时自动隔离缓存** - 无需手动清理
4. **高精度模式内存占用高** - 建议≤4线程
5. **向后兼容** - 根目录的 scanner.py、core.py、ui.py、progress.py、config.py 是兼容层
6. **video_cache.py 保持单文件** - 已高度优化，无需拆分
7. **config.py 保持根目录兼容** - 通过转发层保持兼容性
