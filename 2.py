import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class TernaryReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Ga-In-Sn 三元相图配比读取工具")

        self.image_path = "image.png"
        self.image = None
        self.tk_image = None

        # 顶点顺序：Ga, In, Sn
        self.vertices = []
        self.vertex_names = ["Ga", "In", "Sn"]

        self.marker_items = []
        self.calibrated = False

        self.create_widgets()
        self.load_image(self.image_path)

    def create_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        btn_load = tk.Button(top_frame, text="打开图片", command=self.open_image)
        btn_load.pack(side=tk.LEFT, padx=4)

        btn_reset = tk.Button(top_frame, text="重新标定", command=self.reset_calibration)
        btn_reset.pack(side=tk.LEFT, padx=4)

        self.info_label = tk.Label(
            top_frame,
            text="请依次点击三角形顶点：Ga → In → Sn",
            anchor="w"
        )
        self.info_label.pack(side=tk.LEFT, padx=12)

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.result_label = tk.Label(
            self.root,
            text="结果：尚未标定",
            font=("Arial", 12),
            anchor="w",
            justify="left"
        )
        self.result_label.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)

        self.canvas.bind("<Button-1>", self.on_click)

    def open_image(self):
        path = filedialog.askopenfilename(
            title="选择三元相图图片",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.load_image(path)
            self.reset_calibration()

    def load_image(self, path):
        try:
            self.image = Image.open(path)
            self.image_path = path
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：\n{e}")
            return

        self.tk_image = ImageTk.PhotoImage(self.image)

        w, h = self.image.size
        self.canvas.config(width=w, height=h, scrollregion=(0, 0, w, h))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def reset_calibration(self):
        self.vertices = []
        self.calibrated = False
        self.clear_markers()
        self.info_label.config(text="请依次点击三角形顶点：Ga → In → Sn")
        self.result_label.config(text="结果：尚未标定")

    def clear_markers(self):
        for item in self.marker_items:
            self.canvas.delete(item)
        self.marker_items = []

    def on_click(self, event):
        x, y = event.x, event.y

        if not self.calibrated:
            self.add_vertex(x, y)
        else:
            self.read_composition(x, y)

    def add_vertex(self, x, y):
        idx = len(self.vertices)
        name = self.vertex_names[idx]

        self.vertices.append((x, y))

        r = 5
        oval = self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            outline="red", width=2
        )
        text = self.canvas.create_text(
            x + 12, y - 12,
            text=name,
            fill="red",
            font=("Arial", 12, "bold")
        )
        self.marker_items.extend([oval, text])

        if len(self.vertices) < 3:
            next_name = self.vertex_names[len(self.vertices)]
            self.info_label.config(text=f"已标定 {name}，请继续点击 {next_name} 顶点")
        else:
            self.calibrated = True
            self.info_label.config(text="标定完成。现在点击三角形内部任意点读取配比。")
            self.result_label.config(
                text=(
                    "结果：标定完成\n"
                    f"Ga 顶点: {self.vertices[0]}   "
                    f"In 顶点: {self.vertices[1]}   "
                    f"Sn 顶点: {self.vertices[2]}"
                )
            )

    def barycentric_coordinates(self, x, y):
        """
        根据三个顶点坐标计算点击点的三元组成。
        返回值为 Ga, In, Sn 三个权重，范围理论上为 0~1。
        """

        x_ga, y_ga = self.vertices[0]
        x_in, y_in = self.vertices[1]
        x_sn, y_sn = self.vertices[2]

        denominator = (
            (y_in - y_sn) * (x_ga - x_sn)
            + (x_sn - x_in) * (y_ga - y_sn)
        )

        if abs(denominator) < 1e-12:
            raise ValueError("三个标定点几乎共线，无法计算。请重新标定三角形顶点。")

        ga = (
            (y_in - y_sn) * (x - x_sn)
            + (x_sn - x_in) * (y - y_sn)
        ) / denominator

        inn = (
            (y_sn - y_ga) * (x - x_sn)
            + (x_ga - x_sn) * (y - y_sn)
        ) / denominator

        sn = 1.0 - ga - inn

        return ga, inn, sn

    def read_composition(self, x, y):
        try:
            ga, inn, sn = self.barycentric_coordinates(x, y)
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return

        ga_pct = ga * 100
        in_pct = inn * 100
        sn_pct = sn * 100

        # 判断是否在三角形内部
        inside = (
            ga_pct >= -0.5 and
            in_pct >= -0.5 and
            sn_pct >= -0.5 and
            ga_pct <= 100.5 and
            in_pct <= 100.5 and
            sn_pct <= 100.5
        )

        self.clear_point_marker()

        r = 4
        point = self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill="blue", outline="blue"
        )
        label = self.canvas.create_text(
            x + 10, y + 15,
            text=f"Ga {ga_pct:.1f}%\nIn {in_pct:.1f}%\nSn {sn_pct:.1f}%",
            fill="blue",
            font=("Arial", 10, "bold"),
            anchor="nw"
        )
        self.marker_items.extend([point, label])

        status = "三角形内部" if inside else "三角形外部或靠近边界外侧"

        self.result_label.config(
            text=(
                f"点击坐标：x={x}, y={y}    状态：{status}\n"
                f"Ga = {ga_pct:.2f} wt.%    "
                f"In = {in_pct:.2f} wt.%    "
                f"Sn = {sn_pct:.2f} wt.%    "
                f"总和 = {ga_pct + in_pct + sn_pct:.2f} wt.%"
            )
        )

    def clear_point_marker(self):
        # 保留前三个顶点标定标记，只删除后续点击点标记
        # 每个顶点有 oval 和 text，共 6 个 item
        if len(self.marker_items) > 6:
            for item in self.marker_items[6:]:
                self.canvas.delete(item)
            self.marker_items = self.marker_items[:6]


if __name__ == "__main__":
    root = tk.Tk()
    app = TernaryReader(root)
    root.mainloop()