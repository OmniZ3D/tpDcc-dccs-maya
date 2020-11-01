#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya meshes
"""

from __future__ import print_function, division, absolute_import

import maya.api.OpenMaya


def get_mesh_path_and_components(mesh_name):
    """
    Returns mesh path and components of the given mesh name
    :param mesh_name: str
    :return: MDagPath, MObject
    """

    selection_list = maya.api.OpenMaya.MGlobal.getSelectionListByName('{}.vtx[*]'.format(mesh_name))
    mesh_path, mesh_components = selection_list.getComponent(0)

    return mesh_path, mesh_components
