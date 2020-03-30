#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with namespaces
"""

import types

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import name as naming


def namespace_exists(namespace):
    """
    Returns whether or not given namespace exists
    :param namespace: str
    :return: bool
    """

    return maya.cmds.namespace(exists=namespace)


def get_namespace(name, check_obj=True, top_only=True):
    """
    Returns the namespace of the given object
    :param name: str, name to get namespace from
    :param check_obj: bool, Whether if object exist should be check or not
    :param top_only: bool, Whether to return top level namespace only or not
    :return: str
    """

    if check_obj:
        if not maya.cmds.objExists(name):
            raise Exception('Object "{}" does not exist!'.format(name))

    namespace = ''
    if not name.count(':'):
        return namespace

    if top_only:
        namespace = name.split(':')[0]
    else:
        namespace = name.replace(':' + name.split(':')[-1], '')

    return namespace


def get_namespace_from_list(objs_list, check_obj=True, top_only=True):
    """
    Returns a list of namespaces from a list of names
    :param objs_list: list(str)
    :param check_obj: bool, Whether if object exist should be check or not
    :param top_only: bool, Whether to return top level namespace only or not
    :return: list(str)
    """

    namespaces = list()
    if isinstance(objs_list, types.StringTypes):
        obj_list = [str(objs_list)]
    for obj in objs_list:
        namespace = get_namespace(obj, check_obj=check_obj, top_only=top_only)
        if namespace not in namespaces:
            namespaces.append(namespace)

    return namespaces


def remove_namespace_from_string(name):
    """
    Removes the namespace from the given string
    :param name: str, string we want to remove namespace from
    :return: str
    """

    sub_name = name.split(':')
    new_name = ''
    if sub_name:
        new_name = sub_name[-1]

    return new_name


def remove_empty_namespaces():
    """
    Removes all namespaces that are empty recursively starting from the bottom namespaces until the top one
    :return: list(str), list of deleted namespaces
    """

    delete_namespaces = list()

    def _namespace_children_count(ns):
        return ns.count(':')

    # Retrieve namespaces and sort them in a way that namespaces with more children are located at the front
    namespace_list = maya.cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
    namespace_list.sort(key=_namespace_children_count, reverse=True)

    for namespace in namespace_list:
        try:
            maya.cmds.namespace(removeNamespace=namespace)
            delete_namespaces.append(namespace)
        except RuntimeError:
            pass

    if delete_namespaces:
        maya.logger.info('Namespaces removed: {}'.format(delete_namespaces))

    return delete_namespaces


def get_all_namespaces(exclude_list=None):
    """
    Returns all the available namespaces in the scene
    :return: list(str)
    """

    IGNORE_NAMESPACES = ['UI', 'shared']
    if not exclude_list:
        exclude_list = IGNORE_NAMESPACES
    else:
        exclude_list.extend(IGNORE_NAMESPACES)

    namespaces = maya.cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
    namespaces = list(set(namespaces) - set(exclude_list))
    namespaces = sorted(namespaces)

    return namespaces


def get_current_namespace():
    """
    Returns the current set namespace
    :return: str
    """

    current_namespace = maya.cmds.namespaceInfo(cur=True)
    if not current_namespace.startswith(':'):
        current_namespace = ':{}'.format(current_namespace)

    return current_namespace


def reset_current_namespace():
    """
    Resets given namespace into the global scene namespace
    """

    maya.cmds.namespace(set=':')


def delete_namespace(namespace_name):
    """
    Removes the given namespace
    :param namespace_name: str
    :return: str
    """

    if not namespace_name:
        raise Exception('Invalid namespace specified!')
    if not maya.cmds.namespace(exists=namespace_name):
        raise Exception('Namespace "{}" does not exist!'.format(namespace_name))

    maya.cmds.namespace(mv=[namespace_name, ':'], f=True)
    maya.cmds.namespace(rm=namespace_name)


def move_namespace(source_namespace, target_namespace):
    """
    Moves all items from the source namespace into the target namespace
    :param source_namespace: str, source namespace
    :param target_namespace: str, target namespace
    """

    if not maya.cmds.namespace(exists=source_namespace):
        raise Exception('Source namespace "{}" does not exist!'.format(source_namespace))

    if not maya.cmds.namespace(exists=target_namespace):
        target_namespace = maya.cmds.namespace(add=target_namespace, f=True)

    new_namespace = maya.cmds.namespace(mv=(source_namespace, target_namespace), f=True)

    return new_namespace


def rename_namepace(namespace, new_namespace, parent_namespace=None):
    """
    Renames the given namespace
    :param namespace: str, namespace to rename
    :param new_namespace: str, new namespace name
    :param parent_namespace: str
    :return: str
    """

    if not maya.cmds.namespace(exists=namespace):
        raise Exception('Namespace "{}" does not exist!'.format(namespace))
    if maya.cmds.namespace(exists=new_namespace):
        raise Exception('Namespace "{}" already exist!'.format(new_namespace))

    if not parent_namespace:
        maya.cmds.namespace(rename=[namespace, new_namespace])
    else:
        maya.cmds.namespace(rename=[namespace, new_namespace], parent=parent_namespace)

    return new_namespace


def strip_namespace(obj):
    """
    Returns the given object name after striping the namespace
    :param obj: str, object to strip namespace from
    :return: str
    """

    return obj.split(':')[-1]


def get_all_in_namespace(namespace_name):
    """
    Returns all the dependency nodes contained in the given namespace
    :param namespace_name: str
    :return: list(str)
    """

    if not maya.cmds.namespace(exists=namespace_name):
        raise Exception('Namespace "{}" does not exist!'.format(namespace_name))

    current_namesapce = maya.cmds.namespaceInfo(currentNamespace=True)
    maya.cmds.namespace(set=namespace_name)
    namespace_nodes_list = maya.cmds.namespaceInfo(lod=True, dagPath=True)
    maya.cmds.namespace(set=current_namesapce)

    return namespace_nodes_list


def add_hierarchy_to_namespace(root, namespace, replace_namespace=True):
    """
    Add all the nodes under a root to the given namespace
    :param root: str, hierarchy root object
    :param namespace: str, namespace name
    :param replace_namespace: bool, Whether existing namespaces should be replace or not
    :return: list(str)
    """

    if not maya.cmds.objExists(root):
        raise Exception('Hierarchy root object "{}" does not exist!'.format(root))

    if not maya.cmds.namespace(exists=namespace):
        maya.cmds.namespace(add=namespace)

    hierarchy = maya.cmds.ls(maya.cmds.listRelatives(root, ad=True, pa=True), transform=True)
    hierarchy.append(root)

    for i in range(len(hierarchy)):
        item = hierarchy[i]
        current_namespace = get_namespace(item, check_obj=True, top_only=False)
        if current_namespace:
            maya.cmds.rename(item, item.replace(current_namespace, namespace))
        else:
            maya.cmds.rename(item, '{}:{}'.format(namespace, item))

        hierarchy[i] = item

    return hierarchy


def find_unique_namespace(namespace, increment_fn=None):
    """
    Returns a unique namespace based on the given namespace which does not exists in current scene
    :param namespace: str, namespace to find unique name of
    :param increment_fn: fn(basename, index), returns a unique name generated from the namespace and the index
    representing current iterator
    :return: str, unique namespace that is guaranteed not to exists below the current namespace
    """

    if not namespace_exists(namespace):
        return namespace

    def _increment(b, i):
        return "%s%02i" % (b, i)

    if not increment_fn:
        increment_fn = _increment

    index = 1
    while True:
        test_namespace = increment_fn(namespace, index)
        index += 1
        if not namespace_exists(test_namespace):
            return test_namespace


def assign_namespace_to_object(obj_names, namespace, force_create=True, uuid=None, rename_shape=True):
    """
    Assigns a namespace to given Maya node names
    :param obj_names: str, names of the node to assign namespace to
    :param namespace: str, name of namespace to assign
    :param force_create: bool, Whether to force the creation of the namespace if it does not exists
    :param uuid: str, optional UUID that can be used instead of the object name.
    :param rename_shape: bool, Whether to rename shapes node or not
    :return:str, new name of the object
    """

    def _assign_namespace(obj_name, obj_uuid=None):
        long_prefix, obj_namespace, base_name = naming.get_node_name_parts(obj_name)
        if namespace == obj_namespace:
            return obj_name

        new_name = naming.join_node_name_parts(long_prefix, namespace, base_name)

        return naming.rename(obj_name, new_name, uuid=obj_uuid, rename_shape=rename_shape)

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    if not maya.cmds.namespace(exists=namespace):
        if force_create:
            maya.cmds.namespace(set=':')
            maya.cmds.namespace(add=namespace)
        else:
            return obj_names

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _assign_namespace(obj, uuid_list[i])
        maya.cmds.namespace(set=':')
        return maya.cmds.ls(uuid_list, long=True)
    else:
        return _assign_namespace(obj_names, uuid)


def remove_namespace_from_object(obj_names, namespace, uuid=None, rename_shape=True):
    """
    Removes a namespace to given Maya node names
    :param obj_names: str, names of the node to remove namespace from
    :param namespace: str, name of namespace to remove
    :param uuid: str, optional UUID that can be used instead of the object name.
    :param rename_shape: bool, Whether to rename shapes node or not
    :return:str, new name of the object
    """

    def _remove_namespace(obj_name, obj_uuid=None):
        long_prefix, obj_namespace, base_name = naming.get_node_name_parts(obj_name)
        new_name = naming.join_node_name_parts(long_prefix, '', base_name)

        return naming.rename(obj_name, new_name, uuid=obj_uuid, rename_shape=rename_shape)

    if not obj_names:
        obj_names = maya.cmds.ls(sl=True, long=True)

    if not maya.cmds.namespace(exists=namespace):
        return obj_names

    if isinstance(obj_names, (tuple, list)):
        uuid_list = maya.cmds.ls(obj_names, uuid=True)
        for i, obj in enumerate(obj_names):
            _remove_namespace(obj, uuid_list[i])
        maya.cmds.namespace(set=':')
        remove_empty_namespaces()
        return maya.cmds.ls(uuid_list, long=True)
    else:
        removed_namespaces = _remove_namespace(obj_names, uuid)
        remove_empty_namespaces()
        return removed_namespaces


def assign_namespace_to_object_by_filter(namespace, filter_type, force_create=True, rename_shape=True,
                                         search_hierarchy=False, selection_only=True, dag=False,
                                         remove_maya_defaults=True, transforms_only=True):
    """
    Assigns a namespace to given Maya node names filtered by given type
    :param namespace: str, name of namespace to assign
    :param filter_type: str, filter used to filter nodes to edit index of
    :param force_create: bool, Whether to force the creation of the namespace if it does not exists
    :param rename_shape: bool, Whether to rename shapes node or not
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return:str, new name of the object
    """

    from tpDcc.dccs.maya.core import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        maya.logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return assign_namespace_to_object(
        filtered_obj_list, namespace=namespace, force_create=force_create, rename_shape=rename_shape)


def remove_namespace_from_object_by_filter(namespace, filter_type, rename_shape=True, search_hierarchy=False,
                                           selection_only=True, dag=False, remove_maya_defaults=True,
                                           transforms_only=True):
    """
    Removes namespace from given Maya node names filtered by given type
    :param namespace: str, name of namespace to remove
    :param filter_type: str, filter used to filter nodes to edit index of
    :param rename_shape: bool, Whether to rename shapes node or not
    :param search_hierarchy: bool, Whether to search objects in hierarchies
    :param selection_only: bool, Whether to search all scene objects or only selected ones
    :param dag: bool, Whether to return only DAG nodes
    :param remove_maya_defaults: Whether to ignore Maya default nodes or not
    :param transforms_only: bool, Whether to return only transform nodes or not
    :return:str, new name of the object
    """

    from tpDcc.dccs.maya.core import filtertypes

    filtered_obj_list = filtertypes.filter_by_type(
        filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
        remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)
    if not filtered_obj_list:
        maya.logger.warning('No objects filtered with type "{}" found!'.format(filter_type))
        return

    return remove_namespace_from_object(
        filtered_obj_list, namespace=namespace, rename_shape=rename_shape)
