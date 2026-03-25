import json
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

from runner.config import Config


class ScriptManagerWindow(tk.Toplevel):

    def __init__(self, parent, project_root, refresh_callback, logger):
        super().__init__(parent)
        self.project_root = project_root
        self.refresh_callback = refresh_callback
        self.logger = logger
        self._editing_path = None

        self.title("Script Manager")
        self.geometry(f"{Config.MANAGE_WINDOW_WIDTH}x{Config.MANAGE_WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.config(bg=Config.BG_DARK)
        self.transient(parent)

        self._saved_snapshot = None
        self._dragging = False
        self._drag_start_index = None
        self._toast_label = None
        self._toast_timer = None
        self._needs_refresh = False

        self._build_ui()
        self._refresh_list()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda _: self._on_close())

    def _build_ui(self):
        tk.Label(
            self, text="Script Manager",
            font=Config.HEADER_FONT, fg=Config.ACCENT_BLUE, bg=Config.BG_DARK,
        ).pack(pady=(10, 6))

        content = tk.Frame(self, bg=Config.BG_DARK)
        content.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self._build_list_panel(content)
        self._build_form_panel(content)

        tk.Button(
            self, text="Save", font=Config.BUTTON_FONT,
            fg="#000000", bg=Config.ACCENT_GREEN, bd=0,
            activebackground="#66bb6a", cursor="hand2",
            height=2, command=self._on_save,
        ).pack(fill="x", padx=12, pady=(0, 12))

    def _build_list_panel(self, parent):
        left = tk.Frame(parent, bg=Config.BG_DARK)
        left.pack(side="left", fill="y", padx=(0, 8))

        self._listbox = tk.Listbox(
            left, width=22, bg=Config.CONSOLE_BG, fg=Config.FG_PRIMARY,
            selectbackground=Config.ACCENT_BLUE, selectforeground="#000000",
            font=Config.DEFAULT_FONT, bd=0, highlightthickness=1,
            highlightcolor=Config.BORDER_COLOR, highlightbackground=Config.BORDER_COLOR,
        )
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        self._listbox.bind("<Button-1>", self._on_drag_start)
        self._listbox.bind("<B1-Motion>", self._on_drag_motion)
        self._listbox.bind("<ButtonRelease-1>", self._on_drag_end)

        btn_row = tk.Frame(left, bg=Config.BG_DARK)
        btn_row.pack(fill="x", pady=(6, 0))
        tk.Button(
            btn_row, text="New", font=("Arial", 10, "bold"),
            fg="#000000", bg=Config.ACCENT_BLUE, bd=0, cursor="hand2",
            command=self._on_new,
        ).pack(side="left", expand=True, fill="x", padx=(0, 3))
        tk.Button(
            btn_row, text="Delete", font=("Arial", 10, "bold"),
            fg="#000000", bg=Config.ACCENT_RED, bd=0, cursor="hand2",
            command=self._on_delete,
        ).pack(side="left", expand=True, fill="x", padx=(3, 0))

    def _build_form_panel(self, parent):
        right = tk.Frame(parent, bg=Config.BG_DARK)
        right.pack(side="left", fill="both", expand=True)
        self._build_form_fields(right)
        self._build_form_controls(right)

    def _build_form_fields(self, parent):
        self._entries = {}
        fields = [
            ("tab_name", "Tab Name *"),
            ("script_name", "Script Name"),
            ("script_file", "Script File *"),
            ("description", "Description"),
            ("args", "Args (comma-sep)"),
        ]
        for key, label_text in fields:
            row = tk.Frame(parent, bg=Config.BG_DARK)
            row.pack(fill="x", pady=3)
            tk.Label(
                row, text=label_text, font=("Arial", 10),
                fg=Config.FG_SECONDARY, bg=Config.BG_DARK, width=16, anchor="w",
            ).pack(side="left")
            entry = tk.Entry(
                row, font=Config.DEFAULT_FONT,
                bg=Config.CONSOLE_BG, fg=Config.FG_PRIMARY,
                insertbackground=Config.FG_PRIMARY, bd=0,
                highlightthickness=1, highlightcolor=Config.BORDER_COLOR,
                highlightbackground=Config.BORDER_COLOR,
            )
            entry.pack(side="left", fill="x", expand=True)
            self._entries[key] = entry
            if key == "script_file":
                tk.Button(
                    row, text="\U0001F4C1", font=("Arial", 10),
                    fg="#000000", bg=Config.BG_MID, bd=0, cursor="hand2",
                    command=self._browse_script,
                ).pack(side="left", padx=(4, 0))

    def _build_form_controls(self, parent):
        row = tk.Frame(parent, bg=Config.BG_DARK)
        row.pack(fill="x", pady=3)
        tk.Label(row, text="Enabled", font=("Arial", 10),
                 fg=Config.FG_SECONDARY, bg=Config.BG_DARK, width=16, anchor="w").pack(side="left")
        self._enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(row, variable=self._enabled_var,
                       bg=Config.BG_DARK, activebackground=Config.BG_DARK,
                       selectcolor=Config.CONSOLE_BG).pack(side="left")

        row = tk.Frame(parent, bg=Config.BG_DARK)
        row.pack(fill="x", pady=3)
        tk.Label(row, text="Logging", font=("Arial", 10),
                 fg=Config.FG_SECONDARY, bg=Config.BG_DARK, width=16, anchor="w").pack(side="left")
        self._logging_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row, variable=self._logging_var,
                       bg=Config.BG_DARK, activebackground=Config.BG_DARK,
                       selectcolor=Config.CONSOLE_BG).pack(side="left")

        row = tk.Frame(parent, bg=Config.BG_DARK)
        row.pack(fill="x", pady=3)
        tk.Label(row, text="Order", font=("Arial", 10),
                 fg=Config.FG_SECONDARY, bg=Config.BG_DARK, width=16, anchor="w").pack(side="left")
        self._order_var = tk.IntVar(value=99)
        tk.Spinbox(
            row, from_=1, to=999, textvariable=self._order_var, width=5,
            font=Config.DEFAULT_FONT, bg=Config.CONSOLE_BG, fg=Config.FG_PRIMARY,
            buttonbackground=Config.BG_MID, bd=0,
            highlightthickness=1, highlightcolor=Config.BORDER_COLOR,
            highlightbackground=Config.BORDER_COLOR,
        ).pack(side="left")

    def _manifest_dir(self):
        return os.path.join(self.project_root, Config.MANIFESTS_DIR)

    def _refresh_list(self):
        self._listbox.delete(0, tk.END)
        self._manifest_paths = []
        manifest_dir = self._manifest_dir()
        if not os.path.isdir(manifest_dir):
            return
        items = []
        for fname in os.listdir(manifest_dir):
            if fname.endswith(Config.MANIFEST_EXTENSION):
                path = os.path.join(manifest_dir, fname)
                try:
                    with open(path) as f:
                        data = json.load(f)
                    items.append((path, data))
                except Exception as e:
                    self.logger.warning(f"Failed to load manifest {fname}: {e}")
        items.sort(key=lambda item: item[1].get("order", 999))
        for path, data in items:
            self._listbox.insert(tk.END, data.get("tab_name", os.path.basename(path)))
            self._manifest_paths.append(path)

    def _on_select(self, _event=None):
        if self._dragging:
            return
        sel = self._listbox.curselection()
        if not sel:
            return
        if not self._confirm_discard():
            return
        path = self._manifest_paths[sel[0]]
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            return
        self._editing_path = path
        self._populate_form(data)

    def _populate_form(self, data):
        for key, entry in self._entries.items():
            entry.delete(0, tk.END)
            value = data.get(key, "")
            if key == "args" and isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            entry.insert(0, str(value))
        self._enabled_var.set(data.get("enabled", True))
        self._logging_var.set(data.get("logging", False))
        self._order_var.set(data.get("order", 99))
        self._take_snapshot()

    def _on_drag_start(self, event):
        index = self._listbox.nearest(event.y)
        if index < 0:
            return
        self._drag_start_index = index
        self._dragging = False

    def _on_drag_motion(self, event):
        if self._drag_start_index is None:
            return
        target = self._listbox.nearest(event.y)
        if target < 0 or target == self._drag_start_index:
            return
        if target > self._drag_start_index:
            target = self._drag_start_index + 1
        else:
            target = self._drag_start_index - 1
        self._dragging = True
        src = self._drag_start_index
        src_text = self._listbox.get(src)
        tgt_text = self._listbox.get(target)
        self._listbox.delete(src)
        self._listbox.insert(src, tgt_text)
        self._listbox.delete(target)
        self._listbox.insert(target, src_text)
        self._manifest_paths[src], self._manifest_paths[target] = (
            self._manifest_paths[target], self._manifest_paths[src]
        )
        self._drag_start_index = target
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(target)

    def _on_drag_end(self, _event):
        was_dragging = self._dragging
        self._dragging = False
        self._drag_start_index = None
        if not was_dragging:
            return
        save_failed = False
        for i, path in enumerate(self._manifest_paths):
            try:
                with open(path) as f:
                    data = json.load(f)
                data["order"] = i + 1
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
                    f.write("\n")
            except Exception as e:
                self.logger.error(f"Failed to update order for {path}: {e}")
                messagebox.showerror("Error", f"Failed to update order: {e}", parent=self)
                save_failed = True
                break
        if save_failed:
            self._refresh_list()
            self._needs_refresh = True
            return
        if self._editing_path and self._editing_path in self._manifest_paths:
            new_order = self._manifest_paths.index(self._editing_path) + 1
            self._order_var.set(new_order)
        self._needs_refresh = True

    def _form_snapshot(self):
        return (
            tuple((k, e.get()) for k, e in self._entries.items()),
            self._enabled_var.get(),
            self._logging_var.get(),
            self._order_var.get(),
        )

    def _is_dirty(self):
        return self._saved_snapshot is not None and self._form_snapshot() != self._saved_snapshot

    def _confirm_discard(self):
        if not self._is_dirty():
            return True
        return messagebox.askyesno(
            "Unsaved Changes",
            "You have unsaved changes. Discard them?",
            parent=self,
        )

    def _take_snapshot(self):
        self._saved_snapshot = self._form_snapshot()

    def _on_close(self):
        if not self._confirm_discard():
            return
        needs_refresh = self._needs_refresh
        parent = self.master
        callback = self.refresh_callback
        self.destroy()
        parent.lift()
        parent.focus_force()
        if needs_refresh:
            parent.after(0, callback)

    def _show_toast(self, message="Saved!"):
        if self._toast_timer:
            self.after_cancel(self._toast_timer)
            self._toast_timer = None
        if self._toast_label:
            self._toast_label.destroy()
            self._toast_label = None
        self._toast_label = tk.Label(
            self, text=message,
            font=("Arial", 14, "bold"),
            fg=Config.ACCENT_GREEN, bg=Config.BG_MID,
            padx=20, pady=10,
            relief="solid", bd=1,
            highlightbackground=Config.ACCENT_GREEN, highlightthickness=1,
        )
        self._toast_label.place(relx=0.5, rely=0.0, anchor="n", x=0, y=8)
        self._toast_timer = self.after(1500, self._dismiss_toast)

    def _dismiss_toast(self):
        self._toast_timer = None
        if self._toast_label:
            self._toast_label.destroy()
            self._toast_label = None

    def _on_new(self):
        if not self._confirm_discard():
            return
        self._editing_path = None
        for entry in self._entries.values():
            entry.delete(0, tk.END)
        self._enabled_var.set(True)
        self._logging_var.set(False)
        self._order_var.set(99)
        self._listbox.selection_clear(0, tk.END)
        self._take_snapshot()

    def _on_delete(self):
        sel = self._listbox.curselection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a manifest to delete.", parent=self)
            return
        path = self._manifest_paths[sel[0]]
        name = self._listbox.get(sel[0])
        if not messagebox.askyesno("Confirm Delete", f"Delete manifest \"{name}\"?", parent=self):
            return
        try:
            os.remove(path)
            self.logger.info(f"Deleted manifest: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}", parent=self)
            return
        self._editing_path = None
        self._on_new()
        self._refresh_list()
        self._needs_refresh = True

    def _on_save(self):
        tab_name = self._entries["tab_name"].get().strip()
        script_file = self._entries["script_file"].get().strip()
        if not tab_name or not script_file:
            messagebox.showwarning("Missing Fields", "Tab Name and Script File are required.", parent=self)
            return
        if not self._validate_script_path(script_file):
            return

        data = self._collect_form_data(tab_name, script_file)
        save_path = self._resolve_save_path(tab_name)

        os.makedirs(self._manifest_dir(), exist_ok=True)
        try:
            with open(save_path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            self.logger.info(f"Saved manifest: {save_path}")
            self._show_toast()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}", parent=self)
            return

        self._editing_path = save_path
        self._take_snapshot()
        self._refresh_list()
        self._needs_refresh = True

    def _validate_script_path(self, script_file: str) -> bool:
        resolved = script_file if os.path.isabs(script_file) else os.path.join(self.project_root, script_file)
        if not os.path.isfile(resolved):
            messagebox.showwarning("Script Not Found", f"Script file not found:\n{script_file}", parent=self)
            return False
        return True

    def _collect_form_data(self, tab_name: str, script_file: str) -> dict:
        args_raw = self._entries["args"].get().strip()
        args_list = [a.strip() for a in args_raw.split(",") if a.strip()] if args_raw else []
        data = {
            "tab_name": tab_name,
            "script_name": self._entries["script_name"].get().strip() or tab_name,
            "script_file": script_file,
            "description": self._entries["description"].get().strip(),
            "enabled": self._enabled_var.get(),
            "logging": self._logging_var.get(),
            "order": self._order_var.get(),
        }
        if args_list:
            data["args"] = args_list
        return data

    def _resolve_save_path(self, tab_name: str) -> str:
        if self._editing_path and os.path.exists(self._editing_path):
            return self._editing_path
        slug = re.sub(r"[^a-z0-9]+", "_", tab_name.lower()).strip("_")
        return os.path.join(self._manifest_dir(), f"{slug}{Config.MANIFEST_EXTENSION}")

    def _browse_script(self):
        path = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
            initialdir=os.path.join(self.project_root, Config.SCRIPTS_DIR),
            parent=self,
        )
        if not path:
            return
        rel = os.path.relpath(path, self.project_root)
        entry = self._entries["script_file"]
        entry.delete(0, tk.END)
        entry.insert(0, rel)
