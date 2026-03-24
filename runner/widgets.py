import logging
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from typing import Optional

from runner.config import Config
from runner.script_runner import ScriptRunner


_TAB_BG = Config.BG_MID
_TAB_FG = Config.FG_PRIMARY
_TAB_SELECTED_BG = "#2a7a7a"
_TAB_SELECTED_FG = "#ffffff"
_TAB_HOVER_BG = Config.BG_HOVER
_ARROW_BG = Config.BG_DARK
_ARROW_FG = Config.FG_SECONDARY
_ARROW_HOVER_FG = Config.FG_PRIMARY


def apply_dark_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("default")
    style.configure("TFrame", background=Config.BG_MID)
    style.configure("Dark.TSeparator", background=Config.BORDER_COLOR)


class ScrollableNotebook(tk.Frame):

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, bg=Config.BG_DARK, **kwargs)

        self._tab_buttons: list[tk.Label] = []
        self._tab_frames: list[tk.Widget] = []
        self._tab_texts: list[str] = []
        self._selected_index: int = -1
        self._arrows_visible = False

        self._tab_bar = tk.Frame(self, bg=Config.BG_DARK)
        self._tab_bar.pack(fill="x")

        self._left_arrow = tk.Label(
            self._tab_bar, text="\u25C0", font=("Arial", 12, "bold"),
            bg=_ARROW_BG, fg=_ARROW_FG, padx=6, pady=4, cursor="hand2"
        )
        self._left_arrow.bind("<Button-1>", lambda _: self._scroll_left())
        self._left_arrow.bind("<Enter>", lambda _: self._left_arrow.config(fg=_ARROW_HOVER_FG))
        self._left_arrow.bind("<Leave>", lambda _: self._left_arrow.config(fg=_ARROW_FG))

        self._right_arrow = tk.Label(
            self._tab_bar, text="\u25B6", font=("Arial", 12, "bold"),
            bg=_ARROW_BG, fg=_ARROW_FG, padx=6, pady=4, cursor="hand2"
        )
        self._right_arrow.bind("<Button-1>", lambda _: self._scroll_right())
        self._right_arrow.bind("<Enter>", lambda _: self._right_arrow.config(fg=_ARROW_HOVER_FG))
        self._right_arrow.bind("<Leave>", lambda _: self._right_arrow.config(fg=_ARROW_FG))

        self._canvas = tk.Canvas(
            self._tab_bar, bg=Config.BG_DARK, highlightthickness=0, height=34
        )
        self._canvas.pack(side="left", fill="x", expand=True)

        self._inner = tk.Frame(self._canvas, bg=Config.BG_DARK)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", self._on_inner_resize)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        self._content = tk.Frame(self, bg=Config.BG_MID)
        self._content.pack(fill="both", expand=True)

    def add(self, frame: tk.Widget, text: str = "") -> None:
        index = len(self._tab_buttons)

        btn = tk.Label(
            self._inner, text=text,
            font=Config.DEFAULT_FONT,
            bg=_TAB_BG, fg=_TAB_FG,
            padx=14, pady=6, cursor="hand2",
        )
        btn.pack(side="left", padx=(0, 1))
        btn.bind("<Button-1>", lambda e, i=index: self.select(i))
        btn.bind("<Enter>", lambda e, i=index: self._on_hover(i))
        btn.bind("<Leave>", lambda e, i=index: self._on_unhover(i))

        self._tab_buttons.append(btn)
        self._tab_texts.append(text)
        self._tab_frames.append(frame)

        frame.grid(row=0, column=0, sticky="nsew", in_=self._content)
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        if self._selected_index == -1:
            self.select(0)

    def tab(self, index: int, text: str = None, **kwargs) -> None:
        if text is not None and 0 <= index < len(self._tab_buttons):
            self._tab_texts[index] = text
            self._tab_buttons[index].config(text=text)
            self._update_arrows()

    def select(self, index: int) -> None:
        if index < 0 or index >= len(self._tab_buttons):
            return
        if 0 <= self._selected_index < len(self._tab_buttons):
            self._tab_buttons[self._selected_index].config(bg=_TAB_BG, fg=_TAB_FG)
        self._selected_index = index
        self._tab_buttons[index].config(bg=_TAB_SELECTED_BG, fg=_TAB_SELECTED_FG)
        self._tab_frames[index].tkraise()
        self._ensure_tab_visible(index)

    def _scroll_left(self) -> None:
        self._canvas.xview_scroll(-1, "units")
        self._update_arrows()

    def _scroll_right(self) -> None:
        self._canvas.xview_scroll(1, "units")
        self._update_arrows()

    def _ensure_tab_visible(self, index: int) -> None:
        if index < 0 or index >= len(self._tab_buttons):
            return
        btn = self._tab_buttons[index]
        self._inner.update_idletasks()

        btn_left = btn.winfo_x()
        btn_right = btn_left + btn.winfo_width()
        canvas_w = self._canvas.winfo_width()
        total_w = self._inner.winfo_reqwidth()

        if total_w <= canvas_w:
            self._update_arrows()
            return

        xview = self._canvas.xview()
        vis_left = xview[0] * total_w
        vis_right = xview[1] * total_w

        if btn_left < vis_left:
            self._canvas.xview_moveto(btn_left / total_w)
        elif btn_right > vis_right:
            self._canvas.xview_moveto((btn_right - canvas_w) / total_w)

        self._update_arrows()

    def _on_inner_resize(self, _event=None) -> None:
        self._canvas.config(scrollregion=self._canvas.bbox("all"))
        self._update_arrows()

    def _on_canvas_resize(self, _event=None) -> None:
        self._update_arrows()

    def _update_arrows(self) -> None:
        total_w = self._inner.winfo_reqwidth()
        canvas_w = self._canvas.winfo_width()
        need = total_w > canvas_w

        if need == self._arrows_visible:
            return

        if not need:
            self._left_arrow.pack_forget()
            self._right_arrow.pack_forget()
            self._canvas.pack(side="left", fill="x", expand=True)
            self._arrows_visible = False
        else:
            self._left_arrow.pack_forget()
            self._canvas.pack_forget()
            self._right_arrow.pack_forget()
            self._left_arrow.pack(side="left", fill="y")
            self._canvas.pack(side="left", fill="x", expand=True)
            self._right_arrow.pack(side="right", fill="y")
            self._arrows_visible = True

    def _on_hover(self, index: int) -> None:
        if index != self._selected_index:
            self._tab_buttons[index].config(bg=_TAB_HOVER_BG)

    def _on_unhover(self, index: int) -> None:
        if index != self._selected_index:
            self._tab_buttons[index].config(bg=_TAB_BG)


