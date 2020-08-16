from io import BytesIO
from lxml import html
import requests

class Page:
    def __init__(self, url, img_selector, next_selector,
        prev_selector):
        self.img_selector = img_selector
        self.next_selector = next_selector
        self.prev_selector = prev_selector
        self.request_page(url)

    def prev(self):
        return self.request_page(self.prev_url)

    def next(self):
        return self.request_page(self.next_url)

    def request_page(self, url):
        self.this_url = url

        page = requests.get(url)
        self.tree = html.fromstring(page.content)

        self.prev_url = self.find_attribute(self.prev_selector, 'href')

        self.next_url = self.find_attribute(self.next_selector, 'href')

        img_src = self.find_attribute(self.img_selector, 'src')
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

def queue_pages(current_page, next_queue, prev_queue, block_thread, stop_event):
    with block_thread:
        settings = {
            "img_selector": current_page[0].img_selector,
            "next_selector": current_page[0].next_selector,
            "prev_selector": current_page[0].prev_selector,
        }
    while not stop_event.wait(1.0):
        with block_thread:
            if len(next_queue) == 3:
                next_url = None
            elif len(next_queue) > 0:
                next_url = next_queue[-1].next_url
            else:
                next_url = current_page[0].next_url

            if len(prev_queue) == 3:
                prev_url = None
            elif prev_queue:
                prev_url = prev_queue[0].prev_url
            else:
                prev_url = current_page[0].prev_url

        if next_url:
            next_page = Page(next_url, **settings)
            print(f'Next queue length: {len(next_queue)}')
            with block_thread:
                next_queue.append(next_page)

        if prev_url:
            prev_page = Page(prev_url, **settings)
            print(f'Previous queue length: {len(prev_queue)}')
            with block_thread:
                prev_queue.appendleft(prev_page)
    return 0
