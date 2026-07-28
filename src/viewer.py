import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tomography Point Picker")
        self.root.geometry("560x900")

        # 定义尺寸常量
        self.top_size = 512  # 第一张图片宽高
        self.bottom_width = 512  # 第二张图片宽度
        self.bottom_height = 1920  # 第二张图片高度
        self.display_size = 512  # 显示区域大小

        # 用于存储图片的偏移量（用于坐标计算）
        self.top_offset_x = 0
        self.top_offset_y = 0
        self.top_display_width = 0
        self.top_display_height = 0

        # 存储当前选择的坐标
        self.current_x = None
        self.current_y = None

        self.setup_ui()

    def setup_ui(self):
        """创建界面组件"""

        # ----- 顶部输入区域 -----
        input_frame = tk.Frame(self.root, padx=10, pady=10, bg="#F0F0F0")
        input_frame.pack(fill=tk.X)

        # 第一行：上方图片输入
        row1 = tk.Frame(input_frame, bg="#F0F0F0")
        row1.pack(fill=tk.X, pady=3)

        label1 = tk.Label(row1, text="上方图片(512x512):", font=("微软雅黑", 10), bg="#F0F0F0")
        label1.pack(side=tk.LEFT, padx=(0, 5))

        self.url_entry_top = tk.Entry(row1, font=("微软雅黑", 10))
        self.url_entry_top.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        load_btn1 = tk.Button(
            row1,
            text="加载",
            font=("微软雅黑", 9),
            command=lambda: self.load_image("top"),
            bg="#4CAF50",
            fg="white",
            padx=10
        )
        load_btn1.pack(side=tk.RIGHT)

        # 第二行：下方图片输入
        row2 = tk.Frame(input_frame, bg="#F0F0F0")
        row2.pack(fill=tk.X, pady=3)

        label2 = tk.Label(row2, text="下方图片(512x1920):", font=("微软雅黑", 10), bg="#F0F0F0")
        label2.pack(side=tk.LEFT, padx=(0, 5))

        self.url_entry_bottom = tk.Entry(row2, font=("微软雅黑", 10))
        self.url_entry_bottom.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        load_btn2 = tk.Button(
            row2,
            text="加载",
            font=("微软雅黑", 9),
            command=lambda: self.load_image("bottom"),
            bg="#2196F3",
            fg="white",
            padx=10
        )
        load_btn2.pack(side=tk.RIGHT)

        # 绑定回车键
        self.url_entry_top.bind("<Return>", lambda event: self.load_image("top"))
        self.url_entry_bottom.bind("<Return>", lambda event: self.load_image("bottom"))

        # ----- 图片显示区域 -----
        display_frame = tk.Frame(self.root)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 上方图片显示（固定512x512，无滚动，可点击）
        top_frame = tk.LabelFrame(display_frame, text="上方图片 (512x512) - 点击选择坐标", font=("微软雅黑", 10),
                                  padx=5, pady=5)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.top_image_label = tk.Label(top_frame, bg="white", relief=tk.SUNKEN, bd=2)
        self.top_image_label.pack(fill=tk.BOTH, expand=True)

        # 绑定鼠标点击事件
        self.top_image_label.bind("<Button-1>", self.on_top_image_click)

        # 下方图片显示（固定512x512，带滚动条）
        bottom_frame = tk.LabelFrame(display_frame, text="下方图片 (512x1920 滚动预览)", font=("微软雅黑", 10), padx=5,
                                     pady=5)
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

        # 创建显示图片的标签（用于下方图片）
        self.bottom_image_label = tk.Label(self.bottom_container, bg="white")
        self.bottom_image_label.pack()

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
        self.bottom_display_photo = None  # 用于显示的缩放版本

        # 存储绿线和红线对象
        self.top_line_photo = None
        self.bottom_line_photo = None

    def on_bottom_container_configure(self, event):
        """当容器大小变化时更新Canvas滚动区域"""
        self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def on_bottom_canvas_configure(self, event):
        """当Canvas大小变化时调整内容宽度"""
        # 更新内部容器的宽度以适应Canvas
        self.bottom_canvas.itemconfig(self.bottom_canvas_window, width=event.width)
        # 更新下方图片显示
        self.update_bottom_display()
        # 如果已经有选择的x坐标，重新绘制绿线
        if self.current_x is not None:
            self.draw_bottom_line(self.current_x)

    def show_placeholders(self):
        """显示占位图"""
        # 上方占位图（512x512）
        top_placeholder = Image.new("RGB", (512, 512), (240, 240, 240))
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(top_placeholder)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            font = ImageFont.load_default()

        text = "📷 请加载图片\n512 x 512\n(点击选择坐标)"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (512 - text_width) // 2
        y = (512 - text_height) // 2
        draw.text((x, y), text, fill=(180, 180, 180), font=font)

        self.top_placeholder_photo = ImageTk.PhotoImage(top_placeholder)
        self.top_image_label.config(image=self.top_placeholder_photo)
        self.top_image_label.image = self.top_placeholder_photo

        # 下方占位图（适配显示区域大小）
        bottom_placeholder = Image.new("RGB", (512, 512), (245, 245, 245))
        draw = ImageDraw.Draw(bottom_placeholder)

        text = "📷 请加载图片\n512 x 1920\n(可滚动查看)"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (512 - text_width) // 2
        y = (512 - text_height) // 2
        draw.text((x, y), text, fill=(180, 180, 180), font=font)

        self.bottom_placeholder_photo = ImageTk.PhotoImage(bottom_placeholder)
        self.bottom_image_label.config(image=self.bottom_placeholder_photo)
        self.bottom_image_label.image = self.bottom_placeholder_photo

        # 更新滚动区域
        self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def on_top_image_click(self, event):
        """处理上方图片的点击事件"""
        if self.top_image is None:
            return

        # 获取点击位置相对于标签的坐标
        x = event.x
        y = event.y

        # 获取标签的实际大小
        label_width = self.top_image_label.winfo_width()
        label_height = self.top_image_label.winfo_height()

        # 计算图片在标签中的实际显示位置和大小
        img_width = self.top_display_width
        img_height = self.top_display_height

        # 计算居中偏移
        offset_x = (label_width - img_width) // 2
        offset_y = (label_height - img_height) // 2

        # 计算点击在图片上的实际坐标（相对于图片的左上角）
        img_x = x - offset_x
        img_y = y - offset_y

        # 检查点击是否在图片范围内
        if img_x < 0 or img_x >= img_width or img_y < 0 or img_y >= img_height:
            return

        # 将坐标映射到512x512的原始图片坐标
        original_x = int((img_x / img_width) * 512)
        original_y = int((img_y / img_height) * 512)

        # 确保坐标在[1, 512]范围内
        original_x = max(1, min(512, original_x))
        original_y = max(1, min(512, original_y))

        # 更新当前选择的坐标
        self.current_x = original_x
        self.current_y = original_y

        # 更新窗口标题显示坐标
        self.root.title(f"Tomography Point Picker - X={original_x}, Y={original_y}")

        # 绘制十字准星（绿线+红线）
        self.draw_crosshair(original_x, original_y)

    def draw_crosshair(self, x_coord, y_coord):
        """在上方图片绘制十字准星（绿色竖线+红色横线）"""
        if self.top_image is None:
            return

        # 创建图片的副本
        img_copy = self.top_image.copy()
        draw = ImageDraw.Draw(img_copy)

        # 绘制绿色竖线（在x位置）
        line_x = x_coord - 1  # 转换为0-based坐标
        draw.line([(line_x, 0), (line_x, 511)], fill=(0, 255, 0), width=2)

        # 绘制红色横线（在y位置）
        line_y = y_coord - 1  # 转换为0-based坐标
        draw.line([(0, line_y), (511, line_y)], fill=(255, 0, 0), width=2)

        # 转换为PhotoImage并显示
        self.top_line_photo = ImageTk.PhotoImage(img_copy)
        self.top_image_label.config(image=self.top_line_photo)
        self.top_image_label.image = self.top_line_photo

        # 在下方图片绘制绿色竖线（仅绿线）
        self.draw_bottom_line(x_coord)

    def draw_bottom_line(self, x_coord):
        """在下方图片绘制绿色竖线"""
        if self.bottom_image is None:
            return

        # 创建图片的副本
        img_copy = self.bottom_image.copy()
        draw = ImageDraw.Draw(img_copy)

        # 绘制绿色竖线（在x位置）
        line_x = x_coord - 1  # 转换为0-based坐标
        draw.line([(line_x, 0), (line_x, 1919)], fill=(0, 255, 0), width=2)

        # 保存带绿线的图片
        self.bottom_line_image = img_copy

        # 更新显示
        self.update_bottom_display_with_line()

    def update_bottom_display_with_line(self):
        """更新下方图片的显示（包含绿线）"""
        if not hasattr(self, 'bottom_line_image') or self.bottom_line_image is None:
            return

        # 获取Canvas的实际宽度
        canvas_width = self.bottom_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 480

        # 计算缩放比例以适应宽度
        img_width, img_height = self.bottom_line_image.size
        ratio = canvas_width / img_width

        # 缩放图片
        display_width = canvas_width
        display_height = int(img_height * ratio)

        # 创建显示用的图片
        display_image = self.bottom_line_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(display_image)

        self.bottom_image_label.config(image=photo)
        self.bottom_image_label.image = photo
        self.bottom_display_photo = photo
        self.bottom_line_photo = photo

        # 更新滚动区域
        self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def clear_lines(self):
        """清除绘制的线条"""
        # 恢复上方图片的原始显示
        if self.top_photo is not None:
            self.top_image_label.config(image=self.top_photo)
            self.top_image_label.image = self.top_photo

        # 恢复下方图片的原始显示
        if self.bottom_image is not None:
            self.bottom_line_image = None
            self.update_bottom_display()

        # 清除线条对象的引用
        self.top_line_photo = None
        self.bottom_line_photo = None

    def load_image(self, position):
        """加载单张图片"""
        if position == "top":
            image_path = self.url_entry_top.get().strip()
            target_size = (self.top_size, self.top_size)
            placeholder = self.top_placeholder_photo if hasattr(self, 'top_placeholder_photo') else None
            is_top = True
        else:  # bottom
            image_path = self.url_entry_bottom.get().strip()
            target_size = (self.bottom_width, self.bottom_height)
            placeholder = self.bottom_placeholder_photo if hasattr(self, 'bottom_placeholder_photo') else None
            is_top = False

        if not image_path:
            messagebox.showwarning("提示", f"请输入{'上方' if is_top else '下方'}图片地址！")
            return

        if not os.path.exists(image_path):
            messagebox.showerror("错误", f"找不到图片文件：\n{image_path}")
            if placeholder:
                if is_top:
                    self.top_image_label.config(image=placeholder)
                    self.top_image_label.image = placeholder
                else:
                    self.bottom_image_label.config(image=placeholder)
                    self.bottom_image_label.image = placeholder
                    self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))
            return

        try:
            # 加载原始图片
            original_image = Image.open(image_path)

            if is_top:
                # 上方图片：调整到512x512并直接显示
                resized_image, display_info = self.resize_and_center_with_info(original_image, target_size)
                photo = ImageTk.PhotoImage(resized_image)
                self.top_image_label.config(image=photo)
                self.top_image_label.image = photo
                self.top_photo = photo
                self.top_image = resized_image

                # 保存显示信息用于坐标计算
                self.top_display_width = display_info['display_width']
                self.top_display_height = display_info['display_height']
                self.top_offset_x = display_info['offset_x']
                self.top_offset_y = display_info['offset_y']

                self.root.title(f"Tomography Point Picker - 上方已加载 (点击选择坐标)")

                # 如果有之前选择的坐标，重新绘制十字准星
                if self.current_x is not None and self.current_y is not None:
                    self.draw_crosshair(self.current_x, self.current_y)
            else:
                # 下方图片：保持原始尺寸，但需要调整显示
                resized_image, _ = self.resize_and_center_with_info(original_image, target_size)
                self.bottom_image = resized_image

                # 如果有之前选择的x坐标，绘制绿线
                if self.current_x is not None:
                    # 创建带绿线的副本
                    img_copy = resized_image.copy()
                    draw = ImageDraw.Draw(img_copy)
                    line_x = self.current_x - 1
                    draw.line([(line_x, 0), (line_x, 1919)], fill=(0, 255, 0), width=2)
                    self.bottom_line_image = img_copy
                    self.update_bottom_display_with_line()
                else:
                    self.bottom_line_image = None
                    self.update_bottom_display()

                self.root.title(f"Tomography Point Picker - 下方已加载")

                # 滚动到顶部
                self.bottom_canvas.yview_moveto(0)

            # 更新滚动区域
            self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片：\n{str(e)}")
            if placeholder:
                if is_top:
                    self.top_image_label.config(image=placeholder)
                    self.top_image_label.image = placeholder
                else:
                    self.bottom_image_label.config(image=placeholder)
                    self.bottom_image_label.image = placeholder
                    self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def update_bottom_display(self):
        """更新下方图片的显示（根据当前显示区域大小）"""
        if not hasattr(self, 'bottom_image') or self.bottom_image is None:
            return

        # 获取Canvas的实际宽度
        canvas_width = self.bottom_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 480

        # 计算缩放比例以适应宽度
        img_width, img_height = self.bottom_image.size
        ratio = canvas_width / img_width

        # 缩放图片
        display_width = canvas_width
        display_height = int(img_height * ratio)

        # 创建显示用的图片
        display_image = self.bottom_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(display_image)

        self.bottom_image_label.config(image=photo)
        self.bottom_image_label.image = photo
        self.bottom_display_photo = photo

        # 更新滚动区域
        self.bottom_canvas.configure(scrollregion=self.bottom_canvas.bbox("all"))

    def resize_and_center_with_info(self, image, target_size):
        """调整图片到目标尺寸并居中（保持比例），返回图片和显示信息"""
        target_width, target_height = target_size

        # 创建画布
        resized_image = Image.new("RGB", (target_width, target_height), (255, 255, 255))

        # 计算缩放比例
        width, height = image.size
        ratio = min(target_width / width, target_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        # 缩放图片
        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 居中粘贴
        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        resized_image.paste(scaled_image, (x, y))

        # 返回图片和显示信息
        display_info = {
            'display_width': new_width,
            'display_height': new_height,
            'offset_x': x,
            'offset_y': y
        }

        return resized_image, display_info

    def resize_and_center(self, image, target_size):
        """调整图片到目标尺寸并居中（保持比例）- 简化版本，用于向下兼容"""
        resized_image, _ = self.resize_and_center_with_info(image, target_size)
        return resized_image