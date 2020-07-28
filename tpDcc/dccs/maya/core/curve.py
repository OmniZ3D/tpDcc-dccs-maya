# #! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya Curves
"""

from __future__ import print_function, division, absolute_import

import tpDcc.dccs.maya as maya
from tpDcc.libs.python import mathlib
from tpDcc.dccs.maya.core import exceptions, api, transform, decorators, name as name_utils, shape as shape_utils


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
    crv = maya.cmds.rename(crv, prefix + '_crv')

    if degree > 1:
        crv = maya.cmds.rebuildCurve(crv, d=degree, kcp=True, kr=0, ch=False, rpo=True)[0]

    return crv


def transforms_to_curve(transforms, spans=None, name='from_transforms'):
    """
    Creates a curve from a list of transforms. Each transform will define a curve CV
    Useful when creating a curve from a joint chain (spines/tails)
    :param transforms: list<str>, list of tranfsorms to generate the curve from. Positions will be used to place CVs
    :param spans: int, number of spans the final curve should have
    :param name: str, name for the curve
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
        maya.cmds.rebuildCurve(
            curve, ch=False, rpo=True, rt=0, end=1, kr=False, kcp=False, kep=True,
            kt=False, spans=spans, degree=3, tol=0.01)
    curve = maya.cmds.rename(curve, name_utils.find_unique_name(name))
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


def rebuild_curve(curve, spans=-1, degree=3):
    """
    Rebuilds a curve with given parameters (simplified version)
    :param curve: str, name of the curve to rebuild
    :param spans: int
    :param degree: int
    :return: str
    """

    if spans == -1:
        spans = maya.cmds.getAttr('{}.spans'.format(curve))

    curve = maya.cmds.rebuildCurve(curve, ch=False, rpo=True, rt=False, end=True, kr=False,
                                   kcp=False, kep=True, kt=False, s=spans, d=degree, tol=0.01)

    return curve


def rebulid_curve_at_distance(curve, min_length, max_length, min_spans=3, max_spans=10):
    curve_length = maya.cmds.arcLen(curve, ch=False)
    spans = mathlib.remap_value(curve_length, min_length, max_length, min_spans, max_spans)

    return rebuild_curve(curve, spans=spans, degree=3)


def evenly_position_curve_cvs(curve):
    """
    Given a curve, all its CVs will be evenly position along the given curve
    :param curve: str, name of the curve to evenly its CVs
    :return: str
    """

    cvs = maya.cmds.ls('{}.cv[*}'.format(curve), flatten=True)

    return snap_transforms_to_curve(cvs, curve)


def snap_transforms_to_curve(transforms, curve):
    """
    Snaps the given transforms to the nearest position on the curve
    :param transforms: list(str)
    :param curve: str
    """

    count = len(transforms)
    total_length = maya.cmds.arclen(curve)
    part_length = total_length / (count - 1)
    current_length = 0.0
    if count - 1 == 0:
        part_length = 0
    temp_curve = maya.cmds.duplicate(curve)[0]

    for i in range(0, count):
        param = get_parameter_from_curve_length(temp_curve, current_length)
        pos = get_point_from_curve_parameter(temp_curve, param)
        xform = transforms[i]
        if maya.cmds.nodeType(xform) == 'joint':
            maya.cmds.move(
                pos[0], pos[1], pos[2], '{}.scalePivot'.format(xform), '{}.rotatePivot'.format(xform), a=True)
        else:
            maya.cmds.xform(xform, ws=True, t=pos)

        current_length += part_length

    maya.cmds.delete(temp_curve)


@decorators.undo_chunk
def snap_joints_to_curve(joints, curve=None, count=10):
    """
    Snap given joitns to the given curve
    If the given count is greater than the number of joints, new joints will be added to the curve
    :param joints: list(str(, list of joints to snap to curve
    :param curve: str, name of a curve. If no curve given a simple curve will be created based on the joints
    :param count: int, number of joints, if the joints list does not have the same number joints,
        new ones wil be created
    :return: list(str)
    """

    if not joints:
        return

    # List that will contains temporary objects that will be removed when the snapping process is over
    delete_after = list()

    if not curve:
        curve = transforms_to_curve(joints, spans=count, description='temp')
        delete_after.append(curve)

    joint_count = len(joints)
    if joint_count < count and count:
        missing_count = count - joint_count
        for i in range(missing_count):
            new_jnt = maya.cmds.duplicate(joints[-1])[0]
            new_jnt = maya.cmds.rename(new_jnt, name_utils.find_unique_name(joints[-1]))
            maya.cmds.parent(new_jnt, joints[-1])
            joints.append(new_jnt)
    joint_count = len(joints)
    if not joint_count:
        return

    if count == 0:
        count = joint_count

    total_length = maya.cmds.arclen(curve)
    part_length = total_length / (count - 1)
    current_length = 0.0
    if count - 1 == 0:
        part_length = 0

    for i in range(count):
        param = get_parameter_from_curve_length(curve, current_length)
        pos = get_point_from_curve_parameter(curve, param)
        maya.cmds.move(
            pos[0], pos[1], pos[2], '{}.scalePivot'.format(joints[i]), '{}.rotatePivot'.format(joints[i], a=True))
        current_length += part_length

    if delete_after:
        maya.cmds.delete(delete_after)


