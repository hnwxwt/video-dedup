import os
import gc
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
from core import process_video, process_video_safe, process_video_high_precision, ScanState
from core import process_video_optimized, process_video_safe_optimized  # 导入优化版本
from video_cache import get_cached_video, save_video_cache, flush_cache

def scan_worker(app):
    try:
        left = app.video_list[app.finished_idx:]
        total = len(app.video_list)
        use_thread = app.use_thread.get()
        thread_num = app.thread_num
        rot = app.rotate.get()
        res = app.resize.get()
        mode_safe = app.mode_safe
        mode_high_precision = getattr(app, 'mode_high_precision', False)

        if mode_high_precision:
            mode_name = "高精度"
        elif mode_safe:
            mode_name = "抗水印"
        else:
            mode_name = "精确"
        app.log(f"🔄 启动{mode_name}扫描...")

        if use_thread:
            with ThreadPoolExecutor(max_workers=thread_num) as executor:
                futures = {}
                for path in left:
                    # 检查停止或暂停状态
                    if ScanState.STOP:
                        app.log("\n[INFO] 检测到停止信号，退出扫描")
                        break
                    if ScanState.PAUSE:
                        app.log("\n[INFO] 检测到暂停信号，等待继续...")
                        # 等待直到不再暂停或收到停止信号
                        while ScanState.PAUSE:
                            if ScanState.STOP:
                                app.log("\n[INFO] 暂停期间收到停止信号")
                                break
                            import time
                            time.sleep(0.1)  # 短暂休眠避免CPU占用
                        if ScanState.STOP:
                            break
                    
                    # 先尝试从缓存加载（根据模式选择对应的缓存）
                    cached_result = get_cached_video(path, is_high_precision=mode_high_precision)
                    if cached_result:
                        # 使用缓存数据（不需要提交到线程池）
                        hash_list, frame_list, video_info = cached_result
                        app.video_data[path] = (hash_list, frame_list, video_info)
                        app.finished_idx += 1
                        name = os.path.basename(path)
                        mode_tag = "高精度缓存" if mode_high_precision else "缓存"
                        app.log(f"({app.finished_idx}/{total}) ⚡ {name} ({mode_tag})")
                        app.update_progress()
                    else:
                        # 缓存未命中，提交到线程池扫描
                        # ✅ 使用优化版本（OpenCV直接处理）
                        if mode_safe:
                            futures[executor.submit(process_video_safe_optimized, path)] = path
                        elif mode_high_precision:
                            futures[executor.submit(process_video_high_precision, path)] = path
                        else:
                            futures[executor.submit(process_video_optimized, path, rot, res)] = path

                for future in as_completed(futures):
                    if ScanState.STOP:
                        return
                    path = futures[future]
                    app.finished_idx += 1
                    name = os.path.basename(path)
                    try:
                        data = future.result()
                        if data:
                            # 两个模式都返回4个值: (path, hash_list, frame_list, info)
                            app.video_data[data[0]] = (data[1], data[2], data[3])
                            
                            # 保存到内存缓存（不立即写入磁盘）
                            save_video_cache(data[0], data[1], data[2], data[3])
                            
                            app.log(f"({app.finished_idx}/{total}) ✅ {name}")
                        else:
                            app.log(f"({app.finished_idx}/{total}) ❌ {name} (处理失败)")
                        
                        # ✅ 无论是否命中缓存，都预加载下一个视频
                        next_idx = app.finished_idx
                        if next_idx < len(app.video_list):
                            from video_cache import prefetch_next_video
                            prefetch_next_video(app.video_list[next_idx], mode_high_precision)
                        
                        # 每处理50个视频，强制垃圾回收一次
                        if app.finished_idx % 50 == 0:
                            gc.collect()
                    except Exception as e:
                        app.log(f"({app.finished_idx}/{total}) ❌ {name} ({str(e)[:50]})")
                    app.update_progress()
                    if ScanState.PAUSE:
                        app.after(0, app.on_pause_done)
                        return
            
            # 多线程扫描完成后，批量保存缓存到磁盘
            flush_cache()
            
        else:
            for path in left:
                if ScanState.STOP:
                    app.log("\n[INFO] 检测到停止信号，退出扫描")
                    return
                # 处理暂停状态
                while ScanState.PAUSE:
                    if ScanState.STOP:
                        app.log("\n[INFO] 暂停期间收到停止信号")
                        return
                    import time
                    time.sleep(0.1)  # 短暂休眠避免CPU占用
                
                name = os.path.basename(path)
                app.finished_idx += 1
                
                # 先尝试从缓存加载（根据模式选择对应的缓存）
                cached_result = get_cached_video(path, is_high_precision=mode_high_precision)
                if cached_result:
                    # 使用缓存数据
                    hash_list, frame_list, video_info = cached_result
                    app.video_data[path] = (hash_list, frame_list, video_info)
                    mode_tag = "高精度缓存" if mode_high_precision else "缓存"
                    app.log(f"({app.finished_idx}/{total}) ⚡ {name} ({mode_tag})")
                else:
                    # 缓存未命中，重新扫描
                    if mode_safe:
                        data = process_video_safe(path)
                    elif mode_high_precision:
                        data = process_video_high_precision(path)
                    else:
                        data = process_video(path, rot, res)
                    
                    if data:
                        app.video_data[data[0]] = (data[1], data[2], data[3])
                        # 保存到内存缓存
                        save_video_cache(data[0], data[1], data[2], data[3])
                        app.log(f"({app.finished_idx}/{total}) ✅ {name}")
                    else:
                        app.log(f"({app.finished_idx}/{total}) ❌ {name}")
                
                app.update_progress()
            
            # 单线程扫描完成后，批量保存缓存到磁盘
            flush_cache()

        if not ScanState.STOP:
            app.after(0, app.on_scan_done)
    except Exception as e:
        error_msg = f"扫描过程中发生错误：\n\n{str(e)}"
        app.log(f"❌ {error_msg}")
        # 在主线程中显示错误对话框
        app.after(0, lambda: messagebox.showerror("扫描错误", error_msg))
        app.after(0, app.reset_buttons)
