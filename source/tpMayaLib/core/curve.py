# #! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya Curves
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya
from tpMayaLib.core import exceptions, api, transform, name as name_utils, shape as shape_utils


def check_curve(curve):
    """
    Checks if a node is a valid curve and raise and exception if the curve is not valid
    :param curve: str, name of the node to be checked
    :return: bool, True if the given node is a curve node or False otherwise
    """

    if not is_curve(curve):
        raise exceptions.CurveException(curve)


def is_a_curve(curve):
    """
    Returns whether given node is curve or has a shape that is a curve
    :param curve: str
    :return: bool
    """

    if maya.cmds.objExists('{}.cv[0]'.format(curve)) and not maya.cmds.objExists('{}.cv[0][0]'.format(curve)):
        return True

    return False


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


def transforms_to_curve(transforms, spans=None, description='from_transforms'):
    """
    Creates a curve from a list of transforms. Each transform will define a curve CV
    Useful when creating a curve from a joint chain (spines/tails)
    :param transforms: list<str>, list of tranfsorms to generate the curve from. Positions will be used to place CVs
    :param spans: int, number of spans the final curve should have
    :param description: str, description to given to the curve
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
    curve = maya.cmds.rename(curve, name_utils.find_unique_name('curve_{}'.format(description)))
    maya.cmds.setAttr('{}.inheritsTransform'.format(curve), False)

    return curve


def get_closest_position_on_curve(curve, value_list):
    """
    Returns closes position on a curve from given vector
    :param curve: str, name of a curve
    :param value_list: list(float, float, float)
    :return: list(float, float, float)
    """

    curve_shapes = shape_utils.get_shapes(curve)
    curve = curve_shapes[0] if curve_shapes else curve
    curve = api.NurbsCurveFunction(curve)

    return curve.get_closest_position(value_list)


def get_closest_parameter_on_curve(curve, value_list):
    """
    Returns the closest parameter value (UV) on the curve given a vector
    :param curve: str, name of a curve
    :param value_list: list(int, int, int), vector from which to search for closest parameter
    :return: float
    """

    curve_shapes = shape_utils.get_shapes(curve)
    curve = curve_shapes[0] if curve_shapes else curve
    curve = api.NurbsCurveFunction(curve)
    new_point = curve.get_closest_position(value_list)

    return curve.get_parameter_at_position(new_point)


def get_parameter_from_curve_length(curve, length_value):
    """
    Returns the parameter value (UV) given the length section of a curve
    :param curve: str, name of a curve
    :param length_value: float, length along a curve
    :return: float, parameter value at the length
    """

    curve_shapes = shape_utils.get_shapes(curve)
    curve = curve_shapes[0] if curve_shapes else curve
    curve = api.NurbsCurveFunction(curve)

    return curve.get_parameter_at_length(length_value)


def get_curve_length_from_parameter(curve, parameter_value):
    """
    Returns a curve length at given parameter UV
    :param curve: str
    :param parameter_value:
    :return:
    """

    arc_node = maya.cmds.arcLengthDimension('{}.u[{}]'.format(curve, parameter_value))
    length = maya.cmds.getAttr('{}.arcLength'.format(arc_node))
    parent = maya.cmds.listRelatives(arc_node, p=True)
    if parent:
        maya.cmds.delete(parent[0])

    return length


def get_point_from_curve_parameter(curve, parameter):
    """
    Returns a position on a curve by giving a parameter value
    :param curve: str, name of a curve
    :param parameter: float, parameter value a curve
    :return: list(float, float, float), vector found at the parameter of the curve
    """

    return maya.cmds.pointOnCurve(curve, pr=parameter, ch=False)


def get_curve_position_from_parameter(curve, parameter):
    """
    Returns a position on a curve by giving a parameter value
    :param curve: str, name of a curve
    :param parameter: float, parameter value a curve
    :return: list(float, float, float), vector found at the parameter of the curve
    """

    position = get_point_from_curve_parameter(curve, parameter)

    return position
