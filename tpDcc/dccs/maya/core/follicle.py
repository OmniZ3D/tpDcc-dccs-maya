# #! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya Follicles
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import shape, geometry, constraint as constraint_utils, transform as transform_utils
from tpDcc.dccs.maya.core import mesh as mesh_utils


def create_empty_follicle(description, uv=None):
    """
    Creates a new empty follicle
    :param description: str, description of the follicle
    :param uv: list(int, int), uv where follicle will be created
    :return: str, name of the created follicle
    """

    uv = uv if uv is not None else [0, 0]
    follicle_shape = maya.cmds.createNode('follicle')
    maya.cmds.hide(follicle_shape)
    follicle = maya.cmds.listRelatives(follicle_shape, p=True)[0]
    maya.cmds.setAttr('{}.inheritsTransform'.format(follicle), False)
    if not description:
        follicle = maya.cmds.rename(follicle, tp.Dcc.find_unique_name('follicle_1'))
    else:
        follicle = maya.cmds.rename(follicle, tp.Dcc.find_unique_name('follicle_{}'.format(description)))

    maya.cmds.setAttr('{}.parameterU'.format(follicle), uv[0])
    maya.cmds.setAttr('{}.parameterV'.format(follicle), uv[1])

    return follicle


def create_mesh_follicle(mesh, description=None, uv=None):
    """
    Crates follicle on a mesh
    :param mesh: str, name of the mesh to attach follicle to
    :param description: str, description of the follicle
    :param uv: list(int, int,), corresponds to the UVs of the mesh in which the follicle will be attached
    :return: str, name of the created follicle
    """

    if uv is None:
        uv = [0, 0]

    follicle = create_empty_follicle(description, uv)
    shape = maya.cmds.listRelatives(follicle, shapes=True)[0]
    maya.cmds.connectAttr('{}.outMesh'.format(mesh), '{}.inputMesh'.format(follicle))
    maya.cmds.connectAttr('{}.worldMatrix'.format(mesh), '{}.inputWorldMatrix'.format(follicle))
    maya.cmds.connectAttr('{}.outTranslate'.format(shape), '{}.translate'.format(follicle))
    maya.cmds.connectAttr('{}.outRotate'.format(shape), '{}.rotate'.format(follicle))

    return follicle


def create_surface_follicle(surface, description=None, uv=None):
    """
    Crates follicle on a surface
    :param surface: str, name of the surface to attach follicle to
    :param description: str, description of the follicle
    :param uv: list(int, int,), corresponds to the UVs of the mesh in which the follicle will be attached
    :return: str, name of the created follicle
    """

    if uv is None:
        uv = [0, 0]

    follicle = create_empty_follicle(description, uv)
    shape = maya.cmds.listRelatives(follicle, shapes=True)[0]
    maya.cmds.connectAttr('{}.local'.format(surface), '{}.inputSurface'.format(follicle))
    maya.cmds.connectAttr('{}.worldMatrix'.format(surface), '{}.inputWorldMatrix'.format(follicle))
    maya.cmds.connectAttr('{}.outTranslate'.format(shape), '{}.translate'.format(follicle))
    maya.cmds.connectAttr('{}.outRotate'.format(shape), '{}.rotate'.format(follicle))

    return follicle


def follicle_to_mesh(transform, mesh, u=None, v=None, constraint=True, constraint_type='parentConstraint', local=False):
    """
    Uses a follicle to attach the transform to the mesh.
    If no U an V values are given, the command will try to find the closest position on the mesh
    :param transform: str, name of a transform to follicle to the mesh
    :param mesh: str, name of a mesh to attach follicle to
    :param u: float, U value to attach to
    :param v: float, V, value to attach to
    :param constraint: bool
    :param constraint_type: str
    :param local: bool
    :return: str, name of the follicle created
    """

    if not shape.is_a_shape(mesh):
        mesh = geometry.get_mesh_shape(mesh)

    position = maya.cmds.xform(transform, q=True, ws=True, t=True)
    uv = u, v
    if not u or not v:
        uv = mesh_utils.get_closest_uv_on_mesh(mesh, position)

    follicle = create_mesh_follicle(mesh, transform, uv)

    if constraint:
        if local:
            constraint_utils.constraint_local(follicle, transform, constraint=constraint_type)
        else:
            loc = maya.cmds.spaceLocator(n='locator_{}'.format(follicle))[0]
            maya.cmds.parent(loc, follicle)
            transform_utils.MatchTransform(transform, loc).translation_rotation()
            # cmds.parentConstraint(loc, transform, mo=True)
            eval('cmds.{}("{}", "{}", mo=True)'.format(constraint_type, loc, transform))
    else:
        maya.cmds.parent(transform, follicle)

    return follicle


def follicle_to_surface(transform, surface, u=None, v=None, constraint=False):
    """
    Uses a follicle to attach the transform to the surface
    If no U an V values are given, the command will try to find the closest position on the surface
    :param transform: str, str, name of a transform to follicle to the surface
    :param surface: str, name of a surface to attach follicle to
    :param u: float, U value to attach to
    :param v: float, V value to attach to
    :param constraint: bool
    :return: str, name of the follicle created
    """

    position = maya.cmds.xform(transform, q=True, ws=True, rp=True)
    uv = u, v
    if not u or not v:
        uv = geometry.get_closest_parameter_on_surface(surface, position)

    follicle = create_surface_follicle(surface, transform, uv)

    if constraint:
        loc = maya.cmds.spaceLocator(n='locator_{}'.format(follicle))[0]
        maya.cmds.parent(loc, follicle)
        transform_utils.MatchTransform(transform, loc).translation_rotation()
        maya.cmds.parentConstraint(loc, transform, mo=True)
    else:
        maya.cmds.parent(transform, follicle)

    return follicle
