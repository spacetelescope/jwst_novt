from jdaviz.app import Application
from jdaviz.core.config import get_configuration
from jdaviz.configs.imviz.helper import Imviz


class ViewImage(object):
    def __init__(self):
        # start imviz viewer with custom configuration
        self.app = Application(self._config())
        self.viz = Imviz(self.app)

        # set up viewer sizing for voila app
        self.style = ".jdaviz__content--not-in-notebook " \
                     "{min-height: 80vh; max-height:80vh}"

    def _config(self):
        # create a config dict that does not allow file import or viewer creation,
        # based on MAST Jdaviz configuration
        cc = get_configuration('imviz')
        cc['settings']['viewer_spec'] = cc['settings'].get('configuration', 'default')
        cc['settings']['configuration'] = 'novt'
        cc['settings']['visible'] = {'menu_bar': False, 'toolbar': False, 'tray': False,
                                     'tab_headers': False}
        for tool in ['g-data-tools', 'g-viewer-creator', 'g-image-viewer-creator']:
            if tool in cc['toolbar']:
                cc['toolbar'].remove(tool)
        return cc
