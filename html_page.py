from io import BytesIO
from lxml import html
import requests

class Page:
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

    def prev(self):
        return Page(self.prev_url, **self.kwargs)

    def next(self):
        return Page(self.next_url, **self.kwargs)

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

def queue_pages(
    current_page, next_queue, prev_queue,
    block_thread, dequeue_event, next_ready, prev_ready, stop_event,
    ):
    stop = False
    while not stop:
        with block_thread:
            if len(next_queue) == next_queue.maxlen:
                page = None
            elif len(next_queue) > 0:
                page = next_queue[-1]
            else:
                page = current_page[0]

        if page:
            next_page = page.next()
            if not dequeue_event.wait(0.1):
                with block_thread:
                    next_queue.append(next_page)
                    next_ready.set()

        with block_thread:
            if len(prev_queue) == prev_queue.maxlen:
                page = None
            elif prev_queue:
                page = prev_queue[0]
            else:
                page = current_page[0]

        if page:
            prev_page = page.prev()
            if not dequeue_event.wait(0.1):
                with block_thread:
                    prev_queue.appendleft(prev_page)
                    prev_ready.set()

        dequeue_event.clear()
        stop = stop_event.wait(1.0)
    return 0
