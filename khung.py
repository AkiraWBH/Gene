import time
import random
import pygetwindow as gw
import keyboard
from tkinter import Tk, filedialog, Label, Button, Listbox, Scrollbar, Toplevel, Entry
from pynput import mouse  
import pyautogui

def read_comments(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().splitlines()

def sanitize_comment(comment):
    return comment.replace('@', '') + ' '

class CommentBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nô Lệ Comment")
        self.root.geometry("400x400")

        self.file_path = None
        self.comments = []
        self.running = False
        self.selected_window = None
        self.chat_position = None
        self.delay = 5

        self.file_label = Label(self.root, text="Chưa chọn tệp", wraplength=300)
        self.file_label.pack(pady=10)

        self.select_file_button = Button(self.root, text="Chọn tệp bình luận", command=self.select_file)
        self.select_file_button.pack(pady=10)

        self.select_window_button = Button(self.root, text="Chọn cửa sổ ứng dụng", command=self.select_window)
        self.select_window_button.pack(pady=10)

        self.select_position_button = Button(self.root, text="Chọn vị trí chat", command=self.select_position)
        self.select_position_button.pack(pady=10)

        self.delay_label = Label(self.root, text="Thời gian chờ (giây):")
        self.delay_label.pack(pady=5)

        self.delay_entry = Entry(self.root)
        self.delay_entry.insert(0, "5")
        self.delay_entry.pack(pady=5)

        self.start_button = Button(self.root, text="Bắt đầu gửi bình luận", command=self.start_typing)
        self.start_button.pack(pady=10)

        self.stop_button = Button(self.root, text="Dừng lại", command=self.stop_typing)
        self.stop_button.pack(pady=10)

        self.comment_label = Label(self.root, text="", wraplength=300)
        self.comment_label.pack(pady=10)

    def select_file(self):
        self.file_path = filedialog.askopenfilename(title="Chọn tệp bình luận", filetypes=[("Text Files", "*.txt")])
        if self.file_path:
            self.comments = read_comments(self.file_path)
            if self.comments:
                self.file_label.config(text=f"Đã chọn tệp: {self.file_path}")
            else:
                self.file_label.config(text="Tệp rỗng hoặc không có bình luận.")
        else:
            self.file_label.config(text="Không chọn tệp nào.")

    def select_window(self):
        window_selector = Toplevel(self.root)
        window_selector.title("Chọn cửa sổ ứng dụng")
        window_selector.geometry("300x200")

        label = Label(window_selector, text="Chọn cửa sổ ứng dụng từ danh sách:")
        label.pack(pady=5)

        window_listbox = Listbox(window_selector, selectmode="single")
        scrollbar = Scrollbar(window_selector, orient="vertical", command=window_listbox.yview)
        window_listbox.config(yscrollcommand=scrollbar.set)

        for window in gw.getAllTitles():
            window_listbox.insert("end", window)

        window_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_select():
            selection = window_listbox.curselection()
            if selection:
                self.selected_window = window_listbox.get(selection[0])
                window_selector.destroy()
                self.file_label.config(text=f"Đã chọn cửa sổ: {self.selected_window}")

        select_button = Button(window_selector, text="Chọn", command=on_select)
        select_button.pack(pady=10)

    def select_position(self):
        self.comment_label.config(text="Nhấp chuột vào vị trí bạn muốn chat. Đợi để chọn vị trí...")

        def on_click(x, y, button, pressed):
            if pressed:  
                self.chat_position = (x, y)  
                self.comment_label.config(text=f"Đã chọn vị trí: {self.chat_position}. Bạn có thể bắt đầu gửi bình luận.")
                listener.stop()  

        listener = mouse.Listener(on_click=on_click)
        listener.start()

    def start_typing(self):
        if not self.comments:
            self.comment_label.config(text="Vui lòng chọn tệp bình luận trước.")
            return
        if not self.selected_window:
            self.comment_label.config(text="Vui lòng chọn cửa sổ ứng dụng trước.")
            return
        if not self.chat_position:
            self.comment_label.config(text="Vui lòng chọn vị trí chat trước.")
            return

        try:
            self.delay = int(self.delay_entry.get())
            if self.delay <= 0:
                self.delay = 5
                self.comment_label.config(text="Thời gian chờ không hợp lệ. Sử dụng giá trị mặc định là 5 giây.")
        except ValueError:
            self.delay = 5
            self.comment_label.config(text="Thời gian chờ không hợp lệ. Sử dụng giá trị mặc định là 5 giây.")

        self.running = True
        self.comment_label.config(text="Đang làm việc: Đang gửi bình luận ...")
        self.root.after(100, self.send_random_comment)

    def stop_typing(self):
        self.running = False
        self.comment_label.config(text="Đã dừng lại.")

    def send_random_comment(self):
        if not self.running:
            return

        if not self.comments:
            self.comment_label.config(text="Danh sách bình luận trống.")
            return
        
        comment = random.choice(self.comments)
        sanitized_comment = sanitize_comment(comment)

        window = gw.getWindowsWithTitle(self.selected_window)
        if window:
            chat_window = window[0]
            chat_window.activate()
            pyautogui.click(self.chat_position[0], self.chat_position[1])
            keyboard.write(sanitized_comment, delay=0.05)
            keyboard.press_and_release('enter')

            self.comment_label.config(text=f"Đã gửi bình luận. Chờ {self.delay} giây nhé...")

            if self.running:
                self.root.after(self.delay * 1000, self.send_random_comment)
        else:
            self.comment_label.config(text="Không tìm thấy cửa sổ chat.")

root = Tk()
app = CommentBotApp(root)
root.mainloop()