#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module include data class for components
"""

from __future__ import print_function, division, absolute_import, unicode_literals

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import exceptions, node, shape as shape_utils


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


def get_component_count_api(geometry):
    """
    Returns the number of individual components for the given geometry
    :param geometry: str, geometry to query
    :return: int
    """

    if not maya.cmds.objExists(geometry):
        raise exceptions.GeometryExistsException(geometry)

    geo_obj = node.get_mobject(geometry)
    if geo_obj.hasFn(maya.OpenMaya.MFn.kTransform):
        geometry = maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True)[0]

    geo_path = node.get_mdag_path(geometry)
    geo_it = maya.OpenMaya.MItGeometry(geo_path)

    return geo_it.count()


def get_component_count(transform):
    """
    Returns the number of components under a transform
    :param transform: str, name of the transform
    :return: int, number of components under given transform
    """

    components = get_components(transform)

    return len(maya.cmds.ls(components[0], flatten=True))


def get_components_from_shapes(shapes=None):
    """
    Returns the components from the list of shapes
    Only supports cv and vtx components
    :param shapes: list(str), list of shape names
    :return: list(list), components of the given shapes
    """

    components = list()
    if shapes:
        for shape in shapes:
            found_components = None
            if maya.cmds.nodeType(shape) == 'nurbsSurface' or maya.cmds.nodeType(shape) == 'nurbsCurve':
                found_components = '{}.cv[*]'.format(shape)
            elif maya.cmdsnodeType(shape) == 'mesh':
                found_components = '{}.vtx[*]'.format(shape)
            if found_components:
                components.append(found_components)

    return components


def get_components(transform):
    """
    Returns the name of the components under a transform
    :param transform: str, name of a transform
    :return: name of all components under a transforms
    """

    shapes = shape_utils.get_shapes(transform)
    return get_components_from_shapes(shapes)


def get_components_in_hierarchy(transform):
    """
    Returns all the components in the hierarchy
    This includes all transforms with shapes parented under the transform
    :param transform: str, name of a transform
    :return: list(list), name of all components under transform
    """

    shapes = shape_utils.get_shapes_in_hierarchy(transform)

    return get_components_from_shapes(shapes)
