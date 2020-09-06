import fitz
import os
import shutil
import sys
from PIL import Image

def iter_pages(reader):
    for page_num in range(reader.numPages):
        yield reader.getPage(page_num)

if __name__ == '__main__':
    pdf_path = sys.argv[1]
    destination = sys.argv[2]
    if os.path.exists(destination):
        shutil.rmtree(destination)
    os.mkdir(destination)

    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        path = os.path.join(destination, f"{i}.png")
        for img in doc.getPageImageList(i):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n < 5:       # this is GRAY or RGB
                pix.writePNG(path)
            else:               # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                pix1.writePNG(path)
                pix1 = None
            pix = None
