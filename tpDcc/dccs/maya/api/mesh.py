#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya meshes
"""

from __future__ import print_function, division, absolute_import

import tpDcc.dccs.maya as maya


def get_mesh_path_and_components(mesh_name):
    """
    Returns mesh path and components of the given mesh name
    :param mesh_name: str
    :return: MDagPath, MObject
    """

    if maya.is_new_api():
        selection_list = maya.OpenMaya.MGlobal.getSelectionListByName('{}.vtx[*]'.format(mesh_name))
        mesh_path, mesh_components = selection_list.getComponent(0)
    else:
        selection_list = maya.OpenMaya.MSelectionList()
        maya.OpenMaya.MGlobal.getSelectionListByName('{}.vtx[*]'.format(mesh_name), selection_list)
        mesh_path = maya.OpenMaya.MDagPath()
        mesh_components = maya.OpenMaya.MObject()
        selection_list.getDagPath(0, mesh_path, mesh_components)

    return mesh_path, mesh_components
