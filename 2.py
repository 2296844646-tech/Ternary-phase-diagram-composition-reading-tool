import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk


try:
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_FILTER = Image.LANCZOS


class TernaryReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Ga-In-Sn 三元相图配比读取工具")
        self.root.geometry("1250x800")

        self.image_path = "image.png"
        self.image = None
        self.display_image = None
        self.tk_image = None

        self.zoom = 1.0
        self.min_zoom = 0.15
        self.max_zoom = 8.0

        # 顶点顺序：Ga, In, Sn
        self.vertices = []
        self.vertex_names = ["Ga", "In", "Sn"]

        # 连续取点数据
        self.points = []

        self.vertex_items = []
        self.point_items = []

        self.calibrated = False

        self.create_widgets()

        if os.path.exists(self.image_path):
            self.load_image(self.image_path)
        else:
            self.result_label.config(text="结果：未找到默认 image.png，请点击“打开图片”选择相图。")

    def create_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        btn_load = tk.Button(top_frame, text="打开图片", command=self.open_image)
        btn_load.pack(side=tk.LEFT, padx=4)

        btn_reset = tk.Button(top_frame, text="重新标定", command=self.reset_calibration)
        btn_reset.pack(side=tk.LEFT, padx=4)

        btn_undo_vertex = tk.Button(top_frame, text="撤回顶点", command=self.undo_last_vertex)
        btn_undo_vertex.pack(side=tk.LEFT, padx=4)

        tk.Label(top_frame, text=" | ").pack(side=tk.LEFT, padx=4)

        btn_zoom_in = tk.Button(top_frame, text="放大", command=lambda: self.change_zoom(1.2))
        btn_zoom_in.pack(side=tk.LEFT, padx=4)

        btn_zoom_out = tk.Button(top_frame, text="缩小", command=lambda: self.change_zoom(1 / 1.2))
        btn_zoom_out.pack(side=tk.LEFT, padx=4)

        btn_fit = tk.Button(top_frame, text="适应窗口", command=self.zoom_to_fit)
        btn_fit.pack(side=tk.LEFT, padx=4)

        self.zoom_label = tk.Label(top_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=8)

        self.info_label = tk.Label(
            top_frame,
            text="请依次点击三角形顶点：Ga → In → Sn",
            anchor="w"
        )
        self.info_label.pack(side=tk.LEFT, padx=12)

        main_frame = tk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="white", cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        x_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")

        y_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")

        self.canvas.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        side_frame = tk.Frame(main_frame, width=430)
        side_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=4)

        tk.Label(
            side_frame,
            text="连续取点数据",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=(0, 4))

        columns = ("no", "x", "y", "ga", "in", "sn", "status")
        self.tree = ttk.Treeview(
            side_frame,
            columns=columns,
            show="headings",
            height=24
        )

        self.tree.heading("no", text="序号")
        self.tree.heading("x", text="X")
        self.tree.heading("y", text="Y")
        self.tree.heading("ga", text="Ga wt.%")
        self.tree.heading("in", text="In wt.%")
        self.tree.heading("sn", text="Sn wt.%")
        self.tree.heading("status", text="状态")

        self.tree.column("no", width=50, anchor="center")
        self.tree.column("x", width=65, anchor="center")
        self.tree.column("y", width=65, anchor="center")
        self.tree.column("ga", width=75, anchor="center")
        self.tree.column("in", width=75, anchor="center")
        self.tree.column("sn", width=75, anchor="center")
        self.tree.column("status", width=80, anchor="center")

        tree_scroll = tk.Scrollbar(side_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        point_button_frame = tk.Frame(self.root)
        point_button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(0, 4))

        btn_delete_point = tk.Button(
            point_button_frame,
            text="删除选中取点",
            command=self.delete_selected_points
        )
        btn_delete_point.pack(side=tk.LEFT, padx=4)

        btn_clear_points = tk.Button(
            point_button_frame,
            text="清空取点",
            command=self.clear_points
        )
        btn_clear_points.pack(side=tk.LEFT, padx=4)

        btn_export = tk.Button(
            point_button_frame,
            text="导出 CSV",
            command=self.export_csv
        )
        btn_export.pack(side=tk.LEFT, padx=4)

        self.result_label = tk.Label(
            self.root,
            text="结果：尚未标定",
            font=("Arial", 12),
            anchor="w",
            justify="left"
        )
        self.result_label.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=6)

        self.canvas.bind("<Button-1>", self.on_click)

        # 鼠标滚轮缩放
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)   # Windows / macOS
        self.canvas.bind("<Button-4>", self.on_mousewheel)     # Linux 向上滚
        self.canvas.bind("<Button-5>", self.on_mousewheel)     # Linux 向下滚

        # 快捷键：撤回顶点
        self.root.bind("<Control-z>", lambda event: self.undo_last_vertex())

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

    def load_image(self, path):
        try:
            self.image = Image.open(path)
            self.image_path = path
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：\n{e}")
            return

        self.zoom = 1.0
        self.vertices = []
        self.points = []
        self.calibrated = False

        self.refresh_tree()
        self.render_image()
        self.update_status_text()

    def render_image(self):
        if self.image is None:
            return

        w, h = self.image.size
        display_w = max(1, int(w * self.zoom))
        display_h = max(1, int(h * self.zoom))

        self.display_image = self.image.resize((display_w, display_h), RESAMPLE_FILTER)
        self.tk_image = ImageTk.PhotoImage(self.display_image)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=(0, 0, display_w, display_h))

        self.vertex_items = []
        self.point_items = []
        self.redraw_overlay()

        self.zoom_label.config(text=f"{self.zoom * 100:.0f}%")

    def image_to_canvas(self, x, y):
        return x * self.zoom, y * self.zoom

    def canvas_to_image(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        image_x = canvas_x / self.zoom
        image_y = canvas_y / self.zoom

        return image_x, image_y

    def change_zoom(self, factor, event=None):
        if self.image is None:
            return

        old_zoom = self.zoom
        new_zoom = old_zoom * factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))

        if abs(new_zoom - old_zoom) < 1e-9:
            return

        if event is not None:
            old_canvas_x = self.canvas.canvasx(event.x)
            old_canvas_y = self.canvas.canvasy(event.y)
            anchor_screen_x = event.x
            anchor_screen_y = event.y
        else:
            anchor_screen_x = self.canvas.winfo_width() / 2
            anchor_screen_y = self.canvas.winfo_height() / 2
            old_canvas_x = self.canvas.canvasx(anchor_screen_x)
            old_canvas_y = self.canvas.canvasy(anchor_screen_y)

        anchor_image_x = old_canvas_x / old_zoom
        anchor_image_y = old_canvas_y / old_zoom

        self.zoom = new_zoom
        self.render_image()
        self.root.update_idletasks()

        new_canvas_x = anchor_image_x * new_zoom
        new_canvas_y = anchor_image_y * new_zoom

        target_left = new_canvas_x - anchor_screen_x
        target_top = new_canvas_y - anchor_screen_y

        display_w = max(1, int(self.image.size[0] * new_zoom))
        display_h = max(1, int(self.image.size[1] * new_zoom))

        self.canvas.xview_moveto(max(0, min(1, target_left / display_w)))
        self.canvas.yview_moveto(max(0, min(1, target_top / display_h)))

    def on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.change_zoom(1.12, event)
        elif event.num == 5 or event.delta < 0:
            self.change_zoom(1 / 1.12, event)

        return "break"

    def zoom_to_fit(self):
        if self.image is None:
            return

        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())

        img_w, img_h = self.image.size

        scale_w = canvas_w / img_w
        scale_h = canvas_h / img_h

        self.zoom = max(self.min_zoom, min(self.max_zoom, min(scale_w, scale_h)))
        self.render_image()

    def reset_calibration(self):
        self.vertices = []
        self.points = []
        self.calibrated = False

        self.refresh_tree()
        self.redraw_overlay()
        self.update_status_text()

    def undo_last_vertex(self):
        if not self.vertices:
            messagebox.showinfo("提示", "当前没有可以撤回的顶点。")
            return

        removed_index = len(self.vertices) - 1
        removed_name = self.vertex_names[removed_index]

        self.vertices.pop()
        self.calibrated = False

        # 顶点改变后，原来的取点结果不再可靠，直接清空
        if self.points:
            self.points = []
            self.refresh_tree()

        self.redraw_overlay()
        self.update_status_text()

        self.result_label.config(
            text=f"结果：已撤回 {removed_name} 顶点。请继续标定。"
        )

    def redraw_overlay(self):
        for item in self.vertex_items:
            self.canvas.delete(item)
        for item in self.point_items:
            self.canvas.delete(item)

        self.vertex_items = []
        self.point_items = []

        for idx, (x, y) in enumerate(self.vertices):
            self.draw_vertex(idx, x, y)

        for point in self.points:
            self.draw_point(point)

    def draw_vertex(self, idx, x, y):
        cx, cy = self.image_to_canvas(x, y)
        name = self.vertex_names[idx]

        r = 5
        oval = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline="red",
            width=2
        )

        text = self.canvas.create_text(
            cx + 12,
            cy - 12,
            text=name,
            fill="red",
            font=("Arial", 12, "bold")
        )

        self.vertex_items.extend([oval, text])

    def draw_point(self, point):
        cx, cy = self.image_to_canvas(point["x"], point["y"])

        r = 4
        oval = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill="blue",
            outline="blue"
        )

        label = self.canvas.create_text(
            cx + 8,
            cy + 8,
            text=f"#{point['no']}",
            fill="blue",
            font=("Arial", 10, "bold"),
            anchor="nw"
        )

        self.point_items.extend([oval, label])

    def on_click(self, event):
        if self.image is None:
            messagebox.showinfo("提示", "请先打开三元相图图片。")
            return

        self.canvas.focus_set()

        x, y = self.canvas_to_image(event)

        img_w, img_h = self.image.size
        if not (0 <= x <= img_w and 0 <= y <= img_h):
            return

        if not self.calibrated:
            self.add_vertex(x, y)
        else:
            self.read_composition(x, y)

    def add_vertex(self, x, y):
        if len(self.vertices) >= 3:
            return

        self.vertices.append((x, y))

        if len(self.vertices) == 3:
            self.calibrated = True

        self.redraw_overlay()
        self.update_status_text()

    def update_status_text(self):
        if len(self.vertices) < 3:
            next_name = self.vertex_names[len(self.vertices)]
            self.info_label.config(
                text=f"请依次点击三角形顶点：Ga → In → Sn；当前请点击 {next_name} 顶点。"
            )

            if not self.vertices:
                self.result_label.config(text="结果：尚未标定")
            else:
                vertex_text = "   ".join(
                    f"{self.vertex_names[i]}: ({x:.1f}, {y:.1f})"
                    for i, (x, y) in enumerate(self.vertices)
                )
                self.result_label.config(
                    text=f"结果：已标定 {len(self.vertices)} 个顶点。\n{vertex_text}"
                )
        else:
            self.info_label.config(
                text="标定完成。现在可以连续点击三角形内部点读取配比；滚轮可缩放，Ctrl+Z 可撤回顶点。"
            )

            vertex_text = "   ".join(
                f"{self.vertex_names[i]}: ({x:.1f}, {y:.1f})"
                for i, (x, y) in enumerate(self.vertices)
            )
            self.result_label.config(
                text=f"结果：标定完成。\n{vertex_text}"
            )

    def barycentric_coordinates(self, x, y):
        """
        根据三个顶点坐标计算点击点的三元组成。
        返回值为 Ga, In, Sn 三个权重，理论范围为 0~1。
        """

        if len(self.vertices) != 3:
            raise ValueError("尚未完成三个顶点标定。")

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

        inside = (
            ga >= -0.005 and
            inn >= -0.005 and
            sn >= -0.005 and
            ga <= 1.005 and
            inn <= 1.005 and
            sn <= 1.005
        )

        status = "内部" if inside else "外部"

        point = {
            "no": len(self.points) + 1,
            "x": x,
            "y": y,
            "ga": ga_pct,
            "in": in_pct,
            "sn": sn_pct,
            "status": status
        }

        self.points.append(point)
        self.insert_point_to_tree(point)
        self.redraw_overlay()

        self.result_label.config(
            text=(
                f"最新取点：#{point['no']}    "
                f"图像坐标：x={x:.1f}, y={y:.1f}    状态：{status}\n"
                f"Ga = {ga_pct:.2f} wt.%    "
                f"In = {in_pct:.2f} wt.%    "
                f"Sn = {sn_pct:.2f} wt.%    "
                f"总和 = {ga_pct + in_pct + sn_pct:.2f} wt.%"
            )
        )

    def insert_point_to_tree(self, point):
        self.tree.insert(
            "",
            tk.END,
            values=(
                point["no"],
                f"{point['x']:.1f}",
                f"{point['y']:.1f}",
                f"{point['ga']:.2f}",
                f"{point['in']:.2f}",
                f"{point['sn']:.2f}",
                point["status"]
            )
        )

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for point in self.points:
            self.insert_point_to_tree(point)

    def renumber_points(self):
        for idx, point in enumerate(self.points, start=1):
            point["no"] = idx

        self.refresh_tree()
        self.redraw_overlay()

    def delete_selected_points(self):
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showinfo("提示", "请先在右侧表格中选择需要删除的取点。")
            return

        selected_numbers = set()
        for item in selected_items:
            values = self.tree.item(item, "values")
            if values:
                selected_numbers.add(int(values[0]))

        self.points = [
            point for point in self.points
            if point["no"] not in selected_numbers
        ]

        self.renumber_points()

        self.result_label.config(
            text=f"结果：已删除 {len(selected_numbers)} 个取点。"
        )

    def clear_points(self):
        if not self.points:
            messagebox.showinfo("提示", "当前没有取点数据。")
            return

        self.points = []
        self.refresh_tree()
        self.redraw_overlay()

        self.result_label.config(text="结果：已清空所有取点数据。")

    def export_csv(self):
        if not self.points:
            messagebox.showinfo("提示", "当前没有可导出的取点数据。")
            return

        path = filedialog.asksaveasfilename(
            title="导出取点数据",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)

                writer.writerow([
                    "No",
                    "X_image",
                    "Y_image",
                    "Ga_wt_percent",
                    "In_wt_percent",
                    "Sn_wt_percent",
                    "Status"
                ])

                for point in self.points:
                    writer.writerow([
                        point["no"],
                        f"{point['x']:.3f}",
                        f"{point['y']:.3f}",
                        f"{point['ga']:.6f}",
                        f"{point['in']:.6f}",
                        f"{point['sn']:.6f}",
                        point["status"]
                    ])

            messagebox.showinfo("完成", f"取点数据已导出：\n{path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TernaryReader(root)
    root.mainloop()