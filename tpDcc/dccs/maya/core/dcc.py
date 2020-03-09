#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC functionality for Maya
"""

from __future__ import print_function, division, absolute_import

import logging
from collections import OrderedDict

from Qt.QtWidgets import *

import tpDcc
from tpDcc import register
import tpDcc.dccs.maya as maya
from tpDcc.abstract import dcc as abstract_dcc, progressbar
from tpDcc.dccs.maya.core import gui, helpers, name, namespace, scene, playblast, transform, attribute
from tpDcc.dccs.maya.core import node as maya_node, reference as ref_utils, camera as cam_utils, shader as shader_utils
from tpDcc.dccs.maya.core import sequencer, animation, qtutils, decorators as maya_decorators, shape as shape_utils
from tpDcc.dccs.maya.core import filtertypes

LOGGER = logging.getLogger()


class MayaDcc(abstract_dcc.AbstractDCC, object):

    TYPE_FILTERS = OrderedDict([
        ('All Node Types', filtertypes.ALL_FILTER_TYPE),
        ('Group', filtertypes.GROUP_FILTER_TYPE),
        ('Geometry', ['mesh', 'nurbsSurface']),
        ('Polygon', ['Polygon']),
        ('Nurbs', ['nurbsSurface']),
        ('Joint', ['joint']),
        ('Curve', ['nurbsCurve']),
        ('Locator', ['locator']),
        ('Light', ['light']),
        ('Camera', ['camera']),
        ('Cluster', ['cluster']),
        ('Follicle', ['follicle']),
        ('Deformer', [
            'clusterHandle', 'baseLattice', 'lattice', 'softMod', 'deformBend', 'sculpt',
            'deformTwist', 'deformWave', 'deformFlare']),
        ('Transform', ['transform']),
        ('Controllers', ['control'])
    ])

    @staticmethod
    def get_name():
        """
        Returns the name of the DCC
        :return: str
        """

        return tpDcc.Dccs.Maya

    @staticmethod
    def get_extensions():
        """
        Returns supported extensions of the DCC
        :return: list(str)
        """

        return ['.ma', '.mb']

    @staticmethod
    def get_dpi(value=1):
        """
        Returns current DPI used by DCC
        :param value: float
        :return: float
        """

        qt_dpi = QApplication.devicePixelRatio() if maya.cmds.about(batch=True) else QMainWindow().devicePixelRatio()

        return max(qt_dpi * value, MayaDcc.get_dpi_scale(value))

    @staticmethod
    def get_dpi_scale(value):
        """
        Returns current DPI scale used by DCC
        :return: float
        """

        maya_scale = 1.0 if not hasattr(
            maya.cmds, "mayaDpiSetting") else maya.cmds.mayaDpiSetting(query=True, realScaleValue=True)

        return maya_scale * value

    @staticmethod
    def get_version():
        """
        Returns version of the DCC
        :return: int
        """

        return helpers.get_maya_version()

    @staticmethod
    def get_version_name():
        """
        Returns version of the DCC
        :return: int
        """

        return str(helpers.get_maya_version())

    @staticmethod
    def is_batch():
        """
        Returns whether DCC is being executed in batch mode or not
        :return: bool
        """

        return maya.cmds.about(batch=True)

    @staticmethod
    def get_main_window():
        """
        Returns Qt object that references to the main DCC window
        :return:
        """

        return gui.get_maya_window()

    @staticmethod
    def is_window_floating(window_name):
        """
        Returns whether or not DCC window is floating
        :param window_name: str
        :return: bool
        """

        return gui.is_window_floating(window_name=window_name)

    @staticmethod
    def execute_deferred(fn):
        """
        Executes given function in deferred mode
        """

        maya.utils.executeDeferred(fn)

    @staticmethod
    def object_exists(node):
        """
        Returns whether given object exists or not
        :return: bool
        """

        return maya.cmds.objExists(node)

    @staticmethod
    def object_type(node):
        """
        Returns type of given object
        :param node: str
        :return: str
        """

        return maya.cmds.objectType(node)

    @staticmethod
    def check_object_type(node, node_type, check_sub_types=False):
        """
        Returns whether give node is of the given type or not
        :param node: str
        :param node_type: str
        :param check_sub_types: bool
        :return: bool
        """

        is_type = maya.cmds.objectType(node, isType=node_type)
        if not is_type and check_sub_types:
            is_type = maya.cmds.objectType(node, isAType=node_type)

        return is_type

    @staticmethod
    def create_empty_group(name, parent=None):
        """
        Creates a new empty group node
        :param name: str
        :param parent: str or None
        """

        groups = helpers.create_group(name=name, parent=parent, world=True)
        if groups:
            return groups[0]

    @staticmethod
    def create_node(node_type, node_name):
        """
        Creates a new node of the given type and with the given name
        :param node_type: str
        :param node_name: str
        :return: str
        """

        return maya.cmds.createNode(node_type, name=node_name)

    @staticmethod
    def node_name(node):
        """
        Returns the name of the given node
        :param node: str
        :return: str
        """

        return node

    @staticmethod
    def node_name_without_namespace(node):
        """
        Returns the name of the given node without namespace
        :param node: str
        :return: str
        """

        return name.get_basename(node, remove_namespace=True)

    @staticmethod
    def node_handle(node):
        """
        Returns unique identifier of the given node
        :param node: str
        :return: str
        """

        return maya.cmds.ls(node, uuid=True)

    @staticmethod
    def node_type(node):
        """
        Returns node type of given object
        :param node: str
        :return: str
        """

        return maya.cmds.nodeType(node)

    @staticmethod
    def node_is_empty(node, *args, **kwargs):
        """
        Returns whether given node is an empty one.
        In Maya, an emtpy node is the one that is not referenced, has no child transforms, has no custom attributes
        and has no connections
        :param node: str
        :return: bool
        """

        no_user_attributes = kwargs.pop('no_user_attributes', True)
        no_connections = kwargs.pop('no_connections', True)
        return maya_node.is_empty(node_name=node, no_user_attributes=no_user_attributes, no_connections=no_connections)

    @staticmethod
    def node_world_space_translation(node):
        """
        Returns translation of given node in world space
        :param node: str
        :return: list
        """

        return maya.cmds.xform(node, worldSpace=True, q=True, translation=True)

    @staticmethod
    def translate_node_in_world_space(node, translation_list):
        """
        Translates given node in world space with the given translation vector
        :param node: str
        :param translation_list:  list(float, float, float)
        """

        return maya.cmds.xform(node, worldSpace=True, t=translation_list)

    @staticmethod
    def node_world_space_rotation(node):
        """
        Returns world rotation of given node
        :param node: str
        :return: list
        """

        return maya.cmds.xform(node, worldSpace=True, q=True, rotation=True)

    @staticmethod
    def rotate_node_in_world_space(node, rotation_list):
        """
        Translates given node with the given translation vector
        :param node: str
        :param rotation_list:  list(float, float, float)
        """

        return maya.cmds.xform(node, worldSpace=True, ro=rotation_list)

    @staticmethod
    def node_world_space_scale(node):
        """
        Returns world scale of given node
        :param node: str
        :return: list
        """

        return maya.cmds.xform(node, worldSpace=True, q=True, scale=True)

    @staticmethod
    def scale_node_in_world_space(node, scale_list):
        """
        Scales given node with the given vector list
        :param node: str
        :param scale_list: list(float, float, float)
        """

        return maya.cmds.xform(node, worldSpace=True, s=scale_list)

    @staticmethod
    def all_scene_objects(full_path=True):
        """
        Returns a list with all scene nodes
        :param full_path: bool
        :return: list<str>
        """

        return maya.cmds.ls(long=full_path)

    @staticmethod
    def rename_node(node, new_name, **kwargs):
        """
        Renames given node with new given name
        :param node: str
        :param new_name: str
        :return: str
        """

        uuid = kwargs.get('uuid', None)
        rename_shape = kwargs.get('rename_shape', True)

        return name.rename(node, new_name, uuid=uuid, rename_shape=rename_shape)

    @staticmethod
    def show_object(node):
        """
        Shows given object
        :param node: str
        """

        maya.cmds.showHidden(node)

    @staticmethod
    def hide_object(node):
        """
        Hides given object
        :param node: str
        """

        maya.cmds.hide(node)

    @staticmethod
    def select_object(node, replace_selection=False, **kwargs):
        """
        Selects given object in the current scene
        :param replace_selection: bool
        :param node: str
        """

        maya.cmds.select(node, replace=replace_selection, **kwargs)

    @staticmethod
    def select_hierarchy(root=None, add=False):
        """
        Selects the hierarchy of the given node
        If no object is given current selection will be used
        :param root: str
        :param add: bool, Whether new selected objects need to be added to current selection or not
        """

        if not root or not MayaDcc.object_exists(root):
            sel = maya.cmds.ls(selection=True)
            for obj in sel:
                if not add:
                    maya.cmds.select(clear=True)
                maya.cmds.select(obj, hi=True, add=True)
        else:
            maya.cmds.select(root, hi=True, add=add)

    @staticmethod
    def deselect_object(node):
        """
        Deselects given node from current selection
        :param node: str
        """

        maya.cmds.select(node, deselect=True)

    @staticmethod
    def clear_selection():
        """
        Clears current scene selection
        """

        maya.cmds.select(clear=True)

    @staticmethod
    def delete_object(node):
        """
        Removes given node from current scene
        :param node: str
        """

        maya.cmds.delete(node)

    @staticmethod
    def selected_nodes(full_path=True):
        """
        Returns a list of selected nodes
        :param full_path: bool
        :return: list<str>
        """

        return maya.cmds.ls(sl=True, long=full_path)

    @staticmethod
    def selected_nodes_of_type(node_type, full_path=True):
        """
        Returns a list of selected nodes of given type
        :param node_type: str
        :param full_path: bool
        :return: list(str)
        """

        return maya.cmds.ls(sl=True, type=node_type, long=full_path)

    @staticmethod
    def all_shapes_nodes(full_path=True):
        """
        Returns all shapes nodes in current scene
        :param full_path: bool
        :return: list<str>
        """

        return maya.cmds.ls(shapes=True, long=full_path)

    @staticmethod
    def default_scene_nodes(full_path=True):
        """
        Returns a list of nodes that are created by default by the DCC when a new scene is created
        :param full_path: bool
        :return: list<str>
        """

        return maya.cmds.ls(defaultNodes=True)

    @staticmethod
    def node_short_name(node):
        """
        Returns short name of the given node
        :param node: str
        :return: str
        """

        return name.get_basename(node, remove_namespace=False)

    @staticmethod
    def node_long_name(node):
        """
        Returns long name of the given node
        :param node: str
        :return: str
        """

        return name.get_long_name(node)

    @staticmethod
    def node_object_color(node):
        """
        Returns the color of the given node
        :param node: str
        :return: list(int, int, int, int)
        """

        return maya.cmds.getAttr('{}.objectColor'.format(node))

    @staticmethod
    def node_override_enabled(node):
        """
        Returns whether the given node has its display override attribute enabled or not
        :param node: str
        :return: bool
        """

        return maya.cmds.getAttr('{}.overrideEnabled'.format(node))

    @staticmethod
    def list_namespaces():
        """
        Returns a list of all available namespaces
        :return: list(str)
        """

        return namespace.get_all_namespaces()

    @staticmethod
    def namespace_separator():
        """
        Returns character used to separate namespace from the node name
        :return: str
        """

        return '|'

    @staticmethod
    def namespace_exists(name):
        """
        Returns whether or not given namespace exists in current scene
        :param name: str
        :return: bool
        """

        return namespace.namespace_exists(name)

    @staticmethod
    def unique_namespace(name):
        """
        Returns a unique namespace from the given one
        :param name: str
        :return: str
        """

        return namespace.find_unique_namespace(name)

    @staticmethod
    def node_namespace(node, check_node=True, clean=False):
        """
        Returns namespace of the given node
        :param node: str
        :param check_node: bool
        :param clean: bool
        :return: str
        """

        if MayaDcc.node_is_referenced(node):
            try:
                found_namespace = maya.cmds.referenceQuery(node, namespace=True)
            except Exception as exc:
                found_namespace = namespace.get_namespace(node, check_obj=check_node)
        else:
            found_namespace = namespace.get_namespace(node, check_obj=check_node)
        if not found_namespace:
            return None

        if clean:
            if found_namespace.startswith('|') or found_namespace.startswith(':'):
                found_namespace = found_namespace[1:]

        return found_namespace

    @staticmethod
    def all_nodes_in_namespace(namespace_name):
        """
        Returns all nodes in given namespace
        :return: list(str)
        """

        return namespace.get_all_in_namespace(namespace_name)

    @staticmethod
    def rename_namespace(current_namespace, new_namespace):
        """
        Renames namespace of the given node
        :param current_namespace: str
        :param new_namespace: str
        :return: str
        """

        return namespace.rename_namepace(current_namespace, new_namespace)

    @staticmethod
    def node_parent_namespace(node):
        """
        Returns namespace of the given node parent
        :param node: str
        :return: str
        """

        return maya.cmds.referenceQuery(node, parentNamespace=True)

    @staticmethod
    def node_is_visible(node):
        """
        Returns whether given node is visible or not
        :param node: str
        :return: bool
        """

        return maya_node.is_visible(node=node)

    @staticmethod
    def node_is_referenced(node):
        """
        Returns whether given node is referenced or not
        :param node: str
        :return: bool
        """

        if not maya.cmds.objExists(node):
            return False

        try:
            return maya.cmds.referenceQuery(node, isNodeReferenced=True)
        except Exception as exc:
            return False

    @staticmethod
    def node_reference_path(node, without_copy_number=False):
        """
        Returns reference path of the referenced node
        :param node: str
        :param without_copy_number: bool
        :return: str
        """

        if not maya.cmds.objExists(node):
            return None

        return maya.cmds.referenceQuery(node, filename=True, wcn=without_copy_number)

    @staticmethod
    def node_unreference(node):
        """
        Unreferences given node
        :param node: str
        """

        ref_node = None
        if ref_utils.is_referenced(node):
            ref_node = ref_utils.get_reference_node(node)
        elif ref_utils.is_reference(node):
            ref_node = node

        if ref_node:
            return ref_utils.remove_reference(ref_node)

    @staticmethod
    def node_is_loaded(node):
        """
        Returns whether given node is loaded or not
        :param node: str
        :return: bool
        """

        return maya.cmds.referenceQuery(node, isLoaded=True)

    @staticmethod
    def node_is_locked(node):
        """
        Returns whether given node is locked or not
        :param node: str
        :return: bool
        """

        return maya.cmds.lockNode(node, q=True, long=True)

    @staticmethod
    def node_children(node, all_hierarchy=True, full_path=True):
        """
        Returns a list of children of the given node
        :param node: str
        :param all_hierarchy: bool
        :param full_path: bool
        :return: list<str>
        """

        return maya.cmds.listRelatives(
            node, children=True, allDescendents=all_hierarchy, shapes=False, fullPath=full_path)

    @staticmethod
    def node_parent(node, full_path=True):
        """
        Returns parent node of the given node
        :param node: str
        :param full_path: bool
        :return: str
        """

        node_parent = maya.cmds.listRelatives(node, parent=True, fullPath=full_path)
        if node_parent:
            node_parent = node_parent[0]

        return node_parent

    @staticmethod
    def node_root(node, full_path=True):
        """
        Returns hierarchy root node of the given node
        :param node: str
        :param full_path: bool
        :return: str
        """

        if not node:
            return None

        return scene.get_node_transform_root(node, full_path=full_path)

    @staticmethod
    def set_parent(node, parent):
        """
        Sets the node parent to the given parent
        :param node: str
        :param parent: str
        """

        return maya.cmds.parent(node, parent)

    @staticmethod
    def set_parent_to_world(node):
        """
        Parent given node to the root world node
        :param node: str
        """

        return maya.cmds.parent(node, world=True)

    @staticmethod
    def node_nodes(node):
        """
        Returns referenced nodes of the given node
        :param node: str
        :return: list<str>
        """

        return maya.cmds.referenceQuery(node, nodes=True)

    @staticmethod
    def node_filename(node, no_copy_number=True):
        """
        Returns file name of the given node
        :param node: str
        :param no_copy_number: bool
        :return: str
        """

        return maya.cmds.referenceQuery(node, filename=True, withoutCopyNumber=no_copy_number)

    @staticmethod
    def node_matrix(node):
        """
        Returns the world matrix of the given node
        :param node: str
        :return:
        """

        return transform.get_matrix(transform=node, as_list=True)

    @staticmethod
    def set_node_matrix(node, matrix):
        """
        Sets the world matrix of the given node
        :param node: str
        :param matrix: variant, MMatrix or list
        """

        maya.cmds.xform(node, matrix=matrix, worldSpace=True)

    @staticmethod
    def list_node_types(type_string):
        """
        List all dependency node types satisfying given classification string
        :param type_string: str
        :return:
        """

        return maya.cmds.listNodeTypes(type_string)

    @staticmethod
    def list_nodes(node_name=None, node_type=None, full_path=True):
        """
        Returns list of nodes with given types. If no type, all scene nodes will be listed
        :param node_name:
        :param node_type:
        :param full_path:
        :return:  list<str>
        """

        if not node_name and not node_type:
            return maya.cmds.ls(long=full_path)

        if node_name and node_type:
            return maya.cmds.ls(node_name, type=node_type, long=full_path)
        elif node_name and not node_type:
            return maya.cmds.ls(node_name, long=full_path)
        elif not node_name and node_type:
            return maya.cmds.ls(type=node_type, long=full_path)

    @staticmethod
    def list_children(node, all_hierarchy=True, full_path=True, children_type=None):
        """
        Returns a list of chlidren nodes of the given node
        :param node:
        :param all_hierarchy:
        :param full_path:
        :param children_type:
        :return:
        """

        if children_type:
            return maya.cmds.listRelatives(
                node, children=True, allDescendents=all_hierarchy, fullPath=full_path, type=children_type)
        else:
            return maya.cmds.listRelatives(node, children=True, allDescendents=all_hierarchy, fullPath=full_path)

    @staticmethod
    def list_relatives(
            node, all_hierarchy=True, full_path=True, relative_type=None, shapes=False, intermediate_shapes=False):
        """
        Returns a list of relative nodes of the given node
        :param node:
        :param all_hierarchy:
        :param full_path:
        :param relative_type:
        :param shapes:
        :param intermediate_shapes:
        :return:
        """

        if relative_type:
            return maya.cmds.listRelatives(
                node, allDescendents=all_hierarchy, fullPath=full_path, type=relative_type,
                shapes=shapes, noIntermediate=not intermediate_shapes)
        else:
            return maya.cmds.listRelatives(
                node, allDescendents=all_hierarchy, fullPath=full_path, shapes=shapes,
                noIntermediate=not intermediate_shapes)

    @staticmethod
    def list_shapes(node, full_path=True, intermediate_shapes=False):
        """
        Returns a list of shapes of the given node
        :param node: str
        :param full_path: bool
        :param intermediate_shapes: bool
        :return: list<str>
        """

        return maya.cmds.listRelatives(
            node, shapes=True, fullPath=full_path, children=True, noIntermediate=not intermediate_shapes)

    @staticmethod
    def list_children_shapes(node, all_hierarchy=True, full_path=True, intermediate_shapes=False):
        """
        Returns a list of children shapes of the given node
        :param node:
        :param all_hierarchy:
        :param full_path:
        :param intermediate_shapes:
        :return:
        """

        return shape_utils.get_shapes_in_hierarchy(
            transform_node=node, full_path=full_path, intermediate_shapes=intermediate_shapes)

        # return maya.cmds.listRelatives(node, shapes=True, fullPath=full_path, children=True,
        # allDescendents=all_hierarchy, noIntermediate=not intermediate_shapes)

    @staticmethod
    def shape_transform(shape_node, full_path=True):
        """
        Returns the transform parent of the given shape node
        :param shape_node: str
        :param full_path: bool
        :return: str
        """

        return maya.cmds.listRelatives(shape_node, parent=True, fullPath=full_path)

    @staticmethod
    def default_shaders():
        """
        Returns a list with all thte default shadres of the current DCC
        :return: str
        """

        return shader_utils.get_default_shaders()

    @staticmethod
    def list_materials(skip_default_materials=False, nodes=None):
        """
        Returns a list of materials in the current scene or given nodes
        :param skip_default_materials: bool, Whether to return also standard materials or not
        :param nodes: list(str), list of nodes we want to search materials into. If not given, all scene materials
            will be retrieved
        :return: list(str)
        """

        if nodes:
            all_materials = maya.cmds.ls(nodes, materials=True)
        else:
            all_materials = maya.cmds.ls(materials=True)

        if skip_default_materials:
            default_materials = shader_utils.get_default_shaders()
            for material in default_materials:
                if material in all_materials:
                    all_materials.remove(material)

        return all_materials

    @staticmethod
    def scene_namespaces():
        """
        Returns all the available namespaces in the current scene
        :return: list(str)
        """

        return namespace.get_all_namespaces()

    @staticmethod
    def change_namespace(old_namespace, new_namespace):
        """
        Changes old namespace by a new one
        :param old_namespace: str
        :param new_namespace: str
        """

        return maya.cmds.namespace(rename=[old_namespace, new_namespace])

    @staticmethod
    def change_filename(node, new_filename):
        """
        Changes filename of a given reference node
        :param node: str
        :param new_filename: str
        """

        return maya.cmds.file(new_filename, loadReference=node)

    @staticmethod
    def import_reference(filename):
        """
        Imports object from reference node filename
        :param filename: str
        """

        return maya.cmds.file(filename, importReference=True)

    @staticmethod
    def attribute_default_value(node, attribute_name):
        """
        Returns default value of the attribute in the given node
        :param node: str
        :param attribute_name: str
        :return: object
        """

        try:
            return maya.cmds.attributeQuery(attribute_name, node=node, listDefault=True)
        except Exception:
            try:
                return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), query=True, dv=True)
            except Exception:
                return None

    @staticmethod
    def list_attributes(node, **kwargs):
        """
        Returns list of attributes of given node
        :param node: str
        :return: list<str>
        """

        return maya.cmds.listAttr(node, **kwargs)

    @staticmethod
    def list_user_attributes(node):
        """
        Returns list of user defined attributes
        :param node: str
        :return: list<str>
        """

        return maya.cmds.listAttr(node, userDefined=True)

    @staticmethod
    def add_bool_attribute(node, attribute_name, keyable=False, default_value=False):
        """
        Adds a new boolean attribute into the given node
        :param node: str
        :param attribute_name: str
        :param keyable: bool
        :param default_value: bool
        :return:
        """

        return maya.cmds.addAttr(node, ln=attribute_name, at='bool', k=keyable, dv=default_value)

    @staticmethod
    def add_string_attribute(node, attribute_name, keyable=False):
        """
        Adds a new string attribute into the given node
        :param node: str
        :param attribute_name: str
        :param keyable: bool
        """

        return maya.cmds.addAttr(node, ln=attribute_name, dt='string', k=keyable)

    @staticmethod
    def add_string_array_attribute(node, attribute_name, keyable=False):
        """
        Adds a new string array attribute into the given node
        :param node: str
        :param attribute_name: str
        :param keyable: bool
        """

        return maya.cmds.addAttr(node, ln=attribute_name, dt='stringArray', k=keyable)

    @staticmethod
    def add_message_attribute(node, attribute_name, keyable=False):
        """
        Adds a new message attribute into the given node
        :param node: str
        :param attribute_name: str
        :param keyable: bool
        """

        return maya.cmds.addAttr(node, ln=attribute_name, at='message', k=keyable)

    @staticmethod
    def attribute_query(node, attribute_name, **kwargs):
        """
        Returns attribute qyer
        :param node: str
        :param attribute_name: str
        :param kwargs:
        :return:
        """

        return maya.cmds.attributeQuery(attribute_name, node=node, **kwargs)

    @staticmethod
    def attribute_exists(node, attribute_name):
        """
        Returns whether given attribute exists in given node
        :param node: str
        :param attribute_name: str
        :return: bool
        """

        return maya.cmds.attributeQuery(attribute_name, node=node, exists=True)

    @staticmethod
    def is_attribute_locked(node, attribute_name):
        """
        Returns whether atribute is locked or not
        :param node: str
        :param attribute_name: str
        :return: bool
        """

        return maya.cmds.getAttr('{}.{}'.format(node, attribute_name, lock=True))

    @staticmethod
    def show_attribute(node, attribute_name):
        """
        Shows attribute in DCC UI
        :param node: str
        :param attribute_name: str
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), channelBox=True)

    @staticmethod
    def hide_attribute(node, attribute_name):
        """
        Hides attribute in DCC UI
        :param node: str
        :param attribute_name: str
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), channelBox=False)

    @staticmethod
    def keyable_attribute(node, attribute_name):
        """
        Makes given attribute keyable
        :param node: str
        :param attribute_name: str
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), keyable=True)

    @staticmethod
    def unkeyable_attribute(node, attribute_name):
        """
        Makes given attribute unkeyable
        :param node: str
        :param attribute_name: str
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), keyable=False)

    @staticmethod
    def lock_attribute(node, attribute_name):
        """
        Locks given attribute in given node
        :param node: str
        :param attribute_name: str
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), lock=True)

    @staticmethod
    def unlock_attribute(node, attribute_name):
        """
        Locks given attribute in given node
        :param node: str
        :param attribute_name: str
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), lock=False)

    @staticmethod
    def get_attribute_value(node, attribute_name):
        """
        Returns the value of the given attribute in the given node
        :param node: str
        :param attribute_name: str
        :return: variant
        """

        return attribute.get_attribute(obj=node, attr=attribute_name)

    @staticmethod
    def get_attribute_type(node, attribut_name):
        """
        Returns the type of the given attribute in the given node
        :param node: str
        :param attribute_name: str
        :return: variant
        """

        return maya.cmds.getAttr('{}.{}'.format(node, attribut_name), type=True)

    @staticmethod
    def set_attribute_by_type(node, attribute_name, attribute_value, attribute_type):
        """
        Sets the value of the given attribute in the given node
        :param node: str
        :param attribute_name: str
        :param attribute_value: variant
        :param attribute_type: str
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), attribute_value, type=attribute_type)

    @staticmethod
    def set_boolean_attribute_value(node, attribute_name, attribute_value):
        """
        Sets the boolean value of the given attribute in the given node
        :param node: str
        :param attribute_name: str
        :param attribute_value: int
        :return:
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), bool(attribute_value))

    @staticmethod
    def set_numeric_attribute_value(node, attribute_name, attribute_value, clamp=False):
        """
        Sets the integer value of the given attribute in the given node
       :param node: str
        :param attribute_name: str
        :param attribute_value: int
        :param clamp: bool
        :return:
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), attribute_value, clamp=clamp)

    @staticmethod
    def set_integer_attribute_value(node, attribute_name, attribute_value, clamp=False):
        """
        Sets the integer value of the given attribute in the given node
        :param node: str
        :param attribute_name: str
        :param attribute_value: int
        :param clamp: bool
        :return:
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), int(attribute_value), clamp=clamp)

    @staticmethod
    def set_float_attribute_value(node, attribute_name, attribute_value, clamp=False):
        """
        Sets the integer value of the given attribute in the given node
        :param node: str
        :param attribute_name: str
        :param attribute_value: int
        :param clamp: bool
        :return:
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), float(attribute_value), clamp=clamp)

    @staticmethod
    def set_string_attribute_value(node, attribute_name, attribute_value):
        """
        Sets the string value of the given attribute in the given node
        :param node: str
        :param attribute_name: str
        :param attribute_value: str
        """

        return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), str(attribute_value), type='string')

    @staticmethod
    def set_float_vector3_attribute_value(node, attribute_name, attribute_value):
        """
        Sets the vector3 value of the given attribute in the given node
        :param node: str
        :param attribute_name: str
        :param attribute_value: str
        """

        return maya.cmds.setAttr(
            '{}.{}'.format(node, attribute_name),
            float(attribute_value[0]), float(attribute_value[1]), float(attribute_value[2]), type='double3')

    @staticmethod
    def delete_attribute(node, attribute_name):
        """
        Deletes given attribute of given node
        :param node: str
        :param attribute_name: str
        """

        return maya.cmds.deleteAttr(n=node, at=attribute_name)

    @staticmethod
    def delete_multi_attribute(node, attribute_name, attribute_index):
        """
        Deletes given multi attribute of given node
        :param node: str
        :param attribute_name:str
        :param attribute_index: int or str
        """

        return maya.cmds.removeMultiInstance('{}.{}[{}]'.format(node, attribute_name, attribute_index))

    @staticmethod
    def connect_attribute(source_node, source_attribute, target_node, target_attribute, force=False):
        """
        Connects source attribute to given target attribute
        :param source_node: str
        :param source_attribute: str
        :param target_node: str
        :param target_attribute: str
        :param force: bool
        """

        return maya.cmds.connectAttr(
            '{}.{}'.format(source_node, source_attribute), '{}.{}'.format(target_node, target_attribute), force=force)

    @staticmethod
    def connect_message_attribute(source_node, target_node, message_attribute):
        """
        Connects the message attribute of the input_node into a custom message attribute on target_node
        :param source_node: str, name of a node
        :param target_node: str, name of a node
        :param message_attribute: str, name of the message attribute to create and connect into. If already exists,
        just connect
        """

        attribute.connect_message(source_node, target_node, message_attribute)

    @staticmethod
    def list_connections(node, attribute_name):
        """
        List the connections of the given out attribute in given node
        :param node: str
        :param attribute_name: str
        :return: list<str>
        """

        return maya.cmds.listConnections('{}.{}'.format(node, attribute_name))

    @staticmethod
    def list_connections_of_type(node, connection_type):
        """
        Returns a list of connections with the given type in the given node
        :param node: str
        :param connection_type: str
        :return: list<str>
        """

        return maya.cmds.listConnections(node, type=connection_type)

    @staticmethod
    def list_node_connections(node):
        """
        Returns all connections of the given node
        :param node: str
        :return: list(str)
        """

        return maya.cmds.listConnections(node)

    @staticmethod
    def list_source_destination_connections(node):
        """
        Returns source and destination connections of the given node
        :param node: str
        :return: list<str>
        """

        return maya.cmds.listConnections(node, source=True, destination=True)

    @staticmethod
    def list_source_connections(node):
        """
        Returns source connections of the given node
        :param node: str
        :return: list<str>
        """

        return maya.cmds.listConnections(node, source=True, destination=False)

    @staticmethod
    def list_destination_connections(node):
        """
        Returns source connections of the given node
        :param node: str
        :return: list<str>
        """

        return maya.cmds.listConnections(node, source=False, destination=True)

    @staticmethod
    def new_file(force=True):
        """
        Creates a new file
        :param force: bool
        """

        maya.cmds.file(new=True, f=force)

    @staticmethod
    def open_file(file_path, force=True):
        """
        Open file in given path
        :param file_path: str
        :param force: bool
        """

        return maya.cmds.file(file_path, o=True, f=force, returnNewNodes=True)

    @staticmethod
    def import_file(file_path, force=True, **kwargs):
        """
        Imports given file into current DCC scene
        :param file_path: str
        :param force: bool
        :return:
        """

        namespace = kwargs.get('namespace', None)
        if namespace:
            unique_namespace = kwargs.get('unique_namespace', True)
            if unique_namespace:
                return maya.cmds.file(file_path, i=True, f=force, returnNewNodes=True, namespace=namespace)
            else:
                return maya.cmds.file(
                    file_path, i=True, f=force, returnNewNodes=True, mergeNamespacesOnClash=True, namespace=namespace)
        else:
            return maya.cmds.file(file_path, i=True, f=force, returnNewNodes=True)

    @staticmethod
    def reference_file(file_path, force=True, **kwargs):
        """
        References given file into current DCC scene
        :param file_path: str
        :param force: bool
        :param kwargs: keyword arguments
        :return:
        """

        namespace = kwargs.get('namespace', None)
        if namespace:
            unique_namespace = kwargs.get('unique_namespace', True)
            if unique_namespace:
                return maya.cmds.file(file_path, reference=True, f=force, returnNewNodes=True, namespace=namespace)
            else:
                return maya.cmds.file(
                    file_path, reference=True, f=force, returnNewNodes=True,
                    mergeNamespacesOnClash=True, namespace=namespace)

        else:
            return maya.cmds.file(file_path, reference=True, f=force, returnNewNodes=True)

    @staticmethod
    def is_plugin_loaded(plugin_name):
        """
        Return whether given plugin is loaded or not
        :param plugin_name: str
        :return: bool
        """

        return maya.cmds.pluginInfo(plugin_name, query=True, loaded=True)

    @staticmethod
    def load_plugin(plugin_path, quiet=True):
        """
        Loads given plugin
        :param plugin_path: str
        :param quiet: bool
        """

        return helpers.load_plugin(plugin_path, quiet=quiet)

    @staticmethod
    def unload_plugin(plugin_path):
        """
        Unloads the given plugin
        :param plugin_path: str
        """

        maya.cmds.unloadPlugin(plugin_path)

    @staticmethod
    def list_old_plugins():
        """
        Returns a list of old plugins in the current scene
        :return: list<str>
        """

        return maya.cmds.unknownPlugin(query=True, list=True)

    @staticmethod
    def remove_old_plugin(plugin_name):
        """
        Removes given old plugin from current scene
        :param plugin_name: str
        """

        return maya.cmds.unknownPlugin(plugin_name, remove=True)

    @staticmethod
    def is_component_mode():
        """
        Returns whether current DCC selection mode is component mode or not
        :return: bool
        """

        return maya.cmds.selectMode(query=True, component=True)

    @staticmethod
    def scene_name():
        """
        Returns the name of the current scene
        :return: str
        """

        return maya.cmds.file(query=True, sceneName=True)

    @staticmethod
    def scene_is_modified():
        """
        Returns whether current scene has been modified or not since last save
        :return: bool
        """

        return maya.cmds.file(query=True, modified=True)

    @staticmethod
    def save_current_scene(force=True):
        """
        Saves current scene
        :param force: bool
        """

        scene_name = MayaDcc.scene_name()
        if scene_name:
            return maya.cmds.file(save=True, f=force)
        else:
            if force:
                return maya.cmds.SaveScene()
            else:
                if MayaDcc.scene_is_modified():
                    return maya.cmds.SaveScene()

        return False

    @staticmethod
    def confirm_dialog(title, message, button=None, cancel_button=None, default_button=None, dismiss_string=None):
        """
        Shows DCC confirm dialog
        :param title:
        :param message:
        :param button:
        :param cancel_button:
        :param default_button:
        :param dismiss_string:
        :return:
        """

        if button and cancel_button and dismiss_string and default_button:
            return maya.cmds.confirmDialog(
                title=title, message=message, button=button, cancelButton=cancel_button,
                defaultButton=default_button, dismissString=dismiss_string)

        if button:
            return maya.cmds.confirmDialog(title=title, message=message)
        else:
            return maya.cmds.confirmDialog(title=title, message=message, button=button)

    @staticmethod
    def warning(message):
        """
        Prints a warning message
        :param message: str
        :return:
        """

        maya.cmds.warning(message)

    @staticmethod
    def error(message):
        """
        Prints a error message
        :param message: str
        :return:
        """

        maya.cmds.error(message)

    @staticmethod
    def show_message_in_viewport(msg, **kwargs):
        """
        Shows a message in DCC viewport
        :param msg: str, Message to show
        :param kwargs: dict, extra arguments
        """

        color = kwargs.get('color', '')
        pos = kwargs.get('pos', 'topCenter')

        if color != '':
            msg = "<span style=\"color:{0};\">{1}</span>".format(color, msg)

        maya.cmds.inViewMessage(amg=msg, pos=pos, fade=True, fst=1000, dk=True)

    @staticmethod
    def add_shelf_menu_item(parent, label, command='', icon=''):
        """
        Adds a new menu item
        :param parent:
        :param label:
        :param command:
        :param icon:
        :return:
        """

        return maya.cmds.menuItem(parent=parent, labelong=label, command=command, image=icon or '')

    @staticmethod
    def add_shelf_sub_menu_item(parent, label, icon=''):
        """
        Adds a new sub menu item
        :param parent:
        :param label:
        :param icon:
        :return:
        """

        return maya.cmds.menuItem(parent=parent, labelong=label, icon=icon or '', subMenu=True)

    @staticmethod
    def add_shelf_separator(shelf_name):
        """
        Adds a new separator to the given shelf
        :param shelf_name: str
        """

        return maya.cmds.separator(
            parent=shelf_name, manage=True, visible=True, horizontalong=False,
            style='shelf', enableBackground=False, preventOverride=False)

    @staticmethod
    def shelf_exists(shelf_name):
        """
        Returns whether given shelf already exists or not
        :param shelf_name: str
        :return: bool
        """

        return gui.shelf_exists(shelf_name=shelf_name)

    @staticmethod
    def create_shelf(shelf_name, shelf_labelong=None):
        """
        Creates a new shelf with the given name
        :param shelf_name: str
        :param shelf_label: str
        """

        return gui.create_shelf(name=shelf_name)

    @staticmethod
    def delete_shelf(shelf_name):
        """
        Deletes shelf with given name
        :param shelf_name: str
        """

        return gui.delete_shelf(shelf_name=shelf_name)

    @staticmethod
    def select_file_dialog(title, start_directory=None, pattern=None):
        """
        Shows select file dialog
        :param title: str
        :param start_directory: str
        :param pattern: str
        :return: str
        """

        if not pattern:
            pattern = 'All Files (*.*)'

        res = maya.cmds.fileDialog2(fm=1, dir=start_directory, cap=title, ff=pattern)
        if res:
            res = res[0]

        return res

    @staticmethod
    def select_folder_dialog(title, start_directory=None):
        """
        Shows select folder dialog
        :param title: str
        :param start_directory: str
        :return: str
        """

        res = maya.cmds.fileDialog2(fm=3, dir=start_directory, cap=title)
        if res:
            res = res[0]

        return res

    @staticmethod
    def save_file_dialog(title, start_directory=None, pattern=None):
        """
        Shows save file dialog
        :param title: str
        :param start_directory: str
        :param pattern: str
        :return: str
        """

        res = maya.cmds.fileDialog2(fm=0, dir=start_directory, cap=title, ff=pattern)
        if res:
            res = res[0]

        return res

    @staticmethod
    def get_start_frame():
        """
        Returns current start frame
        :return: int
        """

        return maya.cmds.playbackOptions(query=True, minTime=True)

    @staticmethod
    def get_end_frame():
        """
        Returns current end frame
        :return: int
        """

        return maya.cmds.playbackOptions(query=True, maxTime=True)

    @staticmethod
    def get_current_frame():
        """
        Returns current frame set in time slider
        :return: int
        """

        return gui.get_current_frame()

    @staticmethod
    def set_current_frame(frame):
        """
        Sets the current frame in time slider
        :param frame: int
        """

        return gui.set_current_frame(frame)

    @staticmethod
    def get_time_slider_range():
        """
        Return the time range from Maya time slider
        :return: list<int, int>
        """

        return gui.get_time_slider_range(highlighted=False)

    @staticmethod
    def fit_view(animation=True):
        """
        Fits current viewport to current selection
        :param animation: bool, Animated fit is available
        """

        maya.cmds.viewFit(an=animation)

    @staticmethod
    def refresh_viewport():
        """
        Refresh current DCC viewport
        """

        maya.cmds.refresh()

    @staticmethod
    def set_key_frame(node, attribute_name, **kwargs):
        """
        Sets keyframe in given attribute in given node
        :param node: str
        :param attribute_name: str
        :param kwargs:
        :return:
        """

        return maya.cmds.setKeyframe('{}.{}'.format(node, attribute_name), **kwargs)

    @staticmethod
    def copy_key(node, attribute_name, time=None):
        """
        Copy key frame of given node
        :param node: str
        :param attribute_name: str
        :param time: bool
        :return:
        """

        if time:
            return maya.cmds.copyKey('{}.{}'.format(node, attribute_name), time=time)
        else:
            return maya.cmds.copyKey('{}.{}'.format(node, attribute_name))

    @staticmethod
    def cut_key(node, attribute_name, time=None):
        """
        Cuts key frame of given node
        :param node: str
        :param attribute_name: str
        :param time: str
        :return:
        """

        if time:
            return maya.cmds.cutKey('{}.{}'.format(node, attribute_name), time=time)
        else:
            return maya.cmds.cutKey('{}.{}'.format(node, attribute_name))

    @staticmethod
    def paste_key(node, attribute_name, option, time, connect):
        """
        Paste copied key frame
        :param node: str
        :param attribute_name: str
        :param option: str
        :param time: (int, int)
        :param connect: bool
        :return:
        """

        return maya.cmds.pasteKey('{}.{}'.format(node, attribute_name), option=option, time=time, connect=connect)

    @staticmethod
    def offset_keyframes(node, attribute_name, start_time, end_time, duration):
        """
        Offset given node keyframes
        :param node: str
        :param attribute_name: str
        :param start_time: int
        :param end_time: int
        :param duration: float
        """

        return maya.cmds.keyframe(
            '{}.{}'.format(node, attribute_name), relative=True, time=(start_time, end_time), timeChange=duration)

    @staticmethod
    def find_next_key_frame(node, attribute_name, start_time, end_time):
        """
        Returns next keyframe of the given one
        :param node: str
        :param attribute_name: str
        :param start_time: int
        :param end_time: int
        """

        return maya.cmds.findKeyframe('{}.{}'.format(node, attribute_name), time=(start_time, end_time), which='next')

    @staticmethod
    def set_flat_key_frame(self, node, attribute_name, start_time, end_time):
        """
        Sets flat tangent in given keyframe
        :param node: str
        :param attribute_name: str
        :param start_time: int
        :param end_time: int
        """

        return maya.cmds.keyTangent('{}.{}'.format(node, attribute_name), time=(start_time, end_time), itt='flat')

    @staticmethod
    def find_first_key_in_anim_curve(curve):
        """
        Returns first key frame of the given curve
        :param curve: str
        :return: int
        """

        return maya.cmds.findKeyframe(curve, which='first')

    @staticmethod
    def find_last_key_in_anim_curve(curve):
        """
        Returns last key frame of the given curve
        :param curve: str
        :return: int
        """

        return maya.cmds.findKeyframe(curve, which='last')

    @staticmethod
    def copy_anim_curve(curve, start_time, end_time):
        """
        Copies given anim curve
        :param curve: str
        :param start_time: int
        :param end_time: int
        """

        return maya.cmds.copyKey(curve, time=(start_time, end_time))

    @staticmethod
    def get_current_model_panel():
        """
        Returns the current model panel name
        :return: str | None
        """

        current_panel = maya.maya.cmds.getPanel(withFocus=True)
        current_panel_type = maya.maya.cmds.getPanel(typeOf=current_panel)

        if current_panel_type not in ['modelPanel']:
            return None

        return current_panel

    @staticmethod
    def enable_undo():
        """
        Enables undo functionality
        """

        maya.cmds.undoInfo(openChunk=True)

    @staticmethod
    def disable_undo():
        """
        Disables undo functionality
        """

        maya.cmds.undoInfo(closeChunk=True)

    @staticmethod
    def focus(object_to_focus):
        """
        Focus in given object
        :param object_to_focus: str
        """

        maya.cmds.setFocus(object_to_focus)

    @staticmethod
    def find_unique_name(
            obj_names=None, filter_type=None, include_last_number=True, do_rename=False,
            search_hierarchy=False, selection_only=True, **kwargs):
        """
        Returns a unique node name by adding a number to the end of the node name
        :param obj_names: str, name or list of names to find unique name from
        :param filter_type: str, find unique name on nodes that matches given filter criteria
        :param include_last_number: bool
        :param do_rename: bool
       :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene object
        :return: str
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.find_unique_name_by_filter(
                filter_type=filter_type, include_last_number=include_last_number, do_rename=do_rename,
                rename_shape=rename_shape, search_hierarchy=search_hierarchy, selection_only=selection_only,
                dag=False, remove_maya_defaults=True, transforms_only=True)
        else:
            return name.find_unique_name(
                obj_names=obj_names, include_last_number=include_last_number, do_rename=do_rename,
                rename_shape=rename_shape)

    @staticmethod
    def find_available_name(node_name, **kwargs):
        """
        Returns an available object name in current DCC scene
        :param node_name: str
        :param kwargs: dict
        :return: str
        """

        suffix = kwargs.get('suffix', None)
        index = kwargs.get('index', 0)
        padding = kwargs.get('padding', 0)
        letters = kwargs.get('letters', False)
        capital = kwargs.get('capital', False)

        return name.find_available_name(
            name=node_name, suffix=suffix, index=index, padding=padding, letters=letters, capitalong=capital)

    @staticmethod
    def clean_scene():
        """
        Cleans invalid nodes from current scene
        """

        scene.clean_scene()

    @staticmethod
    def is_camera(node_name):
        """
        Returns whether given node is a camera or not
        :param node_name: str
        :return: bool
        """

        return cam_utils.is_camera(node_name)

    @staticmethod
    def get_all_cameras(full_path=True):
        """
        Returns all cameras in the scene
        :param full_path: bool
        :return: list(str)
        """

        return cam_utils.get_all_cameras(exclude_standard_cameras=True, return_transforms=True, full_path=full_path)

    @staticmethod
    def get_current_camera(full_path=True):
        """
        Returns camera currently being used in scene
        :param full_path: bool
        :return: list(str)
        """

        return cam_utils.get_current_camera(full_path=full_path)

    @staticmethod
    def look_through_camera(camera_name):
        """
        Updates DCC viewport to look through given camera
        :param camera_name: str
        :return:
        """

        return maya.cmds.lookThru(camera_name)

    @staticmethod
    def get_camera_focal_length(camera_name):
        """
        Returns focal length of the given camera
        :param camera_name: str
        :return: float
        """

        return maya.cmds.getAttr('{}.focalLength'.format(camera_name))

    @staticmethod
    def get_playblast_formats():
        """
        Returns a list of supported formats for DCC playblast
        :return: list(str)
        """

        return playblast.get_playblast_formats()

    @staticmethod
    def get_playblast_compressions(playblast_format):
        """
        Returns a list of supported compressions for DCC playblast
        :param playblast_format: str
        :return: list(str)
        """

        return playblast.get_playblast_compressions(format=playblast_format)

    @staticmethod
    def get_viewport_resolution_width():
        """
        Returns the default width resolution of the current DCC viewport
        :return: int
        """

        current_panel = gui.get_active_editor()
        if not current_panel:
            return 0

        return maya.cmds.control(current_panel, query=True, width=True)

    @staticmethod
    def get_viewport_resolution_height():
        """
        Returns the default height resolution of the current DCC viewport
        :return: int
        """

        current_panel = gui.get_active_editor()
        if not current_panel:
            return 0

        return maya.cmds.control(current_panel, query=True, height=True)

    @staticmethod
    def get_renderers():
        """
        Returns dictionary with the different renderers supported by DCC
        :return: dict(str, str)
        """

        active_editor = gui.get_active_editor()
        if not active_editor:
            return {}

        renderers_ui = maya.cmds.modelEditor(active_editor, query=True, rendererListUI=True)
        renderers_id = maya.cmds.modelEditor(active_editor, query=True, rendererList=True)

        renderers = dict(zip(renderers_ui, renderers_id))

        return renderers

    @staticmethod
    def get_default_render_resolution_width():
        """
        Sets the default resolution of the current DCC panel
        :return: int
        """

        return maya.cmds.getAttr('defaultResolution.width')

    @staticmethod
    def get_default_render_resolution_height():
        """
        Sets the default resolution of the current DCC panel
        :return: int
        """

        return maya.cmds.getAttr('defaultResolution.height')

    @staticmethod
    def get_default_render_resolution_aspect_ratio():
        """
        Returns the default resolution aspect ratio of the current DCC render settings
        :return: float
        """

        return maya.cmds.getAttr('defaultResolution.deviceAspectRatio')

    @staticmethod
    def match_translation(source_node, target_node):
        """
        Match translation of the given node to the translation of the target node
        :param source_node: str
        :param target_node: str
        """

        return transform.MatchTransform(source_node, target_node).translation()

    @staticmethod
    def match_rotation(source_node, target_node):
        """
        Match rotation of the given node to the rotation of the target node
        :param source_node: str
        :param target_node: str
        """

        return transform.MatchTransform(source_node, target_node).rotation()

    @staticmethod
    def match_scale(source_node, target_node):
        """
        Match scale of the given node to the rotation of the target node
        :param source_node: str
        :param target_node: str
        """

        return transform.MatchTransform(source_node, target_node).scale()

    @staticmethod
    def match_translation_rotation(source_node, target_node):
        """
        Match translation and rotation of the given node to the translation and rotation of the target node
        :param source_node: str
        :param target_node: str
        """

        return transform.MatchTransform(source_node, target_node).translation_rotation()

    @staticmethod
    def match_transform(source_node, target_node):
        """
        Match the transform (translation, rotation and scale) of the given node to the rotation of the target node
        :param source_node: str
        :param target_node: str
        """

        valid_translate_rotate = transform.MatchTransform(source_node, target_node).translation_rotation()
        valid_scale = transform.MatchTransform(source_node, target_node).scale()

        return bool(valid_translate_rotate and valid_scale)

    @staticmethod
    def open_render_settings():
        """
        Opens DCC render settings options
        """

        gui.open_render_settings_window()

    @staticmethod
    def all_scene_shots():
        """
        Returns all shots in current scene
        :return: list(str)
        """

        return sequencer.get_all_scene_shots()

    @staticmethod
    def shot_is_muted(shot_node):
        """
        Returns whether or not given shot node is muted
        :param shot_node: str
        :return: bool
        """

        return sequencer.get_shot_is_muted(shot_node)

    @staticmethod
    def shot_track_number(shot_node):
        """
        Returns track where given shot node is located
        :param shot_node: str
        :return: int
        """

        return sequencer.get_shot_track_number(shot_node)

    @staticmethod
    def shot_start_frame_in_sequencer(shot_node):
        """
        Returns the start frame of the given shot in sequencer time
        :param shot_node: str
        :return: int
        """

        return sequencer.get_shot_start_frame_in_sequencer(shot_node)

    @staticmethod
    def shot_end_frame_in_sequencer(shot_node):
        """
        Returns the end frame of the given shot in sequencer time
        :param shot_node: str
        :return: int
        """

        return sequencer.get_shot_end_frame_in_sequencer(shot_node)

    @staticmethod
    def shot_pre_hold(shot_node):
        """
        Returns shot prehold value
        :param shot_node: str
        :return: int
        """

        return sequencer.get_shot_post_hold(shot_node)

    @staticmethod
    def shot_post_hold(shot_node):
        """
        Returns shot posthold value
        :param shot_node: str
        :return: int
        """

        return sequencer.get_shot_pre_hold(shot_node)

    @staticmethod
    def shot_scale(shot_node):
        """
        Returns the scale of the given shot
        :param shot_node: str
        :return: int
        """

        return sequencer.get_shot_scale(shot_node)

    @staticmethod
    def shot_start_frame(shot_node):
        """
        Returns the start frame of the given shot
        :param shot_node: str
        :return: int
        """

        return sequencer.get_shot_start_frame(shot_node)

    @staticmethod
    def set_shot_start_frame(shot_node, start_frame):
        """
        Sets the start frame of the given shot
        :param shot_node: str
        :param start_frame: int
        :return: int
        """

        return maya.cmds.setAttr('{}.startFrame'.format(shot_node), start_frame)

    @staticmethod
    def shot_end_frame(shot_node):
        """
        Returns the end frame of the given shot
        :param shot_node: str
        :return: int
        """

        return sequencer.get_shot_end_frame(shot_node)

    @staticmethod
    def set_shot_end_frame(shot_node, end_frame):
        """
        Sets the end frame of the given shot
        :param shot_node: str
        :param end_frame: int
        :return: int
        """

        return maya.cmds.setAttr('{}.endFrame'.format(shot_node), end_frame)

    @staticmethod
    def shot_camera(shot_node):
        """
        Returns camera associated given node
        :param shot_node: str
        :return: str
        """

        return sequencer.get_shot_camera(shot_node)

    @staticmethod
    def export_shot_animation_curves(anim_curves_to_export, export_file_path, start_frame, end_frame, *args, **kwargs):
        """
        Exports given shot animation curves in the given path and in the given frame range
        :param anim_curves_to_export: list(str), animation curves to export
        :param export_file_path: str, file path to export animation curves information into
        :param start_frame: int, start frame to export animation from
        :param end_frame: int, end frame to export animation until
        :param args:
        :param kwargs:
        :return:
        """

        sequencer_least_key = kwargs.get('sequencer_least_key', None)
        sequencer_great_key = kwargs.get('sequencer_great_key', None)

        return sequencer.export_shot_animation_curves(
            anim_curves_to_export=anim_curves_to_export, export_file_path=export_file_path, start_frame=start_frame,
            end_frame=end_frame, sequencer_least_key=sequencer_least_key, sequencer_great_key=sequencer_great_key)

    @staticmethod
    def import_shot_animation_curves(anim_curves_to_import, import_file_path, start_frame, end_frame):
        """
        Imports given shot animation curves in the given path and in the given frame range
        :param anim_curves_to_import: list(str), animation curves to import
        :param import_file_path: str, file path to import animation curves information fron
        :param start_frame: int, start frame to import animation from
        :param end_frame: int, end frame to import animation until
        :param args:
        :param kwargs:
        """

        return sequencer.import_shot_animation_curves(
            anim_curves_to_import=anim_curves_to_import, import_file_path=import_file_path,
            start_frame=start_frame, end_frame=end_frame)

    @staticmethod
    def node_animation_curves(node):
        """
        Returns all animation curves of the given node
        :param node: str
        :return:
        """

        return animation.get_node_animation_curves(node)

    @staticmethod
    def all_animation_curves():
        """
        Returns all animation located in current DCC scene
        :return: list(str)
        """

        return animation.get_all_anim_curves()

    @staticmethod
    def all_keyframes_in_anim_curves(anim_curves=None):
        """
        Retursn al keyframes in given anim curves
        :param anim_curves: list(str)
        :return: list(str)
        """

        return animation.get_all_keyframes_in_anim_curves(anim_curves)

    @staticmethod
    def key_all_anim_curves_in_frames(frames, anim_curves=None):
        """
        Inserts keyframes on all animation curves on given frame
        :param frame: list(int)
        :param anim_curves: list(str)
        """

        return animation.key_all_anim_curves_in_frames(frames=frames, anim_curves=anim_curves)

    @staticmethod
    def remove_keys_from_animation_curves(range_to_delete, anim_curves=None):
        """
        Inserts keyframes on all animation curves on given frame
        :param range_to_delete: list(int ,int)
        :param anim_curves: list(str)
        """

        return animation.delete_keys_from_animation_curves_in_range(
            range_to_delete=range_to_delete, anim_curves=anim_curves)

    @staticmethod
    def check_anim_curves_has_fraction_keys(anim_curves, selected_range=None):
        """
        Returns whether or not given curves have or not fraction keys
        :param anim_curves: list(str)
        :param selected_range: list(str)
        :return: bool
        """

        return animation.check_anim_curves_has_fraction_keys(anim_curves=anim_curves, selected_range=selected_range)

    @staticmethod
    def convert_fraction_keys_to_whole_keys(animation_curves=None, consider_selected_range=False):
        """
        Find keys on fraction of a frame and insert a key on the nearest whole number frame
        Useful to make sure that no keys are located on fraction of frames
        :param animation_curves: list(str)
        :param consider_selected_range: bool
        :return:
        """

        return animation.convert_fraction_keys_to_whole_keys(
            animation_curves=animation_curves, consider_selected_range=consider_selected_range)

    @staticmethod
    def set_active_frame_range(start_frame, end_frame):
        """
        Sets current animation frame range
        :param start_frame: int
        :param end_frame: int
        """

        return animation.set_active_frame_range(start_frame, end_frame)

    @staticmethod
    def create_aim_constraint(source, point_to, **kwargs):
        """
        Sets current animation frame range
        :param source: str
        :param point_to: str
        """

        aim_axis = kwargs.get('aim_axis')
        up_axis = kwargs.get('up_axis')
        world_up_axis = kwargs.get('world_up_axis')
        world_up_type = kwargs.get('world_up_type', 'vector')
        weight = kwargs.get('weight', 1.0)
        return maya.cmds.aimConstraint(
            point_to, source, aim=aim_axis, upVector=up_axis,
            worldUpVector=world_up_axis, worldUpType=world_up_type, weight=weight
        )

    @staticmethod
    def zero_scale_joint(jnt):
        """
        Sets the given scale to zero and compensate the change by modifying the joint translation and rotation
        :param jnt: str
        """

        return maya.cmds.joint(jnt, edit=True, zeroScaleOrient=True)

    @staticmethod
    def delete_history(node):
        """
        Removes the history of the given node
        """

        return transform.delete_history(node=node)

    @staticmethod
    def freeze_transforms(node, **kwargs):
        """
        Freezes the transformations of the given node and its children
        :param node: str
        """

        translate = kwargs.get('translate', True)
        rotate = kwargs.get('rotate', True)
        scale = kwargs.get('scale', True)
        normal = kwargs.get('normal', False)
        preserve_normals = kwargs.get('preserve_normals', True)
        clean_history = kwargs.get('clean_history', False)

        return transform.freeze_transforms(
            node=node, translate=translate, rotate=rotate, scale=scale, normal=normal,
            preserve_normals=preserve_normals, clean_history=clean_history)

    @staticmethod
    def reset_node_transforms(node, **kwargs):
        """
        Reset the transformations of the given node and its children
        :param node: str
        """

        # TODO: We should call freze transforms passing apply as False?

        return maya.cmds.ResetTransformations()

    @staticmethod
    def set_node_rotation_axis_in_object_space(node, x, y, z):
        """
        Sets the rotation axis of given node in object space
        :param node: str
        :param x: int
        :param y: int
        :param z: int
        """

        return maya.cmds.xform(node, rotateAxis=[x, y, z], relative=True, objectSpace=True)

    @staticmethod
    def filter_nodes_by_type(filter_type, search_hierarchy=False, selection_only=True, **kwargs):
        """
        Returns list of nodes in current scene filtered by given filter
        :param filter_type: str, filter used to filter nodes to edit index of
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search all scene objects or only selected ones
        :param kwargs:
        :return: list(str), list of filtered nodes
        """

        dag = kwargs.get('dag', False)
        remove_maya_defaults = kwargs.get('remove_maya_defaults', True)
        transforms_only = kwargs.get('transforms_only', True)

        return filtertypes.filter_by_type(
            filter_type=filter_type, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=dag,
            remove_maya_defaults=remove_maya_defaults, transforms_only=transforms_only)

    @staticmethod
    def add_name_prefix(
            prefix, obj_names=None, filter_type=None, add_underscore=False, search_hierarchy=False,
            selection_only=True, **kwargs):
        """
        Add prefix to node name
        :param prefix: str, string to add to the start of the current node
        :param obj_names: str or list(str), name of list of node names to rename
        :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
        :param add_underscore: bool, Whether or not to add underscore before the suffix
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene objects
        :param kwargs:
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.add_prefix_by_filter(
                prefix=prefix, filter_type=filter_type, rename_shape=rename_shape, add_underscore=add_underscore,
                search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False, remove_maya_defaults=True,
                transforms_only=True)
        else:
            return name.add_prefix(
                prefix=prefix, obj_names=obj_names, add_underscore=add_underscore, rename_shape=rename_shape)

    @staticmethod
    def add_name_suffix(
            suffix, obj_names=None, filter_type=None, add_underscore=False, search_hierarchy=False,
            selection_only=True, **kwargs):
        """
        Add prefix to node name
        :param suffix: str, string to add to the end of the current node
        :param obj_names: str or list(str), name of list of node names to rename
        :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
        :param add_underscore: bool, Whether or not to add underscore before the suffix
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene objects
        :param kwargs:
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.add_suffix_by_filter(
                suffix=suffix, filter_type=filter_type, add_underscore=add_underscore, rename_shape=rename_shape,
                search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False, remove_maya_defaults=True,
                transforms_only=True)
        else:
            return name.add_suffix(
                suffix=suffix, obj_names=obj_names, add_underscore=add_underscore, rename_shape=rename_shape)

    @staticmethod
    def remove_name_prefix(
            obj_names=None, filter_type=None, separator='_', search_hierarchy=False, selection_only=True, **kwargs):
        """
        Removes prefix from node name
        :param obj_names: str or list(str), name of list of node names to rename
        :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
        :param separator: str, separator character for the prefix
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene objects
        :param kwargs:
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.edit_item_index_by_filter(
                index=0, filter_type=filter_type, text='', mode=name.EditIndexModes.REMOVE, separator=separator,
                rename_shape=rename_shape, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False,
                remove_maya_defaults=True, transforms_only=True)
        else:
            return name.edit_item_index(
                obj_names=obj_names, index=0, mode=name.EditIndexModes.REMOVE, separator=separator,
                rename_shape=rename_shape)

    @staticmethod
    def remove_name_suffix(
            obj_names=None, filter_type=None, separator='_', search_hierarchy=False, selection_only=True, **kwargs):
        """
        Removes suffix from node name
        :param obj_names: str or list(str), name of list of node names to rename
        :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
        :param separator: str, separator character for the suffix
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene objects
        :param kwargs:
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.edit_item_index_by_filter(
                index=-1, filter_type=filter_type, text='', mode=name.EditIndexModes.REMOVE, separator=separator,
                rename_shape=rename_shape, search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False,
                remove_maya_defaults=True, transforms_only=True)
        else:
            return name.edit_item_index(
                obj_names=obj_names, index=-1, mode=name.EditIndexModes.REMOVE, separator=separator,
                rename_shape=rename_shape)

    @staticmethod
    def auto_name_suffix(obj_names=None, filter_type=None, search_hierarchy=False, selection_only=True, **kwargs):
        """
        Automatically add a sufix to node names
        :param obj_names: str or list(str), name of list of node names to rename
        :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
        :param separator: str, separator character for the suffix
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene objects
        :param kwargs:
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.auto_suffix_object_by_type(
                filter_type=filter_type, rename_shape=rename_shape, search_hierarchy=search_hierarchy,
                selection_only=selection_only, dag=False, remove_maya_defaults=True, transforms_only=True)
        else:
            return name.auto_suffix_object(obj_names=obj_names, rename_shape=rename_shape)

    @staticmethod
    def remove_name_numbers(
            obj_names=None, filter_type=None, search_hierarchy=False, selection_only=True, remove_underscores=True,
            trailing_only=False, **kwargs):
        """
        Removes numbers from node names
        :param obj_names: str or list(str), name of list of node names to rename
        :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene objects
        :param remove_underscores: bool, Whether or not to remove unwanted underscores
        :param trailing_only: bool, Whether or not to remove only numbers at the ned of the name
        :param kwargs:
        :return:
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.remove_numbers_from_object_by_filter(
                filter_type=filter_type, rename_shape=rename_shape, remove_underscores=remove_underscores,
                trailing_only=trailing_only, search_hierarchy=search_hierarchy, selection_only=selection_only,
                dag=False, remove_maya_defaults=True, transforms_only=True)
        else:
            return name.remove_numbers_from_object(
                obj_names=obj_names, trailing_only=trailing_only, rename_shape=rename_shape,
                remove_underscores=remove_underscores)

    @staticmethod
    def renumber_objects(
            obj_names=None, filter_type=None, remove_trailing_numbers=True, add_underscore=True, padding=2,
            search_hierarchy=False, selection_only=True, **kwargs):
        """
        Removes numbers from node names
        :param obj_names: str or list(str), name of list of node names to rename
        :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
        :param remove_trailing_numbers: bool, Whether to remove trailing numbers before doing the renumber
        :param add_underscore: bool, Whether or not to remove underscore between name and new number
        :param padding: int, amount of numerical padding (2=01, 3=001, etc). Only used if given names has no numbers.
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene objects
        :param kwargs:
        :return:
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.renumber_objects_by_filter(
                filter_type=filter_type, remove_trailing_numbers=remove_trailing_numbers,
                add_underscore=add_underscore, padding=padding, rename_shape=rename_shape,
                search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False, remove_maya_defaults=True,
                transforms_only=True
            )
        else:
            return name.renumber_objects(
                obj_names=obj_names, remove_trailing_numbers=remove_trailing_numbers,
                add_underscore=add_underscore, padding=padding)

    @staticmethod
    def change_suffix_padding(
            obj_names=None, filter_type=None, add_underscore=True, padding=2,
            search_hierarchy=False, selection_only=True, **kwargs):
        """
        Removes numbers from node names
        :param obj_names: str or list(str), name of list of node names to rename
        :param filter_type: str, name of object type to filter the objects to apply changes ('Group, 'Joint', etc)
        :param add_underscore: bool, Whether or not to remove underscore between name and new number
        :param padding: int, amount of numerical padding (2=01, 3=001, etc). Only used if given names has no numbers.
        :param search_hierarchy: bool, Whether to search objects in hierarchies
        :param selection_only: bool, Whether to search only selected objects or all scene objects
        :param kwargs:
        :return:
        """

        rename_shape = kwargs.get('rename_shape', True)

        if filter_type:
            return name.change_suffix_padding_by_filter(
                filter_type=filter_type, add_underscore=add_underscore, padding=padding, rename_shape=rename_shape,
                search_hierarchy=search_hierarchy, selection_only=selection_only, dag=False, remove_maya_defaults=True,
                transforms_only=True
            )
        else:
            return name.change_suffix_padding(obj_names=obj_names, add_underscore=add_underscore, padding=padding)

    @staticmethod
    def dock_widget(widget, *args, **kwargs):
        """
        Docks given widget into current DCC UI
        :param widget: QWidget
        :param args:
        :param kwargs:
        :return:
        """

        return qtutils.dock_widget(widget, *args, **kwargs)

    @staticmethod
    def deferred_function(fn, *args, **kwargs):
        """
        Calls given function with given arguments in a deferred way
        :param fn:
        :param args: list
        :param kwargs: dict
        """

        return maya.cmds.evalDeferred(fn, *args, **kwargs)

    # =================================================================================================================

    @staticmethod
    def get_dockable_window_class():
        return MayaDockedWindow

    @staticmethod
    def get_progress_bar(**kwargs):
        return MayaProgessBar(**kwargs)

    @staticmethod
    def get_progress_bar_class():
        """
        Return class of progress bar
        :return: class
        """

        return MayaProgessBar

    @staticmethod
    def get_undo_decorator():
        """
        Returns undo decorator for current DCC
        """

        return maya_decorators.undo_chunk


