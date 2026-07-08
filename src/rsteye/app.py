import logging
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import Button, Label, messagebox

from dotenv import load_dotenv
from PIL import Image, ImageSequence, ImageTk

load_dotenv()

DEFAULT_POPUP_DURATION_SECONDS = 60
DEFAULT_POPUP_INTERVAL_MINUTES = 60


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rsteye.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)


class RstEyeApp:
    def __init__(
        self,
        image_path: str,
        interval_seconds: int = DEFAULT_POPUP_INTERVAL_MINUTES * 60,
        popup_duration_seconds: int = DEFAULT_POPUP_DURATION_SECONDS,
        fullscreen: bool = False,
    ) -> None:
        self.image_path = resource_path(image_path)
        self.interval = max(1, interval_seconds)
        self.popup_duration = max(1, popup_duration_seconds)
        self.fullscreen = fullscreen
        self.root = tk.Tk()
        self.root.withdraw()
        self._background_image = None
        self._frame_images = []
        self._popup_active = False
        self._ready = True

        logger.info("Initialized RstEyeApp with image path: %s", self.image_path)

        if not os.path.exists(self.image_path):
            logger.error("Image file '%s' not found.", self.image_path)
            messagebox.showerror("Error", f"Image file '{self.image_path}' not found.")
            self.root.destroy()
            self._ready = False

    def _schedule_next_prompt(self) -> None:
        self._popup_active = False
        if self.root.winfo_exists():
            logger.info(
                "Waiting %d seconds before showing the next popup.",
                self.interval,
            )
            self.root.after(self.interval * 1000, self.show_image)

    def show_image(self) -> None:
        if self._popup_active or not self.root.winfo_exists():
            return

        self._popup_active = True

        try:
            popup = tk.Toplevel(self.root)
            popup.title("Please Wait")
            popup.resizable(False, False)
            popup.attributes("-topmost", True)
            popup.transient(self.root)
            logger.info("Showing popup window.")

            popup_width = 350
            popup_height = 200
            screen_width = popup.winfo_screenwidth()
            screen_height = popup.winfo_screenheight()
            x = (screen_width / 2) - (popup_width / 2)
            y = (screen_height / 2) - (popup_height / 2)
            popup.geometry(f"{popup_width}x{popup_height}+{int(x)}+{int(y)}")
            logger.info(
                "Popup window created at position (%d, %d) with size (%dx%d).",
                x,
                y,
                popup_width,
                popup_height,
            )

            background_path = resource_path("resources/rsteye.png")
            if os.path.exists(background_path):
                try:
                    self._background_image = ImageTk.PhotoImage(
                        Image.open(background_path).resize((popup_width, popup_height))
                    )
                except (FileNotFoundError, OSError, tk.TclError):
                    logger.exception("Failed to load popup background image.")
                    messagebox.showerror("Error", "Failed to load popup background image.")
                    popup.destroy()
                    self._schedule_next_prompt()
                    return

                background_label = tk.Label(popup, image=self._background_image)
                background_label.place(relwidth=1, relheight=1)

            popup_label = Label(
                popup,
                text=(
                    "The break animation will start shortly.\n"
                    f"Breathing exercise duration: {self.popup_duration} seconds.\n"
                    "Please wait."
                ),
                font=("Helvetica", 12, "bold"),
                wraplength=300,
                justify="center",
            )
            popup_label.pack(pady=20)

            button_frame = tk.Frame(popup)
            button_frame.pack(pady=10)

            def load_image() -> None:
                try:
                    window = tk.Toplevel(self.root)
                    window.withdraw()
                    window.title("Take a Break")

                    if self.fullscreen:
                        window.attributes("-fullscreen", True)

                    window.configure(bg="black")

                    screen_width = window.winfo_screenwidth()
                    screen_height = window.winfo_screenheight()

                    img = Image.open(self.image_path)
                    self._frame_images = [
                        ImageTk.PhotoImage(
                            frame.copy().resize(
                                (screen_width, screen_height), Image.LANCZOS
                            )
                        )
                        for frame in ImageSequence.Iterator(img)
                    ]

                    label = Label(window, bg="black")
                    label.pack(fill="both", expand=True)
                    break_finished = False

                    def update_frame(frame_index: int) -> None:
                        if not self._frame_images or not window.winfo_exists():
                            return

                        frame = self._frame_images[frame_index]
                        label.configure(image=frame)
                        window.after(
                            50,
                            update_frame,
                            (frame_index + 1) % len(self._frame_images),
                        )

                    def finish_break() -> None:
                        nonlocal break_finished
                        if break_finished:
                            return
                        break_finished = True
                        if window.winfo_exists():
                            window.destroy()
                        self._schedule_next_prompt()

                    window.after(0, update_frame, 0)
                    window.protocol("WM_DELETE_WINDOW", finish_break)
                    window.deiconify()
                    popup.destroy()
                    logger.info(
                        "Image window will close after %d seconds.",
                        self.popup_duration,
                    )
                    window.after(self.popup_duration * 1000, finish_break)
                except (FileNotFoundError, OSError, tk.TclError):
                    logger.exception("Error loading image sequence.")
                    messagebox.showerror("Error", "Failed to load image.")
                    popup.destroy()
                    self._schedule_next_prompt()

            def on_accept() -> None:
                logger.info("User accepted to view the image.")
                self.root.after(0, load_image)

            def on_exit() -> None:
                logger.info("User declined to view the image.")
                popup.destroy()
                self._schedule_next_prompt()

            load_button = Button(
                button_frame,
                text="Yes",
                command=on_accept,
                font=("Helvetica", 12, "bold"),
                relief="flat",
            )
            load_button.pack(side="left", padx=20)

            exit_button = Button(
                button_frame,
                text="No",
                command=on_exit,
                font=("Helvetica", 12, "bold"),
                relief="flat",
            )
            exit_button.pack(side="right", padx=20)

            popup.protocol("WM_DELETE_WINDOW", on_exit)
            popup.grab_set()

        except (tk.TclError, OSError):
            logger.exception("Failed to show image.")
            self._popup_active = False
            self._schedule_next_prompt()
            messagebox.showerror("Error", "Failed to show image.")

    def start(self) -> None:
        if not self._ready:
            return

        logger.info("Starting the RstEyeApp.")
        self.root.after(0, self.show_image)
        self.root.mainloop()


def main() -> None:
    try:
        logger.info("RstEyeApp is starting.")
        app = RstEyeApp(
            "resources/med.gif",
            interval_seconds=read_int_env(
                "POPUP_INTERVAL", DEFAULT_POPUP_INTERVAL_MINUTES
            )
            * 60,
            popup_duration_seconds=read_int_env(
                "POPUP_DURATION", DEFAULT_POPUP_DURATION_SECONDS
            ),
            fullscreen=True,
        )
        app.start()
    except Exception:
        logger.exception("Unhandled exception occurred.")
        messagebox.showerror("Fatal Error", "An unexpected error occurred.")

