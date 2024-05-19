import csv
import keys as ks
import os
import sys
import tkinter as tk
from page_api import LocalPage, OnlinePage, QueueThread
from PIL import Image, ImageTk

def _clear_queue_after_key_release(function):
    def event(app, *args, **kwargs):
        result = function(app, *args, **kwargs)

        #Remove queued KeyRelease events
        app.master.bind("<KeyRelease>", lambda event: None)
        app.master.update()
        app.master.bind("<KeyRelease>", app.key_release_bindings)

        return result
    return event

class Application(tk.Frame):
    img_height = 700

    def init_page(self, settings_path):
        params = {}
        with open(settings_path, 'r') as f:
            reader = csv.reader(f, delimiter=':')
            for line in reader:
                params[line[0]] = line[1]

        self.save_file = params.pop('save_file')

        with open(self.save_file, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            bookmark = next(reader)[0]

        page_type = params.pop('page_type')

        if page_type == 'online':
            self.page = OnlinePage(bookmark, **params)
        elif page_type == 'local':
            self.page = LocalPage(bookmark, **params)

        self.queue_thread = QueueThread(self.page, next_pages=3, prev_pages=2)
        self.queue_thread.start()

    def __init__(self, master, settings_path):
        super().__init__(master)
        self.master = master
        self.pack()
        self.update()

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
        self.queue_thread.stop()
        self.queue_thread.join()

    def save(self):
        with open(self.save_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow([self.page.save_string])

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

        self.btn_change = tk.Button(self.btn_frame, text="Change",
            command=self.change_comic)
        self.btn_change.pack(side=tk.RIGHT, expand=1)

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
        self.canvas.yview_moveto(0)

    @_clear_queue_after_key_release
    def previous_image(self):
        self.page = self.queue_thread.prev()
        self.refresh_image()

    @_clear_queue_after_key_release
    def next_image(self):
        self.page = self.queue_thread.next()
        self.refresh_image()

    @_clear_queue_after_key_release
    def change_comic(self):
        self.save()
        self.queue_thread.stop()
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
    assert len(sys.argv) >= 2, 'Missing settings_path argument'
    settings_path = sys.argv[1]
    app = Application(root, settings_path)

    app.mainloop()
