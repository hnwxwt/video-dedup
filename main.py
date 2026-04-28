import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import send2trash
from PIL import Image, ImageTk
import imagehash
import base64
from io import BytesIO
import re

# 抑制 OpenCV/FFmpeg 的警告日志（必须在导入 cv2 之前设置）
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"

# 重定向 stderr 以抑制 FFmpeg 警告（可选）
import io
class SuppressStderr:
    def __init__(self):
        self._stderr = None
        self._devnull = None
    
    def __enter__(self):
        self._stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self._stderr

# 注意：如果不想看到任何FFmpeg警告，可以在导入cv2前启用
# suppress_stderr = SuppressStderr()

from config import *
from core import reset_state, find_duplicate_groups, find_duplicate_groups_safe, calc_similar_score, ScanState
from ui import create_ui, load_language_preference

# 在应用启动前加载语言偏好
load_language_preference()

from scanner import scan_worker
from progress import save_progress, load_progress
from video_cache import clear_video_cache, flush_cache, reset_memory_cache


def parse_file_size(size_str):
    """解析文件大小字符串，返回MB数值"""
    try:
        match = re.search(r'([\d.]+)\s*MB', size_str)
        if match:
            return float(match.group(1))
        match = re.search(r'([\d.]+)\s*GB', size_str)
        if match:
            return float(match.group(1)) * 1024
        return 0
    except:
        return 0

def parse_resolution(res_str):
    """解析分辨率字符串，返回像素数"""
    try:
        # 支持 '1920x1080' 或 '1920×1080' 格式
        match = re.search(r'(\d+)[x×](\d+)', res_str, re.IGNORECASE)
        if match:
            return int(match.group(1)) * int(match.group(2))
        return 0
    except:
        return 0

