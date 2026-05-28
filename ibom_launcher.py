from __future__ import annotations

import json
import os
import sys
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from generate_ibom import RuntimeOptions, build_payload, inspect_bom_headers, render_generation_report, render_html, validate_runtime_options


def get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


class IbomLauncher:
    def __init__(self) -> None:
        self.state_path = get_runtime_base_dir() / "launcher_state.json"
        self.saved_state = self._load_state()
        self.root = tk.Tk()
        self.root.title("Cadence 交互式 BOM 启动器")
        self.root.geometry("1120x760")
        self.root.minsize(1040, 700)

        self.bom_var = tk.StringVar()
        self.ipc_var = tk.StringVar()
        self.placement_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.title_var = tk.StringVar(value="Cadence 交互式 BOM")
        self.project_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.version_var = tk.StringVar(value=self.saved_state.get("version", "v1.0"))
        self.created_at_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.output_mode_var = tk.StringVar(value=self.saved_state.get("output_mode", "unique"))
        self.include_test_points_var = tk.BooleanVar(value=bool(self.saved_state.get("include_test_points", False)))
        self.auto_open_var = tk.BooleanVar(value=bool(self.saved_state.get("auto_open", True)))
        self.status_var = tk.StringVar(value="请选择 BOM 和 IPC-2581 文件。")
        self.last_html_path = Path(self.saved_state["last_html"]) if self.saved_state.get("last_html") else None
        self.last_report_path = Path(self.saved_state["last_report"]) if self.saved_state.get("last_report") else None
        self.recent_projects = self.saved_state.get("recent_projects", [])

        self._build_ui()
        self._apply_saved_state()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        container.columnconfigure(1, weight=1)
        container.rowconfigure(11, weight=1)

        row = 0
        ttk.Label(container, text="最近项目").grid(row=row, column=0, sticky="w", pady=6)
        recent_frame = ttk.Frame(container)
        recent_frame.grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        recent_frame.columnconfigure(0, weight=1)
        self.recent_var = tk.StringVar()
        self.recent_combo = ttk.Combobox(recent_frame, textvariable=self.recent_var, state="readonly")
        self.recent_combo.grid(row=0, column=0, sticky="ew")
        ttk.Button(recent_frame, text="载入", command=self.load_recent_project).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(recent_frame, text="删除", command=self.remove_recent_project).grid(row=0, column=2, padx=(8, 0))
        row += 1

        self._add_path_row(container, row, "BOM 文件", self.bom_var, self.pick_bom)
        row += 1
        self._add_path_row(container, row, "IPC-2581 XML", self.ipc_var, self.pick_ipc)
        row += 1
        self._add_path_row(container, row, "Placement 文件", self.placement_var, self.pick_placement)
        row += 1
        self._add_path_row(container, row, "输出 HTML", self.output_var, self.pick_output)
        row += 1

        ttk.Label(container, text="页面标题").grid(row=row, column=0, sticky="w", pady=(10, 6))
        ttk.Entry(container, textvariable=self.title_var).grid(row=row, column=1, columnspan=2, sticky="ew", pady=(10, 6))
        row += 1

        ttk.Label(container, text="项目标识").grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.project_var).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(container, text="编写者").grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.author_var).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(container, text="版本").grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.version_var).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(container, text="创建时间").grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.created_at_var).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(container, text="输出策略").grid(row=row, column=0, sticky="w", pady=6)
        ttk.Combobox(
            container,
            textvariable=self.output_mode_var,
            state="readonly",
            values=["unique", "overwrite", "ask"],
        ).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Checkbutton(
            container,
            text="保留测试点",
            variable=self.include_test_points_var,
        ).grid(row=row, column=1, sticky="w", pady=(10, 0))
        ttk.Checkbutton(
            container,
            text="生成后自动打开页面",
            variable=self.auto_open_var,
        ).grid(row=row, column=2, sticky="w", pady=(10, 0))
        row += 1

        note = (
            "最简使用方式：选择 BOM 和 IPC-2581 即可。\n"
            "Placement 文件可不选；如果不指定输出路径，将自动生成到 BOM 同目录下的 dist 文件夹。"
        )
        ttk.Label(container, text=note, foreground="#5b6875", justify=tk.LEFT).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(12, 12)
        )
        row += 1

        preview_frame = ttk.LabelFrame(container, text="检查结果预览")
        preview_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=(0, 12))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=12, wrap=tk.WORD)
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        self.preview_text.insert("1.0", "这里会显示输入检查摘要、表头识别结果和生成结果路径。")
        self.preview_text.configure(state="disabled")
        container.rowconfigure(row, weight=1)
        row += 1

        bottom = ttk.Frame(container)
        bottom.grid(row=row, column=0, columnspan=3, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        ttk.Label(bottom, textvariable=self.status_var, foreground="#5b6875").grid(row=0, column=0, sticky="w")
        ttk.Button(bottom, text="清空上次记录", command=self.clear_saved_state).grid(row=0, column=1, sticky="e", padx=(12, 0))
        ttk.Button(bottom, text="检查输入", command=self.inspect_inputs).grid(row=0, column=2, sticky="e", padx=(12, 0))
        ttk.Button(bottom, text="打开输出目录", command=self.open_output_dir).grid(row=0, column=3, sticky="e", padx=(12, 0))
        ttk.Button(bottom, text="生成 HTML", command=self.generate).grid(row=0, column=4, sticky="e", padx=(12, 0))
        ttk.Button(bottom, text="打开最近页面", command=self.open_last_html).grid(row=1, column=3, sticky="e", padx=(12, 0), pady=(10, 0))
        ttk.Button(bottom, text="打开最近报告", command=self.open_last_report).grid(row=1, column=4, sticky="e", padx=(12, 0), pady=(10, 0))

    def _add_path_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=6, padx=(0, 8))
        ttk.Button(parent, text="选择...", command=command).grid(row=row, column=2, sticky="ew", pady=6)

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self) -> None:
        state = {
            "bom": self.bom_var.get().strip(),
            "ipc": self.ipc_var.get().strip(),
            "placement": self.placement_var.get().strip(),
            "output": self.output_var.get().strip(),
            "title": self.title_var.get().strip(),
            "project": self.project_var.get().strip(),
            "author": self.author_var.get().strip(),
            "version": self.version_var.get().strip(),
            "output_mode": self.output_mode_var.get(),
            "include_test_points": self.include_test_points_var.get(),
            "auto_open": self.auto_open_var.get(),
            "last_html": str(self.last_html_path) if self.last_html_path else "",
            "last_report": str(self.last_report_path) if self.last_report_path else "",
            "recent_projects": self.recent_projects[:8],
        }
        try:
            self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _apply_saved_state(self) -> None:
        if self.saved_state.get("bom"):
            self.bom_var.set(self.saved_state["bom"])
        if self.saved_state.get("ipc"):
            self.ipc_var.set(self.saved_state["ipc"])
        if self.saved_state.get("placement"):
            self.placement_var.set(self.saved_state["placement"])
        if self.saved_state.get("output"):
            self.output_var.set(self.saved_state["output"])
        if self.saved_state.get("title"):
            self.title_var.set(self.saved_state["title"])
        if self.saved_state.get("project"):
            self.project_var.set(self.saved_state["project"])
        if self.saved_state.get("author"):
            self.author_var.set(self.saved_state["author"])
        self._refresh_recent_projects()

    def clear_saved_state(self) -> None:
        self.bom_var.set("")
        self.ipc_var.set("")
        self.placement_var.set("")
        self.output_var.set("")
        self.title_var.set("Cadence 交互式 BOM")
        self.project_var.set("")
        self.author_var.set("")
        self.version_var.set("v1.0")
        self.created_at_var.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.output_mode_var.set("unique")
        self.include_test_points_var.set(False)
        self.auto_open_var.set(True)
        self.last_html_path = None
        self.last_report_path = None
        self.recent_projects = []
        self._refresh_recent_projects()
        self._set_preview_text("这里会显示输入检查摘要、表头识别结果和生成结果路径。")
        self.status_var.set("已清空上次记录。")
        try:
            if self.state_path.exists():
                self.state_path.unlink()
        except Exception:
            pass

    def _refresh_recent_projects(self) -> None:
        values = []
        for item in self.recent_projects:
            bom_name = Path(item.get("bom", "")).name if item.get("bom") else "-"
            project = item.get("project") or bom_name
            values.append(f"{project} | {bom_name}")
        self.recent_combo["values"] = values
        if values:
            self.recent_combo.current(0)
        else:
            self.recent_var.set("")

    def _remember_recent_project(self) -> None:
        snapshot = {
            "bom": self.bom_var.get().strip(),
            "ipc": self.ipc_var.get().strip(),
            "placement": self.placement_var.get().strip(),
            "output": self.output_var.get().strip(),
            "title": self.title_var.get().strip(),
            "project": self.project_var.get().strip(),
            "author": self.author_var.get().strip(),
            "version": self.version_var.get().strip(),
            "output_mode": self.output_mode_var.get(),
            "include_test_points": self.include_test_points_var.get(),
            "auto_open": self.auto_open_var.get(),
        }
        key = (snapshot["bom"], snapshot["ipc"], snapshot["project"])
        deduped = [item for item in self.recent_projects if (item.get("bom", ""), item.get("ipc", ""), item.get("project", "")) != key]
        self.recent_projects = [snapshot, *deduped][:8]
        self._refresh_recent_projects()

    def load_recent_project(self) -> None:
        index = self.recent_combo.current()
        if index < 0 or index >= len(self.recent_projects):
            return
        item = self.recent_projects[index]
        self.bom_var.set(item.get("bom", ""))
        self.ipc_var.set(item.get("ipc", ""))
        self.placement_var.set(item.get("placement", ""))
        self.output_var.set(item.get("output", ""))
        self.title_var.set(item.get("title", "Cadence 交互式 BOM"))
        self.project_var.set(item.get("project", ""))
        self.author_var.set(item.get("author", ""))
        self.version_var.set(item.get("version", "v1.0"))
        self.output_mode_var.set(item.get("output_mode", "unique"))
        self.include_test_points_var.set(bool(item.get("include_test_points", False)))
        self.auto_open_var.set(bool(item.get("auto_open", True)))
        self.status_var.set("已载入最近项目。")

    def remove_recent_project(self) -> None:
        index = self.recent_combo.current()
        if index < 0 or index >= len(self.recent_projects):
            messagebox.showinfo("提示", "请先选择一条最近项目记录。")
            return
        removed = self.recent_projects.pop(index)
        self._refresh_recent_projects()
        self._save_state()
        project_name = removed.get("project") or Path(removed.get("bom", "")).name or "最近项目"
        self.status_var.set(f"已删除最近项目：{project_name}")

    def _expected_auto_title(self, bom_stem: str) -> str:
        return f"{bom_stem} 交互式 BOM"

    def _expected_auto_output(self, bom_path: Path) -> Path:
        return bom_path.parent / "dist" / f"{bom_path.stem}_ibom.html"

    def _should_update_auto_fields(self, bom_path: Path) -> tuple[bool, bool, bool]:
        current_title = self.title_var.get().strip()
        current_project = self.project_var.get().strip()
        current_output = self.output_var.get().strip()
        prev_bom_text = self.saved_state.get("bom", "")
        prev_bom = Path(prev_bom_text) if prev_bom_text else None

        title_auto = (
            not current_title
            or current_title == "Cadence 交互式 BOM"
            or (prev_bom is not None and current_title == self._expected_auto_title(prev_bom.stem))
        )
        project_auto = (
            not current_project
            or (prev_bom is not None and current_project == prev_bom.stem)
        )
        output_auto = (
            not current_output
            or (
                prev_bom is not None
                and Path(current_output).expanduser() == self._expected_auto_output(prev_bom).expanduser()
            )
        )
        return title_auto, project_auto, output_auto

    def pick_bom(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 BOM 文件",
            filetypes=[("BOM files", "*.xlsx *.csv *.tsv *.txt"), ("All files", "*.*")],
            initialdir=self._pick_initial_dir(self.bom_var.get()),
        )
        if not path:
            return
        bom_path = Path(path)
        title_auto, project_auto, output_auto = self._should_update_auto_fields(bom_path)
        self.bom_var.set(path)
        if title_auto:
            self.title_var.set(self._expected_auto_title(bom_path.stem))
        if project_auto:
            self.project_var.set(bom_path.stem)
        if output_auto:
            default_output = self._build_default_output_path(bom_path)
            self.output_var.set(str(default_output))
        self._save_state()

    def _pick_initial_dir(self, current_value: str) -> str:
        value = current_value.strip()
        if value:
            path = Path(value)
            if path.exists():
                return str(path.parent if path.is_file() else path)
        bom = self.bom_var.get().strip()
        if bom:
            bom_path = Path(bom)
            if bom_path.exists():
                return str(bom_path.parent)
        return str(Path.cwd())

    def _build_default_output_path(self, bom_path: Path) -> Path:
        output_dir = bom_path.parent / "dist"
        base = f"{bom_path.stem}_ibom"
        candidate = output_dir / f"{base}.html"
        mode = self.output_mode_var.get()
        if mode == "overwrite":
            return candidate
        if mode == "ask":
            return candidate
        if not candidate.exists():
            return candidate
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stamped = output_dir / f"{base}_{stamp}.html"
        if not stamped.exists():
            return stamped
        index = 2
        while True:
            indexed = output_dir / f"{base}_{stamp}_{index}.html"
            if not indexed.exists():
                return indexed
            index += 1

    def _make_batch_id(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    def _build_batch_artifact_path(self, options: RuntimeOptions, suffix: str, extension: str, batch_id: str | None = None) -> Path:
        batch = batch_id or self._make_batch_id()
        stem = options.output.stem
        return options.output.with_name(f"{stem}_{batch}_{suffix}.{extension}")

    def pick_ipc(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 IPC-2581 XML",
            filetypes=[("IPC-2581 XML", "*.xml"), ("All files", "*.*")],
            initialdir=self._pick_initial_dir(self.ipc_var.get()),
        )
        if path:
            self.ipc_var.set(path)
            self._save_state()

    def pick_placement(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 Placement 文件",
            filetypes=[("Placement files", "*.htm *.html *.xlsx *.csv *.tsv *.txt"), ("All files", "*.*")],
            initialdir=self._pick_initial_dir(self.placement_var.get()),
        )
        if path:
            self.placement_var.set(path)
            self._save_state()

    def pick_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="选择输出 HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("All files", "*.*")],
            initialdir=self._pick_initial_dir(self.output_var.get()),
        )
        if path:
            self.output_var.set(path)
            self._save_state()

    def build_options(self) -> RuntimeOptions:
        bom = Path(self.bom_var.get()).expanduser() if self.bom_var.get().strip() else None
        ipc = Path(self.ipc_var.get()).expanduser() if self.ipc_var.get().strip() else None
        placement = Path(self.placement_var.get()).expanduser() if self.placement_var.get().strip() else None
        output = Path(self.output_var.get()).expanduser() if self.output_var.get().strip() else None

        if output is None and bom is not None:
            if self.output_mode_var.get() == "ask":
                picked = filedialog.asksaveasfilename(
                    title="选择输出 HTML",
                    defaultextension=".html",
                    filetypes=[("HTML", "*.html"), ("All files", "*.*")],
                    initialdir=str((bom.parent / "dist").resolve()),
                    initialfile=f"{bom.stem}_ibom.html",
                )
                if not picked:
                    raise RuntimeError("已取消选择输出 HTML。")
                output = Path(picked).expanduser()
            else:
                output = self._build_default_output_path(bom)
            self.output_var.set(str(output))

        return RuntimeOptions(
            bom=bom,
            placement=placement,
            ipc=ipc,
            board_top=None,
            board_bottom=None,
            board_top_pdf=None,
            board_bottom_pdf=None,
            title=(self.title_var.get().strip() or "Cadence 交互式 BOM"),
            project=(self.project_var.get().strip() or (bom.stem if bom else "interactive_bom")),
            author=self.author_var.get().strip(),
            version=self.version_var.get().strip(),
            created_at=(self.created_at_var.get().strip() or datetime.now().strftime("%Y-%m-%d %H:%M")),
            placement_unit="auto",
            include_test_points=self.include_test_points_var.get(),
            testpoint_rules={},
            image_placement={},
            output=output or Path("interactive_bom.html"),
        )

    def open_output_dir(self) -> None:
        output_text = self.output_var.get().strip()
        bom_text = self.bom_var.get().strip()
        target: Path | None = None
        if output_text:
            output_path = Path(output_text).expanduser()
            target = output_path.parent if output_path.suffix else output_path
        elif bom_text:
            bom_path = Path(bom_text).expanduser()
            target = bom_path.parent / "dist"
        if target is None:
            messagebox.showinfo("提示", "请先选择 BOM 文件或指定输出 HTML。")
            return
        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror("打开失败", f"无法创建或访问输出目录：\n{target}\n\n{exc}")
            return
        os.startfile(str(target))

    def open_last_html(self) -> None:
        if not self.last_html_path or not self.last_html_path.exists():
            messagebox.showinfo("提示", "还没有最近生成的 HTML 文件。")
            return
        webbrowser.open(self.last_html_path.resolve().as_uri())

    def open_last_report(self) -> None:
        if not self.last_report_path or not self.last_report_path.exists():
            messagebox.showinfo("提示", "还没有最近生成的报告文件。")
            return
        os.startfile(str(self.last_report_path))

    def _set_preview_text(self, text: str) -> None:
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state="disabled")

    def generate(self) -> None:
        options: RuntimeOptions | None = None
        try:
            options = self.build_options()
            issues = validate_runtime_options(options)
            if issues:
                messagebox.showerror("输入有误", "\n".join(issues))
                return

            self.status_var.set("正在生成 HTML，请稍候...")
            self.root.update_idletasks()

            payload = build_payload(options)
            options.output.parent.mkdir(parents=True, exist_ok=True)
            options.output.write_text(render_html(payload), encoding="utf-8")
            batch_id = self._make_batch_id()
            report_path = self._build_batch_artifact_path(options, "report", "txt", batch_id)
            report_path.write_text(render_generation_report(payload, options.output, batch_id=batch_id), encoding="utf-8")
            self.last_html_path = options.output
            self.last_report_path = report_path
            self._remember_recent_project()
            self._save_state()

            self.status_var.set(f"生成完成: {options.output}")
            summary = self._format_generation_summary(payload, options.output, report_path)
            self._set_preview_text(summary)
            if self.auto_open_var.get():
                messagebox.showinfo("生成完成", summary)
                webbrowser.open(options.output.resolve().as_uri())
            else:
                messagebox.showinfo("生成完成", summary)
        except Exception as exc:
            self.status_var.set("生成失败。")
            error_log_path = self._write_error_log(options, exc)
            suffix = f"\n\n错误日志:\n{error_log_path}" if error_log_path else ""
            messagebox.showerror("生成失败", f"{exc}\n\n{traceback.format_exc(limit=4)}{suffix}")

    def inspect_inputs(self) -> None:
        options: RuntimeOptions | None = None
        try:
            options = self.build_options()
            issues = validate_runtime_options(options)
            if issues:
                messagebox.showerror("输入有误", "\n".join(issues))
                return

            self.status_var.set("正在检查输入，请稍候...")
            self.root.update_idletasks()

            payload = build_payload(options)
            report = payload.get("report", {})
            summary = report.get("summary", {})
            warnings = report.get("warnings", [])
            info = report.get("info", [])
            header_info = inspect_bom_headers(options.bom) if options.bom else {"headers": [], "mapped": {}}
            lines = [
                "输入检查通过",
                "",
                f"BOM分组: {summary.get('groupCount', 0)}",
                f"位号总数: {summary.get('referenceCount', 0)}",
                f"已定位位号: {summary.get('placedReferenceCount', 0)}",
                f"未定位位号: {summary.get('unplacedReferenceCount', 0)}",
                f"Top器件: {summary.get('topComponentCount', 0)} / Bottom器件: {summary.get('bottomComponentCount', 0)}",
                f"板框: {'已识别' if summary.get('hasBoardOutline') else '未识别'}",
            ]
            if header_info.get("headers"):
                lines.extend(["", "BOM表头识别:"])
                for header in header_info["headers"][:12]:
                    mapped = header_info["mapped"].get(header, "未识别")
                    lines.append(f"- {header} -> {mapped}")
            if info:
                lines.extend(["", "提示:"])
                lines.extend([f"- {item}" for item in info[:5]])
            if warnings:
                lines.extend(["", "警告:"])
                lines.extend([f"- {item}" for item in warnings[:5]])
            inspect_report_path = self._write_inspect_log(options, lines)
            self._remember_recent_project()
            self._save_state()
            self.status_var.set("输入检查通过。")
            suffix = f"\n\n检查报告:\n{inspect_report_path}" if inspect_report_path else ""
            self._set_preview_text("\n".join(lines) + suffix)
            messagebox.showinfo("检查结果", "\n".join(lines) + suffix)
        except Exception as exc:
            self.status_var.set("输入检查失败。")
            error_log_path = self._write_error_log(options, exc)
            suffix = f"\n\n错误日志:\n{error_log_path}" if error_log_path else ""
            self._set_preview_text(f"输入检查失败\n\n{exc}\n\n{traceback.format_exc(limit=4)}{suffix}")
            messagebox.showerror("检查失败", f"{exc}\n\n{traceback.format_exc(limit=4)}{suffix}")

    def _write_inspect_log(self, options: RuntimeOptions | None, lines: list[str]) -> str:
        try:
            if options is None:
                return ""
            options.output.parent.mkdir(parents=True, exist_ok=True)
            batch_id = self._make_batch_id()
            inspect_path = self._build_batch_artifact_path(options, "inspect", "txt", batch_id)
            content = "\n".join(
                [
                    "Cadence Interactive BOM 输入检查报告",
                    "",
                    f"批次号: {batch_id}",
                    f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"BOM: {options.bom or '-'}",
                    f"Placement: {options.placement or '-'}",
                    f"IPC-2581: {options.ipc or '-'}",
                    "",
                    *lines,
                ]
            )
            inspect_path.write_text(content + "\n", encoding="utf-8")
            return str(inspect_path)
        except Exception:
            return ""

    def _write_error_log(self, options: RuntimeOptions | None, exc: Exception) -> str:
        try:
            if options is None:
                return ""
            options.output.parent.mkdir(parents=True, exist_ok=True)
            batch_id = self._make_batch_id()
            error_log_path = self._build_batch_artifact_path(options, "error", "log", batch_id)
            content = "\n".join(
                [
                    "Cadence Interactive BOM 错误日志",
                    "",
                    f"批次号: {batch_id}",
                    f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"BOM: {options.bom or '-'}",
                    f"Placement: {options.placement or '-'}",
                    f"IPC-2581: {options.ipc or '-'}",
                    f"输出HTML: {options.output}",
                    "",
                    f"错误: {exc}",
                    "",
                    "Traceback:",
                    traceback.format_exc(),
                ]
            )
            error_log_path.write_text(content + "\n", encoding="utf-8")
            return str(error_log_path)
        except Exception:
            return ""

    def _format_generation_summary(self, payload: dict, output: Path, report_path: Path) -> str:
        stats = payload.get("stats", {})
        report = payload.get("report", {})
        summary = report.get("summary", {})
        warnings = report.get("warnings", [])
        lines = [
            f"已生成:\n{output}",
            f"\n报告:\n{report_path}",
            "",
            f"BOM分组: {stats.get('groupCount', 0)}",
            f"位号总数: {stats.get('referenceCount', 0)}",
            f"已定位位号: {stats.get('placedReferenceCount', 0)}",
            f"未定位位号: {stats.get('unplacedReferenceCount', 0)}",
            f"Top器件: {summary.get('topComponentCount', 0)} / Bottom器件: {summary.get('bottomComponentCount', 0)}",
            f"板框: {'已识别' if summary.get('hasBoardOutline') else '未识别'}",
        ]
        if warnings:
            lines.extend(["", "警告:"])
            lines.extend([f"- {item}" for item in warnings[:5]])
        return "\n".join(lines)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    IbomLauncher().run()


if __name__ == "__main__":
    main()
