#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya scene
"""

from __future__ import print_function, division, absolute_import

import os
import string
import traceback
import contextlib

from Qt.QtWidgets import *

import tpDcc.dccs.maya as maya
from tpDcc.libs.python import path


class TrackNodes(object):
    """
    Helps track new nodes that get added to a scene after a function is called
    Example of use:
    track_nodes = TrackNodes()
    track_nodes.load()
    custom_funct()
    new_nodes = track_nodes.get_delta()
    """

    def __init__(self, full_path=False):
        self._nodes = None
        self._node_type = None
        self._delta = None
        self._full_path = full_path

    def load(self, node_type=None):
        """
        Initializes TrackNodes states
        :param node_type: str, Maya node type we want to track. If not given, all current scene objects wil lbe tracked
        """

        self._node_type = node_type
        if self._node_type:
            self._nodes = maya.cmds.ls(type=node_type, long=self._full_path)
        else:
            self._nodes = maya.cmds.ls()

    def get_delta(self):
        """
        Returns the new nodes in the Maya scen created after load() was executed
        :return: list<str>
        """

        if self._node_type:
            current_nodes = maya.cmds.ls(type=self._node_type, long=self._full_path)
        else:
            current_nodes = maya.cmds.ls(long=self._full_path)

        new_set = set(current_nodes).difference(self._nodes)

        return list(new_set)


def get_current_scene_name():
    """
    Returns the name of the current scene opened in Maya
    :return: str
    """

    scene_path = maya.cmds.file(query=True, sceneName=True)
    if scene_path:
        return os.path.splitext(os.path.basename(scene_path))[0]

    return None


def get_scene_file(directory=False):
    """
    Returns the scene file name or directory of the current scene
    :param directory: bool, Whether to return scene name or scene path
    :return: str
    """

    scene_path = maya.cmds.file(q=True, sn=True)
    if directory and scene_path:
        scene_path = path.get_dirname(scene_path)

    return scene_path


def new_scene(force=True, do_save=True):
    """
    Creates a new Maya scene
    :param force: bool, True if we want to save the scene without any prompt dialog
    :param do_save: bool, True if you want to save the current scene before creating new scene
    """

    if do_save:
        save()

    maya.cmds.file(new=True, force=force)
    maya.cmds.flushIdleQueue()


def import_scene(file_path, force=True, do_save=True):
    """
    Imports a Maya scene into the current scene
    :param file_path: str, Path of the Maya scene to import
    :param force: bool, True if we want to save the scene without any prompt dialog
    :param do_save: bool, True if you want to save the current scene before importing a new scene
    :return:
    """

    if do_save:
        save()

    maya.cmds.file(file_path, i=True, force=force, iv=True, pr=True)


def open_scene(file_path, force=True, do_save=True):
    """
    Open a Maya scene given its file path
    :param file_path: str, Path of the Maya scene to open
    :param force: bool, True if we want to save the scene without any prompt dialog
    :param do_save: bool, True if you want to save the current scene before opening a new scene
    """

    if save:
        save()

    maya.cmds.file(file_path, open=True, force=force)


def reference_scene(file_path, namespace=None, save=True):
    """
    References a Maya file
    :param file_path: str, full path and filename of the scene we want to reference
    :param namespace: variant, str || None, namespace to add to the nodes in Maya. If None, default is the name of
        the file
    :param save: bool, True if you want to save the current scene before importing file
    """

    if not namespace:
        namespace = os.path.basename(file_path)
        split_name = namespace.split('.')
        if split_name:
            namespace = string.join(split_name[:-1], '_')

    maya.cmds.file(file_path, reference=True, mergeNamespacesOnClash=False, namespace=namespace)


def save():
    """
    Saves current scene in current Maya file
    :return: bool, Whether the scene was saved or not
    """

    file_check_state = maya.cmds.file(query=True, modified=True)
    if file_check_state:
        msg_box = QMessageBox()
        msg_box.setText('The Maya scene has been modified')
        msg_box.setInformativeText('Do you want to save your changes?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        res = msg_box.exec_()
        if res == QMessageBox.Yes:
            maya.cmds.SaveScene()
            return True

    return False


def save_as(file_path):
    """
    Saves Maya scene into the given file path
    :param file_path: str
    :return: bool
    """

    saved = False
    if not file_path:
        return saved

    maya.logger.debug('Saving "{}"'.format(file_path))

    file_type = 'mayaAscii'
    if file_path.endswith('.mb'):
        file_type = 'mayaBinary'

    try:
        maya.cmds.file(rename=file_path)
        maya.cmds.file(save=True, type=file_type)
        saved = True
    except Exception:
        maya.logger.error(str(traceback.format_exc()))
        saved = False

    if saved:
        maya.logger.debug('Scene saved successfully into: {}'.format(file_path))
    else:
        if not maya.cmds.about(batch=True):
            maya.cmds.confirmDialog(message='Warning:\n\nMaya was unable to save!', button='Confirm')
        maya.logger.warning('Scene not saved: {}'.format(file_path))

    return saved


def iter_references():
    """
    Generator function that returns a MObject for each valid reference node
    :return: Generator<OpenMaya.MObject>
    """

    iterator = maya.OpenMaya.MItDependencyNodes(maya.OpenMaya.MFn.kReference)
    while not iterator.isDone():
        try:
            fn = maya.OpenMaya.MFnReference(iterator.thisNode())
            try:
                if not fn.isLoaded() or fn.isLocked():
                    continue
            except RuntimeError:
                continue
            yield fn.object()
        finally:
            iterator.next()


def find_additional_scene_dependencies(references=True, textures=True):
    """
    Find additional dependencies from the scene by looking at the file references and texture paths
    :param references: bool
    :param textures: bool
    :return: set<str>
    """

    ref_paths = set()
    if references:
        ref_paths.union(find_scene_references())
    if textures:
        ref_paths.union(find_scene_textures())

    return ref_paths


def find_scene_textures():
    """
    Find scene texture dependencies of the current scene that are not referenced
    :return: set<str>
    """

    paths = set()
    for f in maya.cmds.ls(long=True, type='file'):
        if maya.cmds.referenceQuery(f, isNodeReferenced=True):
            continue

        texture_path = maya.cmds.getAttr(os.path.normpath('.'.join([f, 'fileTextureName'])))
        if texture_path:
            paths.add(texture_path)

    return paths


def find_texture_node_pairs():
    """
    Returns pair with scene texture maya node, texture name of texture dependencies of the current
    scene that are not referenced
    :return: set<str>
    """

    paths = set()
    for f in maya.cmds.ls(long=True, type='file'):
        if maya.cmds.referenceQuery(f, isNodeReferenced=True):
            continue

        texture_path = maya.cmds.getAttr(os.path.normpath('.'.join([f, 'fileTextureName'])))
        if texture_path:
            paths.add((f, texture_path))

    return paths


def iter_texture_node_pairs(include_references=False):
    """
    :param include_references: bool
    :return:
    """

    for f in maya.cmds.ls(long=True, type='file'):
        if include_references and maya.cmds.referenceQuery(f, isNodeReferenced=True):
            continue

        texture_path = maya.cmds.getAttr(os.path.normpath('.'.join([f, 'fileTextureName'])))
        if texture_path:
            yield ([f, texture_path])


def find_scene_references():
    paths = set()

    for ref in iter_references():
        ref_path = ref.fileName(True, False, False).replace('/', os.path.sep)
        if ref_path:
            paths.add(ref_path)

    return paths


@contextlib.contextmanager
def isolated_nodes(nodes, panel):
    """
    Context Manager for isolating nodes in Maya model panel
    :param nodes:
    :param panel:
    :return:
    """

    maya.cmds.isolateSelect(panel, state=True)
    for obj in nodes:
        maya.cmds.isolateSelect(panel, addDagObject=obj)
    yield
    maya.cmds.isolateSelect(panel, state=False)


def is_batch():
    """
    Returns whether Maya is in batch mode or node
    :return: bool
    """

    return maya.cmds.about(batch=True)


def get_scene_cameras(include_default_cameras=True, include_non_default_cameras=True, get_transforms=False):
    """
    Returns a list with all cameras in the scene
    :param include_default_cameras: bool, Whether to get default cameras or not
    :param include_non_default_cameras: Whether to get non default cameras or not
    :param get_transforms: bool, Whether to return cameras shape or camera transform
    :return: list<str>
    """

    final_list = list()
    cameras = maya.cmds.ls(type='camera', long=True)
    startup_cameras = [camera for camera in cameras if maya.cmds.camera(maya.cmds.listRelatives(
        camera, parent=True)[0], startupCamera=True, q=True)]
    non_startup_cameras = list(set(cameras) - set(startup_cameras))
    if include_default_cameras:
        final_list.extend(startup_cameras)
    if include_non_default_cameras:
        final_list.extend(non_startup_cameras)

    if get_transforms:
        return map(lambda x: maya.cmds.listRelatives(x, parent=True)[0], final_list)

    return final_list


def get_top_dag_nodes(exclude_cameras=True, namespace=None):
    """
    Returns all transform that are at located in the root scene
    :param exclude_cameras: bool, Whether to include or not cameras
    :param namespace: str, if given, namespace of the objects that we want to get
    :return: list<str>
    """

    top_transforms = maya.cmds.ls(assemblies=True)
    if exclude_cameras:
        cameras = get_scene_cameras(get_transforms=True)
        for camera in cameras:
            if camera in top_transforms:
                top_transforms.remove(camera)

    if namespace:
        found = list()
        for transform in top_transforms:
            if transform.startswith(namespace + ':'):
                found.append(transform)
        top_transforms = found

    return top_transforms


def get_top_dag_nodes_in_list(list_of_transforms):
    """
    Given a list of transforms, returns only the ones at the top of the hierarchy (childs of the scene root)
    :param list_of_transforms: list<str>
    :return: list<str>
    """

    found = list()
    for xform in list_of_transforms:
        long_name = maya.cmds.ls(xform, long=True)
        if long_name:
            if long_name[0].count('|') == 1:
                found.append(xform)

    return found


def get_node_transform_root(node, full_path=True):
    """
    :param node: str
    Returns the transform root of the given node taking into account its hierarchy
    :return: str
    """

    while True:
        parent = maya.cmds.listRelatives(node, parent=True, fullPath=full_path)
        if not parent:
            break

        node = parent[0]

    return node


def get_root_node():
    """
    Returns the root Maya object
    :return:
    """

    from tpDcc.dccs.maya.core import node

    for n in node.get_objects_of_mtype_iterator(object_type=maya.OpenMaya.MFn.kWorld):
        return n

    return None


def get_all_scene_nodes():
    """
    Returns all nodes in the scene
    :return:
    """

    from tpDcc.dccs.maya.core import node

    obj_types = (maya.OpenMaya.MFn.kDagNode, maya.OpenMaya.MFn.kCharacter, maya.OpenMaya.MFn.kDependencyNode)
    return node.get_objects_of_mtype_iterator(obj_types)


def get_all_parent_nodes(node_name):
    """
    Returns all parent nodes of the given Maya node
    :param node_name: str, name of the Maya node
    :return: list(str)
    """

    def _append_parents(node_name, node_list_):
        """
        Internal function to recursvely append parents to list
        :param node_name: str
        :param node_list_: list<str>
        """

        parents = maya.cmds.listRelatives(node_name, parent=True, fullPath=True, type='transform')
        if parents:
            for parent in parents:
                node_list_.append(parent)
                _append_parents(parent, node_list_)

    node_list = list()
    _append_parents(node_name, node_list)

    return node_list


def get_all_children_nodes(node_name):
    """
    Return all children nodes of the given node
    :param node_name: str
    :return: list<str>
    """

    def _append_children(node_name, node_list_):
        """
        Internal function to recursively append children to list
        :param node_name: str
        :param node_list_: list<str>
        """

        children = maya.cmds.listRelatives(node_name, fullPath=True, type='transform')
        if children:
            for child in children:
                node_list_.append(child)
                _append_children(child, node_list_)

    node_list = list()
    _append_children(node_name, node_list)

    return node_list


def get_sets():
    """
    Returns a list of sets found in the scene (outliner)
    :return: list<str>
    """

    sets = maya.cmds.ls(type='objectSet')
    top_sets = list()
    for obj_set in sets:
        if obj_set == 'defaultObjectSet':
            continue

        outputs = maya.cmds.listConnections(
            obj_set, plugs=False, connections=False, destination=True, source=False, skipConversionNodes=True)
        if not outputs:
            top_sets.append(obj_set)

    return top_sets


def delete_unknown_nodes():
    """
    Find all unknown nodes and delete them
    """

    unknown = maya.cmds.ls(type='unknown')
    deleted = list()
    for n in unknown:
        if maya.cmds.objExists(n):
            maya.cmds.lockNode(n, lock=False)
            maya.cmds.delete(n)
            deleted.append(n)

    maya.logger.debug('Deleted uknowns: {}'.format(deleted))


def delete_turtle_nodes():
    """
    Find all turtle nodes in a scene and delete them
    """

    from tpDcc.dccs.maya.core import node

    plugin_list = maya.cmds.pluginInfo(query=True, pluginsInUse=True)
    turtle_nodes = list()
    if plugin_list:
        for plugin in plugin_list:
            if plugin[0] == 'Turtle':
                turtle_types = ['ilrBakeLayer',
                                'ilrBakeLayerManager',
                                'ilrOptionsNode',
                                'ilrUIOptionsNode']
                turtle_nodes = node.delete_nodes_of_type(turtle_types)
                break

    maya.logger.debug('Removed Turtle nodes: {}'.format(turtle_nodes))


def delete_unused_plugins():
    """
    Removes all nodes in the scene that belongs to unused plugins (plugins that are not loaded)
    """

    # This functionality is not available in old Maya versions
    list_cmds = dir(maya.cmds)
    if 'unknownPlugin' not in list_cmds:
        return

    unknown_nodes = maya.cmds.ls(type='unknown')
    if unknown_nodes:
        return

    unused = list()
    unknown_plugins = maya.cmds.unknownPlugin(query=True, list=True)
    if unknown_plugins:
        for p in unknown_plugins:
            try:
                maya.cmds.unknownPlugin(p, remove=True)
            except Exception:
                continue
            unused.append(p)

    maya.logger.debug('Removed unused plugins: {}'.format(unused))


def delete_garbage():
    """
    Delete all garbage nodes from scene
    """

    from tpDcc.dccs.maya.core import helpers, node

    straight_delete_types = list()
    if helpers.get_maya_version() > 2014:
        straight_delete_types += ['hyperLayout', 'hyperView']       # Maya 2014 crashes when tyring to remove those
        if 'hyperGraphLayout' in straight_delete_types:
            straight_delete_types.remove('hyperGraphLayout')

    deleted_nodes = node.delete_nodes_of_type(straight_delete_types)
    check_connection_node_type = ['shadingEngine', 'partition', 'objectSet']
    check_connection_nodes = list()
    for check_type in check_connection_node_type:
        nodes_of_type = maya.cmds.ls(type=check_type)
        check_connection_nodes += nodes_of_type

    garbage_nodes = list()
    if deleted_nodes:
        garbage_nodes = deleted_nodes

    nodes_to_skip = ['characterPartition']

    for n in check_connection_nodes:
        if not n or not maya.cmds.objExists(n):
            continue
        if n in nodes_to_skip:
            continue
        if node.is_empty(n):
            maya.cmds.lockNode(n, lock=False)
            try:
                maya.cmds.delete(n)
            except Exception:
                pass

            if not maya.cmds.objExists(n):
                garbage_nodes.append(n)

    maya.logger.debug('Delete Garbage Nodes: {}'.format(garbage_nodes))


def clean_scene():
    """
    Cleans invalid nodes from current scene
    """

    delete_unknown_nodes()
    delete_turtle_nodes()
    delete_unused_plugins()
    delete_garbage()
