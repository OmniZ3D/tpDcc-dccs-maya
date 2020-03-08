#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to maya filter types
"""

from __future__ import print_function, division, absolute_import

import tpDcc
from tpDcc.libs.python import python
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import camera

ALL_FILTER_TYPE = 'ALL'
GROUP_FILTER_TYPE = 'GROUP'

PROTECTED_NODES = [
    "layerManager", "renderLayerManager", "poseInterpolatorManager", "defaultRenderLayer",
    "defaultLayer", "lightLinker1", "shapeEditorManager"
]


def filter_all_node_types(
        selection_only=True, search_hierarchy=False, dag=False, transforms_only=False, remove_maya_defaults=True):
    """
    Function that filters current scene objects by node types
    :param selection_only:
    :param search_hierarchy:
    :param dag:
    :param transforms_only:
    :param remove_maya_defaults:
    :return:
    """

    if not selection_only:
        all_objs = maya.cmds.ls(long=True, dagObjects=search_hierarchy, dag=dag)
        if not remove_maya_defaults:
            protected = maya.cmds.ls(defaultNodes=True) + PROTECTED_NODES
            scene_filtered = list(set(all_objs) - set(protected))
            if not transforms_only:
                return scene_filtered
            else:
                return filter_transforms_from_shapes_list(scene_filtered)

        default_cameras = camera.get_startup_camera_transforms() + camera.get_startup_camera_shapes()
        maya_defaults = default_cameras + maya.cmds.ls(defaultNodes=True) + PROTECTED_NODES
        scene_filtered = list(set(all_objs) - set(maya_defaults))
        if not transforms_only:
            return scene_filtered
        else:
            return filter_transforms_from_shapes_list(scene_filtered)

    all_selected_objs = maya.cmds.ls(sl=True, long=True, dagObjects=search_hierarchy, dag=dag)
    if not all_selected_objs:
        maya.logger.warning('No objects selected, select at least one please!')
        return list()

    if not transforms_only:
        return all_selected_objs
    else:
        return filter_transforms_from_shapes_list(all_selected_objs)


def filter_transforms_from_shapes_list(objs_list, allow_joints=True, allow_dg=True):
    """
    If a shape node is found in given objects, it will be replace by its transform parent
    :param objs_list: list(str), list of Maya object names
    :param allow_joints: bool, Whether to include joints in the returned list or not. They will be treat as
        transform nodes
    :param allow_dg: bool, Whether to return DG nodes in the returned list of not.
    :return: list(str)
    """

    transform_list = list()

    for obj in objs_list:
        if maya.cmds.objectType(obj, isType='transform'):
            transform_list.append(obj)
        elif allow_joints and maya.cmds.objectType(obj, isType='joint'):
            transform_list.append(obj)
        else:
            if 'dagNode' in maya.cmds.nodeType(obj, inherited=True):
                transform_list.append(maya.cmds.listRelatives(obj, parent=True, fullPath=True)[0])
            elif allow_dg:
                # Not DAG nodes do not have transform nodes, we add them directly
                transform_list.append(obj)

    return list(set(transform_list))


def filter_by_group(selection_only, search_hierarchy, dag):
    """
    Returns nodes that are groups (empty transform nodes with no shape nodes)
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param search_hierarchy: bool, Whether to search the hierarchy below the objects list or not
    :param dag: bool, Whether to only return DAG nodes or not
    :return: list(str( .list of group nodes
    """

    objs_list = list()
    group_list = list()

    if selection_only:
        objs_list = maya.cmds.ls(sl=True, long=True)
        if not objs_list:
            maya.logger.warning('Nothing is selected, please select at least one object!')
            return list()

    obj_transforms = filter_list_by_types(
        filter_types='transform', objs_list=objs_list, search_hierarchy=search_hierarchy,
        selection_only=selection_only, dag=dag)
    if not obj_transforms:
        maya.logger.warning('No groups found!')
        return list()

    # We check again to avoid not wanted transforms (such as joints, or shape nodes)
    for obj in obj_transforms:
        if not maya.cmds.listRelatives(obj, shapes=True) and maya.cmds.objectType(obj, isType='transform'):
            group_list.append(obj)

    return group_list


def filter_dag_transforms(filter_types, search_hierarchy=False, selection_only=True, dag=False, transforms_only=True):
    """
    Returns a list of Maya objects that match filter type and returns only transform parent of shape nodes
    :param filter_types: list(str), list of node types to filter by
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return: list(str), list of filtered DAG transform nodes
    """

    if selection_only:
        sel_objs = maya.cmds.ls(sl=True, long=True)
        if not sel_objs:
            maya.logger.warning('No objects selected. Please select at least one!')
            return list()
        shapes_list = maya.cmds.listRelatives(sel_objs, shapes=True, fullPath=True)
        if shapes_list:
            sel_objs += shapes_list
        filtered_shapes = filter_list_by_types(
            filter_types=filter_types, objs_list=sel_objs, search_hierarchy=search_hierarchy, dag=dag)
    else:
        filtered_shapes = filter_list_by_types(
            filter_types=filter_types, search_hierarchy=search_hierarchy, selection_only=True, dag=dag)

    if not transforms_only:
        return filtered_shapes

    return filter_transforms_from_shapes_list(filtered_shapes)


def filter_by_type(
        filter_type, search_hierarchy=False, selection_only=True, dag=False, remove_maya_defaults=True,
        transforms_only=True):
    """
    Returns a list of objects that match the given node type
    :param filter_type: str
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return:
    """

    if not selection_only:
        search_hierarchy = False

    obj_type_list = tpDcc.Dcc.TYPE_FILTERS.get(filter_type, None)
    if not obj_type_list:
        maya.logger.warning('Filter Type "{}" is not supported in Maya!'.format(filter_type))
        return None

    if obj_type_list == ALL_FILTER_TYPE:
        return filter_all_node_types(
            selection_only=selection_only, search_hierarchy=search_hierarchy, transforms_only=transforms_only,
            dag=dag, remove_maya_defaults=remove_maya_defaults)
    elif obj_type_list == GROUP_FILTER_TYPE:
        return filter_by_group(selection_only=selection_only, search_hierarchy=search_hierarchy, dag=dag)
    else:
        return filter_dag_transforms(
            filter_types=obj_type_list, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag)


def filter_list_by_types(filter_types, objs_list=None, search_hierarchy=False, selection_only=True, dag=False):
    """
    Returns a list of objecst that match the given node type
    :param filter_types: list(str), list of node types to filter by
    :param objs_list: list(str), list of maya nodes to filter
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :return: list(str), list of filtered objects
    """

    if not filter_types:
        return

    if not objs_list:
        objs_list = list()

    filter_types = python.force_list(filter_types)

    filtered_objs = list()
    if not selection_only:
        for filter_type in filter_types:
            filtered_objs += maya.cmds.ls(type=filter_type, long=True, dagObjects=search_hierarchy, dag=dag)
    else:
        for filter_type in filter_types:
            filtered_objs += maya.cmds.ls(objs_list, type=filter_type, long=True, dagObjects=search_hierarchy, dag=dag)

    return list(set(filtered_objs))
