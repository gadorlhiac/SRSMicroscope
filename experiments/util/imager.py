import numpy as np
import cv2
import matplotlib.pyplot as plt
import time

class Imager(object):
    def __init__(self, pixsize):
        self.current_im = np.zeros([512, 512])
        pass

    # Create image from zidaq output
    # Requires info from frame and line input on the scanning
    def form_image(self, r, frame, line):
        iframeon = np.where(frame[:-1]+1 < frame[1:]) + 1
        ilineon = np.where(line[:-1]+1 < line[1:]) + 1
        ilineoff = np.where(line[:-1]+1 > line[1:]) + 1
        lines = [(on, off) for on, off in ilineon, ilineoff]

        im = np.zeros([512, 512])
        for i, l in enumerate(lines):
            im[i] = cv2.resize(np.array(r[l[0]:l[1], ndmin=2, dtype=float), dsize=(512,1))

        self.current_im = im
        return im

    # Display current image
    def display(self):
        while 1:
            time.sleep(1)
            plt.cla()
            plt.clf()
            plt.imshow(self.current_im)