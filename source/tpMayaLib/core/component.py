#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module include data class for components
"""

from __future__ import print_function, division, absolute_import, unicode_literals

import tpMayaLib as maya
from tpMayaLib.core import exceptions


component_filter = [28, 30, 31, 32, 34, 35, 36, 37, 38, 46, 47]

mesh_filter = [31, 32, 34, 35]
subd_filter = [36, 37, 38]
nurbs_filter = [28, 30]
curve_filter = [28, 30, 40]
surface_filter = [28, 30, 42]

mesh_vert_filter = 31
mesh_edge_filter = 32
mesh_face_filter = 34

lattice_filter = 46
particle_filter = 47


def is_component(component):
    """
    Returns True if the given object is a valid component
    :param component: str, object t otest as component
    :return: bool
    """

    return bool(maya.cmds.filterExpand(component, ex=True, sm=component_filter))


def get_component_count(geometry):
    """
    Returns the number of individual components for the given geometry
    :param geometry: str, geometry to query
    :return: int
    """

    from tpMayaLib.core import node

    if not maya.cmds.objExists(geometry):
        raise exceptions.GeometryExistsException(geometry)

    geo_obj = node.get_mobject(geometry)
    if geo_obj.hasFn(maya.OpenMaya.MFn.kTransform):
        geo_shape = maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True)[0]

    geo_path = node.get_mdag_path(geometry)
    geo_it = maya.OpenMaya.MItGeometry(geo_path)

    return geo_it.count()
