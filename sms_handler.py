import os
import time
import fitz
import serial
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SMSHandler:
    def __init__(self, folder, port, baudrate, delete_files, status_callback):
        self.folder = folder
        self.port = port
        self.baudrate = baudrate
        self.delete_files = delete_files
        self.status_callback = status_callback
        self.observer = None
        self.running = False

    def start(self):
        self.running = True
        self.observer = Observer()
        event_handler = PDFHandler(self.port, self.baudrate, self.delete_files, self.status_callback)
        self.observer.schedule(event_handler, self.folder, recursive=False)
        self.observer.start()
        self.status_callback("المراقبة نشطة", "green")

    def stop(self):
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.status_callback("تم الإيقاف", "black")

    def is_running(self):
        return self.running

class PDFHandler(FileSystemEventHandler):
    def __init__(self, port, baudrate, delete_files, status_callback):
        self.port = port
        self.baudrate = baudrate
        self.delete_files = delete_files
        self.status_callback = status_callback

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.pdf'):
            return

        self.status_callback(f"اكتشاف ملف جديد: {event.src_path}", "blue")
        time.sleep(1)  # انتظار اكتمال الكتابة

        try:
            # استخراج النص
            text = self.extract_text(event.src_path)
            if not text:
                self.status_callback("ملف فارغ!", "red")
                return

            # استخراج الرقم
            phone_number = self.extract_phone_number(text)
            if not phone_number:
                self.status_callback("لم يتم العثور على رقم صالح", "red")
                return

            # إرسال الرسالة
            if self.send_sms(phone_number, text):
                self.status_callback(f"تم الإرسال إلى {phone_number}", "green")
                if self.delete_files:
                    os.remove(event.src_path)
            else:
                self.status_callback("فشل في الإرسال", "red")

        except Exception as e:
            self.status_callback(f"خطأ: {str(e)}", "red")

    def extract_text(self, pdf_path):
        doc = fitz.open(pdf_path)
        return "\n".join(page.get_text() for page in doc)

    def extract_phone_number(self, text):
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.isdigit() and len(stripped) == 9:
                return stripped
        return None

    def send_sms(self, phone, message):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=10) as modem:
                modem.write(b'AT+CMGF=1\r')
                time.sleep(1)
                modem.write(f'AT+CMGS="{phone}"\r'.encode())
                time.sleep(1)
                modem.write(message.encode() + b"\x1A")
                time.sleep(5)
                response = modem.read_all().decode()
                return "OK" in response
        except Exception as e:
            self.status_callback(f"خطأ في المودم: {str(e)}", "red")
            return False
