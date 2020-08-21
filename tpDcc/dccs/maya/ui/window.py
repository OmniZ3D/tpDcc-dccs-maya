#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for Maya windows
"""

from __future__ import print_function, division, absolute_import

from Qt.QtWidgets import *
from Qt.QtCore import *

from tpDcc.libs.qt.core import window as core_window
from tpDcc.dccs import maya as maya

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

BOOTSTRAP_WIDGETS = dict()


class MayaWindow(core_window.MainWindow, object):
    def __init__(self, *args, **kwargs):
        super(MayaWindow, self).__init__(*args, **kwargs)
        self.setProperty('saveWindowPref', True)

    def bootstrap_widget(self):
        bootstrap_widget = self.property("bootstrapWidget")

        if self._current_docked is None and bootstrap_widget is not None:
            self._current_docked = not bootstrap_widget.isFloating()

        return bootstrap_widget

    def docked(self):
        """
        Returns if the window is current docked
        """

        bootstrap = self.bootstrap_widget()

        if bootstrap is None:
            return False
        else:
            return not bootstrap.isFloating()

    def close(self):
        try:
            super(MayaWindow, self).close()
        except RuntimeError:
            pass

        if self.docked():
            self.delete_bootstrap()

    def delete_bootstrap(self):
        """ Delete the bootstrap Widget

        :return:
        :rtype:
        """
        bootstrap = self.bootstrap_widget()

        if bootstrap is not None:
            self.setProperty("bootstrapWidget", None)   # avoid recursion by setting to none
            bootstrap.close()


# class MayaDockWindow(core_window.DockWindow, object):
#     def __init__(self, *args, **kwargs):
#         super(MayaDockWindow, self).__init__(*args, **kwargs)
#
#
# class MayaSubWindow(core_window.SubWindow, object):
#     def __init__(self, *args, **kwargs):
#         super(MayaSubWindow, self).__init__(*args, **kwargs)


class BootStrapWidget(MayaQWidgetDockableMixin, QWidget):
    width = maya.cmds.optionVar(query='workspacesWidePanelInitialWidth') * 0.75
    INITIAL_SIZE = QSize(width, 600)
    PREFERRED_SIZE = QSize(width, 420)
    MINIMUM_SIZE = QSize((width * 0.95), 220)

    def __init__(self, widget, title, icon=None, uid=None, parent=None):
        super(BootStrapWidget, self).__init__(parent=parent)

        global BOOTSTRAP_WIDGETS
        BOOTSTRAP_WIDGETS[uid] = self

        self.setWindowTitle(title)
        if icon:
            self.setWindowIcon(icon)
        self._docking_frame = QMainWindow(self)
        self._docking_frame.layout().setContentsMargins(0, 0, 0, 0)
        self._docking_frame.setWindowFlags(Qt.Widget)
        self._docking_frame.setDockOptions(QMainWindow.AnimatedDocks)

        self.central_widget = widget
        self._docking_frame.setCentralWidget(self.central_widget)

        bootstrap_layout = QVBoxLayout(self)
        bootstrap_layout.addWidget(self._docking_frame, 0)
        bootstrap_layout.setContentsMargins(0, 0, 0, 0)
        bootstrap_layout.setSpacing(0)
        self.setLayout(bootstrap_layout)
        widget.setProperty('bootstrapWidget', self)

    def __del__(self, *args, **kwargs):
        """
        Overriding to do nothing to avoid C++ object already deleted error
        since they try to destroy the workspace after its QObject has already been deleted
        """

        pass

    def setSizeHint(self, size):
        self._preferred_size = size

    def close(self, *args, **kwargs):
        """
        Overridden to call the bootstrap user widget.close()
        """

        self.central_widget.close()
        super(BootStrapWidget, self).close(*args, **kwargs)

    def show(self, **kwargs):
        name = self.objectName()
        name = name + "WorkspaceControl"
        if maya.cmds.workspaceControl(name, query=True, exists=True):
            maya.cmds.deleteUI(name)
            maya.cmds.workspaceControlState(name, remove=True)
        kwargs["retain"] = False
        kwargs["uiScript"] = 'try: from tpDcc.dccs.maya.ui import window;window.rebuild("{}")\n' \
                             'except ImportError: pass'.format(self.objectName())
        kwargs["closeCallback"] = 'try: from tpDcc.dccs.maya.ui import window;window.bootstrap_destroy_window("{}")\n' \
                                  'except ImportError: pass'.format(self.objectName())
        super(BootStrapWidget, self).show(**kwargs)


def rebuild(object_name):
    """If the bootstrap widget exists then we reapply it to mayas layout, otherwise do nothing.

    :param object_name: the bootStrap objectName
    :type object_name: str
    """
    global BOOTSTRAP_WIDGETS
    wid = BOOTSTRAP_WIDGETS.get(object_name)
    if wid is None:
        return False

    parent = maya.OpenMayaUI.MQtUtil.getCurrentParent()
    mixinPtr = maya.OpenMayaUI.MQtUtil.findControl(wid.objectName())
    maya.OpenMayaUI.MQtUtil.addWidgetToMayaLayout(long(mixinPtr), long(parent))
    return True


def bootstrap_destroy_window(object_name):
    """
    Function to destroy a bootstrapped widget, this use the maya workspaceControl objectName
    :param object_name: The bootstrap Widget objectName
    :type object_name: str
    :rtype: bool
    """
    global BOOTSTRAP_WIDGETS
    wid = BOOTSTRAP_WIDGETS.get(object_name)

    if wid is not None:
        BOOTSTRAP_WIDGETS.pop(object_name)
        wid.close()
        return True
    return False
