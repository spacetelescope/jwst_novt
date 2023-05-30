import base64

import ipyvuetify as v
import ipywidgets as ipw

from jwst_novt.constants import NOVT_DIR

__all__ = ["read_image", "ToggleButton", "FileDownloadLink"]


def read_image(image_file, width="100px", height="100px", margin="10px"):
    """
    Read an image file into a displayable widget.

    Parameters
    ----------
    image_file : str
        Name of an image file in the jwst_novt/data directory.
    width : str, optional
        Width to apply to the image widget.
    height : str, optional
        Height to apply to the image widget.
    margin : str, optional
        Margin to apply around the image.

    Returns
    -------
    widget : ipywidgets.Image
        Image widget.
    """
    image_path = NOVT_DIR / "data" / image_file
    with image_path.open("rb") as fh:
        image = fh.read()
    image_widget = ipw.Image(value=image, format="png", width=width, height=height)
    image_widget.layout.object_fit = "contain"
    if margin is not None:
        image_widget.layout.margin = margin
    return image_widget


class ToggleButton(v.Btn):
    """
    Button widget with styling classes and toggle methods.

    Buttons are initially disabled when created. They can
    be enabled directly, or via the reset method.

    Toggle style uses the primary class when active and
    the `alternate_class` when inactive. By default, the alternate
    class is 'accent', but it may be changed after creation as
    needed.
    """

    def __init__(self, **kwargs):
        super().__init__(class_="mx-2 my-2 primary active", **kwargs)
        self.alternate_class = "accent"
        self.disabled = True

    def is_active(self):
        """Test whether button is currently active."""
        return "active" in self.class_

    def reset(self):
        """Reset button to active, enabled state."""
        self.class_list.add("active")
        self.class_list.replace(self.alternate_class, "primary")
        self.disabled = False

    def toggle(self):
        """Toggle button between active and inactive states."""
        if self.is_active():
            self.class_list.remove("active")
            self.class_list.replace("primary", self.alternate_class)
        else:
            self.class_list.add("active")
            self.class_list.replace(self.alternate_class, "primary")


class FileDownloadLink(ipw.HTML):
    """
    Clickable HTML link to download a small file.

    On creation, the HTML element contains only input text
    values and is disabled. Use the `edit_link` method to set a
    link in the element and enable the element.

    File contents are stored client-side after the link is
    created, so this method is suitable only for very small files.
    Clear the link after download with the `clear_link` method.
    """

    def __init__(self, *args, **kwargs):
        self.value = ""
        self.prefix = kwargs.get("value", "")
        self.url = ""
        self.style_value = "color: #00617E"
        self.down_arrow = "\u2913"

        super().__init__(*args, **kwargs)
        self.disabled = True

    def edit_link(self, filename, data):
        """
        Edit the HTML element to add a link to download a file.

        Parameters
        ----------
        filename : str
            Filename to assign to the file on download.
        data : str
            Contents of the file.
        """
        b64 = base64.b64encode(data.encode())
        payload = b64.decode()
        self.url = f"data:text/plain;base64,{payload}"

        html = (
            f"<a "
            f'style="{self.style_value}"'
            f'download="{filename}" '
            f'href="{self.url}" '
            f'target="_blank">'
            f"{self.prefix} {filename} {self.down_arrow}"
            f"</a>"
        )
        self.value = html
        self.disabled = False

    def clear_link(self, *args, **kwargs):
        """Clear any current link out of the HTML element and disable it."""
        self.url = ""
        self.value = self.prefix
        self.disabled = True
