import time
import random
import pygetwindow as gw
import pyautogui
import vlc
from tkinter import Tk, filedialog, Label, Button, Listbox, Scrollbar, Toplevel, Entry, StringVar, Scale, Frame, Canvas, HORIZONTAL, VERTICAL
from pynput import mouse
import yt_dlp
import os

def read_comments(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().splitlines()

def sanitize_comment(comment):
    return comment.replace('@', '') + ' '

class CommentBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nô Lệ Comment")
        self.root.geometry("400x500")
        
        self.file_path = None
        self.comments = []
        self.running = False
        self.selected_window = None
        self.chat_position = None
        self.delay = 5
        self.remaining_time = 0
        self.music_url = StringVar()
        self.music_file = None
        self.player = vlc.MediaPlayer()
        self.is_music_playing = False
        self.music_pos = 0

        self.canvas = Canvas(root, bg='#e0e0e0')
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar_y = Scrollbar(root, orient=VERTICAL, command=self.canvas.yview)
        self.scrollbar_y.pack(side="right", fill="y")

        self.scrollbar_x = Scrollbar(root, orient=HORIZONTAL, command=self.canvas.xview)
        self.scrollbar_x.pack(side="bottom", fill="x")

        self.canvas.config(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        self.scrollable_frame = Frame(self.canvas, bg='#f0f0f0')
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.comment_frame = Frame(self.scrollable_frame, bg='#f9f9f9', padx=10, pady=10)
        self.comment_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.music_frame = Frame(self.scrollable_frame, bg='#d9d9d9', padx=10, pady=10)
        self.music_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.file_label = Label(self.comment_frame, text="Chưa chọn tệp", wraplength=300, bg='#f9f9f9')
        self.file_label.grid(row=0, column=0, columnspan=2, pady=5, sticky="w")

        self.select_file_button = Button(self.comment_frame, text="Chọn tệp bình luận", command=self.select_file, bg='#4CAF50', fg='white')
        self.select_file_button.grid(row=1, column=0, pady=5, sticky="ew")

        self.select_window_button = Button(self.comment_frame, text="Chọn cửa sổ ứng dụng", command=self.select_window, bg='#2196F3', fg='white')
        self.select_window_button.grid(row=2, column=0, pady=5, sticky="ew")

        self.select_position_button = Button(self.comment_frame, text="Chọn vị trí chat", command=self.select_position, bg='#FF9800', fg='white')
        self.select_position_button.grid(row=3, column=0, pady=5, sticky="ew")

        self.delay_label = Label(self.comment_frame, text="Thời gian chờ (giây):", bg='#f9f9f9')
        self.delay_label.grid(row=4, column=0, pady=5, sticky="w")

        self.delay_entry = Entry(self.comment_frame, width=10)
        self.delay_entry.insert(0, "5")
        self.delay_entry.grid(row=4, column=1, pady=5, sticky="ew")

        self.start_button = Button(self.comment_frame, text="Bắt đầu gửi bình luận", command=self.start_typing, bg='#FF5722', fg='white')
        self.start_button.grid(row=5, column=0, pady=5, sticky="ew")

        self.stop_button = Button(self.comment_frame, text="Dừng lại", command=self.stop_typing, bg='#F44336', fg='white')
        self.stop_button.grid(row=6, column=0, pady=5, sticky="ew")

        self.comment_label = Label(self.comment_frame, text="", wraplength=300, bg='#f9f9f9')
        self.comment_label.grid(row=7, column=0, columnspan=2, pady=5, sticky="w")

        self.countdown_label = Label(self.comment_frame, text="", bg='#f9f9f9')
        self.countdown_label.grid(row=8, column=0, columnspan=2, pady=5, sticky="w")

        self.music_label = Label(self.music_frame, text="Nhập URL nhạc YouTube:", bg='#d9d9d9')
        self.music_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.music_entry = Entry(self.music_frame, textvariable=self.music_url, width=20)
        self.music_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.toggle_music_button = Button(self.music_frame, text="Phát nhạc", command=self.toggle_music, bg='#4CAF50', fg='white')
        self.toggle_music_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.volume_label = Label(self.music_frame, text="Âm lượng:", bg='#d9d9d9')
        self.volume_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.volume_slider = Scale(self.music_frame, from_=0, to_=100, orient=HORIZONTAL, command=self.set_volume, length=150)
        self.volume_slider.set(100)
        self.volume_slider.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        self.comment_frame.columnconfigure([0, 1], weight=1)
        self.comment_frame.rowconfigure([0, 1, 2, 3, 4, 5, 6, 7, 8], weight=1)
        
        self.music_frame.columnconfigure([0, 1, 2], weight=1)
        self.music_frame.rowconfigure([0, 1], weight=1)

    def select_file(self):
        self.file_path = filedialog.askopenfilename(title="Chọn tệp bình luận", filetypes=[("Text Files", "*.txt")])
        if self.file_path:
            self.comments = read_comments(self.file_path)
            self.file_label.config(text=f"Đã chọn tệp: {self.file_path}" if self.comments else "Tệp rỗng hoặc không có bình luận.")
        else:
            self.file_label.config(text="Không chọn tệp nào.")

    def select_window(self):
        window_selector = Toplevel(self.root)
        window_selector.title("Chọn cửa sổ ứng dụng")
        window_selector.geometry("250x150")

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
                self.comment_label.config(text=f"Đã chọn cửa sổ: {self.selected_window}")
                window_selector.destroy()

        select_button = Button(window_selector, text="Chọn", command=on_select, bg='#2196F3', fg='white')
        select_button.pack(pady=5)

    def select_position(self):
        self.comment_label.config(text="Nhấp vào vị trí trên màn hình chat để chọn vị trí...")
        self.chat_position = None

        def on_click(x, y, button, pressed):
            if pressed:
                self.chat_position = (x, y)
                self.comment_label.config(text=f"Vị trí chat đã chọn: {self.chat_position}")
                return False

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

    def start_typing(self):
        if not self.selected_window or not self.chat_position:
            self.comment_label.config(text="Vui lòng chọn cửa sổ ứng dụng và vị trí chat trước.")
            return

        try:
            self.delay = int(self.delay_entry.get()) or 5
        except ValueError:
            self.delay = 5

        self.running = True
        self.comment_label.config(text="Đang làm việc: Đang gửi bình luận ...")
        self.root.after(100, self.send_random_comment)

    def stop_typing(self):
        self.running = False
        self.comment_label.config(text="Đã dừng lại.")
        self.countdown_label.config(text="")

    def start_countdown(self):
        if self.remaining_time > 0:
            self.countdown_label.config(text=f"Còn lại {self.remaining_time} giây")
            self.remaining_time -= 1
            self.root.after(1000, self.start_countdown)
        else:
            self.countdown_label.config(text="")

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

            for char in sanitized_comment:
                pyautogui.typewrite(char, interval=0.05)
            
            pyautogui.press('enter')

            self.comment_label.config(text=f"Đã gửi bình luận. Chờ {self.delay} giây nhé...")

            self.remaining_time = self.delay
            self.start_countdown()

            if self.running:
                self.root.after(self.delay * 1000, self.send_random_comment)
        else:
            self.comment_label.config(text="Không tìm thấy cửa sổ chat.")

    def play_music(self):
        url = self.music_url.get()
        if url:
            try:
                if self.music_file and os.path.exists(self.music_file):
                    os.remove(self.music_file)

                self.music_file = self.download_music(url)
                
                self.player.set_media(vlc.Media(self.music_file))
                self.player.play()
                self.set_volume(self.volume_slider.get())
                time.sleep(1)
                self.music_pos = 0
                self.is_music_playing = True
                self.toggle_music_button.config(text="Dừng nhạc")
            except Exception as e:
                self.comment_label.config(text=f"Lỗi khi phát nhạc: {e}")

    def toggle_music(self):
        if self.is_music_playing:
            self.music_pos = self.player.get_time() / 1000
            self.player.stop()
            self.is_music_playing = False
            self.toggle_music_button.config(text="Phát nhạc")
            self.comment_label.config(text="Đã dừng nhạc.")
        else:
            if self.music_file:
                self.player.set_media(vlc.Media(self.music_file))
                self.player.set_time(int(self.music_pos * 1000))
                self.player.play()
                self.set_volume(self.volume_slider.get())
                self.is_music_playing = True
                self.toggle_music_button.config(text="Dừng nhạc")
                self.comment_label.config(text="Đang tiếp tục phát nhạc...")
            else:
                self.play_music()
                self.toggle_music_button.config(text="Dừng nhạc")

    def download_music(self, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'music.%(ext)s',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return 'music.' + info_dict['ext']

    def set_volume(self, volume):
        self.player.audio_set_volume(int(volume))

if __name__ == "__main__":
    root = Tk()
    app = CommentBotApp(root)
    root.mainloop()