class MayaProgessBar(progressbar.AbstractProgressBar, object):
    """
    Util class to manipulate Maya progress bar
    """

    def __init__(self, title='', count=None, begin=True):
        super(MayaProgessBar, self).__init__(title=title, count=count, begin=begin)

        if maya.cmds.about(batch=True):
            self.title = title
            self.count = count
            msg = '{} count: {}'.format(title, count)
            self.status_string = ''
            LOGGER.debug(msg)
            return
        else:
            self.progress_ui = gui.get_progress_bar()
            if begin:
                self.__class__.inc_value = 0
                self.end()
            if not title:
                title = maya.cmds.progressBar(self.progress_ui, query=True, status=True)
            if not count:
                count = maya.cmds.progressBar(self.progress_ui, query=True, maxValue=True)

            maya.cmds.progressBar(
                self.progress_ui, edit=True, beginProgress=begin, isInterruptable=True, status=title, maxValue=count)

    def set_count(self, count_number):
        maya.cmds.progressBar(self.progress_ui, edit=True, maxValue=int(count_number))

    def get_count(self):
        return maya.cmds.progressBar(self.progress_ui, query=True, maxValue=True)

    def inc(self, inc=1):
        """
        Set the current increment
        :param inc: int, increment value
        """

        if maya.cmds.about(batch=True):
            return

        super(MayaProgessBar, self).inc(inc)

        maya.cmds.progressBar(self.progress_ui, edit=True, step=inc)

    def step(self):
        """
        Increments current progress value by one
        """

        if maya.cmds.about(batch=True):
            return

        self.__class__.inc_value += 1
        maya.cmds.progressBar(self.progress_ui, edit=True, step=1)

    def status(self, status_str):
        """
        Set the status string of the progress bar
        :param status_str: str
        """

        if maya.cmds.about(batch=True):
            self.status_string = status_str
            return

        maya.cmds.progressBar(self.progress_ui, edit=True, status=status_str)

    def end(self):
        """
        Ends progress bar
        """

        if maya.cmds.about(batch=True):
            return

        if maya.cmds.progressBar(self.progress_ui, query=True, isCancelled=True):
            maya.cmds.progressBar(self.progress_ui, edit=True, beginProgress=True)

        maya.cmds.progressBar(self.progress_ui, edit=True, ep=True)

    def break_signaled(self):
        """
        Breaks the progress bar loop so that it stop and disappears
        """

        if maya.cmds.about(batch=True):
            return False

        break_progress = maya.cmds.progressBar(self.progress_ui, query=True, isCancelled=True)
        if break_progress:
            self.end()
            return True

        return False

