from PIL import Image

import bb
from app import MainApp
import requests
import numpy as np
import io
class ImageHandler:
    def __init__(self,app:MainApp):
        self.app=app

    @classmethod
    def read_image_file( path, gray=False):
        img = Image.open(path)
        if gray:
            img = img.convert('L')  # Convert image to grayscale
        return img
        
        return values

    def pic_mark(self, dIm):
        w3 = self.app.w_pic * 3

        height, width = self.app.mask.shape

        for row in range(2, height - 1):  # Adjusted the range to prevent out-of-bounds access
            for col in range(width):
                i = (row * self.app.w_pic + col) * 3  # Convert 2D indices to 1D for dIm

                if self.app.mask[row, col] < 10:
                    self.set_pix(dIm, i, 0)
                    continue

                cp = sum(self.app.pusto[i:i + 3])
                c1 = sum(dIm[i:i + 3])

                if abs(c1 - cp) < self.app.img_tolerant:
                    self.set_pix(dIm, i, 0)
                    c1 = 0

                if c1 < 10:
                    if dIm[i - 9] < 10:
                        self.set_pix(dIm, i - 3, 0)  # del .,,.
                        self.set_pix(dIm, i - 6, 0)  # del .,,.
                    elif dIm[i - 6] < 10:
                        self.set_pix(dIm, i - 3, 0)  # del .,.
                    elif dIm[i - w3 - w3] < 10:
                        self.set_pix(dIm, i - w3, 0)  # del .,.
        return dIm

    def claster(self):
        self.app.list_clast = []

        for cbb in self.app.short_list_bb:
            found = False
            if cbb.t > 0 and cbb.t != 2:
                for cc in self.app.list_clast:
                    if not (cc.y > cbb.y2 or cc.y2 < cbb.y or cc.x2 < cbb.x or cc.x > cbb.x2):
                        cc.x2 = max(cc.x2, cbb.x2)
                        cc.x = min(cc.x, cbb.x)
                        cc.y2 = max(cc.y2, cbb.y2)
                        cc.y = min(cc.y, cbb.y)
                        cc.w = cc.x2 - cc.x
                        cc.h = cc.y2 - cc.y

                        if cc.t == 0:
                            cc.t = 1
                        if cbb.t == 3:
                            cc.t += 3
                        found = True
                        break

                if not found:
                    nclast = bb.BB(cbb.x, cbb.y, cbb.w, cbb.h)
                    nclast.t = 3 if cbb.t == 3 else 0
                    self.app.list_clast.append(nclast)

    def get_img(self):
        response = requests.get(self.app.json_input['dataServer'])
        im = response.content
        print(f"Loaded: {len(im)} bytes")

        if len(im) < 10000:
            raise ValueError("No load image")

        # Convert byte data to a PIL image
        image = Image.open(io.BytesIO(im))

        # Ensure the image has RGB channels
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Get image data as a list
        data = list(image.getdata())

        # Swap red and blue channels
        swapped_data = [(b, g, r) for r, g, b in data]

        # Create a new PIL image with swapped channels
        swapped_image = Image.new('RGB', image.size)
        swapped_image.putdata(swapped_data)

        # If you need the swapped data as an array for further processing:
        pixels = bytearray(swapped_image.tobytes())
        self.app.canvFull=swapped_image
        # Set the swapped image to mydata attribute
        self.app.mydata = swapped_image

        # In Python, there's no direct equivalent to 'ctx.put_image_data()'.
        # You can save the image or show it using PIL directly.


        return pixels

    def set_pix(self, ar, i, v):
        i = max(0, i)
        ar[i] = v
        ar[i + 1] = v
        ar[i + 2] = v

    def check_old_bb(self, x, y):
        # We want to check up to 30 old bounding boxes
        for olbb in range(1, min(31, len(self.app.list_bb) + 1)):
            # Access older bounding boxes from the end of the list
            if self.app.list_bb[-olbb].inBB(x, y):
                return True
        return False

    def mark_bb(self, d_im, step=10):
        self.app.list_bb = []

        for y in range(self.app.min_y + self.app.size, self.app.h_pic - self.app.size, step):
            tsize = round(self.app.min_size + (self.app.max_size - self.app.min_size) * (y / self.app.h_pic))

            for x in range(30, self.app.w_pic - step, step):
                if self.check_old_bb(x, y):
                    continue

                np = (self.app.h_pic - y) * self.app.w_pic + x

                if (d_im[np * 3] > 0) or (d_im[np * 3 - 6] > 0) or (d_im[np * 3 + 6] > 0):
                    co = 0.1
                    spx, spy = 0, 0

                    for iy in range(-tsize, tsize, 2):
                        for ix in range(-tsize, tsize, 2):
                            if d_im[(np + ix + iy * self.w_pic) * 3] > 0:
                                co += 1
                                spx += ix
                                spy += iy

                    nx = round(min(max(0, x + spx / co - tsize), self.w_pic - 2 * tsize))
                    ny = round(min(max(0, y - spy / co - tsize), self.h_pic - 2 * tsize))

                    if co > 50 and not self.check_old_bb(nx, ny):
                        self.app.list_bb.append(self.bb(nx, ny, 2 * tsize, 2 * tsize))



