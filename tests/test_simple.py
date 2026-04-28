import tkinter as tk
from tkinter import ttk
import os
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

from config import *
from ui import create_ui

class TestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("测试")
        self.geometry("1500x900")
        self.use_thread = tk.IntVar(value=1)
        self.rotate = tk.IntVar(value=1)
        self.resize = tk.IntVar(value=1)
        self.scan_subdir = tk.IntVar(value=0)
        self.show_hints = tk.BooleanVar(value=False)
        self.thread_cnt = tk.IntVar(value=DEFAULT_THREAD)
        self.hash_val = tk.IntVar(value=DEFAULT_HASH_LIMIT)
        self.scan_path = tk.StringVar()
        self.prev_w = tk.StringVar(value=str(DEFAULT_THUMB_W))
        self.prev_h = tk.StringVar(value=str(DEFAULT_THUMB_H))
        self.sim_filter_val = tk.StringVar(value="100")
        self.mode_safe = False
        self.mode_high_precision = False
        self.video_list = []
        self.finished_idx = 0
        self.video_data = {}
        self.check_vars = []
        self.image_refs = []
        self.current_groups = []
        self.group_scores = {}
        
        # 需要的方法
        self.progress_bar = None
        self.compare_progress_bar = None
        self.log_text = None
        
        print("创建UI...", flush=True)
        create_ui(self, self)
        print("UI创建完成", flush=True)

app = TestApp()
app.update()
print("进入mainloop", flush=True)
app.mainloop()
print("结束")
