from collections import deque
from io import BytesIO
from lxml import html
import os
import requests
import threading


class LocalPage:
    def __init__(self, page_num, folder):
        self.folder = folder
        self.page_num = int(page_num)
        self.path = self.give_path(self.page_num)
        self.img = self.load_img()

    @property
    def save_string(self):
        return self.page_num

    def give_path(self, page_num):
        return os.path.join(self.folder, f'{page_num}.png')

    @property
    def has_prev(self):
        return os.path.exists(self.give_path(self.page_num - 1))

    @property
    def has_next(self):
        return os.path.exists(self.give_path(self.page_num + 1))

    def is_prev(self, page):
        return self.page_num == page.page_num + 1

    def is_next(self, page):
        return self.page_num == page.page_num - 1

    def prev(self):
        return self.__class__(self.page_num - 1, self.folder)

    def next(self):
        return self.__class__(self.page_num + 1, self.folder)

    def load_img(self):
        fp = BytesIO()
        with open(self.path, 'rb') as f:
            fp.write(f.read())
        fp.seek(0)
        return fp


class OnlinePage:
    def __init__(self, url, img_selector, next_selector,
        prev_selector, href_format, src_format):
        self.img_selector = img_selector
        self.next_selector = next_selector
        self.prev_selector = prev_selector
        self.href_format = href_format
        self.src_format = src_format
        self.kwargs = {
            'img_selector': img_selector,
            'next_selector': next_selector,
            'prev_selector': prev_selector,
            'href_format': href_format,
            'src_format': src_format,
        }
        self.request_page(url)

    @property
    def save_string(self):
        return self.this_url

    @property
    def has_prev(self):
        return bool(self.prev_url)

    @property
    def has_next(self):
        return bool(self.next_url)

    def is_prev(self, page):
        return self.this_url == page.next_url

    def is_next(self, page):
        return self.this_url == page.prev_url

    def prev(self):
        return self.__class__(self.prev_url, **self.kwargs)

    def next(self):
        return self.__class__(self.next_url, **self.kwargs)

    def request_page(self, url):
        self.this_url = url

        page = requests.get(url)
        self.tree = html.fromstring(page.content)

        self.prev_url = self.find_attribute(self.prev_selector, 'href')
        self.next_url = self.find_attribute(self.next_selector, 'href')

        if self.href_format == 'relative':
            base_url = '/'.join(self.this_url.split('/')[:-1])
            self.next_url = base_url + self.next_url
            self.prev_url = base_url + self.prev_url
        elif self.href_format == 'absolute':
            split_url = self.this_url.split('/')
            base_url = f'{split_url[0]}//{split_url[2]}'
            self.next_url = base_url + self.next_url
            self.prev_url = base_url + self.prev_url

        img_src = self.find_attribute(self.img_selector, 'src')
        if self.src_format == 'no_schema':
            img_src = f'https:{img_src}'

        self.img = self.request_image(img_src)
        return self.img

    def find_attribute(self, selector, attribute_name):
        try:
            element = self.tree.xpath(selector)[0]
        except IndexError:
            return None
        else:
            return element.attrib.get(attribute_name, None)

    def request_image(self, img_src):
        page = requests.get(img_src)
        img = page.content
        fp = BytesIO()
        fp.write(img)
        fp.seek(0)
        return fp


class QueueThread(threading.Thread):
    def __init__(self, initial_page, next_pages, prev_pages, **kwargs):
        self.current_page = initial_page
        self.next_queue = deque(maxlen=next_pages)
        self.prev_queue = deque(maxlen=prev_pages)

        self.block_thread = threading.Lock()
        self.next_ready = threading.Event()
        self.prev_ready = threading.Event()
        self.stop_event = threading.Event()

        super().__init__(name="QueueThread", daemon=True, kwargs=kwargs)

    def stop(self):
        self.stop_event.set()

    def next(self):
        if self.current_page.has_next:
            self.next_ready.wait()
            with self.block_thread:
                self.prev_queue.append(self.current_page)
                self.prev_ready.set()
                self.current_page = self.next_queue.popleft()
                if not self.next_queue:
                    self.next_ready.clear()
        return self.current_page

    def prev(self):
        if self.current_page.has_prev:
            self.prev_ready.wait()
            with self.block_thread:
                self.next_queue.appendleft(self.current_page)
                self.next_ready.set()
                self.current_page = self.prev_queue.pop()
                if not self.prev_queue:
                    self.prev_ready.clear()
        return self.current_page

    def can_append_next(self, page):
        if len(self.next_queue) == self.next_queue.maxlen:
            return False
        elif not self.next_queue and self.current_page.is_next(page):
            return True
        elif self.next_queue and self.next_queue[-1].is_next(page):
            return True
        else:
            return False

    def can_append_prev(self, page):
        if len(self.prev_queue) == self.prev_queue.maxlen:
            return False
        elif not self.prev_queue and self.current_page.is_prev(page):
            return True
        elif self.prev_queue and self.prev_queue[0].is_prev(page):
            return True
        else:
            return False

    def run(self, *args, **kwargs):
        stop = False
        while not stop:
            with self.block_thread:
                if len(self.next_queue) == self.next_queue.maxlen:
                    page = None
                elif self.next_queue:
                    page = self.next_queue[-1]
                else:
                    page = self.current_page

            if page and page.has_next:
                next_page = page.next()
                with self.block_thread:
                    if self.can_append_next(next_page):
                        self.next_queue.append(next_page)
                        self.next_ready.set()

            with self.block_thread:
                if len(self.prev_queue) == self.prev_queue.maxlen:
                    page = None
                elif self.prev_queue:
                    page = self.prev_queue[0]
                else:
                    page = self.current_page

            if page and page.has_prev:
                prev_page = page.prev()
                with self.block_thread:
                    if self.can_append_prev(prev_page):
                        self.prev_queue.appendleft(prev_page)
                        self.prev_ready.set()

            stop = self.stop_event.wait(1.0)
        return 0
