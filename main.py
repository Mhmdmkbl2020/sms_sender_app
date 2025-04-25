import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from sms_handler import SMSHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF SMS Sender")
        self.root.geometry("500x400")
        
        # متغيرات الواجهة
        self.watch_folder = tk.StringVar()
        self.modem_port = tk.StringVar(value="COM3")
        self.baud_rate = tk.IntVar(value=9600)
        
        # إنشاء العناصر
        tk.Label(root, text="مجلد المراقبة:").pack(pady=5)
        self.folder_entry = tk.Entry(root, textvariable=self.watch_folder, width=50)
        self.folder_entry.pack(pady=5)
        tk.Button(root, text="اختيار المجلد", command=self.select_folder).pack(pady=5)
        
        tk.Label(root, text="إعدادات المودم GSM").pack(pady=10)
        tk.Label(root, text="منفذ COM:").pack()
        tk.Entry(root, textvariable=self.modem_port).pack()
        tk.Label(root, text="معدل الباود:").pack()
        tk.Entry(root, textvariable=self.baud_rate).pack()
        
        self.status_label = tk.Label(root, text="جاهز", fg="green")
        self.status_label.pack(pady=20)
        
        self.start_button = tk.Button(root, text="بدء المراقبة", command=self.start_monitoring)
        self.start_button.pack(pady=10)
        
        self.sms_handler = None
        self.observer = None

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.watch_folder.set(folder)

    def start_monitoring(self):
        if not self.watch_folder.get():
            messagebox.showerror("خطأ", "يرجى اختيار مجلد المراقبة")
            return
            
        self.status_label.config(text="يعمل...", fg="blue")
        self.start_button.config(state=tk.DISABLED)
        
        self.sms_handler = SMSHandler(
            watch_folder=self.watch_folder.get(),
            modem_port=self.modem_port.get(),
            baud_rate=self.baud_rate.get(),
            status_callback=self.update_status
        )
        
        threading.Thread(target=self.sms_handler.start_observer, daemon=True).start()

    def update_status(self, message, color="black"):
        self.status_label.config(text=message, fg=color)
        if "تم الإرسال" in message:
            self.start_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
