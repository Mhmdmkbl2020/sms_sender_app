import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from sms_handler import SMSHandler
import os

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF SMS Sender v1.0")
        self.root.geometry("600x500")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Variables
        self.watch_folder = tk.StringVar()
        self.modem_port = tk.StringVar(value="COM3")
        self.baud_rate = tk.IntVar(value=9600)
        self.delete_after_send = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="جاهز")

        # UI Components
        self.create_ui()

    def create_ui(self):
        # Folder Selection
        tk.Label(self.root, text="مجلد المراقبة:").pack(pady=5)
        frame = ttk.Frame(self.root)
        frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Entry(frame, textvariable=self.watch_folder, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="اختيار المجلد", command=self.select_folder).pack(side=tk.RIGHT)

        # Modem Settings
        ttk.Label(self.root, text="إعدادات المودم GSM", font=('Arial', 10, 'bold')).pack(pady=10)
        settings_frame = ttk.Frame(self.root)
        settings_frame.pack(padx=10, pady=5)
        ttk.Label(settings_frame, text="منفذ COM:").grid(row=0, column=0, padx=5)
        ttk.Entry(settings_frame, textvariable=self.modem_port).grid(row=0, column=1, padx=5)
        ttk.Label(settings_frame, text="معدل الباود:").grid(row=0, column=2, padx=5)
        ttk.Entry(settings_frame, textvariable=self.baud_rate, width=10).grid(row=0, column=3, padx=5)

        # Options
        options_frame = ttk.Frame(self.root)
        options_frame.pack(pady=10)
        ttk.Checkbutton(options_frame, text="حذف الملف بعد الإرسال", variable=self.delete_after_send).pack()

        # Status
        ttk.Label(self.root, textvariable=self.status_text).pack(pady=10)

        # Action Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        self.start_button = ttk.Button(button_frame, text="بدء المراقبة", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(button_frame, text="إيقاف", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=5)

        # Initialize
        self.sms_handler = None
        self.observer = None

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.watch_folder.set(folder)

    def start_monitoring(self):
        if not self.watch_folder.get():
            messagebox.showerror("خطأ", "يرجى اختيار مجلد المراقبة!")
            return

        self.status_text.set("جاري المراقبة...")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.sms_handler = SMSHandler(
            folder=self.watch_folder.get(),
            port=self.modem_port.get(),
            baudrate=self.baud_rate.get(),
            delete_files=self.delete_after_send.get(),
            status_callback=self.update_status
        )

        threading.Thread(target=self.sms_handler.start, daemon=True).start()

    def stop_monitoring(self):
        if self.sms_handler:
            self.sms_handler.stop()
        self.status_text.set("تم الإيقاف")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def update_status(self, message, color="black"):
        self.status_text.set(message)
        self.root.update_idletasks()

    def on_close(self):
        if self.sms_handler and self.sms_handler.is_running():
            self.stop_monitoring()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
