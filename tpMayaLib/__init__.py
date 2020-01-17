#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpMayaLib
"""

from __future__ import print_function, division, absolute_import

try:
    # Do not remove Maya imports
    import maya.cmds as cmds
    import maya.mel as mel
    import maya.utils as utils
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaUI as OpenMayaUI
    import maya.OpenMayaAnim as OpenMayaAnim
    import maya.OpenMayaRender as OpenMayaRender
except ImportError:
    # NOTE: We use this empty try/catch to avoid errors during CI/CD
    pass


new_api = True
try:
    import maya.api.OpenMaya as OpenMayaV2
    import maya.api.OpenMayaUI as OpenMayaUIV2
    import maya.api.OpenMayaAnim as OpenMayaAnimV2
    import maya.api.OpenMayaRender as OpenMayaRenderV2
except Exception:
    new_api = False

try:
    api = {
        'OpenMaya': OpenMaya,
        'OpenMayaUI': OpenMayaUI,
        'OpenMayaAnim': OpenMayaAnim,
        'OpenMayaRender': OpenMayaRender
    }

    if new_api:
        api2 = {
            'OpenMaya': OpenMayaV2,
            'OpenMayaUI': OpenMayaUIV2,
            'OpenMayaAnim': OpenMayaAnimV2,
            'OpenMayaRender': OpenMayaRenderV2
        }
    else:
        api2 = api

    OpenMaya = OpenMaya
    OpenMayaUI = OpenMayaUI
    OpenMayaAnim = OpenMayaAnim
    OpenMayaRender = OpenMayaRender
except Exception:
    # NOTE: We use this empty try/catch to avoid errors during CI/CD
    pass


def use_new_api(flag=False):
    """
    Enables new Maya API usage
    """

    global OpenMaya
    global OpenMayaUI
    global OpenMayaAnim

    if new_api:
        if flag:
            OpenMaya = api2['OpenMaya']
            OpenMayaUI = api2['OpenMayaUI']
            OpenMayaAnim = api2['OpenMayaAnim']
            OpenMayaRender = api2['OpenMayaRender']
        else:
            OpenMaya = api['OpenMaya']
            OpenMayaUI = api['OpenMayaUI']
            OpenMayaAnim = api['OpenMayaAnim']
            OpenMayaRender = api['OpenMayaRender']
    else:
        OpenMaya = api['OpenMaya']
        OpenMayaUI = api['OpenMayaUI']
        OpenMayaAnim = api['OpenMayaAnim']
        OpenMayaRender = api['OpenMayaRender']


def is_new_api():
    """
    Returns whether new Maya API is used or not
    :return: bool
    """

    return not OpenMaya == api['OpenMaya']