def parse_duration(dur_str):
    """解析时长字符串，返回秒数"""
    try:
        parts = dur_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except:
        return 0

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("视频去重工具")
        self.geometry("1300x900")

        self.use_thread = tk.IntVar(value=1)
        self.rotate = tk.IntVar(value=1)
        self.resize = tk.IntVar(value=1)
        self.scan_subdir = tk.IntVar(value=0)

        self.thread_cnt = tk.IntVar(value=DEFAULT_THREAD)
        self.hash_val = tk.IntVar(value=DEFAULT_HASH_LIMIT)
        self.scan_path = tk.StringVar()
        self.prev_w = tk.StringVar(value=str(DEFAULT_THUMB_W))
        self.prev_h = tk.StringVar(value=str(DEFAULT_THUMB_H))

        # 新增变量
        self.sim_filter_val = tk.StringVar(value="100")

        self.mode_safe = False
        self.mode_high_precision = False

        self.video_list = []
        self.finished_idx = 0
        self.video_data = {}
        self.check_vars = []
        self.image_refs = []
        self.current_groups = []
        self.group_scores = {}  # 存储每组的相似度 {group: score}
        self.all_groups = []  # 所有原始组列表（用于筛选重置）
        self.scan_start_time = None  # 扫描开始时间

        create_ui(self, self)
        
        # 设置缓存日志回调，将日志输出到UI
        from video_cache import set_log_callback
        set_log_callback(self.log)

    def log(self, msg):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def update_progress(self):
        p = int(self.finished_idx / len(self.video_list) * 100) if self.video_list else 0
        self.progress_bar["value"] = p

    def select_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.scan_path.set(p)

    def get_videos(self, folder):
        v = []
        if self.scan_subdir.get():
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(VIDEO_FORMATS):
                        v.append(os.path.join(root, f))
        else:
            for f in os.listdir(folder):
                fp = os.path.join(folder, f)
                if os.path.isfile(fp) and f.lower().endswith(VIDEO_FORMATS):
                    v.append(fp)
        return v

    def start(self, resume=False):
        import time
        path = self.scan_path.get()
        if not path or not os.path.isdir(path):
            messagebox.showwarning("提示", "请选择文件夹")
            return
        
        # 记录扫描开始时间
        self.scan_start_time = time.time()
        
        # 设置当前扫描目录（用于按需加载缓存）
        from video_cache import set_current_scan_dir
        set_current_scan_dir(path)
        
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.NORMAL)
        # 删除对设置窗口中按钮的引用
        # self.btn_save 和 self.btn_load 现在在设置窗口中，通过设置窗口管理
        reset_state()
        
        # 如果不是恢复进度，重置内存缓存以便重新从磁盘加载
        if not resume:
            reset_memory_cache()
        
        self.video_list = self.get_videos(path)
        if not resume:
            self.finished_idx = 0
            self.video_data.clear()
            self.log_text.delete(1.0, tk.END)
            for w in self.preview_frame.winfo_children():
                w.destroy()
            self.check_vars.clear()
            self.image_refs.clear()
            self.current_groups = []
            self.group_scores = {}
            self.all_groups = []
            # 隐藏比对进度条
            self.compare_progress_bar.pack_forget()
            self.compare_progress_bar["value"] = 0
        self.log(f"✅ 找到 {len(self.video_list)} 个视频，从第 {self.finished_idx + 1} 个继续扫描")
        
        # 根据模式调整线程数
        mode_high_precision = getattr(self, 'mode_high_precision', False)
        if mode_high_precision:
            # 高精度模式：限制线程数避免内存溢出
            from config import HIGH_PRECISION_MAX_THREADS, HIGH_PRECISION_DEFAULT_THREADS
            max_threads = HIGH_PRECISION_MAX_THREADS
            default_threads = HIGH_PRECISION_DEFAULT_THREADS
            self.thread_num = max(1, min(max_threads, int(self.thread_cnt.get())))
            if self.thread_num > max_threads:
                self.log(f"⚠️ 高精度模式自动限制线程数为 {max_threads}（原设置：{int(self.thread_cnt.get())}）")
        else:
            # 普通模式：使用原有逻辑
            self.thread_num = max(MIN_THREAD, min(MAX_THREAD, int(self.thread_cnt.get())))
        
        # 启动预加载线程
        from video_cache import start_prefetch_thread
        start_prefetch_thread()
        
        threading.Thread(target=scan_worker, args=(self,), daemon=True).start()

    def pause(self):
        """暂停/继续扫描"""
        try:
            if not ScanState.PAUSE:
                # 暂停扫描
                ScanState.PAUSE = True
                self.btn_pause.config(text="▶ 继续", state=tk.DISABLED)
                self.log("\n[INFO] 正在暂停扫描，等待当前任务完成...")
                # 保存按钮保持启用，允许用户保存进度
            else:
                # 继续扫描
                ScanState.PAUSE = False
                self.btn_pause.config(text=" 暂停")
                self.log("\n[INFO] 继续扫描...")
                
                # 只在单线程模式下需要重新启动线程
                if not self.use_thread.get():
                    threading.Thread(target=scan_worker, args=(self,), daemon=True).start()
                else:
                    # 多线程模式下，线程池会自动继续处理
                    self.log("[INFO] 多线程扫描已恢复")
        except Exception as e:
            self.log(f"\n[ERROR] 暂停/继续操作失败: {str(e)}")
            self.btn_pause.config(text="⏸ 暂停", state=tk.NORMAL)

    def stop(self):
        """停止扫描"""
        try:
            ScanState.STOP = True
            ScanState.PAUSE = False
            self.btn_pause.config(text="⏸ 暂停", state=tk.NORMAL)
            self.log("\n[INFO] 正在停止扫描...")
            # 停止时保存缓存到磁盘
            flush_cache()
            self.log("\n[SUCCESS] 扫描已停止")
        except Exception as e:
            self.log(f"\n[ERROR] 停止操作失败: {str(e)}")

    def on_pause_done(self):
        """暂停完成回调"""
        self.log("\n[SUCCESS] 扫描已暂停")
        self.btn_pause.config(text="▶ 继续", state=tk.NORMAL)
        self.log("[INFO] 缓存已自动保存，可通过设置窗口导出进度备份")
        # 暂停时保存缓存到磁盘
        flush_cache()

    def on_scan_done(self):
        try:
            self.log("\n📊 开始比对重复...")
            
            # 显示比对进度条
            self.compare_progress_bar.pack(fill=tk.X)
            self.compare_progress_bar["value"] = 0
            
            if self.mode_high_precision:
                mode_name = "高精度"
                from core import find_duplicate_groups_high_precision
                groups = find_duplicate_groups_high_precision(self.video_data, int(self.hash_val.get()))
            elif self.mode_safe:
                mode_name = "抗水印"
                groups = find_duplicate_groups_safe(self.video_data, int(self.hash_val.get()))
            else:
                mode_name = "精确"
                groups = find_duplicate_groups(self.video_data, int(self.hash_val.get()))
            
            self.log(f"📋 使用模式：{mode_name}模式")

            if not groups:
                self.log("✅ 未发现重复")
                self.compare_progress_bar.pack_forget()
            else:
                # 计算每组相似度（带进度）
                self.group_scores = {}
                self.all_groups = list(groups)  # 保存原始列表用于筛选重置
                total_groups = len(groups)
                for idx, group in enumerate(groups):
                    scores = []
                    for i in range(len(group)):
                        for j in range(i+1, len(group)):
                            data1 = self.video_data[group[i]][0]
                            data2 = self.video_data[group[j]][0]
                            
                            # 判断是否为高精度模式（字典类型）
                            if isinstance(data1, dict) and isinstance(data2, dict):
                                from core import calculate_high_precision_similarity
                                score = calculate_high_precision_similarity(data1, data2)
                            else:
                                score = calc_similar_score(data1, data2)
                            
                            scores.append(score)
                    avg_score = sum(scores) / len(scores) if scores else 0
                    self.group_scores[group] = avg_score
                    
                    # 更新比对进度
                    prog = int((idx + 1) / total_groups * 100)
                    self.compare_progress_bar["value"] = prog
                    self.update_idletasks()

                self.current_groups = list(groups)
                
                # 隐藏比对进度条
                self.compare_progress_bar.pack_forget()
                
                self.progress_bar["value"] = 100
                
                # 计算总用时
                import time
                if self.scan_start_time:
                    elapsed = time.time() - self.scan_start_time
                    hours = int(elapsed // 3600)
                    minutes = int((elapsed % 3600) // 60)
                    seconds = int(elapsed % 60)
                    if hours > 0:
                        time_str = f"{hours}小时{minutes}分{seconds}秒"
                    elif minutes > 0:
                        time_str = f"{minutes}分{seconds}秒"
                    else:
                        time_str = f"{seconds}秒"
                    self.log(f"\n⏱️ 总用时: {time_str}")
                
                # 显示缓存统计信息
                from video_cache import get_cache_stats, stop_prefetch_thread
                stats_msg = get_cache_stats()
                self.log(f"\n{stats_msg}")
                
                # 停止预加载线程
                stop_prefetch_thread()
                
                self.log(f"🎉 共 {len(self.current_groups)} 组重复 ({sum(len(g) for g in self.current_groups)} 个文件)")
                self.show_groups(self.current_groups)
            self.reset_buttons()
        except Exception as e:
            error_msg = f"比对过程中发生错误：\n\n{str(e)}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("比对错误", error_msg)
            self.reset_buttons()

    def reset_buttons(self):
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        # 删除对设置窗口中按钮的引用
        # 启用一键选择按钮（如果有重复组）
        if hasattr(self, 'btn_select'):
            if self.current_groups:
                self.btn_select.config(state=tk.NORMAL)
                self.log(f"✅ 启用一键选择按钮，当前有 {len(self.current_groups)} 组重复")
            else:
                self.btn_select.config(state=tk.DISABLED)
                self.log("⚠️ 禁用一键选择按钮，没有重复组")
        
        # 启用删除按钮（如果有重复组）
        if hasattr(self, 'btn_delete'):
            if self.current_groups:
                self.btn_delete.config(state=tk.NORMAL)
            else:
                self.btn_delete.config(state=tk.DISABLED)

    def reset_filter(self):
        """重置筛选，显示所有组"""
        self.sim_filter_val.set("100")
        self.apply_filter()
    
    def apply_filter(self):
        """应用相似度筛选"""
        if not self.all_groups:
            return
        try:
            max_sim = float(self.sim_filter_val.get())
        except:
            max_sim = 100
        
        # 如果设置为100，显示所有组（取消筛选）
        if max_sim >= 100:
            self.log(f"🔍 已取消筛选，显示全部 {len(self.all_groups)} 组")
            self.progress_bar["value"] = 0
            self.current_groups = list(self.all_groups)
            self.show_groups(self.current_groups)
            return
        
        # 基于原始列表筛选
        filtered = [g for g in self.all_groups if self.group_scores.get(g, 999) <= max_sim]
        
        self.log(f"🔍 筛选后：{len(filtered)} 组（相似度≤{max_sim}）")
        
        self.current_groups = filtered
        self.progress_bar["value"] = 0
        self.show_groups(self.current_groups)

    def select_by_condition(self):
        """按条件选择文件"""
        self.log("🔧 开始执行一键选择")
        
        # 检查必要属性
        if not hasattr(self, 'select_by_size'):
            self.log("❌ 缺少select_by_size属性")
            return
        
        if not hasattr(self, 'select_by_res'):
            self.log("❌ 缺少select_by_res属性")
            return
        
        if not hasattr(self, 'check_vars'):
            self.log("❌ 缺少check_vars属性")
            return
        
        if not hasattr(self, 'current_groups'):
            self.log("❌ 缺少current_groups属性")
            return
        
        if not self.current_groups:
            self.log("❌ current_groups为空")
            return
        
        if not self.check_vars:
            self.log(f"❌ check_vars为空（长度={len(self.check_vars)}），请先显示预览")
            return
        
        self.log(f"📊 当前状态：{len(self.current_groups)}组，{len(self.check_vars)}个复选框")
        
        # 检查选择状态
        size_selected = self.select_by_size.get()
        res_selected = self.select_by_res.get()
        self.log(f"🔍 选择条件：最小文件={size_selected}，最低分辨率={res_selected}")
        
        if not size_selected and not res_selected:
            self.log("⚠️ 请至少选择一个条件")
            return
        
        # ✅ 关键修复：先清空所有选择 - 直接操作widget
        cleared_count = 0
        for var, path in self.check_vars:
            var.set(False)
            # 同时通过widget取消选中
            if hasattr(self, 'check_widgets') and path in self.check_widgets:
                self.check_widgets[path].state(['!selected'])
            cleared_count += 1
        self.log(f"✅ 已清空 {cleared_count} 个复选框")
        
        selected_count = 0
        total_count = 0
        error_count = 0
        
        for group_idx, group in enumerate(self.current_groups):
            if len(group) < 2:
                continue
            
            total_count += len(group)
            
            # 收集属性
            sizes = {}
            ress = {}
            for p in group:
                try:
                    if p not in self.video_data:
                        self.log(f"⚠️ 视频数据缺失：{os.path.basename(p)}")
                        error_count += 1
                        continue
                    
                    # 🔍 调试：打印数据结构
                    video_tuple = self.video_data[p]
                    if len(video_tuple) < 3:
                        self.log(f"⚠️ 视频数据结构错误：{os.path.basename(p)}，长度={len(video_tuple)}")
                        error_count += 1
                        continue
                    
                    video_info = video_tuple[2]
                    if not isinstance(video_info, dict):
                        self.log(f"⚠️ video_info不是字典：{os.path.basename(p)}，类型={type(video_info)}")
                        error_count += 1
                        continue
                    
                    if 'size' not in video_info or 'resolution' not in video_info:
                        self.log(f"⚠️ video_info缺少字段：{os.path.basename(p)}，keys={list(video_info.keys())}")
                        error_count += 1
                        continue
                    
                    size_str = video_info['size']
                    res_str = video_info['resolution']
                    sizes[p] = parse_file_size(size_str)
                    ress[p] = parse_resolution(res_str)
                    
                except Exception as e:
                    import traceback
                    self.log(f"❌ 解析文件属性失败：{os.path.basename(p)} - {str(e)}")
                    self.log(f"   详细错误：{traceback.format_exc()}")
                    error_count += 1
                    sizes[p] = 0
                    ress[p] = 0
            
            if not sizes or not ress:
                self.log(f"⚠️ 第{group_idx+1}组数据不完整，跳过")
                continue
            
            # 找最小/最低
            min_size = min(sizes.values())
            min_size_count = sum(1 for s in sizes.values() if s == min_size)
            min_res = min(ress.values())
            min_res_count = sum(1 for r in ress.values() if r == min_res)
            
            self.log(f"📋 第{group_idx+1}组：{len(group)}个文件，最小大小={min_size}(出现{min_size_count}次)，最低分辨率={min_res}(出现{min_res_count}次)")
            
            # ✅ 关键修复：直接在check_vars中查找并设置
            for var, p in self.check_vars:
                if p not in group:
                    continue
                
                should_select = False
                
                # 两个选项都选时：同时满足最小 AND 最低分辨率
                both_selected = size_selected and res_selected
                if both_selected:
                    # 两个都选：必须同时是最小文件且最低分辨率，且不能有并列
                    if sizes.get(p, 0) == min_size and ress.get(p, 0) == min_res and min_size_count == 1 and min_res_count == 1:
                        should_select = True
                        self.log(f"  ✅ 选中（双条件）：{os.path.basename(p)}")
                else:
                    # 只有一个选中：按各自条件选择，如果有并列则不选中
                    if size_selected and sizes.get(p, 0) == min_size and min_size_count == 1:
                        should_select = True
                        self.log(f"  ✅ 选中（最小文件）：{os.path.basename(p)}")
                    elif res_selected and ress.get(p, 0) == min_res and min_res_count == 1:
                        should_select = True
                        self.log(f"  ✅ 选中（最低分辨率）：{os.path.basename(p)}")
                
                if should_select:
                    var.set(True)
                    # ✅ 直接操作widget确保UI更新
                    if hasattr(self, 'check_widgets') and p in self.check_widgets:
                        self.check_widgets[p].state(['selected'])
                    selected_count += 1
        
        # ✅ 关键修复：强制刷新UI，确保复选框状态更新可见
        self.preview_frame.update_idletasks()
        self.canvas.update_idletasks()
        
        # 输出统计信息
        if error_count > 0:
            self.log(f"⚠️ 处理过程中遇到 {error_count} 个错误")
        
        if selected_count == 0:
            self.log("⚠️ 没有找到符合条件的文件（可能存在并列情况）")
        else:
            self.log(f"✅ 一键选择完成：共 {total_count} 个视频，已选择 {selected_count} 个")

    def show_groups(self, groups):
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        # ✅ 清空widget字典
        if hasattr(self, 'check_widgets'):
            self.check_widgets.clear()
        self.image_refs.clear()

        try:
            w, h = int(self.prev_w.get()), int(self.prev_h.get())
        except:
            w, h = DEFAULT_THUMB_W, DEFAULT_THUMB_H

        # 获取canvas实际宽度，用于动态调整wraplength
        canvas_width = self.canvas.winfo_width()
        # 预留边距和复选框、预览图的空间（约300px）
        text_area_width = max(300, canvas_width - 300)

        for group_idx, group in enumerate(groups):
            # 从 group_scores 获取相似度
            avg_score = self.group_scores.get(group, 0)
            
            # 组标题 - 减少上下间距
            header_frame = ttk.Frame(self.preview_frame)
            header_frame.pack(fill=tk.X, pady=(8, 3), padx=5)
            
            score_color = "green" if avg_score < 5 else ("orange" if avg_score < 12 else "red")
            ttk.Label(header_frame, text=f"📦 组 {group_idx + 1}", font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)
            ttk.Label(header_frame, text=f"相似度: {avg_score:.1f}", foreground=score_color,
                     font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT, padx=15)
            ttk.Label(header_frame, text=f"({len(group)} 个文件)").pack(side=tk.LEFT)

            # 组容器 - 减少外边距
            group_frame = ttk.Frame(self.preview_frame, relief=tk.RIDGE, borderwidth=1)
            group_frame.pack(fill=tk.X, padx=5, pady=(0, 6))

            for path in group:
                row = ttk.Frame(group_frame)
                row.pack(fill=tk.X, pady=2, padx=4)

                # 复选框 - 保存widget引用以便直接操作
                var = tk.BooleanVar(value=False)
                cb = ttk.Checkbutton(row, variable=var, width=3)
                cb.pack(side=tk.LEFT)
                
                # 同时保存var和widget引用
                self.check_vars.append((var, path))
                # 添加widget到字典，方便通过路径查找
                if not hasattr(self, 'check_widgets'):
                    self.check_widgets = {}
                self.check_widgets[path] = cb

                # 视频信息 - 使用expand=True占满剩余空间
                info_frame = ttk.Frame(row)
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 8))

                video_info = self.video_data[path][2]
                name = os.path.basename(path)

                # 分析此文件在组内的优劣
                file_flags = self.analyze_file_in_group(path, group)

                # 文件名 - 根据canvas宽度动态设置wraplength
                ttk.Label(info_frame, text=name, font=("微软雅黑", 9, "bold"), wraplength=text_area_width).pack(anchor=tk.W)

                # 文件大小（相同不变色）
                size_color = "red" if file_flags.get("size_bad") else ("green" if file_flags.get("size_good") else "black")
                size_txt = f"大小：{video_info['size']}"
                if file_flags.get("size_bad"):
                    size_txt += " ⚠最小"
                elif file_flags.get("size_good"):
                    size_txt += " ✓最大"
                ttk.Label(info_frame, text=size_txt, foreground=size_color).pack(anchor=tk.W)

                # 分辨率（相同不变色）
                res_color = "red" if file_flags.get("res_bad") else ("green" if file_flags.get("res_good") else "black")
                res_txt = f"分辨率：{video_info['resolution']}"
                if file_flags.get("res_bad"):
                    res_txt += " ⚠最低"
                elif file_flags.get("res_good"):
                    res_txt += " ✓最高"
                ttk.Label(info_frame, text=res_txt, foreground=res_color).pack(anchor=tk.W)

                ttk.Label(info_frame, text=f"时长：{video_info['duration']} | 码率：{video_info['bitrate']}").pack(anchor=tk.W)

                # 预览图
                frame_list = self.video_data[path][1]
                valid_frames = [img for img in frame_list if img is not None]
                if valid_frames:
                    for img in valid_frames[:2]:
                        try:
                            thumb = img.resize((w, h), Image.Resampling.LANCZOS)
                            im = ImageTk.PhotoImage(thumb)
                            self.image_refs.append(im)
                            lab = ttk.Label(row, image=im)
                            lab.pack(side=tk.RIGHT, padx=2)
                        except:
                            pass
                else:
                    ttk.Label(row, text="(无预览)", foreground="gray").pack(side=tk.RIGHT, padx=10)

        self.preview_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def analyze_file_in_group(self, path, group):
        """分析单个文件在组内的优劣，仅在有差异时标记"""
        diff_info = {}
        if len(group) < 2:
            return diff_info

        sizes = {p: parse_file_size(self.video_data[p][2]['size']) for p in group}
        ress = {p: parse_resolution(self.video_data[p][2]['resolution']) for p in group}

        # 检查是否有差异
        unique_sizes = set(sizes.values())
        unique_ress = set(ress.values())
        
        # 只有存在差异时才标记
        if len(unique_sizes) > 1:
            min_size = min(sizes.values())
            max_size = max(sizes.values())
            if sizes[path] == min_size:
                diff_info["size_bad"] = True
            elif sizes[path] == max_size:
                diff_info["size_good"] = True
        
        if len(unique_ress) > 1:
            min_res = min(ress.values())
            max_res = max(ress.values())
            if ress[path] == min_res:
                diff_info["res_bad"] = True
            elif ress[path] == max_res:
                diff_info["res_good"] = True

        return diff_info

    def uncheck_all(self):
        for var, path in self.check_vars:
            var.set(False)
        self.log("📋 已取消全选")

    def delete_selected(self):
        try:
            cnt = 0
            failed_files = []
            paths_to_delete = [p for var, p in self.check_vars if var.get()]
            if not paths_to_delete:
                messagebox.showwarning("提示", "未选择任何视频")
                return
            if not messagebox.askyesno("确认删除", f"确定删除选中的 {len(paths_to_delete)} 个视频？"):
                return

            for path in paths_to_delete:
                normalized_path = os.path.normpath(path)
                if os.path.exists(normalized_path):
                    try:
                        send2trash.send2trash(normalized_path)
                        cnt += 1
                        del self.video_data[path]
                    except Exception as e:
                        error_detail = f"{os.path.basename(path)}: {str(e)}"
                        failed_files.append(error_detail)
                        self.log(f"❌ 删除失败：{error_detail}")
                else:
                    try:
                        import ctypes
                        GetShortPathName = ctypes.windll.kernel32.GetShortPathNameW
                        short_path = GetShortPathName(normalized_path, None, 0)
                        if short_path > 0:
                            buffer = ctypes.create_unicode_buffer(short_path)
                            GetShortPathName(normalized_path, buffer, short_path)
                            send2trash.send2trash(buffer.value)
                            cnt += 1
                            del self.video_data[path]
                    except Exception as e:
                        error_detail = f"{os.path.basename(path)}: {str(e)}"
                        failed_files.append(error_detail)
                        self.log(f"❌ 删除失败：{error_detail}")

            # 显示结果
            if failed_files:
                error_msg = f"成功删除 {cnt} 个视频\n\n以下文件删除失败：\n" + "\n".join(failed_files[:10])
                if len(failed_files) > 10:
                    error_msg += f"\n...还有 {len(failed_files) - 10} 个文件"
                messagebox.showwarning("部分删除失败", error_msg)
            else:
                messagebox.showinfo("完成", f"成功删除 {cnt} 个视频")
            
            self.log(f"✅ 删除完成：{cnt} 个")

            # 刷新
            if self.mode_high_precision:
                from core import find_duplicate_groups_high_precision
                groups = find_duplicate_groups_high_precision(self.video_data, int(self.hash_val.get()))
            elif self.mode_safe:
                groups = find_duplicate_groups_safe(self.video_data, int(self.hash_val.get()))
            else:
                groups = find_duplicate_groups(self.video_data, int(self.hash_val.get()))
            
            # 计算新组的相似度分数
            self.group_scores = {}
            self.all_groups = list(groups)
            for group in groups:
                scores = []
                for i in range(len(group)):
                    for j in range(i+1, len(group)):
                        data1 = self.video_data[group[i]][0]
                        data2 = self.video_data[group[j]][0]
                        
                        if isinstance(data1, dict) and isinstance(data2, dict):
                            from core import calculate_high_precision_similarity
                            score = calculate_high_precision_similarity(data1, data2)
                        else:
                            score = calc_similar_score(data1, data2)
                        
                        scores.append(score)
                avg_score = sum(scores) / len(scores) if scores else 0
                self.group_scores[group] = avg_score
            
            self.current_groups = list(groups)
            self.show_groups(self.current_groups)
        except Exception as e:
            error_msg = f"删除过程中发生错误：\n\n{str(e)}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("删除错误", error_msg)

    def save_progress(self):
        """导出进度备份"""
        try:
            save_progress(self.scan_path.get(), self.scan_subdir.get(), self.finished_idx, self.video_list, self.video_data)
            self.log("\n[SUCCESS] 进度备份已导出")
        except Exception as e:
            self.log(f"\n[ERROR] 导出进度失败: {str(e)}")

    def load_progress(self):
        """导入进度备份"""
        try:
            self.video_list = []
            self.finished_idx = 0
            self.video_data.clear()
            self.check_vars.clear()
            self.image_refs.clear()
            self.current_groups = []
            self.group_scores = {}
            self.all_groups = []
            self.progress_bar["value"] = 0
            self.log_text.delete(1.0, tk.END)
            for w in self.preview_frame.winfo_children():
                w.destroy()

            data = load_progress()
            if not data:
                self.log("\n[ERROR] 无进度文件")
                return
            self.scan_path.set(data["scan_path"])
            self.scan_subdir.set(data["scan_subdir"])
            self.finished_idx = data["finished_idx"]
            self.video_list = data["video_list"]

            def deserialize_video_data(data_dict):
                result = {}
                for k, v in data_dict.items():
                    hash_list, frame_list, info = v
                    hashes = [imagehash.hex_to_hash(h) if h is not None else None for h in hash_list]
                    frames = []
                    for frame_b64 in frame_list:
                        if frame_b64 is not None:
                            frames.append(Image.open(BytesIO(base64.b64decode(frame_b64))))
                        else:
                            frames.append(None)
                    result[k] = (hashes, frames, info)
                return result

            self.video_data = deserialize_video_data(data["video_data"])
            self.log(f"\n[SUCCESS] 进度已导入，从第 {self.finished_idx+1} 个继续扫描")
            self.log_text.delete(1.0, tk.END)
            self.start(resume=True)
        except Exception as e:
            self.log(f"\n[ERROR] 加载进度失败: {str(e)}")

    def clear_cache(self, mode="all"):
        """清空视频扫描缓存
        
        Args:
            mode: 清除模式 - "precise"(精确+抗水印共用), "high_precision"(高精度), "all"(全部)
        """
        if mode == "all":
            confirm_msg = "确定要清空所有模式的视频扫描缓存吗？\n这将导致下次扫描时重新处理所有视频。"
            log_msg = "\n[SUCCESS] 所有模式缓存已清空"
        elif mode == "precise":
            confirm_msg = "确定要清空精确模式和抗水印模式的缓存吗？\n\n[INFO] 这两个模式共用同一缓存"
            log_msg = "\n[SUCCESS] 精确+抗水印模式缓存已清空"
        elif mode == "high_precision":
            confirm_msg = "确定要清空高精度模式的视频扫描缓存吗？"
            log_msg = "\n[SUCCESS] 高精度模式缓存已清空"
        
        if messagebox.askyesno("确认清空", confirm_msg):
            try:
                # 使用video_cache模块的统一清理函数
                from video_cache import clear_video_cache as clear_all_cache
                result = clear_all_cache(mode)
                
                if result:
                    self.log(log_msg)
                    # 重置内存缓存
                    reset_memory_cache()
                else:
                    self.log("\n[ERROR] 清空缓存失败")
            except Exception as e:
                self.log(f"\n[ERROR] 清空缓存失败: {str(e)}")

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[INFO] 程序已被用户中断")
    except Exception as e:
        print(f"\n[ERROR] 程序异常退出: {str(e)}")
        import traceback
        traceback.print_exc()