#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya API curve nodes
"""

from __future__ import print_function, division, absolute_import

from copy import copy
from collections import OrderedDict

import maya.cmds
import maya.api.OpenMaya

from tpDcc.libs.python import python
from tpDcc.dccs.maya import api
from tpDcc.dccs.maya.api import plugs, node as node_api

SHAPE_INFO = {
    'cvs': (),
    'degree': 3,
    'form': 1,
    'knots': (),
    'matrix': (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    'outlinerColor': (0.0, 0.0, 0.0),
    'overrideColorRGB': (0.0, 0.0, 0.0),
    'overrideEnabled': False,
    'overrideRGBColors': False,
    'useOutlinerColor': False
}


class CurveCV(list):
    """
    Base class used to represent curve CVs
    """

    def ControlVWrapper(self):
        def wrapper(*args, **kwargs):
            f = self(*[a if isinstance(a, CurveCV) else CurveCV([a, a, a]) for a in args], **kwargs)
            return f
        return wrapper

    @ControlVWrapper
    def __mul__(self, other):
        return CurveCV([self[i] * other[i] for i in range(3)])

    @ControlVWrapper
    def __sub__(self, other):
        return CurveCV([self[i] - other[i] for i in range(3)])

    @ControlVWrapper
    def __add__(self, other):
        return CurveCV([self[i] + other[i] for i in range(3)])

    def __imul__(self, other):
        return self * other

    def __rmul__(self, other):
        return self * other

    def __isub__(self, other):
        return self - other

    def __rsub__(self, other):
        return self - other

    def __iadd__(self, other):
        return self + other

    def __radd__(self, other):
        return self + other

    @staticmethod
    def mirror_vector():
        return {
            None: CurveCV([1, 1, 1]),
            'None': CurveCV([1, 1, 1]),
            'XY': CurveCV([1, 1, -1]),
            'YZ': CurveCV([-1, 1, 1]),
            'ZX': CurveCV([1, -1, 1])
        }

    def reorder(self, order):
        """
        With a given order sequence CVs will be reordered (for axis order purposes)
        :param order: list(int)
        """

        return CurveCV([self[i] for i in order])


def get_curve_data(curve_shape, space=None, color_data=True, parent=None):
    """
    Returns curve dat from the given shape node
    :param curve_shape: str, node that represents nurbs curve shape
    :param space: MSpace, coordinate space to query the point data
    :param color_data: bool
    :param parent:
    :return: dict
    """

    if python.is_string(curve_shape):
        curve_shape = node_api.as_mobject(curve_shape)
    if parent and python.is_string(parent):
        parent = node_api.as_mobject(parent)

    space = space or maya.api.OpenMaya.MSpace.kObject
    shape = maya.api.OpenMaya.MFnDagNode(curve_shape).getPath()
    data = node_api.get_node_color_data(shape.node()) if color_data else dict()
    curve = maya.api.OpenMaya.MFnNurbsCurve(shape)
    if parent:
        parent = maya.api.OpenMaya.MFnDagNode(parent).getPath().partialPathName()

    curve_knots = tuple(curve.knots())
    curve_degree = int(curve.degree)
    curve_form = int(curve.form)
    curve_matrix = tuple(node_api.get_world_matrix(curve.object()))
    curve_cvs = map(tuple, curve.cvPositions(space))
    curve_cvs = [cv[:-1] for cv in curve_cvs]       # OpenMaya returns 4 elements in the cvs, ignore last one

    data.update({
        'knots': curve_knots,
        'cvs': curve_cvs,
        'degree': curve_degree,
        'form': curve_form,
        'matrix': curve_matrix,
        'shape_parent': parent
    })

    return data


def serialize_transform_curve(node, space=None, color_data=True):
    """
    Serializes given transform shapes curve data and returns a dictionary with that data
    :param node: MObject, object that represents the transform above the nurbsCurve shapes we want to serialize
    :param space: MSpace, coordinate space to query the point data
    :param color_data: bool, Whether to include or not color curve related data
    :return: dict
    """

    space = space or maya.api.OpenMaya.MSpace.kObject
    shapes = node_api.get_shapes(
        maya.api.OpenMaya.MDagPath(node).getPath(), filter_types=maya.api.OpenMaya.MFn.kNurbsCurve)
    data = dict()
    for shape in shapes:
        shape_dag = api.DagNode(shape.node())
        is_intermediate = shape_dag.is_intermediate_object()
        if not is_intermediate:
            data[maya.api.OpenMaya.MNamespace.stripNamespaceFromName(
                shape_dag.get_name())] = get_curve_data(shape, space, color_data=color_data)

    return data


def iterate_curve_points(dag_path, count, space=None):
    """
    Generator function that iterates given DAG path pointing a curve shape node, containing the position, normal and
    tangent for the curve in the given point count
    :param dag_path: MDagPath, dagPat to the curve shape node
    :param count: int, point count to generate
    :param space: MSpace, coordinate space to query the point data
    :return: tuple(MVector, MVector, MVector), position, normal and tangent of the curve points
    """

    space = space or maya.api.OpenMaya.MSpace.kObject
    curve_fn = api.NurbsCurveFunction(dag_path)
    length = curve_fn.get_length()
    distance = length / float(count - 1)
    current = 0.001
    default_normal = [1.0, 0.0, 0.0]
    default_tangent = [0.0, 1.0, 0.0]
    max_param = curve_fn.get_parameter_at_length(length)
    for i in range(count):
        param = curve_fn.get_parameter_at_length(current)
        if param == max_param:
            param = max_param - 0.0001
        point = maya.api.OpenMaya.MVector(curve_fn.get_position_at_parameter(param, space=space))
        try:
            yield point, curve_fn.get_normal(param), curve_fn.get_tangent(param)
        except RuntimeError:
            # In flat curves (Y pointing completely up), exception is raised and normal is [1.0, 0.0, 0.0} and tangent
            # is [0.0, 1.0, 0.0
            yield point, default_normal, default_tangent
        current += distance


def mirror_curve_cvs(curve_obj, axis='x', space=None):
    """
    Mirrors the given curev transform shape CVs by the given axis
    :param curve_obj: MObject, curves transform to mirror
    :param axis: str, axis to mirror ('x', 'y' or 'z')
    :param space: int, space to mirror (MSpace.kObject, MSpace.kWorld)
    :return:
    """

    space = space or maya.api.OpenMaya.MSpace.kObject
    axis = axis.lower()
    axis_dict = {'x': 0, 'y': 1, 'z': 2}
    axis_to_mirror = set(axis_dict[ax] for ax in axis)

    for shape in node_api.iterate_shapes(maya.api.OpenMaya.MFnDagNode(curve_obj).getPath()):
        curve = maya.api.OpenMaya.MFnNurbsCurve(shape)
        cvs = curve.cvPositions(space)
        for i in cvs:
            for ax in axis_to_mirror:
                i[ax] *= -1
        curve.setCVPositions(cvs)
        curve.updateCurve()


def match_curves(driver, targets, space=None):
    """
    Matches the curves from the driver to the targets
    :param driver: MObject, transform node of the shape to match
    :param targets: list(MObject) or tuple(MObject), list of transforms that will have the shapes replaced
    :param space: MSpace, coordinate space to query the point data
    :return: list(MObject)
    """

    space = space or maya.api.OpenMaya.MSpace.kObject
    driver_data = serialize_transform_curve(driver, space=space)
    shapes = list()
    for target in targets:
        target_shapes = [node_api.name_from_mobject(i.node()) for i in node_api.iterate_shapes(
            maya.api.OpenMaya.MDagPath.getAPathTo(target))]
        if target_shapes:
            maya.cmds.delete(target_shapes)
        shapes.extend(create_curve_shape(target, driver_data, space=space)[1])

    return shapes


def create_curve_shape(
        curve_data, parent=None, space=None, curve_size=1.0, translate_offset=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0), axis_order='XYZ', color=None, mirror=None):
    """
    Creates a NURBS curve based on the given curve data
    :param curve_data: dict, data, {"shapeName": {"cvs": [], "knots":[], "degree": int, "form": int, "matrix": []}}
    :param parent: MObject, transform that takes ownership of the curve shapes. If not parent is given a new transform
    will be created
    :param space: MSpace, coordinate space to set the point data
    :return: tuple(MObject, list(MObject)), tuple containing the parent MObject and the list of MObject shapes
    """

    parent_inverse_matrix = api.Matrix()
    if parent is None:
        parent = maya.api.OpenMaya.MObject.kNullObj
    else:
        if python.is_string(parent):
            parent = node_api.as_mobject(parent)
        if parent != maya.api.OpenMaya.MObject.kNullObj:
            parent_inverse_matrix = node_api.get_world_inverse_matrix(parent)

    translate_offset = CurveCV(translate_offset)
    scale = CurveCV(scale)
    order = [{'X': 0, 'Y': 1, 'Z': 2}[x] for x in axis_order]

    curves_to_create = OrderedDict()
    for shape_name, shape_data in curve_data.items():
        if not isinstance(shape_data, dict):
            continue
        curves_to_create[shape_name] = list()
        shape_parent = shape_data.get('shape_parent', None)
        if shape_parent:
            if shape_parent in curves_to_create:
                curves_to_create[shape_parent].append(shape_name)

    created_curves = list()
    all_shapes = list()
    created_parents = dict()

    # If parent already has a shape with the same name we delete it
    # TODO: We should compare the bounding boxes of the parent shape and the new one and scale it to fit new bounding
    # TODO: box to the old one
    parent_shapes = list()
    if parent and parent != maya.api.OpenMaya.MObject.kNullObj:
        parent_shapes = node_api.get_shapes(maya.api.OpenMaya.MFnDagNode(parent).getPath())

    for shape_name, shape_children in curves_to_create.items():

        for parent_shape in parent_shapes:
            if parent_shape.partialPathName() == shape_name:
                if not node_api.is_valid_mobject(parent_shape.node()):
                    continue
                maya.cmds.delete(parent_shape.fullPathName())
                break

        if shape_name not in created_curves:
            shape_name, parent, new_shapes, new_curve = _create_curve(
                shape_name, curve_data[shape_name], space, curve_size, translate_offset, scale, order, color,
                mirror, parent, parent_inverse_matrix)
            created_curves.append(shape_name)
            all_shapes.extend(new_shapes)
            created_parents[shape_name] = parent

        for child_name in shape_children:
            if child_name not in created_curves:
                to_parent = created_parents[shape_name] if shape_name in created_parents else parent
                child_name, child_parent, new_shapes, new_curve = _create_curve(
                    child_name, curve_data[child_name], space, curve_size, translate_offset, scale, order, color,
                    mirror, maya.api.OpenMaya.MObject.kNullObj, parent_inverse_matrix)
                created_curves.append(child_name)
                all_shapes.extend(new_shapes)
                created_parents[child_name] = child_parent
                node_api.set_parent(new_curve.parent(0), to_parent)

    return parent, all_shapes


def create_curve_from_points(name, points, shape_dict=None, parent=None):
    """
    Creates a new curve from the given points and the given data curve info
    :param name: str
    :param points: list(MPoint)
    :param shape_dict: dict
    :param parent: MObject
    :return:
    """

    shape_dict = shape_dict or SHAPE_INFO

    name = '{}Shape'.format(name)
    degree = 3
    total_cvs = len(points)
    # append two zeros to the front of the knot count so it lines up with maya specs
    # (ncvs - deg) + 2 * deg - 1
    knots = [0, 0] + range(total_cvs)
    # remap the last two indices to match the third from last
    knots[-1] = knots[len(knots) - degree]
    knots[-2] = knots[len(knots) - degree]

    shape_dict['cvs'] = points
    shape_dict['knots'] = knots

    return create_curve_shape({name: shape_dict}, parent)


def _create_curve(
        shape_name, shape_data, space, curve_size, translate_offset, scale, order, color, mirror,
        parent, parent_inverse_matrix):
    new_curve = maya.api.OpenMaya.MFnNurbsCurve()
    new_shapes = list()

    # transform cvs
    curve_cvs = shape_data['cvs']
    transformed_cvs = list()
    cvs = [CurveCV(pt) for pt in copy(curve_cvs)]
    for i, cv in enumerate(cvs):
        cv *= curve_size * scale.reorder(order)
        cv += translate_offset.reorder(order)
        cv *= CurveCV.mirror_vector()[mirror]
        cv = cv.reorder(order)
        transformed_cvs.append(cv)

    cvs = api.PointArray()
    cvs.set(transformed_cvs)
    degree = shape_data['degree']
    form = shape_data['form']
    knots = shape_data.get('knots', None)
    if not knots:
        knots = tuple([float(i) for i in range(-degree + 1, cvs.length())])

    enabled = shape_data.get('overrideEnabled', False) or color is not None
    if space == maya.api.OpenMaya.MSpace.kWorld and parent != maya.api.OpenMaya.MObject.kNullObj:
        for i in range(len(cvs._obj)):
            cvs._obj[i] *= parent_inverse_matrix
    shape = new_curve.create(cvs._obj, knots, degree, form, False, False, parent)
    node_api.rename_mobject(shape, shape_name)
    new_shapes.append(shape)
    if parent == maya.api.OpenMaya.MObject.kNullObj and shape.apiType() == maya.api.OpenMaya.MFn.kTransform:
        parent = shape
    if enabled:
        plugs.set_plug_value(
            new_curve.findPlug('overrideEnabled', False), int(shape_data.get('overrideEnabled', bool(color))))
        colors = color or shape_data['overrideColorRGB']
        outliner_color = shape_data.get('outlinerColor', None)
        use_outliner_color = shape_data.get('useOutlinerColor', False)
        node_api.set_node_color(
            new_curve.object(), colors, outliner_color=outliner_color, use_outliner_color=use_outliner_color)

    return shape_name, parent, new_shapes, new_curve
