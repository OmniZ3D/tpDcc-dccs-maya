#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for Maya windows
"""

from __future__ import print_function, division, absolute_import


import tpQtLib
import tpDccLib as tp
from tpQtLib.core import window as core_window


try:
    from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

    class MayaWindow(MayaQWidgetBaseMixin, core_window.MainWindow):
        def __init__(self, *args, **kwargs):
            super(MayaWindow, self).__init__(*args, **kwargs)

    class MayaDockWindow(MayaQWidgetDockableMixin, core_window.DockWindow):
        def __init__(self, *args, **kwargs):
            super(MayaDockWindow, self).__init__(*args, **kwargs)

    if 2017 <= tp.Dcc.get_version() < 2019:
        class MayaSubWindow(core_window.SubWindow, object):
            def __init__(self, *args, **kwargs):
                super(MayaSubWindow, self).__init__(*args, **kwargs)
    else:
        class MayaSubWindow(MayaQWidgetBaseMixin, core_window.SubWindow):
            def __init__(self, *args, **kwargs):
                super(MayaSubWindow, self).__init__(*args, **kwargs)

except ImportError:

    class MayaWindow(core_window.MainWindow, object):
        def __init__(self, *args, **kwargs):
            super(MayaWindow, self).__init__(*args, **kwargs)

    class MayaDockWindow(core_window.DockWindow, object):
        def __init__(self, *args, **kwargs):
            super(MayaDockWindow, self).__init__(*args, **kwargs)


    class MayaSubWindow(core_window.SubWindow, object):
        def __init__(self, *args, **kwargs):
            super(MayaSubWindow, self).__init__(*args, **kwargs)


tpQtLib.MainWindow = MayaWindow
tpQtLib.DockWindow = MayaDockWindow
tpQtLib.SubWindow = MayaSubWindow
