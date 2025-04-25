import os
import time
import fitz
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import serial
import serial.tools.list_ports

class SMSHandler:
    def __init__(self, watch_folder, modem_port, baud_rate, status_callback):
        self.watch_folder = watch_folder
        self.modem_port = modem_port
        self.baud_rate = baud_rate
        self.status_callback = status_callback
        self.observer = None

    def start_observer(self):
        event_handler = PDFEventHandler(
            sms_handler=self,
            status_callback=self.status_callback
        )
        self.observer = Observer()
        self.observer.schedule(event_handler, self.watch_folder, recursive=False)
        self.observer.start()
        try:
            while self.observer.is_alive():
                self.observer.join(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def send_sms_via_modem(self, phone_number, message):
        try:
            # تهيئة المودم
            modem = serial.Serial(self.modem_port, self.baud_rate, timeout=5)
            time.sleep(2)  # انتظار استقرار الاتصال
            
            # إرسال أوامر AT
            modem.write(b'AT+CMGF=1\r')  # وضع النص
            time.sleep(1)
            modem.write(f'AT+CMGS="{phone_number}"\r'.encode())
            time.sleep(1)
            modem.write(message.encode() + b"\x1A")  # 1A هو Ctrl+Z لإرسال الرسالة
            time.sleep(5)  # انتظار الإرسال
            
            # قراءة الرد
            response = modem.read_all().decode()
            modem.close()
            
            return "OK" in response
        except Exception as e:
            self.status_callback(f"فشل الإرسال: {str(e)}", "red")
            return False

class PDFEventHandler(FileSystemEventHandler):
    def __init__(self, sms_handler, status_callback):
        self.sms_handler = sms_handler
        self.status_callback = status_callback

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.pdf'):
            return

        try:
            # تحويل PDF إلى نص
            pdf_path = event.src_path
            doc = fitz.open(pdf_path)
            text = "".join(page.get_text() for page in doc)
            
            # استخراج الرقم
            phone_number = None
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.isdigit() and len(stripped) == 9:
                    phone_number = stripped
                    break
            
            if not phone_number:
                self.status_callback("رقم غير موجود في الملف", "red")
                return

            # إرسال الرسالة
            success = self.sms_handler.send_sms_via_modem(phone_number, text)
            if success:
                self.status_callback(f"تم الإرسال إلى {phone_number}", "green")
                os.remove(pdf_path)
            else:
                self.status_callback("فشل الإرسال", "red")
                
        except Exception as e:
            self.status_callback(f"خطأ: {str(e)}", "red")
