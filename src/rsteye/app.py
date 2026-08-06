from __future__ import annotations

import logging
import os
import signal
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageSequence

APP_NAME = "RstEye"
DEFAULT_POPUP_DURATION_SECONDS = 60
DEFAULT_POPUP_INTERVAL_MINUTES = 60
MINIMUM_SECONDS = 1

tk = None
messagebox = None
ImageTk = None


def _load_gui_modules() -> None:
    global ImageTk, messagebox, tk
    if tk is not None:
        return

    import tkinter as tk_module
    from tkinter import messagebox as messagebox_module

    from PIL import ImageTk as image_tk_module

    tk = tk_module
    messagebox = messagebox_module
    ImageTk = image_tk_module


def config_file_path() -> Path:
    """Return the per-user dotenv path used by installed applications."""
    configured_path = os.getenv("RSTEYE_CONFIG_FILE")
    if configured_path:
        return Path(configured_path).expanduser()

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME / ".env"

    config_home = Path(
        os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    ).expanduser()
    return config_home / "rsteye" / ".env"


def log_file_path() -> Path:
    """Return a writable per-user log path, with an explicit override."""
    configured_path = os.getenv("RSTEYE_LOG_FILE")
    if configured_path:
        return Path(configured_path).expanduser()

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / APP_NAME / "rsteye.log"

    state_home = Path(
        os.getenv("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    ).expanduser()
    return state_home / "rsteye" / "rsteye.log"


load_dotenv(config_file_path(), override=False)
load_dotenv(override=False)


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("rsteye")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    try:
        path = log_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            path,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.addHandler(logging.NullHandler())

    if os.getenv("RSTEYE_LOG_STDERR", "").lower() in {"1", "true", "yes"}:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


logger = configure_logging()


def read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default

    try:
        parsed = int(value)
    except ValueError:
        logger.warning("Invalid integer for %s; using %d.", name, default)
        return default

    if parsed < MINIMUM_SECONDS:
        logger.warning(
            "%s must be at least %d; using %d.",
            name,
            MINIMUM_SECONDS,
            MINIMUM_SECONDS,
        )
        return MINIMUM_SECONDS
    return parsed


def resource_path(relative_path: str) -> str:
    """Resolve a bundled resource in source and PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)


class RstEyeApp:
    def __init__(
        self,
        image_path: str,
        interval_seconds: int = DEFAULT_POPUP_INTERVAL_MINUTES * 60,
        popup_duration_seconds: int = DEFAULT_POPUP_DURATION_SECONDS,
        fullscreen: bool = False,
        root: tk.Tk | None = None,
    ) -> None:
        _load_gui_modules()
        self.image_path = resource_path(image_path)
        self.interval = max(MINIMUM_SECONDS, interval_seconds)
        self.popup_duration = max(MINIMUM_SECONDS, popup_duration_seconds)
        self.fullscreen = fullscreen
        self.root = root or tk.Tk()
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self._background_image: ImageTk.PhotoImage | None = None
        self._frame_images: list[ImageTk.PhotoImage] = []
        self._frame_delays: list[int] = []
        self._popup: tk.Toplevel | None = None
        self._break_window: tk.Toplevel | None = None
        self._scheduled_prompt: str | None = None
        self._popup_active = False
        self._closing = False
        self._ready = Path(self.image_path).is_file()
        self._previous_sigint = None

        logger.info(
            "Initialized %s with image path %s, interval %d seconds, duration %d seconds.",
            APP_NAME,
            self.image_path,
            self.interval,
            self.popup_duration,
        )

        if not self._ready:
            logger.error("Image file not found: %s", self.image_path)
            self._show_error(f"Image file not found:\n{self.image_path}")
            self.shutdown()

    def _show_error(self, message: str) -> None:
        if self._closing:
            return
        try:
            messagebox.showerror(APP_NAME, message, parent=self.root)
        except tk.TclError:
            logger.error(message)

    @staticmethod
    def _destroy_window(window: tk.Toplevel | None) -> None:
        if window is None:
            return
        try:
            if window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass

    def _root_exists(self) -> bool:
        try:
            return bool(self.root.winfo_exists())
        except tk.TclError:
            return False

    def _schedule_next_prompt(self) -> None:
        self._popup_active = False
        self._scheduled_prompt = None
        if self._closing or not self._root_exists():
            return

        logger.info("Waiting %d seconds before the next reminder.", self.interval)
        self._scheduled_prompt = self.root.after(
            self.interval * 1000,
            self.show_image,
        )

    def _install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            return
        self._previous_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_sigint)

    def _restore_signal_handlers(self) -> None:
        if self._previous_sigint is None:
            return
        try:
            signal.signal(signal.SIGINT, self._previous_sigint)
        except ValueError:
            pass
        self._previous_sigint = None

    def _handle_sigint(self, _signum: int, _frame: object) -> None:
        logger.info("Interrupt received; shutting down.")
        if self._root_exists():
            self.root.after(0, self.shutdown)

    @staticmethod
    def _set_topmost(window: tk.Toplevel, enabled: bool) -> None:
        try:
            window.attributes("-topmost", enabled)
        except tk.TclError:
            logger.debug("Display server does not support the topmost attribute.")

    def show_image(self) -> None:
        if self._closing or self._popup_active or not self._root_exists():
            return

        self._popup_active = True
        popup: tk.Toplevel | None = None
        accepted = False

        try:
            popup = tk.Toplevel(self.root)
            self._popup = popup
            popup.title("RstEye reminder")
            popup.resizable(False, False)
            self._set_topmost(popup, True)
            popup.transient(self.root)

            popup_width, popup_height = 350, 220
            screen_width = popup.winfo_screenwidth()
            screen_height = popup.winfo_screenheight()
            x = int((screen_width - popup_width) / 2)
            y = int((screen_height - popup_height) / 2)
            popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

            background_path = resource_path("resources/rsteye.png")
            if Path(background_path).is_file():
                with Image.open(background_path) as background:
                    resized_background = background.convert("RGB").resize(
                        (popup_width, popup_height)
                    )
                self._background_image = ImageTk.PhotoImage(
                    resized_background,
                    master=popup,
                )
                tk.Label(popup, image=self._background_image).place(
                    relwidth=1,
                    relheight=1,
                )

            tk.Label(
                popup,
                text=(
                    "Time for an eye break.\n"
                    f"The breathing exercise will run for {self.popup_duration} seconds."
                ),
                font=("Helvetica", 12, "bold"),
                wraplength=300,
                justify="center",
            ).pack(pady=(22, 12))

            button_frame = tk.Frame(popup)
            button_frame.pack(pady=8)

            def close_reminder(schedule: bool = True) -> None:
                self._destroy_window(popup)
                self._popup = None
                if schedule:
                    self._schedule_next_prompt()

            def load_image() -> None:
                nonlocal accepted
                if accepted or self._closing:
                    return
                accepted = True
                logger.info("User accepted the break reminder.")
                try:
                    window = tk.Toplevel(self.root)
                    self._break_window = window
                    window.withdraw()
                    window.title("RstEye breathing break")
                    window.configure(bg="black")
                    if self.fullscreen:
                        window.attributes("-fullscreen", True)

                    screen_width = window.winfo_screenwidth()
                    screen_height = window.winfo_screenheight()
                    frames: list[ImageTk.PhotoImage] = []
                    delays: list[int] = []
                    with Image.open(self.image_path) as image:
                        canvas = Image.new("RGBA", image.size)
                        for frame in ImageSequence.Iterator(image):
                            composed = canvas.copy()
                            composed.alpha_composite(frame.convert("RGBA"))
                            resized = composed.resize(
                                (screen_width, screen_height),
                                Image.Resampling.LANCZOS,
                            )
                            frames.append(ImageTk.PhotoImage(resized, master=window))
                            delays.append(max(20, int(frame.info.get("duration", 50))))
                            canvas = composed

                    if not frames:
                        raise OSError("The breathing animation has no frames.")

                    self._frame_images = frames
                    self._frame_delays = delays
                    label = tk.Label(window, bg="black")
                    label.pack(fill="both", expand=True)
                    label.configure(image=frames[0])
                    label.image = frames[0]
                    break_finished = False

                    def finish_break() -> None:
                        nonlocal break_finished
                        if break_finished:
                            return
                        break_finished = True
                        logger.info("Breathing break finished.")
                        self._destroy_window(window)
                        self._break_window = None
                        self._frame_images = []
                        self._frame_delays = []
                        self._schedule_next_prompt()

                    def update_frame(frame_index: int) -> None:
                        if break_finished or not window.winfo_exists():
                            return
                        current_frame = frames[frame_index]
                        label.configure(image=current_frame)
                        label.image = current_frame
                        window.after(
                            delays[frame_index],
                            update_frame,
                            (frame_index + 1) % len(frames),
                        )

                    window.protocol("WM_DELETE_WINDOW", finish_break)
                    window.bind("<Escape>", lambda _event: finish_break())
                    window.bind("<Control-q>", lambda _event: finish_break())
                    window.bind("<Command-q>", lambda _event: finish_break())
                    window.after(0, update_frame, 0)
                    window.deiconify()
                    window.update_idletasks()
                    window.lift()
                    self._set_topmost(window, True)
                    window.focus_force()
                    window.after(250, lambda: self._set_topmost(window, False))
                    close_reminder(schedule=False)
                    window.after(self.popup_duration * 1000, finish_break)
                except (FileNotFoundError, OSError, tk.TclError):
                    logger.exception("Failed to load the breathing animation.")
                    close_reminder()
                    self._show_error("Failed to load the breathing animation.")

            def skip_reminder() -> None:
                logger.info("User skipped the break reminder.")
                close_reminder()

            tk.Button(
                button_frame,
                text="Start break",
                command=load_image,
                width=12,
            ).pack(side="left", padx=5)
            tk.Button(
                button_frame,
                text="Skip",
                command=skip_reminder,
                width=8,
            ).pack(side="left", padx=5)
            tk.Button(
                button_frame,
                text="Quit",
                command=self.shutdown,
                width=8,
            ).pack(side="left", padx=5)

            popup.protocol("WM_DELETE_WINDOW", skip_reminder)
            popup.bind("<Escape>", lambda _event: skip_reminder())
            popup.bind("<Control-q>", lambda _event: self.shutdown())
            popup.bind("<Command-q>", lambda _event: self.shutdown())
            popup.grab_set()
            logger.info("Showing break reminder.")
        except (OSError, tk.TclError):
            logger.exception("Failed to show the break reminder.")
            self._destroy_window(popup)
            self._popup = None
            self._schedule_next_prompt()
            self._show_error("Failed to show the break reminder.")

    def shutdown(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._popup_active = False
        logger.info("Shutting down %s.", APP_NAME)

        if self._scheduled_prompt and self._root_exists():
            try:
                self.root.after_cancel(self._scheduled_prompt)
            except tk.TclError:
                pass
            self._scheduled_prompt = None

        self._destroy_window(self._popup)
        self._destroy_window(self._break_window)
        self._popup = None
        self._break_window = None
        self._frame_images = []
        self._frame_delays = []
        self._restore_signal_handlers()

        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

    def start(self) -> None:
        if not self._ready or self._closing:
            return

        self._install_signal_handlers()
        logger.info("Starting %s.", APP_NAME)
        self.root.after(0, self.show_image)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown()


def main() -> int:
    try:
        app = RstEyeApp(
            "resources/med.gif",
            interval_seconds=read_int_env(
                "POPUP_INTERVAL",
                DEFAULT_POPUP_INTERVAL_MINUTES,
            )
            * 60,
            popup_duration_seconds=read_int_env(
                "POPUP_DURATION",
                DEFAULT_POPUP_DURATION_SECONDS,
            ),
            fullscreen=True,
        )
        app.start()
        return 0
    except Exception as exc:
        if tk is not None and isinstance(exc, tk.TclError):
            logger.error("Unable to start the graphical application: %s", exc)
            print(
                "RstEye needs an active graphical desktop session. "
                "Start it from your logged-in macOS or Ubuntu desktop.",
                file=sys.stderr,
            )
            return 1

        logger.exception("Unhandled exception while starting %s.", APP_NAME)
        print("RstEye could not start. Check the log for details.", file=sys.stderr)
        return 1
