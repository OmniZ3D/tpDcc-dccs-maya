#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya API nodes
"""

from __future__ import print_function, division, absolute_import

import maya.api.OpenMaya

from tpDcc.libs.python import python
from tpDcc.dccs.maya import api
from tpDcc.dccs.maya.api import plugs, exceptions


def is_valid_mobject(node):
    """
    Returns whether or not given node is a valid MObject
    :param node: MObject
    :return: bool
    """

    handle = maya.api.OpenMaya.MObjectHandle(node)

    return handle.isValid() and handle.isAlive()


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

    if mobj.hasFn(maya.api.OpenMaya.MFn.kDagNode):
        dag_node = api.DagNode(mobj)
        node_name = dag_node.get_partial_path() if partial_name else dag_node.get_full_path()
    else:
        node_name = api.DependencyNode(mobj).get_name()

    if not include_namespace:
        node_name = maya.api.OpenMaya.MNamespace.stripNamespaceFromName(node_name)

    return node_name


def names_from_mobject_handles(mobjs_list):
    """
    Returns names of the given list of MObjectHandles
    :param mobjs_list: list(MObjectHandle)
    :return: list(str)
    """

    names_list = list()
    for mobj in mobjs_list:
        object_handle = maya.api.OpenMaya.MObjectHandle(mobj)
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

    dag_mod = maya.api.OpenMaya.MDagModifier()
    dag_mod.renameNode(mobj, new_name)
    dag_mod.doIt()

    return mobj


def set_matrix(mobj, matrix, space=None):
    """
    Sets the object matrix using MTransform
    :param mobj: MObject, the transform MObject to modify
    :param matrix: MMatrix, MMatrix to set
    :param space: MSpace, coordinate space to set the matrix by
    :return:
    """

    space = space or maya.api.OpenMaya.MSpace.kTransform
    dag = maya.api.OpenMaya.MFnDagNode(mobj)
    transform = maya.api.OpenMaya.MFnTransform(dag.getPath())
    transform_matrix = maya.api.OpenMaya.MTransformationMatrix(matrix)
    transform.setTranslation(transform_matrix.translation(space), space)
    transform.setRotation(transform_matrix.rotation(asQuaternion=True), space)
    transform.setScale(transform_matrix.scale(space))


def get_world_matrix_plug(mobj):
    """
    Returns the MPlug pointing worldMatrix of the given MObject pointing a DAG node
    :param mobj: MObject
    :return: MPlug
    """

    world_matrix = maya.api.OpenMaya.MFnDependencyNode(mobj).findPlug('worldMatrix', False)
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


def set_parent(child, new_parent=None, maintain_offset=False, mod=None, apply=True):
    """
    Sets the parent of the given child
    :param child: MObject, child node which will have its parent changed
    :param new_parent: MObject, new parent for the child
    :param maintain_offset: bool, Whether or not current transformation is maintained relative to the new parent
    :param mod: MDagModifier, MDagModifier to add to; if None, a new will be created
    :param apply: bool, Whether or not to apply modifier immediately
    :return:
    """

    new_parent = new_parent or maya.api.OpenMaya.MObject.kNullObj
    if child == new_parent:
        return False

    mod = mod or maya.api.OpenMaya.MDagModifier()
    if maintain_offset:
        if new_parent == maya.api.OpenMaya.MObject.kNullObj:
            offset = get_world_matrix(child)
        else:
            start = get_world_matrix(new_parent)
            end = get_world_matrix(child)
            offset = end * start.inverse()
    mod.reparentNode(child, new_parent)
    if apply:
        mod.doIt()
    if maintain_offset:
        set_matrix(child, offset)

    return mod


def decompose_transform_matrix(matrix, rotation_order, space=None):
    """
    Returns decomposed translation, rotation and scale of the given Maya Matrix
    :param matrix: MMatrix, maya transforms matrix to decompose
    :param rotation_order:
    :param space: MSpace, coordinate space to decompose matrix of
    :return: tuple(MVector, MVector, MVector)
    """

    transform_matrix = maya.api.OpenMaya.MTransformationMatrix(matrix)
    transform_matrix.reorderRotation(rotation_order)
    rotation_as_quaterion = space == maya.api.OpenMaya.MSpace.kWorld

    translation = transform_matrix.translation(space)
    rotation = transform_matrix.rotation(asQuaternion=rotation_as_quaterion)
    scale = transform_matrix.scale(space)

    return translation, rotation, scale


def get_node_color_data(mobj):
    """
    Returns the color data in the given Maya node
    :param mobj: str or OpenMaya.MObject
    :return: dict
    """

    depend_node = maya.api.OpenMaya.MFnDagNode(api.DagNode(mobj).get_path())
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


def set_node_color(mobj, color, outliner_color=None, use_outliner_color=False):
    """
    Sets the given Maya object its override color. MObject can represent an object or a shape
    :param mobj: MObject, Maya object we want to change color of
    :param color: MColor or tuple(float, float, float), RGB color to set
    :param outliner_color: MColor or tuple(float, float, float) or None, RGB color to set to outliner item
    :param use_outliner_color: bool, Whether or not to apply outliner color
    """

    depend_node = maya.api.OpenMaya.MFnDagNode(api.DagNode(mobj).get_path())
    plug = depend_node.findPlug('overrideColorRGB', False)
    enabled_plug = depend_node.findPlug('overrideEnabled', False)
    override_rgb_colors = depend_node.findPlug('overrideRGBColors', False)
    if not enabled_plug.asBool():
        enabled_plug.setBool(True)
    if not override_rgb_colors.asBool():
        depend_node.findPlug('overrideRGBColors', False).setBool(True)
    plugs.set_plug_value(plug, color)

    if outliner_color:
        use_outliner = depend_node.findPlug('useOutlinerColor', False)
        if use_outliner_color:
            use_outliner.setBool(True)
        plugs.set_plug_value(depend_node.findPlug('outlinerColor', False), outliner_color)


def iterate_shapes(dag_path, filter_types=None):
    """
    Generator function that returns all the given shape DAG paths directly below the given DAG path
    :param dag_path: MDagPath, path to search shapes of
    :param filter_types: list(str), list of filter shapes for teh shapes to return
    :return: list(MDagPath)
    """

    filter_types = python.force_list(filter_types)
    for i in range(dag_path.numberOfShapesDirectlyBelow()):
        shape_dag_path = maya.api.OpenMaya.MDagPath(dag_path)
        shape_dag_path.extendToShape(i)
        if not filter_types or shape_dag_path.apiType() in filter_types:
            yield shape_dag_path


def get_shapes(dag_path, filter_types=None):
    """
    Returns all the given shape DAG paths directly below the given DAG path as a list
    :param dag_path: MDagPath, path to search shapes of
    :param filter_types: list(str), list of filter shapes for teh shapes to return
    :return: list(str)
    """

    return list(iterate_shapes(dag_path, filter_types=filter_types))


def get_child_path_at_index(path, index):
    """
    Returns MDagPath of the child node at given index from given MDagPath
    :param path: MDagPath
    :param index: int
    :return: MDagPath, child path at given index
    """

    existing_child_count = path.childCount()
    if existing_child_count < 1:
        return None
    index = index if index >= 0 else path.childCount() - abs(index)
    copy_path = maya.api.OpenMaya.MDagPath(path)
    copy_path.push(path.child(index))

    return copy_path


def get_child_paths(path):
    """
    Returns all MDagPaths that are child of the given MDagPath
    :param path: MDagPath
    :return: list(MDagPath)
    """

    out_paths = [get_child_path_at_index(path, i) for i in range(path.childCount())]

    return out_paths


def get_child_paths_by_fn(path, fn):
    """
    Returns all children paths of the given MDagPath that supports given MFn type
    :param path: MDagPath
    :param fn: MFn
    :return: list(MDagPath)
    """

    return [child_path for child_path in get_child_paths(path) if child_path.hasFn(fn)]


def get_child_transforms(path):
    """
    Returns all the child transforms of the given MDagPath
    :param path: MDagPath
    :return: list(MDagPath), list of all transforms below given path
    """

    return get_child_paths_by_fn(path, maya.api.OpenMaya.MFn.kTransform)


def lock_node(mobj, state=True, modifier=True):
    """
    Sets the lock state of the given node
    :param mobj: MObject, the node mobject to set the lock state of
    :param state: bool, lock state for the node
    :param modifier: MDagModifier or None
    :return: MDagModifier
    """

    if maya.api.OpenMaya.MFnDependencyNode(mobj).isLocked != state:
        mod = modifier or maya.api.OpenMaya.MDGModifier()
        mod.setNodeLockState(mobj, state)
        if modifier is not None:
            modifier.doIt()
        return modifier


def unlock_connected_attributes(mobj):
    """
    Unlocks all connected attributes to the given MObject
    :param mobj: MObject, MObject representing a DG node
    """

    for source, target in iter_connections(mobj, source=True, destination=True):
        if source.isLocked:
            source.isLocked = False


def unlock_and_disconnect_connected_attributes(mobj):
    """
    Unlocks and disconnects all attributes to the given MObject
    :param mobj: MObject, MObject representing a DG node
    """

    for source, target in iter_connections(mobj, source=False, destination=True):
        plugs.disconnect_plug(source)


def iter_connections(node, source=True, destination=True):
    """
    Returns a generator function containing a tuple of MPlugs
    :param node: MObject, MObject node to serach
    :param source: bool, If True, all upstream connections are returned
    :param destination: if True, all downstream connections are returned
    :return: generator(tuple(MPlug, Mplug)), tuple of MPlug instances, the first element is the connected MPlug of the
        given node and the other one is the connected MPlug from the other node
    """

    dep = maya.api.OpenMaya.MFnDependencyNode(node)
    for plug in iter(dep.getConnections()):
        if source and plug.isSource:
            for i in iter(plug.destinations()):
                yield plug, i
        if destination and plug.isDestination:
            yield plug, plug.source()


def delete(node):
    """
    Deletes given node
    :param node: MObject
    :return:
    """

    if not is_valid_mobject(node):
        return

    lock_node(node, False)
    unlock_and_disconnect_connected_attributes(node)

    dag_modifier = maya.api.OpenMaya.MDagModifier()
    dag_modifier.deleteNode(node)
    dag_modifier.doIt()
