# #! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya Curves
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya
from tpMayaLib.core import exceptions, transform, name as name_utils


def check_curve(curve):
    """
    Checks if a node is a valid curve and raise and exception if the curve is not valid
    :param curve: str, name of the node to be checked
    :return: bool, True if the given node is a curve node or False otherwise
    """

    if not is_curve(curve):
        raise exceptions.CurveException(curve)


def is_curve(curve):
    """
    Checks if the given object is a curve or transform parent of a curve
    :param curve: str, object to query
    :return: bool, True if the given object is a valid curve or False otherwise
    """

    if not maya.cmds.objExists(curve):
        return False

    if maya.cmds.objectType(curve) == 'transform':
        curve = maya.cmds.listRelatives(curve, shapes=True, noIntermediate=True, pa=True)
    if maya.cmds.objectType(curve) != 'nurbsCurve' and maya.cmds.objectType(curve) != 'bezierCurve':
        return False

    return True


def get_curve_fn(curve):
    """
    Creates an MFnNurbsCurve class object from the specified NURBS curve
    :param curve: str, curve to create function class for
    :return: MFnNurbsCurve function class initialized with the given curve object
    """

    check_curve(curve)

    if maya.cmds.objectType(curve) == 'transform':
        curve = maya.cmds.listRelatives(curve, shapes=True, noIntermediate=True)[0]

    if maya.is_new_api():
        curve_sel = maya.OpenMaya.getSelectionListByName(curve)
        curve_path = curve_sel.getDagPath(0)
    else:
        curve_sel = maya.OpenMaya.MSelectionList()
        maya.OpenMaya.MGlobal.getSelectionListByName(curve, curve_sel)
        curve_path = maya.OpenMaya.MDagPath()
        curve_sel.getDagPath(0, curve_path)
    curve_fn = maya.OpenMaya.MFnNurbsCurve(curve_path)

    return curve_fn


def create_from_point_list(point_list, degree=3, prefix=''):
    """
    Build a NURBS curve from a list of world positions
    :param point_list:  list<int>, list of CV world positions
    :param degree: int, degree of the curve to create
    :param prefix: str, name prefix for newly created curves
    :return: name of the new created curve
    """

    cv_list = [transform.get_position(i) for i in point_list]

    crv = maya.cmds.curve(p=cv_list, k=range(len(cv_list)), d=1)
    crv = maya.cmds.rename(crv, prefix+'_crv')

    if degree > 1:
        crv = maya.cmds.rebuildCurve(crv, d=degree, kcp=True, kr=0, ch=False, rpo=True)[0]

    return crv


def transforms_to_curve(transforms, curve_name, spans=None):
    """
    Creates a curve from a list of transforms. Each transform will define a curve CV
    Useful when creating a curve from a joint chain (spines/tails)
    :param transforms: list<str>, list of tranfsorms to generate the curve from. Positions will be used to place CVs
    :param spans: int, number of spans the final curve should have
    :param curve_name: str, name the new curve should have
    :return: str name of the new curve
    """

    if not transforms:
        maya.logger.warning('Impossible to create curve from transforms because no transforms given!')
        return None

    transform_positions = list()
    for xform in transforms:
        xform_pos = maya.cmds.xform(xform, q=True, ws=True, rp=True)
        transform_positions.append(xform_pos)

    curve = maya.cmds.curve(p=transform_positions, degree=1)
    if spans:
        maya.cmds.rebuildCurve(curve, ch=False, rpo=True, rt=0, end=1, kr=False, kcp=False, kep=True, kt=False, spans=spans, degree=3, tol=0.01)
    curve = maya.cmds.rename(curve, name_utils.find_unique_name(curve_name))
    maya.cmds.setAttr('{}.inheritsTransform'.format(curve), False)

    return curve
