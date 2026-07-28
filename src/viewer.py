import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import re
import os
import glob


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tomography Point Picker")
        self.root.geometry("565x900")

        # 定义尺寸常量
        self.top_size = 512
        self.bottom_width = 512
        self.bottom_height = 1920
        self.display_size = 512

        # 用于存储图片的偏移量（用于坐标计算）
        self.top_offset_x = 0
        self.top_offset_y = 0
        self.top_display_width = 0
        self.top_display_height = 0

        # 存储当前选择的坐标
        self.current_x = None
        self.current_y = None

        # 存储下方图片路径列表
        self.bottom_image_paths = []

        self.setup_ui()

    def setup_ui(self):
        """创建界面组件"""

        # ----- 顶部输入区域 -----
        input_frame = tk.Frame(self.root, padx=10, pady=10, bg="#F0F0F0")
        input_frame.pack(fill=tk.X)

        # 第一行：上方图片输入（直接传入图片路径）
        row1 = tk.Frame(input_frame, bg="#F0F0F0")
        row1.pack(fill=tk.X, pady=3)

        label1 = tk.Label(row1, text="上方图片路径:", font=("微软雅黑", 10), bg="#F0F0F0")
        label1.pack(side=tk.LEFT, padx=(0, 5))

        self.url_entry_top = tk.Entry(row1, font=("微软雅黑", 10))
        self.url_entry_top.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        load_btn1 = tk.Button(
            row1,
            text="加载上方图片",
            font=("微软雅黑", 9),
            command=lambda: self.load_image("top_only"),
            bg="#4CAF50",
            fg="white",
            padx=10
        )
        load_btn1.pack(side=tk.RIGHT)

        # 第二行：下方图片输入（传入文件夹路径，包含Angio和B-scan_PixelRatio）
        row2 = tk.Frame(input_frame, bg="#F0F0F0")
        row2.pack(fill=tk.X, pady=3)

        label2 = tk.Label(row2, text="数据文件夹路径:", font=("微软雅黑", 10), bg="#F0F0F0")
        label2.pack(side=tk.LEFT, padx=(0, 5))

        self.url_entry_bottom = tk.Entry(row2, font=("微软雅黑", 10))
        self.url_entry_bottom.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        load_btn2 = tk.Button(
            row2,
            text="加载数据图片",
            font=("微软雅黑", 9),
            command=lambda: self.load_image("both"),
            bg="#2196F3",
            fg="white",
            padx=10
        )
        load_btn2.pack(side=tk.RIGHT)

        # 显示当前B-scan索引
        info_frame = tk.Frame(input_frame, bg="#F0F0F0")
        info_frame.pack(fill=tk.X, pady=3)

        self.info_label = tk.Label(info_frame, text="B-scan: 未加载", font=("微软雅黑", 10), bg="#F0F0F0", fg="#666666")
        self.info_label.pack()

        # 绑定回车键
        self.url_entry_top.bind("<Return>", lambda event: self.load_image("top_only"))
        self.url_entry_bottom.bind("<Return>", lambda event: self.load_image("both"))

        # ----- 图片显示区域 -----
        display_frame = tk.Frame(self.root)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 上方图片显示
        top_frame = tk.LabelFrame(display_frame, text="上方图片 - 点击选择坐标", font=("微软雅黑", 10),
                                  padx=5, pady=5)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.top_image_label = tk.Label(top_frame, bg="white", relief=tk.SUNKEN, bd=2, anchor="nw")
        self.top_image_label.pack(fill=tk.BOTH, expand=True)

        # 绑定鼠标点击事件
        self.top_image_label.bind("<Button-1>", self.on_top_image_click)

        # 下方图片显示
        bottom_frame = tk.LabelFrame(display_frame, text="下方图片", font=("微软雅黑", 10),
                                     padx=5, pady=5)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Canvas和滚动条
        self.bottom_canvas = tk.Canvas(bottom_frame, bg="white", relief=tk.SUNKEN, bd=2, highlightthickness=0)
        self.bottom_scrollbar = tk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.bottom_canvas.yview)

        self.bottom_canvas.configure(yscrollcommand=self.bottom_scrollbar.set)

        # 创建内部容器
        self.bottom_container = tk.Frame(self.bottom_canvas, bg="white")
        self.bottom_canvas_window = self.bottom_canvas.create_window((0, 0), window=self.bottom_container, anchor="nw")

        # 布局
        self.bottom_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bottom_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建显示图片的标签
        self.bottom_image_label = tk.Label(self.bottom_container, bg="white")
        self.bottom_image_label.pack(anchor="nw")

        # 绑定事件
        self.bottom_container.bind("<Configure>", self.on_bottom_container_configure)
        self.bottom_canvas.bind("<Configure>", self.on_bottom_canvas_configure)

        # 显示占位图
        self.show_placeholders()

        # 存储图片对象
        self.top_photo = None
        self.bottom_photo = None
        self.top_image = None
        self.bottom_image = None
        self.bottom_display_photo = None

        # 存储线条对象
        self.top_line_photo = None
        self.bottom_line_photo = None

    def on_bottom_container_configure(self, event):
        self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def on_bottom_canvas_configure(self, event):
        self.bottom_canvas.itemconfig(self.bottom_canvas_window, width=event.width)
        self.update_bottom_display()
        if self.current_x is not None:
            self.draw_bottom_line(self.current_x)

    def show_placeholders(self):
        # 上方占位图
        top_placeholder = Image.new("RGB", (512, 512), (240, 240, 240))
        draw = ImageDraw.Draw(top_placeholder)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            font = ImageFont.load_default()

        text = ""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (512 - text_width) // 2
        y = (512 - text_height) // 2
        draw.text((x, y), text, fill=(180, 180, 180), font=font)

        self.top_placeholder_photo = ImageTk.PhotoImage(top_placeholder)
        self.top_image_label.config(image=self.top_placeholder_photo)
        self.top_image_label.image = self.top_placeholder_photo

        bottom_placeholder = Image.new("RGB", (512, 512), (245, 245, 245))
        draw = ImageDraw.Draw(bottom_placeholder)

        text = ""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (512 - text_width) // 2
        y = (512 - text_height) // 2
        draw.text((x, y), text, fill=(180, 180, 180), font=font)

        self.bottom_placeholder_photo = ImageTk.PhotoImage(bottom_placeholder)
        self.bottom_image_label.config(image=self.bottom_placeholder_photo)
        self.bottom_image_label.image = self.bottom_placeholder_photo

        self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def on_top_image_click(self, event):
        if self.top_image is None:
            return

        x = event.x
        y = event.y

        label_width = self.top_image_label.winfo_width()
        label_height = self.top_image_label.winfo_height()

        img_width = self.top_display_width
        img_height = self.top_display_height

        offset_x = (label_width - img_width) // 2
        offset_y = (label_height - img_height) // 2

        img_x = x - offset_x
        img_y = y - offset_y

        if img_x < 0 or img_x >= img_width or img_y < 0 or img_y >= img_height:
            return

        original_x = int((img_x / img_width) * 512)
        original_y = int((img_y / img_height) * 512)

        original_x = max(1, min(512, original_x))
        original_y = max(1, min(512, original_y))

        self.current_x = original_x
        self.current_y = original_y

        self.root.title(f"Tomography Point Picker - X={original_x}, Y={original_y}")

        self.draw_crosshair(original_x, original_y)

        self.switch_bottom_image_by_y(original_y)

    def draw_crosshair(self, x_coord, y_coord):
        if self.top_image is None:
            return

        img_copy = self.top_image.copy()
        draw = ImageDraw.Draw(img_copy)

        line_x = x_coord - 1
        draw.line([(line_x, 0), (line_x, 511)], fill=(0, 255, 0), width=2)

        line_y = y_coord - 1
        draw.line([(0, line_y), (511, line_y)], fill=(255, 0, 0), width=2)

        self.top_line_photo = ImageTk.PhotoImage(img_copy)
        self.top_image_label.config(image=self.top_line_photo)
        self.top_image_label.image = self.top_line_photo

        self.draw_bottom_line(x_coord)

    def draw_bottom_line(self, x_coord):
        if self.bottom_image is None:
            return

        img_copy = self.bottom_image.copy()
        draw = ImageDraw.Draw(img_copy)

        line_x = x_coord - 1
        draw.line([(line_x, 0), (line_x, 1919)], fill=(0, 255, 0), width=2)

        self.bottom_line_image = img_copy
        self.update_bottom_display_with_line()

    def update_bottom_display_with_line(self):
        """更新下方图片的显示（包含绿线）"""
        if not hasattr(self, 'bottom_line_image') or self.bottom_line_image is None:
            return

        canvas_width = self.bottom_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 480

        img_width, img_height = self.bottom_line_image.size
        ratio = canvas_width / img_width

        display_width = 512
        display_height = 1920

        display_image = self.bottom_line_image
        photo = ImageTk.PhotoImage(display_image)

        self.bottom_image_label.config(image=photo)
        self.bottom_image_label.image = photo
        self.bottom_display_photo = photo
        self.bottom_line_photo = photo

        self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def switch_bottom_image_by_y(self, y_coord):
        if not self.bottom_image_paths:
            return

        index = y_coord - 1

        if index < 0 or index >= len(self.bottom_image_paths):
            return

        try:
            image_path = self.bottom_image_paths[index]
            original_image = Image.open(image_path)

            resized_image, _ = self.resize_and_center_with_info(original_image, (512, 1920))
            self.bottom_image = resized_image

            self.info_label.config(text=f"图片{index + 1}/{len(self.bottom_image_paths)} (Y={y_coord})",
                                   fg="#2196F3")

            # 如果有x坐标，绘制绿线
            if self.current_x is not None:
                img_copy = resized_image.copy()
                draw = ImageDraw.Draw(img_copy)
                line_x = self.current_x - 1
                draw.line([(line_x, 0), (line_x, 1919)], fill=(0, 255, 0), width=2)
                self.bottom_line_image = img_copy
                self.update_bottom_display_with_line()
            else:
                self.bottom_line_image = None
                self.update_bottom_display()

            # 滚动到顶部
            self.bottom_canvas.yview_moveto(0)

        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败：\n{str(e)}")

    def sort_by_number(self, filename):
        match = re.search(r'_(\d+)\.png$', filename)
        if match:
            return int(match.group(1))
        return 0

    def load_image(self, mode):
        if mode == "top_only":
            image_path = self.url_entry_top.get().strip()

            if not image_path:
                messagebox.showwarning("提示", "请输入图片路径！")
                return

            if not os.path.exists(image_path):
                messagebox.showerror("错误", f"找不到图片文件：\n{image_path}")
                return

            try:
                original_image = Image.open(image_path)
                resized_image, display_info = self.resize_and_center_with_info(original_image, (512, 512))
                photo = ImageTk.PhotoImage(resized_image)

                self.top_image_label.config(image=photo)
                self.top_image_label.image = photo
                self.top_photo = photo
                self.top_image = resized_image

                self.top_display_width = display_info['display_width']
                self.top_display_height = display_info['display_height']
                self.top_offset_x = display_info['offset_x']
                self.top_offset_y = display_info['offset_y']

                self.root.title(f"Tomography Point Picker - Angio已加载")

                # 恢复十字准星
                if self.current_x is not None and self.current_y is not None:
                    self.draw_crosshair(self.current_x, self.current_y)

            except Exception as e:
                messagebox.showerror("错误", f"加载图片失败：\n{str(e)}")

        elif mode == "both":
            # 同时加载Angio和B-scan
            base_path = self.url_entry_bottom.get().strip()

            if not base_path:
                messagebox.showwarning("提示", "请输入数据文件夹路径！")
                return

            if not os.path.exists(base_path):
                messagebox.showerror("错误", f"找不到路径：\n{base_path}")
                return

            try:
                # 加载Angio
                angio_path = os.path.join(base_path, "Angio")
                if os.path.exists(angio_path):
                    png_files = glob.glob(os.path.join(angio_path, "*.png"))
                    if png_files:
                        image_path = png_files[0]
                        original_image = Image.open(image_path)
                        resized_image, display_info = self.resize_and_center_with_info(original_image, (512, 512))
                        photo = ImageTk.PhotoImage(resized_image)

                        self.top_image_label.config(image=photo)
                        self.top_image_label.image = photo
                        self.top_photo = photo
                        self.top_image = resized_image

                        self.top_display_width = display_info['display_width']
                        self.top_display_height = display_info['display_height']
                        self.top_offset_x = display_info['offset_x']
                        self.top_offset_y = display_info['offset_y']

                # 加载B-scan
                bscan_path = os.path.join(base_path, "B-scan_PixelRatio")
                if not os.path.exists(bscan_path):
                    messagebox.showerror("错误", f"找不到B-scan_PixelRatio文件夹：\n{bscan_path}")
                    return

                png_files = sorted(glob.glob(os.path.join(bscan_path, "*.png")))
                if not png_files:
                    messagebox.showerror("错误", f"B-scan_PixelRatio文件夹中没有png图片：\n{bscan_path}")
                    return

                self.bottom_image_paths = sorted(png_files, key=self.sort_by_number)

                if self.current_y is not None:
                    self.switch_bottom_image_by_y(self.current_y)
                else:
                    self.switch_bottom_image_by_y(1)

                self.root.title(f"Tomography Point Picker - Angio + B-scan已加载 ({len(png_files)}张)")

                # 恢复十字准星
                if self.current_x is not None and self.current_y is not None:
                    self.draw_crosshair(self.current_x, self.current_y)

            except Exception as e:
                messagebox.showerror("错误", f"加载失败：\n{str(e)}")

    def update_bottom_display(self):
        """更新下方图片的显示"""
        if not hasattr(self, 'bottom_image') or self.bottom_image is None:
            return

        canvas_width = self.bottom_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 480

        display_width = 512
        display_height = 1920

        display_image = self.bottom_image
        photo = ImageTk.PhotoImage(display_image)

        self.bottom_image_label.config(image=photo)
        self.bottom_image_label.image = photo
        self.bottom_display_photo = photo

        self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def resize_and_center_with_info(self, image, target_size):
        """调整图片到目标尺寸并居中（保持比例）"""
        target_width, target_height = target_size

        resized_image = Image.new("RGB", (target_width, target_height), (255, 255, 255))

        width, height = image.size
        ratio = min(target_width / width, target_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        resized_image.paste(scaled_image, (x, y))

        display_info = {
            'display_width': new_width,
            'display_height': new_height,
            'offset_x': x,
            'offset_y': y
        }

        return resized_image, display_info
