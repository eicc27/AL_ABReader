import os
import numpy as np
from PIL import Image


def rm_mkdir(dir: str):
    if os.path.exists(dir):
        for file in os.listdir(dir):
            os.remove(os.path.join(dir, file))
    else:
        os.mkdir(dir)


def read_img(file: str):
    return np.array(Image.open(file))
