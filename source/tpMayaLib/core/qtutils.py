#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utils functions to work with Qt in Maya
"""

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpMayaLib as maya
from tpQtLib.core import qtutils as qt
from tpMayaLib.core import gui


def dock_widget(widget_class):
    """
    Creates an instance of the class and dock into Maya UI
    :param widget_class:
    """

    workspace_control = widget_class.__name__ + '_workspace_control'

    try:
        maya.cmds.deleteUI(workspace_control)
        maya.debug('Removing workspace {0}'.format(workspace_control))
    except Exception:
        pass

    if gui.get_maya_api_version() >= 201700:

        main_control = maya.cmds.workspaceControl(workspace_control, ttc=["AttributeEditor", -1], iw=425, mw=True, wp='preferred', label='{0} - {1}'.format(widget_class.title, widget_class.version))
        control_widget = maya.OpenMayaUI.MQtUtil.findControl(workspace_control)
        control_wrap = qt.wrapinstance(long(control_widget), QWidget)
        control_wrap.setAttribute(Qt.WA_DeleteOnClose)
        win = widget_class(name=workspace_control, parent=control_wrap, layout=control_wrap.layout())
        maya.cmds.evalDeferred(lambda *args: maya.cmds.workspaceControl(main_control, e=True, rs=True))
    else:
        win = None

    return win


def dock_window(window_class):
    try:
        maya.cmds.deleteUI(window_class.name)
    except Exception:
        pass

    main_control = maya.cmds.workspaceControl(window_class.name, ttc=["AttributeEditor", -1], iw=300, mw=True, wp='preferred', label=window_class.title)

    control_widget = maya.OpenMayaUI.MQtUtil.findControl(window_class.name)
    control_wrap = qt.wrapinstance(long(control_widget), QWidget)
    control_wrap.setAttribute(Qt.WA_DeleteOnClose)
    win = window_class(control_wrap)

    maya.cmds.evalDeferred(lambda *args: maya.cmds.workspaceControl(main_control, e=True, rs=True))

    return win.run()
