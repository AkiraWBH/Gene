import threading
import time
import pygetwindow as gw
import pyautogui
import vlc
from tkinter import Tk, filedialog, Label, Button, Listbox, Scrollbar, Toplevel, Entry, StringVar, Scale, Frame, Canvas, HORIZONTAL, VERTICAL, PhotoImage
from pynput import mouse
import yt_dlp
import os
import random
import pyperclip

def read_comments(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().splitlines()

def sanitize_comment(comment):
    return comment.replace('@', '') + ' '

class PositionSelector:
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self.position = None
        self.listener = mouse.Listener(on_click=self.on_click)
        self.create_instructions_window()
        self.listener.start()
    
    def create_instructions_window(self):
        self.instructions_window = Toplevel(self.root)
        self.instructions_window.title("Chọn Vị trí Chat")
        self.instructions_window.geometry("300x150")
        self.instructions_window.attributes("-topmost", True)
        
        label = Label(self.instructions_window, text="Nhấp vào cửa sổ ứng dụng để chọn vị trí chat.", pady=20)
        label.pack()
        self.instructions_window.protocol("WM_DELETE_WINDOW", self.cleanup)
    
    def on_click(self, x, y, button, pressed):
        if pressed:
            self.position = (x, y)
            self.cleanup()
    
    def cleanup(self):
        if self.listener:
            self.listener.stop()
        if self.instructions_window:
            self.instructions_window.destroy()
        if self.callback:
            self.callback(self.position)

class CommentBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nô Lệ Comment")
        self.root.geometry("400x400")
        self.root.resizable(False, False)

        self.file_path = None
        self.comments = []
        self.running = False
        self.selected_window = None
        self.chat_position = None
        self.delay = 5
        self.music_url = StringVar()
        self.player = vlc.MediaPlayer()
        self.is_music_playing = False
        self.current_song_info = StringVar()

        self.root.iconphoto(True, PhotoImage(file=r'C:\Users\letha\OneDrive\Documents\python\auto chat fb\neko.gif'))

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

        self.comment_frame = Frame(self.scrollable_frame, bg='#d9d9d9', padx=10, pady=10)
        self.comment_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.music_frame = Frame(self.scrollable_frame, bg='#d9d9d9', padx=10, pady=10)
        self.music_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.file_label = Label(self.comment_frame, text="Chưa chọn tệp", wraplength=300, bg='#d9d9d9')
        self.file_label.grid(row=0, column=0, columnspan=2, pady=5, sticky="w")

        self.select_file_button = Button(self.comment_frame, text="Chọn tệp bình luận", command=self.select_file, bg='#4CAF50', fg='white')
        self.select_file_button.grid(row=1, column=0, pady=5, sticky="ew")

        self.select_window_button = Button(self.comment_frame, text="Chọn cửa sổ ứng dụng", command=self.select_window, bg='#2196F3', fg='white')
        self.select_window_button.grid(row=2, column=0, pady=5, sticky="ew")

        self.select_position_button = Button(self.comment_frame, text="Chọn vị trí chat", command=self.open_position_selector, bg='#FF9800', fg='white')
        self.select_position_button.grid(row=3, column=0, pady=5, sticky="ew")

        self.delay_label = Label(self.comment_frame, text="Thời gian chờ (giây):", bg='#d9d9d9')
        self.delay_label.grid(row=4, column=0, pady=5, sticky="w")

        self.delay_entry = Entry(self.comment_frame, width=10)
        self.delay_entry.insert(0, "5")
        self.delay_entry.grid(row=5, column=0, pady=5, sticky="ew")

        self.start_button = Button(self.comment_frame, text="Bắt đầu gửi bình luận", command=self.start_typing, bg='#FF5722', fg='white')
        self.start_button.grid(row=6, column=0, pady=5, sticky="ew")

        self.stop_button = Button(self.comment_frame, text="Dừng lại", command=self.stop_typing, bg='#F44336', fg='white')
        self.stop_button.grid(row=7, column=0, pady=5, sticky="ew")

        self.comment_label = Label(self.comment_frame, text="", wraplength=300, bg='#d9d9d9')
        self.comment_label.grid(row=8, column=0, columnspan=2, pady=5, sticky="w")

        self.countdown_label = Label(self.comment_frame, text="", bg='#d9d9d9')
        self.countdown_label.grid(row=9, column=0, columnspan=2, pady=5, sticky="w")

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

        self.current_song_label = Label(self.music_frame, textvariable=self.current_song_info, bg='#d9d9d9')
        self.current_song_label.grid(row=2, column=0, columnspan=3, pady=5, sticky="w")

        # Xóa các Label cho thời gian đã chạy và thời gian còn lại
        # self.current_time_label = Label(self.music_frame, text="Thời gian đã chạy: 0 giây", bg='#d9d9d9')
        # self.current_time_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="w")

        # self.remaining_time_label = Label(self.music_frame, text="Thời gian còn lại: 0 giây", bg='#d9d9d9')
        # self.remaining_time_label.grid(row=4, column=0, columnspan=3, pady=5, sticky="w")

        # Thêm Label mới để hiển thị tổng thời gian
        self.total_time_label = Label(self.music_frame, text="00:00:00/00:00:00", bg='#d9d9d9', font=('Helvetica', 12))
        self.total_time_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="nsew")

        self.comment_frame.columnconfigure([0, 1], weight=1)
        self.comment_frame.rowconfigure([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], weight=1)
        
        self.music_frame.columnconfigure([0, 1, 2], weight=1)
        self.music_frame.rowconfigure([0, 1, 2, 3, 4], weight=1)

        self.root.bind_all("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.root.bind_all("<Button-4>", self.on_mouse_wheel)  # Linux
        self.root.bind_all("<Button-5>", self.on_mouse_wheel)  # Linux

    def select_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if self.file_path:
            self.comments = read_comments(self.file_path)
            self.file_label.config(text=f"Đã chọn tệp: {os.path.basename(self.file_path)}")
        else:
            self.file_label.config(text="Chưa chọn tệp")

    def select_window(self):
        window_titles = [window.title for window in gw.getWindowsWithTitle("")]
        if window_titles:
            window_selector = Toplevel(self.root)
            window_selector.title("Chọn Cửa Sổ")

            window_listbox = Listbox(window_selector)
            scrollbar = Scrollbar(window_selector, orient="vertical", command=window_listbox.yview)
            window_listbox.config(yscrollcommand=scrollbar.set)

            for title in window_titles:
                window_listbox.insert("end", title)

            def select_window():
                selected_title = window_listbox.get(window_listbox.curselection())
                self.selected_window = gw.getWindowsWithTitle(selected_title)[0]
                window_selector.destroy()

            select_button = Button(window_selector, text="Chọn", command=select_window)

            window_listbox.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            select_button.pack(pady=5)

    def open_position_selector(self):
        PositionSelector(self.root, self.set_chat_position)

    def set_chat_position(self, position):
        self.chat_position = position

    def start_typing(self):
        try:
            self.delay = int(self.delay_entry.get())
        except ValueError:
            self.comment_label.config(text="Vui lòng nhập số hợp lệ cho thời gian chờ.")
            return

        if not self.comments:
            self.comment_label.config(text="Vui lòng chọn tệp bình luận.")
            return

        if not self.selected_window:
            self.comment_label.config(text="Vui lòng chọn cửa sổ ứng dụng.")
            return

        if not self.chat_position:
            self.comment_label.config(text="Vui lòng chọn vị trí chat.")
            return

        self.comment_label.config(text="")
        self.running = True
        self.typing_thread = threading.Thread(target=self.send_comments)
        self.typing_thread.start()

    def stop_typing(self):
        self.running = False

    def send_comments(self):
        self.selected_window.activate()
        random.shuffle(self.comments)
        for comment in self.comments:
            if not self.running:
                break
            sanitized_comment = sanitize_comment(comment)
            pyautogui.click(self.chat_position)

            pyperclip.copy(sanitized_comment + ' ')
            self.comment_label.config(text=f"Đã gửi bình luận: '{sanitized_comment.strip()}'")

            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press("enter")

            for i in range(self.delay, 0, -1):
                if not self.running:
                    break
                self.countdown_label.config(text=f"Đợi {i} giây trước khi gửi bình luận tiếp theo.")
                time.sleep(1)

            self.countdown_label.config(text="Tiếp tục gửi bình luận.")
            time.sleep(1)

        self.countdown_label.config(text="Đã dừng lại.")

    def on_mouse_wheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.canvas.yview_scroll(1, "units")
        if event.num == 4 or event.delta == 120:
            self.canvas.yview_scroll(-1, "units")

    def toggle_music(self):
        if not self.is_music_playing:
            self.start_music()
        else:
            self.stop_music()

    def start_music(self):
        url = self.music_url.get()
        if not url:
            return
        stream_url = self.download_music(url)
        if stream_url:
            self.play_music(stream_url)

            self.current_song_info.set(f"Đang phát: {self.get_song_title(url)}")
            self.is_music_playing = True
            self.toggle_music_button.config(text="Dừng nhạc")
            self.update_current_time()

    def stop_music(self):
        if self.player:
            self.player.stop()
        self.is_music_playing = False
        self.toggle_music_button.config(text="Phát nhạc")
        self.current_song_info.set("")
        self.total_time_label.config(text="00:00:00/00:00:00")

    def set_volume(self, volume):
        self.player.audio_set_volume(int(volume))

    def download_music(self, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                return info_dict['url']
        except Exception as e:
            self.comment_label.config(text=f"Không thể tải nhạc: {str(e)}")
            return None

    def play_music(self, stream_url):
        media = vlc.Media(stream_url)
        self.player.set_media(media)
        self.player.play()

    def get_song_title(self, url):
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'noplaylist': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                return info_dict['title']
        except Exception:
            return "Không rõ"

    def update_current_time(self):
        if self.is_music_playing:
            current_time = int(self.player.get_time() / 1000)
            total_time = int(self.player.get_length() / 1000)

            self.total_time_label.config(text=f"{self.format_time(current_time)}/{self.format_time(total_time)}")

            self.root.after(1000, self.update_current_time)

    def format_time(self, total_seconds):
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

if __name__ == "__main__":
    root = Tk()
    app = CommentBotApp(root)
    root.mainloop()