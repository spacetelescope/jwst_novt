import os

import ipywidgets as ipw

from novt.constants import NOVT_DIR

__all__ = ['read_image']


def read_image(image_file, width='100px', height='100px', margin='10px'):
    image_path = os.path.join(NOVT_DIR, 'data', image_file)
    with open(image_path, 'rb') as fh:
        image = fh.read()
    image_widget = ipw.Image(value=image, format='png',
                             width=width, height=height)
    image_widget.layout.object_fit = 'contain'
    if margin is not None:
        image_widget.layout.margin = margin
    return image_widget
