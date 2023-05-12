import base64
import os

import ipywidgets as ipw
import ipyvuetify as v


from novt.constants import NOVT_DIR

__all__ = ['read_image', 'ToggleButton', 'FileDownloadLink']


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


class ToggleButton(v.Btn):
    """Button widget with primary class."""
    def __init__(self, **kwargs):
        super().__init__(class_='mx-2 my-2 primary active',
                         **kwargs)
        self.alternate_class = 'accent'
        self.disabled = True

    def is_active(self):
        return 'active' in self.class_

    def reset(self):
        self.class_list.add('active')
        self.class_list.replace(self.alternate_class, 'primary')
        self.disabled = False

    def toggle(self):
        if self.is_active():
            self.class_list.remove('active')
            self.class_list.replace('primary', self.alternate_class)
        else:
            self.class_list.add('active')
            self.class_list.replace(self.alternate_class, 'primary')


class FileDownloadLink(ipw.HTML):
    def __init__(self, *args, **kwargs):
        self.value = ''
        self.prefix = kwargs.get('value', '')
        self.url = ''
        self.style_value = 'color: #00617E'
        self.down_arrow = '\u2913'

        super().__init__(*args, **kwargs)
        self.disabled = True

    def edit_link(self, filename, data):
        b64 = base64.b64encode(data.encode())
        payload = b64.decode()
        self.url = f"data:text/plain;base64,{payload}"

        html = f'<a ' \
               f'style="{self.style_value}"' \
               f'download="{filename}" ' \
               f'href="{self.url}" ' \
               f'target="_blank">' \
               f'{self.prefix} {filename} {self.down_arrow}' \
               f'</a>'
        self.value = html
        self.disabled = False

    def clear_link(self, *args, **kwargs):
        self.url = ''
        self.value = self.prefix
        self.disabled = True