# WE CANNOT USE TPQTLIB.MAINWINDOW HERE (MOVE THIS CLASS TO OTHER PLACE)
# class MayaDockedWindow(MayaQWidgetDockableMixin, window.MainWindow):
#     def __init__(self, parent=None, **kwargs):
#         self._dock_area = kwargs.get('dock_area', 'right')
#         self._dock = kwargs.get('dock', False)
#         super(MayaDockedWindow, self).__init__(parent=parent, **kwargs)
#
#         self.setProperty('saveWindowPref', True)
#
#         if self._dock:
#             self.show(dockable=True, floating=False, area=self._dock_area)
#
#     def ui(self):
#         if self._dock:
#             ui_name = str(self.objectName())
#             if maya.cmds.about(version=True) >= 2017:
#                 workspace_name = '{}WorkspaceControl'.format(ui_name)
#                 workspace_name = workspace_name.replace(' ', '_')
#                 workspace_name = workspace_name.replace('-', '_')
#                 if maya.cmds.workspaceControl(workspace_name, exists=True):
#                     maya.cmds.deleteUI(workspace_name)
#             else:
#                 dock_name = '{}DockControl'.format(ui_name)
#                 dock_name = dock_name.replace(' ', '_')
#                 dock_name = dock_name.replace('-', '_')
#                 # dock_name = 'MayaWindow|%s' % dock_name       # TODO: Check if we need this
#                 if maya.cmds.dockControl(dock_name, exists=True):
#                     maya.cmds.deleteUI(dock_name, controlong=True)
#
#             self.setAttribute(Qt.WA_DeleteOnClose, True)
#
#         super(MayaDockedWindow, self).ui()


register.register_class('Dcc', MayaDcc)
