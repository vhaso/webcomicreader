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

        if self.href_format == 'relative':
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
