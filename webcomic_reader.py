import csv
import keys as ks
import os
import sys
import threading
import tkinter as tk
from collections import deque
from html_page import Page, queue_pages
from PIL import Image, ImageTk

class Application(tk.Frame):
    img_height = 700

    def _clear_queue_after_key_release(function):
        def event(self, *args, **kwargs):
            result = function(self, *args, **kwargs)

            #Remove queued KeyRelease events
            self.master.bind("<KeyRelease>", lambda event: None)
            self.master.update()
            self.master.bind("<KeyRelease>", self.key_release_bindings)

            return result
        return event

    def init_page(self, settings_path):
        params = {}
        with open(settings_path, 'r') as f:
            reader = csv.reader(f, delimiter=':')
            for line in reader:
                params[line[0]] = line[1]

        self.save_file = params.pop('save_file')

        with open(self.save_file, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            url = next(reader)

        self.page = Page(url[0], **params)

        self.current_page = [self.page,]
        self.block_thread = threading.Lock()
        self.next_queue = deque(maxlen=3)
        self.prev_queue = deque(maxlen=3)
        self.stop_queue = threading.Event()
        self.queue_thread = threading.Thread(
            target=queue_pages,
            name='QueueingThread',
            daemon=True,
            kwargs={
                "current_page": self.current_page,
                "next_queue": self.next_queue,
                "prev_queue": self.prev_queue,
                "block_thread": self.block_thread,
                "stop_event": self.stop_queue,
            }
        )
        self.queue_thread.start()

    def __init__(self, master, settings_path):
        super().__init__(master)
        self.master = master
        self.pack()

        self.img_height = master.winfo_screenheight() - 32
        self.max_width = master.winfo_screenwidth()

        self.settings_path = settings_path
        self.init_page(self.settings_path)

        self.settings_path_var = tk.StringVar(master)
        self.settings_path_var.set(self.settings_path)

        self.create_widgets()

        self.keys = {
            ks.RIGHT_ARROW: self.next_image,
            ks.LEFT_ARROW: self.previous_image,
            ks.UP_ARROW: self.scroll_up,
            ks.DOWN_ARROW: self.scroll_down,
            ks.SPACE_BAR: self.next_image,
            ks.Q: self.master.destroy,
            ks.ESCAPE: self.master.destroy,
            ks.ENTER: self.change_comic,
        }
        self.bind_keys()

    def destroy(self):
        self.save()
        self.stop_queue.set()
        self.queue_thread.join()

    def save(self):
        with open(self.save_file, 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow([self.page.this_url])

    def create_widgets(self):
        image = self.load_image()

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(self, yscrollcommand=self.scrollbar.set,
            width=image.width(), height=self.img_height)
        self.canvas.configure(background='#121212',highlightthickness=0)
        self.canvas.pack(side=tk.TOP)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image)
        self.canvas.image = image
        self.canvas.config(scrollregion=(0,0,0,image.height()))

        self.scrollbar.config(command=self.canvas.yview)

        self.btn_frame = tk.Frame(self.master)
        self.btn_frame.pack(side=tk.BOTTOM)

        self.btn_previous = tk.Button(self.btn_frame, text="<< Previous",
            command=self.previous_image)
        self.btn_previous.pack(side=tk.LEFT, expand=1)

        self.btn_next = tk.Button(self.btn_frame, text="Next >>",
            command=self.next_image)
        self.btn_next.pack(side=tk.RIGHT, expand=1)

        settings_paths = ['settings/' + file.name for file
            in os.scandir('settings/')]
        self.option_menu = tk.OptionMenu(self.btn_frame, self.settings_path_var,
            *settings_paths)
        self.option_menu.pack(side=tk.TOP)

    def load_image(self):
        load = Image.open(self.page.img)
        while load.size[0] > self.max_width:
            load = load.resize(
                (int(load.size[0]/2), int(load.size[1]/2)),
                Image.ANTIALIAS
            )
        return ImageTk.PhotoImage(load)

    def refresh_image(self):
        image = self.load_image()
        self.canvas.config(width=image.width(), height=self.img_height)
        self.canvas.config(scrollregion=(0,0,0,image.height()))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image)
        self.canvas.image = image

    @_clear_queue_after_key_release
    def previous_image(self):
        with self.block_thread:
            if self.prev_queue:
                self.next_queue.appendleft(self.page)
                self.page = self.prev_queue.pop()
            elif self.page.prev_url:
                self.next_queue.appendleft(self.page)
                self.page.prev()
                self.refresh_image()
                self.canvas.yview_moveto(0)
            self.current_page = [self.page,]


    @_clear_queue_after_key_release
    def next_image(self):
        with self.block_thread:
            if self.next_queue:
                self.prev_queue.append(self.page)
                self.page = self.next_queue.popleft()
            elif self.page.next_url:
                self.prev_queue.append(self.page)
                self.page.next()
                self.refresh_image()
                self.canvas.yview_moveto(0)
            self.current_page = [self.page,]


    @_clear_queue_after_key_release
    def change_comic(self):
        self.save()
        self.stop_queue.set()
        self.queue_thread.join()
        settings_path = self.settings_path_var.get()
        self.init_page(settings_path)
        self.refresh_image()

    def scroll_up(self):
        self.canvas.yview_scroll(-1, tk.UNITS)

    def scroll_down(self):
        self.canvas.yview_scroll(1, tk.UNITS)

    def bind_keys(self):
        self.master.bind("<KeyRelease>", self.key_release_bindings)

    def key_release_bindings(self, event):
        callback = self.keys.get(event.keycode, lambda: None)
        callback()

if __name__ == '__main__':
    root = tk.Tk()
    root.configure(background='#121212')
    root.attributes("-fullscreen", True)
    settings_path = sys.argv[1] if len(sys.argv) > 1 else ''
    app = Application(root, settings_path)

    app.mainloop()
