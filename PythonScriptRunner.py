#!/usr/bin/env python3
"""
Python Script Runner - GUI for running Python scripts

"""

import json
import logging
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from runner.config import Config, about_text
from runner.script_manager import ScriptManagerWindow
from runner.script_runner import ScriptRunner
from runner.venv_manager import setup_venv, venv_python_path
from runner.widgets import (
    Console, StatusLabel, AppMenu, TabData,
    ScrollableNotebook, apply_dark_theme,
)



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


class App:

    def __init__(self):
        self.root = tk.Tk()
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.tabs: list = []

        self._init_ui()
        self._init_venv()

    def _init_ui(self) -> None:
        self._init_window()
        apply_dark_theme(self.root)
        self._build_header()
        self._build_tabs()
        self._build_footer()
        self._build_menu()
        log.info(f"{Config.APP_NAME} v{Config.APP_VERSION} ready")

    def _init_window(self) -> None:
        self.root.title(Config.APP_NAME)
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.config(bg=Config.BG_DARK)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Command-r>", lambda _: self._on_run_shortcut())
        self.root.bind("<Control-r>", lambda _: self._on_run_shortcut())
        self.root.bind("<Command-w>", lambda _: self._on_stop_shortcut())
        self.root.bind("<Control-w>", lambda _: self._on_stop_shortcut())
        self.root.bind("<Escape>", lambda _: self._on_close())

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=Config.BG_DARK)
        header.pack(fill="x", pady=(10, 0))

        left = tk.Frame(header, bg=Config.BG_DARK)
        left.pack(side="left", padx=(10, 0))

        self.header_label = tk.Label(
            left, text=Config.APP_NAME,
            font=Config.HEADER_FONT, fg=Config.ACCENT_BLUE,
            bg=Config.BG_DARK, anchor="w",
        )
        self.header_label.pack(anchor="w")

        tk.Label(
            left, text=Config.APP_DESCRIPTION,
            font=Config.STATUS_BAR_FONT, fg=Config.FG_SECONDARY,
            bg=Config.BG_DARK, anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        right = tk.Frame(header, bg=Config.BG_DARK)
        right.pack(side="right", padx=(0, 10))

        self._manage_btn = tk.Button(
            right, text="\u2699  Manage",
            font=Config.BUTTON_FONT, fg="#000000",
            bg=Config.ACCENT_BLUE, activebackground="#6ab4ff",
            activeforeground="#000000", bd=0, cursor="hand2",
            command=self._show_manager,
        )
        self._manage_btn.pack(pady=(4, 4))

        ttk.Separator(self.root, orient="horizontal", style="Dark.TSeparator").pack(fill="x", padx=10)

    def _build_tabs(self) -> None:
        self.notebook = ScrollableNotebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(6, 0))

        manifests = self._scan_manifests()
        if not manifests:
            frame = tk.Frame(self.notebook, bg=Config.BG_MID)
            self.notebook.add(frame, text="No Scripts")
            tk.Label(
                frame, text="No manifest files found in the scripts folder.",
                bg=Config.BG_MID, fg=Config.FG_SECONDARY, font=Config.DEFAULT_FONT
            ).pack(expand=True)
            return

        for m in manifests:
            self.tabs.append(self._build_tab(m))

        self.notebook.select(0)

    def _build_tab(self, manifest: dict) -> TabData:
        frame = tk.Frame(self.notebook, bg=Config.BG_MID)
        tab_name = manifest.get("tab_name", "Script")
        if manifest.get("_warning"):
            tab_name = f"{Config.TAB_INDICATOR_WARNING} {tab_name}"
        self.notebook.add(frame, text=tab_name)

        console = Console(frame)
        status = StatusLabel(frame)
        separator = ttk.Separator(frame, orient="horizontal", style="Dark.TSeparator")
        run_btn, stop_btn = self._make_run_stop_btns(frame)

        td = TabData(manifest, frame, console, status, run_btn, stop_btn)
        run_btn.config(command=lambda t=td: self._on_run(t))
        stop_btn.config(command=lambda t=td: self._on_stop(t))

        clear_btn = tk.Button(
            frame, text="\u2715  Clear Console",
            font=("Arial", 10),
            fg="#000000", bg=Config.BG_MID,
            activebackground=Config.BG_HOVER, activeforeground=Config.FG_PRIMARY,
            bd=0, cursor="hand2",
            command=lambda c=console: (c.clear(), c.append("(console screen cleared -- check logs if previous text needed)\n")),
        )

        console.pack(fill="both", expand=True, padx=12, pady=(8, 4))
        clear_btn.pack(anchor="e", padx=12, pady=(0, 2))
        separator.pack(fill="x", padx=12, pady=(2, 4))
        status.pack(fill="x", padx=12, pady=(0, 4))
        run_btn.pack(fill="x", padx=12, pady=(0, 2))
        stop_btn.pack(fill="x", padx=12, pady=(0, 8))

        script_name = manifest.get("script_name", "Script")
        console.append(f'Press "Run" to begin {script_name}.\n')
        desc = manifest.get("description", "")
        if desc:
            console.append(f"{desc}\n")

        return td

    def _make_run_stop_btns(self, frame: tk.Frame):
        run_btn = tk.Button(
            frame, text="\u25B6  Run",
            font=Config.BUTTON_FONT, fg="#000000",
            bg=Config.ACCENT_GREEN, activebackground="#66bb6a",
            activeforeground="#000000", bd=0,
            height=Config.BUTTON_HEIGHT, cursor="hand2",
        )
        stop_btn = tk.Button(
            frame, text="\u25A0  Stop",
            font=Config.BUTTON_FONT,
            fg=Config.BUTTON_DISABLED_FG, bg=Config.BUTTON_DISABLED_BG,
            activebackground=Config.BUTTON_DISABLED_BG,
            activeforeground=Config.BUTTON_DISABLED_FG,
            bd=0, height=Config.BUTTON_HEIGHT,
            cursor="X_cursor", state=tk.DISABLED,
        )
        return run_btn, stop_btn

    def _build_footer(self) -> None:
        self._footer = tk.Frame(self.root, bg=Config.BG_DARK, height=24)
        self._footer.pack(fill="x", side="bottom", padx=10, pady=(0, 4))

        n = len(self.tabs)
        tk.Label(
            self._footer, text=f"v{Config.APP_VERSION}",
            font=Config.STATUS_BAR_FONT, fg=Config.FG_SECONDARY, bg=Config.BG_DARK
        ).pack(side="left")
        tk.Label(
            self._footer, text=f"{n} script{'s' if n != 1 else ''} loaded",
            font=Config.STATUS_BAR_FONT, fg=Config.FG_SECONDARY, bg=Config.BG_DARK
        ).pack(side="right")

    def _build_menu(self) -> None:
        self._menu = AppMenu(self.root, self._show_about, log)

    def _scan_manifests(self) -> list:
        manifests_dir = os.path.join(self.project_root, Config.MANIFESTS_DIR)
        os.makedirs(manifests_dir, exist_ok=True)
        manifests = []
        for fname in sorted(os.listdir(manifests_dir)):
            if not fname.endswith(Config.MANIFEST_EXTENSION):
                continue
            path = os.path.join(manifests_dir, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
                if not data.get("enabled", True):
                    log.info(f"Skipped disabled manifest: {fname}")
                    continue
                missing = [f for f in Config.MANIFEST_REQUIRED_FIELDS if f not in data]
                if missing:
                    log.warning(f"{fname} missing fields: {missing} — skipped")
                    continue
                manifests.append(data)
                script_file = data.get("script_file", "")
                script_path = script_file if os.path.isabs(script_file) else os.path.join(self.project_root, script_file)
                if not os.path.isfile(script_path):
                    data["_warning"] = "Script file not found"
                    log.warning(f"{fname}: script not found: {script_file}")
                log.info(f"Loaded manifest: {fname}")
            except Exception as e:
                log.error(f"Failed to load {fname}: {e}")
        manifests.sort(key=lambda m: m.get("order", 999))
        return manifests

    def _init_venv(self) -> None:
        if not self.tabs:
            return
        venv_path = os.path.join(self.project_root, ".venv")
        python_bin = venv_python_path(venv_path)

        if not os.path.exists(venv_path) or not os.path.exists(python_bin):
            for td in self.tabs:
                self._toggle_buttons(td, run=False, stop=False)
            first = self.tabs[0]
            first.status_label.set_text("Setting up dependencies...")
            first.console.append(
                "First-time setup: creating virtual environment and installing dependencies.\n"
            )
            first.console.append("Please wait — this only happens once.\n\n")
            threading.Thread(target=self._setup_venv_bg, daemon=True).start()

    def _setup_venv_bg(self) -> None:
        first = self.tabs[0]

        def output(text):
            self.root.after(0, first.console.append, text)

        ok = setup_venv(self.project_root, output, log)

        def restore():
            for td in self.tabs:
                self._toggle_buttons(td, run=True, stop=False)
            first.status_label.set_text("Ready" if ok else "Setup failed — see console")

        self.root.after(0, restore)

    def _toggle_buttons(self, td: TabData, run: bool, stop: bool) -> None:
        try:
            if run:
                td.run_btn.config(
                    state=tk.NORMAL,
                    bg=Config.ACCENT_GREEN, fg="#000000",
                    activebackground="#66bb6a", activeforeground="#000000",
                    cursor="hand2"
                )
            else:
                td.run_btn.config(
                    state=tk.DISABLED,
                    bg=Config.BUTTON_DISABLED_BG, fg=Config.BUTTON_DISABLED_FG,
                    activebackground=Config.BUTTON_DISABLED_BG,
                    activeforeground=Config.BUTTON_DISABLED_FG,
                    cursor="X_cursor"
                )
            if stop:
                td.stop_btn.config(
                    state=tk.NORMAL,
                    bg=Config.ACCENT_RED, fg="#000000",
                    activebackground="#ef5350", activeforeground="#000000",
                    cursor="hand2"
                )
            else:
                td.stop_btn.config(
                    state=tk.DISABLED,
                    bg=Config.BUTTON_DISABLED_BG, fg=Config.BUTTON_DISABLED_FG,
                    activebackground=Config.BUTTON_DISABLED_BG,
                    activeforeground=Config.BUTTON_DISABLED_FG,
                    cursor="X_cursor"
                )
        except Exception as e:
            log.error(f"Button state error: {e}")

    def _set_tab_status(self, td: TabData, status: str) -> None:
        td.status = status
        icons = {
            TabData.STATUS_IDLE: "",
            TabData.STATUS_RUNNING: Config.TAB_INDICATOR_RUNNING,
            TabData.STATUS_COMPLETE: Config.TAB_INDICATOR_COMPLETE,
            TabData.STATUS_ERROR: Config.TAB_INDICATOR_ERROR,
            TabData.STATUS_STOPPED: Config.TAB_INDICATOR_STOPPED,
        }
        icon = icons.get(status, "")
        warning = td.manifest.get("_warning")
        if icon:
            label = f"{icon} {td.base_tab_name}"
        elif warning:
            label = f"{Config.TAB_INDICATOR_WARNING} {td.base_tab_name}"
        else:
            label = td.base_tab_name
        try:
            self.notebook.tab(self.tabs.index(td), text=label)
        except (ValueError, tk.TclError) as e:
            log.error(f"Tab label update error: {e}")

    def _start_timer(self, td: TabData) -> None:
        td.start_time = time.time()
        self._tick_timer(td)

    def _tick_timer(self, td: TabData) -> None:
        if td.status != TabData.STATUS_RUNNING or td.start_time is None:
            return
        elapsed = int(time.time() - td.start_time)
        m, s = divmod(elapsed, 60)
        td.status_label.set_text(f"Script running... ({f'{m}m {s}s' if m else f'{s}s'})")
        td.timer_id = self.root.after(1000, self._tick_timer, td)

    def _stop_timer(self, td: TabData) -> None:
        if td.timer_id:
            self.root.after_cancel(td.timer_id)
            td.timer_id = None
        td.start_time = None

    def _on_run(self, td: TabData) -> None:
        try:
            self._toggle_buttons(td, run=False, stop=True)
            self._set_tab_status(td, TabData.STATUS_RUNNING)
            td.console.clear()

            name = td.manifest.get("script_name", "script")
            script_file = td.manifest.get("script_file", "")
            args = td.manifest.get("args", [])
            td.console.append(f"Starting {name}...\n")
            if args:
                td.console.append(f"Args: {', '.join(str(a) for a in args)}\n")
            self._start_timer(td)

            script_path = os.path.join(self.project_root, script_file)
            venv_path = os.path.join(self.project_root, ".venv")
            if not os.path.exists(venv_path):
                td.console.append("Virtual environment not found. Setting up...\n")
                self._run_after_venv_setup(td, script_path)
                return

            self._exec_script(td, script_path)
            log.info(f"Started {name}")

        except Exception as e:
            log.error(f"Run failed: {e}")
            self._stop_timer(td)
            td.console.append(f"ERROR: {e}\n")
            td.status_label.set_text("Failed to start script")
            self._toggle_buttons(td, run=True, stop=False)
            self._set_tab_status(td, TabData.STATUS_ERROR)

    def _run_after_venv_setup(self, td: TabData, script_path: str) -> None:
        def setup_then_run():
            def output(text):
                self.root.after(0, td.console.append, text)

            ok = setup_venv(self.project_root, output, log)

            def after_setup():
                if not ok:
                    self._stop_timer(td)
                    td.status_label.set_text("Venv setup failed")
                    self._toggle_buttons(td, run=True, stop=False)
                    self._set_tab_status(td, TabData.STATUS_ERROR)
                    return
                self._exec_script(td, script_path)

            self.root.after(0, after_setup)

        threading.Thread(target=setup_then_run, daemon=True).start()

    def _exec_script(self, td: TabData, script_path: str) -> None:
        log_file = None
        if td.manifest.get("logging", False):
            logs_dir = os.path.join(self.project_root, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            script_name = td.manifest.get("script_name", "script")
            log_path = os.path.join(logs_dir, f"{script_name}.log")
            log_file = open(log_path, "a", encoding="utf-8")
            td.console.append(f"Logging output to: logs/{script_name}.log\n")

        def on_output(text):
            if log_file:
                log_file.write(text)
                log_file.flush()
            self.root.after(0, td.console.append, text)

        def on_result(text):
            self.root.after(0, td.status_label.set_text, text)

        def on_done(run_en, stop_en, t=td):
            def finish():
                if log_file:
                    log_file.close()
                if t.status != TabData.STATUS_RUNNING:
                    return
                self._stop_timer(t)
                self._toggle_buttons(t, run_en, stop_en)
                if run_en and not stop_en:
                    ok = t.runner and t.runner.process and t.runner.process.returncode == 0
                    self._set_tab_status(t, TabData.STATUS_COMPLETE if ok else TabData.STATUS_ERROR)
            self.root.after(0, finish)

        args = td.manifest.get("args", [])
        runner = ScriptRunner(self.project_root, log)
        td.runner = runner
        runner.run_script(script_path, on_output, on_result, on_done, script_args=args)

    def _on_stop(self, td: TabData) -> None:
        try:
            self._stop_timer(td)
            self._toggle_buttons(td, run=True, stop=False)
            if td.runner and td.runner.stop_script():
                td.console.append("\nScript cancelled by user.\n")
                td.status_label.set_text("Script cancelled")
                self._set_tab_status(td, TabData.STATUS_STOPPED)
                log.info("Script cancelled")
            else:
                td.console.append("No running script to cancel.\n")
                td.status_label.set_text("No script running")
        except Exception as e:
            log.error(f"Stop failed: {e}")
            td.console.append(f"ERROR: {e}\n")
            td.status_label.set_text("Cancel failed")

    def _current_tab(self) -> TabData:
        if not self.tabs:
            return None
        idx = self.notebook._selected_index
        if 0 <= idx < len(self.tabs):
            return self.tabs[idx]
        return None

    def _on_run_shortcut(self) -> None:
        td = self._current_tab()
        if td and td.status != TabData.STATUS_RUNNING:
            self._on_run(td)

    def _on_stop_shortcut(self) -> None:
        td = self._current_tab()
        if td and td.status == TabData.STATUS_RUNNING:
            self._on_stop(td)

    def _on_close(self) -> None:
        running = [td.base_tab_name for td in self.tabs if td.status == TabData.STATUS_RUNNING]
        if running:
            names = ", ".join(running)
            if not messagebox.askokcancel(
                "Scripts Running",
                f"The following scripts are still running:\n{names}\n\nClose anyway?"
            ):
                return
            for td in self.tabs:
                if td.runner:
                    td.runner.stop_script()
        self.root.destroy()

    def _show_about(self) -> None:
        messagebox.showinfo(f"About {Config.APP_NAME}", about_text())

    def _show_manager(self) -> None:
        ScriptManagerWindow(self.root, self.project_root, self._reload_tabs, log)

    def _reload_tabs(self) -> None:
        running = self._collect_running_tabs()

        self.tabs.clear()
        self.notebook.destroy()
        self._footer.destroy()
        self._build_tabs()
        self._build_footer()

        self._reattach_running_tabs(running)

        for old in running.values():
            self._stop_timer(old)
            if old.runner:
                old.runner.stop_script()

    def _collect_running_tabs(self) -> dict:
        running = {}
        for td in self.tabs:
            if td.status == TabData.STATUS_RUNNING and td.runner:
                running[td.manifest.get("script_file", "")] = td
            else:
                self._stop_timer(td)
        return running

    def _reattach_running_tabs(self, running: dict) -> None:
        for i, td in enumerate(list(self.tabs)):
            key = td.manifest.get("script_file", "")
            if key not in running:
                continue
            old = running.pop(key)
            old.frame = td.frame
            old.console = td.console
            old.status_label = td.status_label
            old.run_btn = td.run_btn
            old.stop_btn = td.stop_btn
            old.manifest = td.manifest
            old.base_tab_name = td.base_tab_name
            old.run_btn.config(command=lambda t=old: self._on_run(t))
            old.stop_btn.config(command=lambda t=old: self._on_stop(t))
            self.tabs[i] = old
            self._toggle_buttons(old, run=False, stop=True)
            self._set_tab_status(old, TabData.STATUS_RUNNING)
            old.console.append("(Script still running — tab was refreshed)\n")
            self._tick_timer(old)

    def run(self) -> None:
        log.info("Starting main loop")
        self.root.mainloop()


def main() -> None:
    try:
        App().run()
    except KeyboardInterrupt:
        log.info("Interrupted")
    except Exception as e:
        log.error(f"Fatal: {e}")
        raise


if __name__ == "__main__":
    main()
