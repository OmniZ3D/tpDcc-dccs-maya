#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with cameras
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya
from tpMayaLib.core import node, transform, mathutils


def check_camera(node):
    """
    Checks if given node is a camera. If not, exception is raised
    :param node: str
    """

    if not is_camera(node):
        raise Exception('Object "{}" is not a valid camera!'.format(node))

    return True


def is_camera(node):
    """
    Returns whether given node is a valid camera or not
    :param node: str
    :return: bool
    """

    if not maya.cmds.objExists(node):
        return False

    node_shapes = [node]
    if transform.is_transform(node):
        node_shapes = maya.cmds.listRelatives(node, s=True, pa=True)
        if not node_shapes:
            return False

    for shape in node_shapes:
        if maya.cmds.objectType(shape) == 'camera':
            return True

    return False


def get_all_cameras(exclude_standard_cameras=True, return_transforms=True):
    """
    Returns all cameras in current scene
    :param exclude_standard_cameras: bool, Whether standard cameras (persp, top, front, and side) cameras should be excluded or not
    :param return_transforms: bool, Whether tor return camera shapes or transform nodes
    :return: list(str)
    """

    if exclude_standard_cameras:
        cameras = [c for c in maya.cmds.ls(type='camera') if not maya.cmds.camera(c, query=True, sc=True)]
    else:
        cameras = maya.cmds.ls(type='camera') or list()

    if return_transforms:
        return [maya.cmds.listRelatives(c, p=True)[0] for c in cameras]

    return cameras


def get_current_camera(use_api=True, full_path=True):
    """
    Returns the currently active camera
    :param use_api: bool, Whether to use OpenMaya API to retrieve the camera path or not
    :param full_path: bool
    :return: str, name of the active camera transform
    """

    if use_api:
        if maya.is_new_api():
            camera_path = maya.OpenMayaUI.M3dView().active3dView().getCamera()
            if full_path:
                return camera_path.fullPathName()
            else:
                return camera_path.partialPathName()
        else:
            camera_path = maya.OpenMaya.MDagPath()
            maya.OpenMayaUI.M3dView().active3dView().getCamera(camera_path)
            if full_path:
                return camera_path.fullPathName()
            else:
                return camera_path.partialPathName()
    else:
        panel = maya.cmds.getPanel(withFocus=True)
        if maya.cmds.getPanel(typeOf=panel) == 'modelPanel':
            cam = maya.cmds.modelEditor(panel, query=True, camera=True)
            if cam:
                if maya.cmds.nodeType(cam) == 'transform':
                    return cam
                elif maya.cmds.objectType(cam, isAType='shape'):
                    parent = maya.cmds.listRelatives(cam, parent=True, fullPath=full_path)
                    if parent:
                        return parent[0]

        cam_shapes = maya.cmds.ls(sl=True, type='camera')
        if cam_shapes:
            return maya.cmds.listRelatives(cam_shapes, parent=True, fullPath=full_path)[0]

        transforms = maya.cmds.ls(sl=True, type='transform')
        if transforms:
            cam_shapes = maya.cmds.listRelatives(transforms, shapes=True, type='camera')
            if cam_shapes:
                return maya.cmds.listRelatives(cam_shapes, parent=True, fullPath=full_path)[0]


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


def get_eye_point(camera_name):
    """
    Returns camera eye point
    :param camera_name: str
    :return: list(float, float, float)
    """

    check_camera(camera_name)

    camera_shape = maya.cmds.ls(maya.cmds.listRelatives(camera_name, s=True, pa=True), type='camera')[0]
    camera_dag_path = node.get_mdag_path(camera_shape)
    camera_fn = maya.OpenMaya.MFnCamera(camera_dag_path)
    camera_pt = camera_fn.eyePoint(maya.OpenMaya.MSpace.kWorld)

    return [camera_pt.x, camera_pt.y, camera_pt.z]


def get_distance_to_camera(transform_node, camera_node):
    """
    Returns the distance between the given node (transform) and a camera
    :param transform_node: str, transform node to calculate distance to camera from
    :param camera_node: str, camera to calculate distance from
    :return: float
    """

    node.check_node(transform_node)
    transform.check_transform(node)
    node.check_node(camera_node)
    check_camera(camera_node)

    cam_pt = get_eye_point(camera_node)
    node_pt = maya.cmds.xform(transform_node, query=True, ws=True, rp=True)
    distance = mathutils.distance_between(cam_pt, node_pt)

    return distance
