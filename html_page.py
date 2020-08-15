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