def attach_to_curve(transform, curve, maintain_offset=False, parameter=None):
    """
    Attaches the transform to the given curve using a point on curve
    :param transform: str, name of transform to attach to curve
    :param curve: str, name of curve
    :param maintain_offset: bool, Whether to attach to transform and maintain its offset from the curve
    :param parameter: float, parameter on the curve where the transform should attach
    :return: str, name of the pointOnCurveInfo node
    """

    position = maya.cmds.xform(transform, query=True, ws=True, rp=True)
    if not parameter:
        parameter = get_closest_parameter_on_curve(curve, position)

    curve_info_node = maya.cmds.pointOnCurve(curve, pr=parameter, ch=True)

    if maintain_offset:
        plus_node = maya.cmds.createNode('plusMinusAverage', n='{}_subtract_offset'.format(transform))
        maya.cmds.setAttr('{}.operation'.format(plus_node), 1)
        for axis in 'XYZ':
            value = maya.cmds.getAttr('{}.position{}'.format(curve_info_node, axis))
            value_orig = maya.cmds.getAttr('{}.translate{}'.format(transform, axis))
            maya.cmds.connectAttr('{}.position{}'.format(curve_info_node, axis), '{}.input3D[0].input3D{}'.format(
                plus_node, axis.lower()))
            maya.cmds.setAttr('{}.input3D[1].input3D{}'.format(plus_node, axis.lower()), -value)
            maya.cmds.setAttr('{}.input3D[2].input3D{}'.format(plus_node, axis.lower()), value_orig)
            maya.cmds.connectAttr(
                '{}.output3D{}'.format(plus_node, axis.lower()), '{}.translate{}'.format(transform, axis))
    else:
        for axis in 'XYZ':
            maya.cmds.connectAttr(
                '{}.position{}'.format(curve_info_node, axis), '{}.translate{}'.format(transform, axis))

    return curve_info_node


def snap_curve_to_surface(curve, surface, offset=1, project=False):
    """
    Snaps curves CVs on given surface
    :param curve: str, name of the curve to snap onto surface
    :param surface: str, name of surface curve wil be snapped to
    :param offset: int, offset between curve and surface
    :param project: bool, Whether to snap or snap and project the curve into the surface
    """

    from tpDcc.dccs.maya.core import mesh

    center = maya.cmds.xform(curve, query=True, ws=True, rp=True)
    shapes = shape_utils.get_shapes(curve)
    for shape in shapes:
        cvs = maya.cmds.ls('{}.cv[*]'.format(shape), flatten=True)
        for cv in cvs:
            pos = maya.cmds.xform(cv, query=True, ws=True, t=True)
            if mesh.is_a_mesh(surface):
                mesh_fn = api.MeshFunction(surface)
                if project:
                    closest_point = mesh_fn.get_closest_intersection(pos, center)
                else:
                    closest_point = mesh_fn.get_closest_position(pos)
                maya.cmds.xform(cv, ws=True, t=closest_point)
        maya.cmds.scale(offset, offset, offset, cvs, r=True)


def snap_project_curve_to_surface(curve, surface, offset=1):
    """
    Projects curves CVs on given surface
   :param curve: str, name of the curve to snap onto surface
    :param surface: str, name of surface curve wil be snapped to
    :param offset: int, offset between curve and surface
    """

    return snap_curve_to_surface(curve=curve, surface=surface, offset=offset, project=True)


def curve_to_nurbs_surface(curve, description, spans=-1, offset_axis='X', offset_amount=1):
    """
    Creates a new NURBS surface given a curve
    :param curve: str
    :param description: str
    :param spans: int
    :param offset_axis: str
    :param offset_amount: float
    :return: str, newly created NURBS surface
    """

    curve1 = maya.cmds.duplicate(curve)[0]
    curve2 = maya.cmds.duplicate(curve)[0]
    offset_axis = offset_axis.upper()
    pos_move = mathlib.get_axis_vector(offset_axis, offset_amount)
    neg_move = mathlib.get_axis_vector(offset_axis, offset_amount * -1)
    maya.cmds.move(pos_move[0], pos_move[1], pos_move[2], curve1)
    maya.cmds.move(neg_move[0], neg_move[1], neg_move[2], curve2)
    curves = [curve1, curve2]

    if not spans == -1:
        for curve in curves:
            maya.cmds.rebuildCurve(
                curve, ch=False, rpo=True, rt=0, end=1, kr=False,
                kcp=False, kep=True, kt=False, spans=spans, degree=3, tol=0.01)

    loft = maya.cmds.loft(
        curve1, curve2, n=name_utils.find_unique_name('nurbsSurface_{}'.forat(description)), ss=1, degree=1, ch=False)
    spans = maya.cmds.getAttr('{}.spans'.format(curve1))
    maya.cmds.rebuildSurface(
        loft, ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kc=0, su=1, du=1, sv=spans, dv=3, tol=0.01, fr=0, dir=2)
    maya.cmds.delete(curve1, curve2)

    return loft[0]
