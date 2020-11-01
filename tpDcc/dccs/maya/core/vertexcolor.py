#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with vertex colors and color sets
"""

from __future__ import print_function, division, absolute_import

import maya.cmds

from tpDcc.libs.python import python
from tpDcc.dccs.maya import api
from tpDcc.dccs.maya.core import node


def get_mesh_vertex_colors(mesh):
    """
    Returns vertex colors applied to given mesh
    :param mesh:, str mesh shape node we want to check for vertex colors
    :return: bool
    """

    mesh_node = node.get_mobject(mesh)
    mesh_vertex_it = api.IterateVertices(mesh_node)

    return mesh_vertex_it.has_vertex_colors()


def set_mesh_vertex_color(mesh, rgb=[1, 0, 0], flip_color=False):
    """
    Sets the vertex color of the given geometry
    :param mesh: str
    :param rgb: list
    :param flip_color: bool
    :return:
    """

    rgb = python.force_list(rgb)
    if not rgb:
        return

    copy_rgb = rgb[:]

    if flip_color:
        copy_rgb[0] = copy_rgb[0] * (1 - copy_rgb[0] * 0.5)
        copy_rgb[1] = copy_rgb[1] * (1 - copy_rgb[1] * 0.5)
        copy_rgb[2] = copy_rgb[2] * (1 - copy_rgb[2] * 0.5)

    maya.cmds.polyColorPerVertex(mesh, colorRGB=rgb, colorDisplayOption=True)

    return copy_rgb


def check_all_mesh_vertices_has_vertex_colors(mesh):
    """
    Returns whether or not all vertices of the given mesh have vertex colors applied
    :param mesh: str, str mesh shape node we want to check for vertex colors
    :return: bool
    """

    mesh_node = node.get_mobject(mesh)
    mesh_vertex_it = api.IterateVertices(mesh_node)

    mesh_vertex_colors = mesh_vertex_it.get_vertex_colors(skip_vertices_without_vertex_colors=False)
    return None in mesh_vertex_colors.values()
