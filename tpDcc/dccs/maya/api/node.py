#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya API nodes
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.python import python
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya import api
from tpDcc.dccs.maya.api import plugs, exceptions


def as_mobject(name):
    """
    Returns the MObject from the given name
    :param name: str, node name of Maya to retrieve MObject of
    :return: MObject
    """

    sel = api.SelectionList()
    try:
        sel.add(name)
    except RuntimeError:
        raise exceptions.MissingObjectByName(name)
    try:
        return sel.get_dag_path(0).node()
    except TypeError:
        return sel.get_depend_node(0)


def name_from_mobject(mobj, partial_name=False, include_namespace=True):
    """
    Returns full or partial name for a given MObject (which must be valid)
    :param mobj: MObject, Maya object we want to retrieve name of
    :param partial_name: bool, Whether to return full path or partial name of the Maya object
    :param include_namespace: bool, Whether or not object namespace should be included in the path or stripped
    :return: str, name of the Maya object
    """

    if mobj.hasFn(maya.OpenMaya.MFn.kDagNode):
        dag_node = api.DagNode(mobj)
        node_name = dag_node.get_partial_path() if partial_name else dag_node.get_full_path()
    else:
        node_name = api.DependencyNode(mobj).get_name()

    if not include_namespace:
        node_name = maya.OpenMaya.MNamespace.stripNamespaceFromName(node_name)

    return node_name


def names_from_mobject_handles(mobjs_list):
    """
    Returns names of the given list of MObjectHandles
    :param mobjs_list: list(MObjectHandle)
    :return: list(str)
    """

    names_list = list()
    for mobj in mobjs_list:
        object_handle = maya.OpenMaya.MObjectHandle(mobj)
        if not object_handle.isValid() or not object_handle.isAlive():
            continue
        names_list.append(name_from_mobject(object_handle.object()))

    return names_list


def rename_mobject(mobj, new_name):
    """
    Renames given MObject dependency node with the new given name
    :param mobj: MObject
    :param new_name: str
    :return:
    """

    dag_mod = maya.OpenMaya.MDagModifier()
    dag_mod.renameNode(mobj, new_name)
    dag_mod.doIt()

    return mobj


def get_world_matrix_plug(mobj):
    """
    Returns the MPlug pointing worldMatrix of the given MObject pointing a DAG node
    :param mobj: MObject
    :return: MPlug
    """

    world_matrix = maya.OpenMaya.MFnDependencyNode(mobj).findPlug('worldMatrix', False)
    return world_matrix.elementByLogicalIndex(0)


def get_world_matrix(mobj):
    """
    Returns world matrix of the given MObject pointing to DAG node
    :param mobj: MObject
    :return: MMatrix
    """

    return plugs.get_plug_value(get_world_matrix_plug(mobj))


def get_world_inverse_matrix(mobj):
    """
    Returns world inverts matrix of the given Maya object
    :param mobj: MObject, Maya object we want to retrieve world inverse matrix of
    :return: MMatrix
    """

    inverse_matrix_plug = api.DependencyNode(mobj).find_plug('worldInverseMatrix', want_networked_plug=False)
    inverse_matrix_plug.evaluateNumElements()
    matrix_plug = inverse_matrix_plug.elementByPhysicalIndex(0)

    return plugs.get_plug_value(matrix_plug)


def get_parent_matrix(mobj):
    """
    Returns the parent matrix of the given Maya object
    :param mobj: MObject
    :return: MMatrix
    """

    parent_matrix_plug = api.DependencyNode(mobj).find_plug('parentMatrix', want_networked_plug=False)
    parent_matrix_plug.evaluateNumElements()
    matrix_plug = parent_matrix_plug.elementByPhysicalIndex(0)

    return plugs.get_plug_value(matrix_plug)


def get_parent_inverse_matrix_plug(mobj):
    """
    Returns parent inverse matrix MPlug of the given Maya object
    :param mobj: MObject
    :return: MPlug
    """

    parent_inverse_matrix_plug = api.DependencyNode(mobj).find_plug('parentInverseMatrix', want_networked_plug=False)
    return parent_inverse_matrix_plug.elementByLogicalIndex(0)


def get_parent_inverse_matrix(mobj):
    """
    Returns the parent inverse matrix of the given Maya object
    :param mobj: MObject
    :return: MMatrix
    """

    parent_inverse_matrix_plug = get_parent_inverse_matrix_plug(mobj)
    return plugs.get_plug_value(parent_inverse_matrix_plug)


def decompose_transform_matrix(matrix, rotation_order, space=None):
    """
    Returns decomposed translation, rotation and scale of the given Maya Matrix
    :param matrix: MMatrix, maya transforms matrix to decompose
    :param rotation_order:
    :param space: MSpace, coordinate space to decompose matrix of
    :return: tuple(MVector, MVector, MVector)
    """

    transform_matrix = maya.OpenMaya.MTransformationMatrix(matrix)
    transform_matrix.reorderRotation(rotation_order)
    rotation_as_quaterion = space == maya.OpenMaya.MSpace.kWorld

    if maya.is_new_api():
        translation = transform_matrix.translation(space)
        rotation = transform_matrix.rotation(asQuaternion=rotation_as_quaterion)
        scale = transform_matrix.scale(space)
    else:
        translation = maya.OpenMaya.MVector()
        rotation = maya.OpenMaya.MVector()
        scale = maya.OpenMaya.MVector()
        transform_matrix.translation(translation, space)
        transform_matrix.rotation(rotation, asQuaternion=rotation_as_quaterion)
        transform_matrix.scale(scale, space)

    return translation, rotation, scale


def get_node_color_data(mobj):
    """
    Returns the color data in the given Maya node
    :param mobj: str or OpenMaya.MObject
    :return: dict
    """

    depend_node = maya.OpenMaya.MFnDagNode(maya.OpenMaya.MFnDagNode(mobj).getPath())
    plug = depend_node.findPlug('overrideColorRGB', False)
    enabled_plug = depend_node.findPlug('overrideEnabled', False)
    override_rgb_colors = depend_node.findPlug('overrideRGBColors', False)
    use_outliner = depend_node.findPlug('useOutlinerColor', False)

    return {
        'overrideEnabled': plugs.get_plug_value(enabled_plug),
        'overrideColorRGB': plugs.get_plug_value(plug),
        'overrideRGBColors': plugs.get_plug_value(override_rgb_colors),
        'useOutlinerColor': plugs.get_plug_value(use_outliner),
        'outlinerColor': plugs.get_plug_value(depend_node.findPlug('outlinerColor', False))
    }


def iterate_shapes(dag_path, filter_types=None):
    """
    Generator function that returns all the given shape DAG paths directly below the given DAG path
    :param dag_path: MDagPath, path to search shapes of
    :param filter_types: list(str), list of filter shapes for teh shapes to return
    :return: list(MDagPath)
    """

    filter_types = python.force_list(filter_types)
    for i in range(dag_path.numberOfShapesDirectlyBelow()):
        shape_dag_path = maya.OpenMaya.MDagPath(dag_path)
        shape_dag_path.extendToShape(i)
        if not filter_types or shape_dag_path.apiType() in filter_types:
            yield shape_dag_path


def get_shapes(dag_path, filter_types):
    """
    Returns all the given shape DAG paths directly below the given DAG path as a list
    :param dag_path: MDagPath, path to search shapes of
    :param filter_types: list(str), list of filter shapes for teh shapes to return
    :return: list(str)
    """

    return list(iterate_shapes(dag_path, filter_types=filter_types))
