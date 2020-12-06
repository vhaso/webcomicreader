import fitz
import csv
import os
import sys
from PIL import Image

if __name__ == '__main__':
    pdf_path = sys.argv[1]
    destination = sys.argv[2]
    if not os.path.exists(destination):
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

    _, foldername = os.path.split(destination)
    filename = foldername.lower() + '.csv'
    page_save = os.path.join('page_saves', filename)
    with open(page_save, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow([0])
    settings = os.path.join('settings', filename)
    with open(settings, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=':')
        writer.writerow(['page_type', 'local'])
        writer.writerow(['save_file', page_save])
        writer.writerow(['folder', destination])