class Console(scrolledtext.ScrolledText):

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        defaults = {
            'wrap': tk.WORD,
            'state': tk.DISABLED,
            'bg': Config.CONSOLE_BG,
            'fg': Config.CONSOLE_FG,
            'insertbackground': Config.CONSOLE_FG,
            'selectbackground': Config.ACCENT_BLUE,
            'selectforeground': "#ffffff",
            'font': Config.CONSOLE_FONT,
            'height': Config.CONSOLE_HEIGHT,
            'width': Config.CONSOLE_WIDTH,
            'relief': 'flat',
            'borderwidth': 1,
            'highlightbackground': Config.BORDER_COLOR,
            'highlightthickness': 1,
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)
        self._init_menu()

    def append(self, text: str) -> None:
        self.config(state=tk.NORMAL)
        self.insert(tk.END, text)
        self.config(state=tk.DISABLED)
        self.see(tk.END)

    def clear(self) -> None:
        self.config(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.config(state=tk.DISABLED)

    def _init_menu(self) -> None:
        self._ctx_menu = tk.Menu(self, tearoff=0,
                                 bg=Config.BG_MID, fg=Config.FG_PRIMARY,
                                 activebackground=Config.ACCENT_BLUE,
                                 activeforeground="#ffffff")
        self._ctx_menu.add_command(label="Copy", command=self._copy)
        self._ctx_menu.add_command(label="Select All", command=self._select_all)
        self.bind("<Button-2>", self._on_right_click)
        self.bind("<Button-3>", self._on_right_click)

    def _on_right_click(self, event) -> None:
        try:
            self._ctx_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._ctx_menu.grab_release()

    def _copy(self) -> None:
        try:
            text = self.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(text)
        except tk.TclError:
            pass

    def _select_all(self) -> None:
        self.tag_add(tk.SEL, "1.0", tk.END)
        self.mark_set(tk.INSERT, "1.0")
        self.see(tk.INSERT)


class StatusLabel(tk.Label):

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        defaults = {
            'text': 'Idle.',
            'bg': Config.BG_MID,
            'fg': Config.FG_PRIMARY,
            'font': Config.DEFAULT_FONT,
            'padx': 1,
            'pady': 10,
            'anchor': 'w',
            'relief': 'flat',
            'bd': 0,
            'highlightbackground': Config.BORDER_COLOR,
            'highlightthickness': 1,
        }
        defaults.update(kwargs)
        super().__init__(parent, **defaults)

    def set_text(self, text: str) -> None:
        self.config(text=text)


class AppMenu:

    def __init__(self, root: tk.Tk, on_about, logger: logging.Logger) -> None:
        self._root = root
        self._on_about = on_about
        self._logger = logger
        self._build()

    def _build(self) -> None:
        menubar = tk.Menu(self._root, bg=Config.BG_MID, fg=Config.FG_PRIMARY,
                          activebackground=Config.ACCENT_BLUE, activeforeground="#ffffff")
        self._root.config(menu=menubar)
        app_menu = tk.Menu(menubar, tearoff=0,
                           bg=Config.BG_MID, fg=Config.FG_PRIMARY,
                           activebackground=Config.ACCENT_BLUE, activeforeground="#ffffff")
        menubar.add_cascade(label=Config.APP_NAME, menu=app_menu)
        app_menu.add_command(label="About", command=self._on_about)


class TabData:

    STATUS_IDLE = "idle"
    STATUS_RUNNING = "running"
    STATUS_COMPLETE = "complete"
    STATUS_ERROR = "error"
    STATUS_STOPPED = "stopped"

    def __init__(self, manifest: dict, frame: tk.Frame,
                 console: Console, status_label: StatusLabel,
                 run_btn: tk.Button, stop_btn: tk.Button) -> None:
        self.manifest = manifest
        self.frame = frame
        self.console = console
        self.status_label = status_label
        self.run_btn = run_btn
        self.stop_btn = stop_btn
        self.runner: Optional[ScriptRunner] = None
        self.base_tab_name: str = manifest.get("tab_name", "Script")
        self.status: str = self.STATUS_IDLE
        self.timer_id: Optional[str] = None
        self.start_time: Optional[float] = None
