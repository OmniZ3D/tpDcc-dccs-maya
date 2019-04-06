#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with cameras
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya
from tpMayaLib.core import node


def get_current_camera(use_api=True):
    """
    Returns the currently active camera
    :param use_api: bool, Whether to use OpenMaya API to retrieve the camera path or not
    :return: str, name of the active camera transform
    """

    if use_api:
        if maya.is_new_api():
            camera_path = maya.OpenMayaUI.M3dView().active3dView().getCamera()
            return camera_path.fullPathName()
        else:
            camera_path = maya.OpenMaya.MDagPath()
            maya.OpenMayaUI.M3dView().active3dView().getCamera(camera_path)
            return camera_path.fullPathName()
    else:
        panel = maya.cmds.getPanel(withFocus=True)
        if maya.cmds.getPanel(typeOf=panel) == 'modelPanel':
            cam = maya.cmds.modelEditor(panel, query=True, camera=True)
            if cam:
                if maya.cmds.nodeType(cam) == 'transform':
                    return cam
                elif maya.cmds.objectType(cam, isAType='shape'):
                    parent = maya.cmds.listRelatives(cam, parent=True, fullPath=True)
                    if parent:
                        return parent[0]

        cam_shapes = maya.cmds.ls(sl=True, type='camera')
        if cam_shapes:
            return maya.cmds.listRelatives(cam_shapes, parent=True, fullPath=True)[0]

        transforms = maya.cmds.ls(sl=True, type='transform')
        if transforms:
            cam_shapes = maya.cmds.listRelatives(transforms, shapes=True, type='camera')
            if cam_shapes:
                return maya.cmds.listRelatives(cam_shapes, parent=True, fullPath=True)[0]


def set_current_camera(camera_name):
    """
    Sets the camera to be used in the active view
    :param camera_name: str, name of the camera to use
    """

    view = maya.OpenMayaUI.M3dView.active3dView()
    if maya.cmds.nodeType(camera_name) == 'transform':
        shapes = maya.cmds.listRelatives(camera_name, shapes=True)
        if shapes and maya.cmds.nodeType(shapes[0]) == 'camera':
            camera_name = shapes[0]

    mobj = node.get_mobject(camera_name)
    cam = maya.OpenMaya.MDagPath(mobj)
    view.setCamera(cam)

    maya.cmds.refresh()
