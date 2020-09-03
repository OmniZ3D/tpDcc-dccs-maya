#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC functionality for Maya
"""

from __future__ import print_function, division, absolute_import

import os
import sys
from collections import OrderedDict

from Qt.QtWidgets import *

import tpDcc
from tpDcc.libs.python import python
import tpDcc.dccs.maya as maya
from tpDcc.abstract import dcc as abstract_dcc, progressbar
from tpDcc.dccs.maya.core import helpers, name, namespace, scene, playblast, transform, attribute, gui, mathutils
from tpDcc.dccs.maya.core import node as maya_node, reference as ref_utils, camera as cam_utils, shader as shader_utils
from tpDcc.dccs.maya.core import sequencer, animation, qtutils, decorators as maya_decorators, shape as shape_utils
from tpDcc.dccs.maya.core import filtertypes, joint as joint_utils, space as space_utils, curve as curve_utils
from tpDcc.dccs.maya.core import geometry as geo_utils, ik as ik_utils, deformer as deform_utils, color as maya_color
from tpDcc.dccs.maya.core import follicle as follicle_utils, rivet as rivet_utils, constraint as constraint_utils


class MayaDcc(abstract_dcc.AbstractDCC, object):

    class DialogResult(object):
        Yes = 'Yes'
        No = 'No'
        Cancel = 'No'
        Close = 'No'

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

    SIDE_LABELS = ['Center', 'Left', 'Right', 'None']
    TYPE_LABELS = [
        'None', 'Root', 'Hip', 'Knee', 'Foot', 'Toe', 'Spine', 'Neck', 'Head', 'Collar', 'Shoulder', 'Elbow', 'Hand',
        'Finger', 'Thumb', 'PropA', 'PropB', 'PropC', 'Other', 'Index Finger', 'Middle Finger', 'Ring Finger',
        'Pinky Finger', 'Extra Finger', 'Big Toe', 'Index Toe', 'Middle Toe', 'Ring Toe', 'Pinky Toe', 'Foot Thumb'
    ]

    ROTATION_AXES = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']

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
        :return: str
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
    def enable_component_selection():
        """
        Enables DCC component selection mode
        """

        return maya.cmds.selectMode(component=True)

    @staticmethod
    def get_main_window():
        """
        Returns Qt object that references to the main DCC window
        :return:
        """

        return gui.get_maya_window()

    @staticmethod
    def get_main_menubar():
        """
        Returns Qt object that references to the main DCC menubar
        :return:
        """

        win = MayaDcc.get_main_window()
        menu_bar = win.menuBar()

        return menu_bar

    @staticmethod
    def is_window_floating(window_name):
        """
        Returns whether or not DCC window is floating
        :param window_name: str
        :return: bool
        """

        return gui.is_window_floating(window_name=window_name)

    @staticmethod
    def focus_ui_panel(panel_name):
        """
        Focus UI panel with given name
        :param panel_name: str
        """

        return maya.cmds.setFocus(panel_name)

    @staticmethod
    def enable_wait_cursor():
        """
        Enables wait cursor in current DCC
        """

        return maya.cmds.waitCursor(state=True)

    @staticmethod
    def disable_wait_cursor():
        """
        Enables wait cursor in current DCC
        """

        return maya.cmds.waitCursor(state=False)

    @staticmethod
    def execute_deferred(fn):
        """
        Executes given function in deferred mode
        """

        maya.utils.executeDeferred(fn)

    @staticmethod
    def new_scene(force=True, do_save=True):
        """
        Creates a new DCC scene
        :param force: bool, True if we want to save the scene without any prompt dialog
        :param do_save: bool, True if you want to save the current scene before creating new scene
        :return:
        """

        return scene.new_scene(force=force, do_save=do_save)

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
        Creates a new empty group node
        :param name: str
        :param parent: str or None
        """

        groups = helpers.create_group(name=name, parent=parent, world=True)
        if groups:
            return groups[0]

    @staticmethod
    def create_buffer_group(node, **kwargs):
        """
        Creates a buffer group on top of the given node
        :param node: str
        :return: str
        """

        return transform.create_buffer_group(node, **kwargs)

    @staticmethod
    def get_buffer_group(node, **kwargs):
        """
        Returns buffer group above given node
        :param node: str
        :return: str
        """

        suffix = kwargs.get('suffix', 'buffer')

        return transform.get_buffer_group(node, suffix=suffix)

    @staticmethod
    def group_node(node, name, parent=None):
        """
        Creates a new group and parent give node to it
        :param node: str
        :param name: str
        :param parent: str
        :return: str
        """

        groups = helpers.create_group(name=name, nodes=node, parent=parent, world=True)
        if groups:
            return groups[0]

    @staticmethod
    def create_node(node_type, node_name=None):
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
    def node_is_transform(node):
        """
        Returns whether or not given node is a transform node
        :param node: str
        :return: bool
        """

        return maya.cmds.nodeType(node) == 'transform'

    @staticmethod
    def node_is_joint(node):
        """
        Returns whether or not given node is a joint node
        :param node: str
        :return: bool
        """

        return maya.cmds.nodeType(node) == 'joint'

    @staticmethod
    def node_is_locator(node):
        """
        Returns whether or not given node is a locator node
        :param node: str
        :return: bool
        """

        return maya.cmds.nodeType(node) == 'locator' or shape_utils.get_shape_node_type(node) == 'locator'

    @staticmethod
    def get_closest_transform(source_transform, targets):
        """
        Given the list of target transforms, find the closest to the source transform
        :param source_transform: str, name of the transform to test distance to
        :param targets: list<str>, list of targets to test distance against
        :return: str, name of the target in targets that is closest to source transform
        """

        return transform.get_closest_transform(source_transform, targets)

    @staticmethod
    def node_world_matrix(node):
        """
        Returns node world matrix of given node
        :param node: str
        :return: list
        """

        return maya.cmds.xform(node, matrix=True, query=True, worldSpace=True)

    @staticmethod
    def set_node_world_matrix(node, world_matrix):
        """
        Sets node world matrix of given node
        :param node: str
        :param world_matrix: list
        :return: list
        """

        return maya.cmds.xform(node, matrix=world_matrix, worldSpace=True)

    @staticmethod
    def node_world_space_translation(node):
        """
        Returns translation of given node in world space
        :param node: str
        :return: list
        """

        return maya.cmds.xform(node, worldSpace=True, q=True, translation=True)

    @staticmethod
    def node_world_bounding_box(node):
        """
        Returns world bounding box of given node
        :param node: str
        :return: list(float, float, float, float, float, float)
        """

        return maya.cmds.xform(node, worldSpace=True, q=True, boundingBox=True)

    @staticmethod
    def set_rotation_axis(node, rotation_axis):
        """
        Sets the rotation axis used by the given node
        :param node: str
        :param rotation_axis: str or int
        """

        if python.is_string(rotation_axis):
            rotation_axis = MayaDcc.ROTATION_AXES.index(rotation_axis)

        MayaDcc.set_attribute_value(node, 'rotateOrder', rotation_axis)

    @staticmethod
    def move_node(node, x, y, z, **kwargs):
        """
        Moves given node
        :param node: str
        :param x: float
        :param y: float
        :param z: float
        :param kwargs:
        """

        relative = kwargs.get('relative', False)
        object_space = kwargs.get('object_space', False)
        world_space_distance = kwargs.get('world_space_distance', False)

        return maya.cmds.move(x, y, z, node, relative=relative, os=object_space, wd=world_space_distance)

    @staticmethod
    def translate_node_in_world_space(node, translation_list, **kwargs):
        """
        Translates given node in world space with the given translation vector
        :param node: str
        :param translation_list:  list(float, float, float)
        """

        relative = kwargs.pop('relative', False)

        return maya.cmds.xform(node, worldSpace=True, t=translation_list, relative=relative)

    @staticmethod
    def translate_node_in_object_space(node, translation_list, **kwargs):
        """
        Translates given node with the given translation vector
        :param node: str
        :param translation_list:  list(float, float, float)
        """

        relative = kwargs.pop('relative', False)

        return maya.cmds.xform(node, objectSpace=True, t=translation_list, relative=relative)

    @staticmethod
    def node_world_space_rotation(node):
        """
        Returns world rotation of given node
        :param node: str
        :return: list
        """

        return maya.cmds.xform(node, worldSpace=True, q=True, rotation=True)

    @staticmethod
    def rotate_node(node, x, y, z, **kwargs):
        """
        Rotates given node
        :param node: str
        :param x: float
        :param y: float
        :param z: float
        :param kwargs:
        """

        relative = kwargs.get('relative', False)

        return maya.cmds.rotate(x, y, z, node, relative=relative)

    @staticmethod
    def rotate_node_in_world_space(node, rotation_list, **kwargs):
        """
        Translates given node with the given translation vector
        :param node: str
        :param rotation_list:  list(float, float, float)
        """

        relative = kwargs.pop('relative', False)

        return maya.cmds.xform(node, worldSpace=True, ro=rotation_list, relative=relative)

    @staticmethod
    def rotate_node_in_object_space(node, rotation_list, **kwargs):
        """
        Translates given node with the given translation vector
        :param node: str
        :param rotation_list:  list(float, float, float)
        """

        relative = kwargs.pop('relative', False)

        return maya.cmds.xform(node, objectSpace=True, ro=rotation_list, relative=relative)

    @staticmethod
    def node_world_space_scale(node):
        """
        Returns world scale of given node
        :param node: str
        :return: list
        """

        return maya.cmds.xform(node, worldSpace=True, q=True, scale=True)

    @staticmethod
    def scale_node(node, x, y, z, **kwargs):
        """
        Scales node
        :param node: str
        :param x: float
        :param y: float
        :param z: float
        :param kwargs:
        """

        pivot = kwargs.get('pivot', False)
        relative = kwargs.get('relative', False)

        return maya.cmds.scale(x, y, z, node, pivot=pivot, relative=relative)

    @staticmethod
    def scale_node_in_world_space(node, scale_list, **kwargs):
        """
        Scales given node with the given vector list
        :param node: str
        :param scale_list: list(float, float, float)
        """

        relative = kwargs.pop('relative', False)

        return maya.cmds.xform(node, worldSpace=True, s=scale_list, relative=relative)

    @staticmethod
    def scale_node_in_object_space(node, scale_list, **kwargs):
        """
        Scales given node with the given vector list
        :param node: str
        :param scale_list: list(float, float, float)
        """

        relative = kwargs.pop('relative', False)

        return maya.cmds.xform(node, objectSpace=True, s=scale_list, relative=relative)

    @staticmethod
    def node_world_space_pivot(node):
        """
        Returns node pivot in world space
        :param node: str
        :return:
        """

        return maya.cmds.xform(node, query=True, rp=True, ws=True)

    @staticmethod
    def mirror_transform(create_if_missing=False, transforms=None, left_to_right=True, **kwargs):
        """
        Mirrors the position of all transforms
        :param create_if_missing:
        :param transforms:
        :param left_to_right:
        :param kwargs:
        """

        prefix = kwargs.get('prefix', None)
        suffix = kwargs.get('suffix', None)
        string_search = kwargs.get('string_search', None)

        return transform.mirror_transform(
            prefix=prefix, suffix=suffix, string_search=string_search, create_if_missing=create_if_missing,
            transforms=transforms, left_to_right=left_to_right)

    @staticmethod
    def orient_joints(joints_to_orient=None, **kwargs):
        """
        Orients joints
        :param joints_to_orient: list(str) or None
        :param kwargs:
        :return:
        """

        force_orient_attributes = kwargs.get('force_orient_attributes', False)

        return joint_utils.OrientJointAttributes.orient_with_attributes(
            objects_to_orient=joints_to_orient, force_orient_attributes=force_orient_attributes)

    @staticmethod
    def zero_orient_joint(joints_to_zero_orient):
        """
        Zeroes the orientation of the given joints
        :param joints_to_zero_orient: list(str)
        """

        return joint_utils.OrientJointAttributes.zero_orient_joint(joints_to_zero_orient)

    @staticmethod
    def start_joint_tool():
        """
        Starts the DCC tool used to create new joints/bones
        """

        return joint_utils.start_joint_tool()

    @staticmethod
    def insert_joints(count, root_joint=None):
        """
        Inserts the given number of joints between the root joint and its direct child
        """

        return joint_utils.insert_joints(joint_count=count)

    @staticmethod
    def set_joint_local_rotation_axis_visibility(flag, joints_to_apply=None):
        """
        Sets the visibility of selected joints local rotation axis
        :param flag: bool
        :param joints_to_apply: list(str) or None
        :return: bool
        """

        return joint_utils.set_joint_local_rotation_axis_visibility(joints=joints_to_apply, bool_value=flag)

    @staticmethod
    def get_joint_display_size():
        """
        Returns current DCC joint display size
        :return: float
        """

        return maya.cmds.jointDisplayScale(query=True, absolute=True)

    @staticmethod
    def set_joint_display_size(value):
        """
        Returns current DCC joint display size
        :param value: float
        """

        if value <= 0.0:
            return False

        return maya.cmds.jointDisplayScale(value, absolute=True)

    @staticmethod
    def toggle_xray_joints():
        """
        Toggles XRay joints functionality (joints are rendered in front of the geometry)
        """

        current_panel = maya.cmds.getPanel(withFocus=True)
        if maya.cmds.modelEditor(current_panel, query=True, jointXray=True):
            maya.cmds.modelEditor(current_panel, edit=True, jointXray=False)
        else:
            maya.cmds.modelEditor(current_panel, edit=True, jointXray=True)

    @staticmethod
    def toggle_xray():
        """
        Toggle XRay functionality (model is displayed with transparency)
        """

        current_panel = maya.cmds.getPanel(withFocus=True)
        try:
            if maya.cmds.modelEditor(current_panel, query=True, xray=True):
                maya.cmds.modelEditor(current_panel, edit=True, xray=False)
            else:
                maya.cmds.modelEditor(current_panel, edit=True, xray=True)
        except Exception as exc:
            maya.logger.warning('Error while toggling xray: {}'.format(exc))

    @staticmethod
    def toggle_xray_on_selection():
        """
        Toggle XRay functionality (model is displayed with transparency) on selected geometry
        """

        selected = maya.cmds.ls(sl=True, dagObjects=True, shapes=True)
        for obj in selected:
            xray_state = maya.cmds.displaySurface(obj, query=True, xRay=True)[0]
            maya.cmds.displaySurface(obj, xRay=not xray_state)

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
        return_long_name = kwargs.get('return_long_name', False)

        return name.rename(node, new_name, uuid=uuid, rename_shape=rename_shape, return_long_name=return_long_name)

    @staticmethod
    def rename_transform_shape_nodes(node):
        """
        Renames all shape nodes of the given transform node
        :param node: str
        """

        return shape_utils.rename_shapes(transform_node=node)

    @staticmethod
    def show_object(node):
        """
        Shows given object
        :param node: str
        """

        return maya.cmds.showHidden(node)

    @staticmethod
    def select_object(node, replace_selection=True, **kwargs):
        """
        Selects given object in the current scene
        :param replace_selection: bool
        :param node: str
        """

        return maya.cmds.select(node, replace=replace_selection, add=not replace_selection, **kwargs)

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

        return maya.cmds.select(node, deselect=True)

    @staticmethod
    def clear_selection():
        """
        Clears current scene selection
        """

        return maya.cmds.select(clear=True)

    @staticmethod
    def duplicate_object(node, name='', only_parent=False):
        """
        Duplicates given object in current scene
        :param node: str
        :param name: str
        :param only_parent: bool, If True, only given node will be duplicated (ignoring its children)
        :return: str
        """

        return maya.cmds.duplicate(node, name=name, po=only_parent)[0]

    @staticmethod
    def delete_object(node):
        """
        Removes given node from current scene
        :param node: str
        """

        return maya.cmds.delete(node)

    @staticmethod
    def clean_construction_history(node):
        """
        Removes the construction history of the given node
        :param node: str
        """

        return maya.cmds.delete(node, constructionHistory=True)

    @staticmethod
    def selected_nodes(full_path=True, **kwargs):
        """
        Returns a list of selected nodes
        :param full_path: bool
        :return: list<str>
        """

        flatten = kwargs.get('flatten', False)

        return maya.cmds.ls(sl=True, long=full_path, flatten=flatten)

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
    def selected_hilited_nodes(full_path=True):
        """
        Returns a list of selected nodes that are hilited for component selection
        :param full_path: bool
        :return: list(str)
        """

        return maya.cmds.ls(long=full_path, hilite=True)

    @staticmethod
    def filter_nodes_by_selected_components(filter_type, nodes=None, full_path=False, **kwargs):
        """
        Function that filter nodes taking into account specific component filters
        Maya Components Filter Type Values
        Handle:                     0
        Nurbs Curves:               9
        Nurbs Surfaces:             10
        Nurbs Curves On Surface:    11
        Polygon:                    12
        Locator XYZ:                22
        Orientation Locator:        23
        Locator UV:                 24
        Control Vertices (CVs):     28
        Edit Points:                30
        Polygon Vertices:           31
        Polygon Edges:              32
        Polygon Face:               34
        Polygon UVs:                35
        Subdivision Mesh Points:    36
        Subdivision Mesh Edges:     37
        Subdivision Mesh Faces:     38
        Curve Parameter Points:     39
        Curve Knot:                 40
        Surface Parameter Points:   41
        Surface Knot:               42
        Surface Range:              43
        Trim Surface Edge:          44
        Surface Isoparms:           45
        Lattice Points:             46
        Particles:                  47
        Scale Pivots:               49
        Rotate Pivots:              50
        Select Handles:             51
        Subdivision Surface:        68
        Polygon Vertex Face:        70
        NURBS Surface Face:         72
        Subdivision Mesh UVs:       73
        :param filter_type: int
        :param nodes: list(str)
        :param full_path: bool
        :param kwargs:
        :return: list(str)
        """

        nodes = nodes or MayaDcc.selected_nodes()

        return maya.cmds.filterExpand(nodes, selectionMask=filter_type, fullPath=full_path)

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
    def node_short_name(node, **kwargs):
        """
        Returns short name of the given node
        :param node: str
        :return: str
        """

        remove_attribute = kwargs.get('remove_attribute', False)
        remove_namespace = kwargs.get('remove_namespace', False)

        return name.get_basename(node, remove_namespace=remove_namespace, remove_attribute=remove_attribute)

    @staticmethod
    def node_long_name(node):
        """
        Returns long name of the given node
        :param node: str
        :return: str
        """

        return name.get_long_name(node)

    @staticmethod
    def node_attribute_name(node_and_attr):
        """
        Returns the attribute part of a given node name
        :param node_and_attr: str
        :return: str
        """

        return attribute.get_attribute_name(node_and_attr)

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
    def assign_node_namespace(node, node_namespace, force_create=True, **kwargs):
        """
        Assigns a namespace to given node
        :param node: str
        :param node_namespace: str
        :param force_create: bool
        """

        rename_shape = kwargs.get('rename_shape', True)

        return namespace.assign_namespace_to_object(
            node, node_namespace, force_create=force_create, rename_shape=rename_shape)

    @staticmethod
    def node_is_visible(node):
        """
        Returns whether given node is visible or not
        :param node: str
        :return: bool
        """

        return maya_node.is_visible(node=node)

    @staticmethod
    def node_color(node):
        """
        Returns color of the given node
        :param node: str
        :return:
        """

        return attribute.get_color(node)

    @staticmethod
    def set_node_color(node, color):
        """
        Sets the color of the given node
        :param node: str
        :param color:
        """

        return attribute.set_color(node, color)

    @staticmethod
    def node_components(node):
        """
        Returns all components of the given node
        :param node: str
        :return: list(str)
        """

        return shape_utils.get_components_from_shapes(node)

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
    def set_shape_parent(shape, transform_node):
        """
        Sets given shape parent
        :param shape: str
        :param transform_node: str
        """

        return maya.cmds.parent(shape, transform_node, r=True, shape=True)

    @staticmethod
    def add_node_to_parent(node, parent_node):
        """
        Add given object under the given parent preserving its local transformations
        :param node: str
        :param parent_node: str
        """

        return maya.cmds.parent(node, parent_node, add=True, s=True)

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

        return maya.cmds.xform(node, matrix=matrix, worldSpace=True)

    @staticmethod
    def show_node(node):
        """
        Shows given node
        :param node: str
        """

        return maya.cmds.showHidden(node)

    @staticmethod
    def hide_node(node):
        """
        Hides given node
        :param node: str
        """

        return maya.cmds.hide(node)

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
            children = maya.cmds.listRelatives(
                node, children=True, allDescendents=all_hierarchy, fullPath=full_path, type=children_type)
        else:
            children = maya.cmds.listRelatives(node, children=True, allDescendents=all_hierarchy, fullPath=full_path)
        if not children:
            return list()

        children.reverse()

        return children

    @staticmethod
    def list_relatives(
            node, all_hierarchy=False, full_path=True, relative_type=None, shapes=False, intermediate_shapes=False):
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
    def node_is_a_shape(node):
        """
        Returns whether or not given node is a shape one
        :param node: str
        :return: bool
        """

        return shape_utils.is_a_shape(node)

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
    def list_shapes_of_type(node, shape_type=None, full_path=True, intermediate_shapes=False):
        """
        Returns a list of shapes of the given node
        :param node: str
        :param shape_type: str
        :param full_path: bool
        :param intermediate_shapes: bool
        :return: list<str>
        """

        return shape_utils.get_shapes_of_type(
            node_name=node, shape_type=shape_type, full_path=full_path, no_intermediate=not intermediate_shapes)

    @staticmethod
    def node_has_shape_of_type(node, shape_type):
        """
        Returns whether or not given node has a shape of the given type attached to it
        :param node: str
        :param shape_type: str
        :return: bool
        """

        return shape_utils.has_shape_of_type(node, shape_type=shape_type)

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

        if all_hierarchy:
            return shape_utils.get_shapes_in_hierarchy(
                transform_node=node, full_path=full_path, intermediate_shapes=intermediate_shapes)
        else:
            return maya.cmds.listRelatives(
                node, shapes=True, fullPath=full_path, noIntermediate=not intermediate_shapes, allDescendents=False)

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
    def rename_shapes(node):
        """
        Rename all shapes of the given node with a standard DCC shape name
        :param node: str
        """

        return shape_utils.rename_shapes(node)

    @staticmethod
    def node_bounding_box_pivot(node):
        """
        Returns the bounding box pivot center of the given node
        :param node: str
        :return: list(float, float, float)
        """

        shapes = shape_utils.get_shapes_of_type(node, shape_type='nurbsCurve')
        components = shape_utils.get_components_from_shapes(shapes)
        bounding = transform.BoundingBox(components)
        pivot = bounding.get_center()

        return pivot

    @staticmethod
    def shapes_bounding_box_pivot(shapes):
        """
        Returns the bounding box pivot center point of the given meshes
        :param shapes: list(str)
        :return: list(float, float, float)
        """

        components = shape_utils.get_components_from_shapes(shapes)
        bounding = transform.BoundingBox(components)
        pivot = bounding.get_center()

        return pivot

    @staticmethod
    def default_shaders():
        """
        Returns a list with all thte default shadres of the current DCC
        :return: str
        """

        return shader_utils.get_default_shaders()

    @staticmethod
    def create_surface_shader(shader_name, **kwargs):
        """
        Creates a new basic DCC surface shader
        :param shader_name: str
        :return: str
        """

        return_shading_group = kwargs.get('return_shading_group', False)

        shader = maya.cmds.shadingNode('surfaceShader', name=shader_name, asShader=True)
        sg = maya.cmds.sets(name='{}SG'.format(shader), renderable=True, noSurfaceShader=True, empty=True)
        maya.cmds.connectAttr('{}.outColor'.format(shader), '{}.surfaceShader'.format(sg), force=True)

        if return_shading_group:
            return sg

        return shader

    @staticmethod
    def apply_shader(material, node):
        """
        Applies material to given node
        :param material: str
        :param node: str
        """

        shading_group = None
        if maya.cmds.nodeType(material) in ['surfaceShader', 'lambert']:
            shading_groups = maya.cmds.listConnections(material, type='shadingEngine')
            shading_group = shading_groups[0] if shading_groups else None
        elif maya.cmds.nodeType(material) == 'shadingEngine':
            shading_group = material
        if not shading_group:
            tpDcc.logger.warning('Impossible to apply material "{}" into "{}"'.format(material, node))
            return False

        maya.cmds.sets(node, e=True, forceElement=shading_group)

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
    def add_bool_attribute(node, attribute_name, default_value=False, **kwargs):
        """
        Adds a new boolean attribute into the given node
        :param node: str
        :param attribute_name: str
        :param default_value: bool
        :return:
        """

        lock = kwargs.pop('lock', False)
        channel_box_display = kwargs.pop('channel_box_display', True)
        keyable = kwargs.pop('keyable', True)

        maya.cmds.addAttr(node, ln=attribute_name, at='bool', dv=default_value, **kwargs)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)

    @staticmethod
    def add_integer_attribute(node, attribute_name, default_value=0, **kwargs):
        """
        Adds a new float attribute into the given node
        :param node: str
        :param attribute_name: str
        :param default_value: float
        :return:
        """

        lock = kwargs.pop('lock', False)
        channel_box_display = kwargs.get('channel_box_display', True)
        keyable = kwargs.pop('keyable', True)
        min_value = kwargs.pop('min_value', -sys.maxsize - 1)
        max_value = kwargs.pop('max_value', sys.maxsize + 1)

        maya.cmds.addAttr(
            node, ln=attribute_name, at='long', dv=default_value, min=float(min_value), max=float(max_value), **kwargs)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)

    @staticmethod
    def add_float_attribute(node, attribute_name, default_value=0.0, **kwargs):
        """
        Adds a new float attribute into the given node
        :param node: str
        :param attribute_name: str
        :param default_value: float
        :return:
        """

        lock = kwargs.pop('lock', False)
        channel_box_display = kwargs.get('channel_box_display', True)
        keyable = kwargs.pop('keyable', True)
        min_value = kwargs.pop('min_value', float(-sys.maxsize - 1))
        max_value = kwargs.pop('max_value', float(sys.maxsize + 1))

        maya.cmds.addAttr(node, ln=attribute_name, at='float', dv=default_value, min=min_value, max=max_value, **kwargs)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)

    @staticmethod
    def add_double_attribute(node, attribute_name, default_value=0.0, **kwargs):
        """
        Adds a new boolean float into the given node
        :param node: str
        :param attribute_name: str
        :param default_value: float
        :return:
        """

        lock = kwargs.pop('lock', False)
        channel_box_display = kwargs.get('channel_box_display', True)
        keyable = kwargs.pop('keyable', True)
        min_value = kwargs.pop('min_value', float(-sys.maxsize - 1))
        max_value = kwargs.pop('max_value', float(sys.maxsize + 1))

        maya.cmds.addAttr(
            node, ln=attribute_name, at='double', dv=default_value, min=min_value, max=max_value, **kwargs)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)

    @staticmethod
    def add_string_attribute(node, attribute_name, default_value='', **kwargs):
        """
        Adds a new string attribute into the given node
        :param node: str
        :param attribute_name: str
        :param default_value: str
        """

        lock = kwargs.pop('lock', False)
        channel_box_display = kwargs.get('channel_box_display', True)
        keyable = kwargs.pop('keyable', True)

        maya.cmds.addAttr(node, ln=attribute_name, dt='string', **kwargs)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), default_value, type='string')
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)

    @staticmethod
    def add_string_array_attribute(node, attribute_name, **kwargs):
        """
        Adds a new string array attribute into the given node
        :param node: str
        :param attribute_name: str
        :param keyable: bool
        """

        lock = kwargs.get('lock', False)
        channel_box_display = kwargs.get('channel_box_display', True)
        keyable = kwargs.pop('keyable', True)

        maya.cmds.addAttr(node, ln=attribute_name, dt='stringArray', **kwargs)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)

    @staticmethod
    def add_title_attribute(node, attribute_name, **kwargs):
        """
        Adds a new title attribute into the given node
        :param node: str
        :param attribute_name: str
        :param kwargs:
        :return:
        """

        return attribute.create_title(node, attribute_name)

    @staticmethod
    def add_message_attribute(node, attribute_name, **kwargs):
        """
        Adds a new message attribute into the given node
        :param node: str
        :param attribute_name: str
        """

        lock = kwargs.get('lock', False)
        channel_box_display = kwargs.get('channel_box_display', True)
        keyable = kwargs.pop('keyable', True)

        maya.cmds.addAttr(node, ln=attribute_name, at='message', **kwargs)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)

    @staticmethod
    def add_enum_attribute(node, attribute_name, value, **kwargs):
        """
        Adds a new enum attribute into the given node
        :param node: str
        :param attribute_name: str
        :param value: list(str)
        :param kwargs:
        :return:
        """

        lock = kwargs.get('lock', False)
        channel_box_display = kwargs.get('channel_box_display', True)
        keyable = kwargs.pop('keyable', True)

        maya.cmds.addAttr(node, ln=attribute_name, attributeType='enum', enumName=value, **kwargs)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, lock=lock, channelBox=channel_box_display)
        maya.cmds.setAttr('{}.{}'.format(node, attribute_name), edit=True, keyable=keyable)

    @staticmethod
    def get_enum_attribute_values(node, attribute_name):
        """
        Return list of enum attribute values in the given attribute
        :param node: str
        :param attribute_name: str
        :return: list(str)
        """

        return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), query=True, enumName=True)

    @staticmethod
    def set_enum_attribute_value(node, attribute_name, value):
        """
        Return list of enum attribute values in the given attribute
        :param node: str
        :param attribute_name: str
        :param value: str
        """

        return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, enumName=value)

    @staticmethod
    def attribute_query(node, attribute_name, **kwargs):
        """
        Returns attribute qyer
        :param node: str
        :param attribute_name: str
        :param kwargs:
        :return:
        """

        return maya.cmds.attributeQuery(attribute_name, node=node, **kwargs)[0]

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
        Returns whether given attribute is locked or not
        :param node: str
        :param attribute_name: str
        :return: bool
        """

        return maya.cmds.getAttr('{}.{}'.format(node, attribute_name, lock=True))

    @staticmethod
    def is_attribute_connected(node, attribute_name):
        """
        Returns whether given attribute is connected or not
        :param node: str
        :param attribute_name: str
        :return: bool
        """

        return attribute.is_connected('{}.{}'.format(node, attribute_name))

    @staticmethod
    def is_attribute_connected_to_attribute(source_node, source_attribute_name, target_node, target_attribute_name):
        """
        Returns whether given source attribute is connected or not to given target attribute
        :param source_node: str
        :param source_attribute_name: str
        :param target_node: str
        :param target_attribute_name: str
        :return: bool
        """

        return maya.cmds.isConnected(
            '{}.{}'.format(source_node, source_attribute_name), '{}.{}'.format(target_node, target_attribute_name))

    @staticmethod
    def get_maximum_integer_attribute_value(node, attribute_name):
        """
        Returns the maximum value that a specific integer attribute has set
        :param node: str
        :param attribute_name: str
        :return: float
        """

        return maya.cmds.attributeQuery(attribute_name, max=True, node=node)[0]

    @staticmethod
    def set_maximum_integer_attribute_value(node, attribute_name, max_value):
        """
        Sets the maximum value that a specific integer attribute has set
        :param node: str
        :param attribute_name: str
        :param max_value: float
        """

        return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, maxValue=max_value, hasMaxValue=True)

    @staticmethod
    def get_maximum_float_attribute_value(node, attribute_name):
        """
        Returns the maximum value that a specific float attribute has set
        :param node: str
        :param attribute_name: str
        :return: float
        """

        return maya.cmds.attributeQuery(attribute_name, max=True, node=node)[0]

    @staticmethod
    def set_maximum_float_attribute_value(node, attribute_name, max_value):
        """
        Sets the maximum value that a specific float attribute has set
        :param node: str
        :param attribute_name: str
        :param max_value: float
        """

        return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, maxValue=max_value, hasMaxValue=True)

    @staticmethod
    def get_minimum_integer_attribute_value(node, attribute_name):
        """
        Returns the minimum value that a specific integer attribute has set
        :param node: str
        :param attribute_name: str
        :return: float
        """

        return maya.cmds.attributeQuery(attribute_name, min=True, node=node)[0]

    @staticmethod
    def set_minimum_integer_attribute_value(node, attribute_name, min_value):
        """
        Sets the minimum value that a specific integer attribute has set
        :param node: str
        :param attribute_name: str
        :param min_value: float
        """

        return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, minValue=min_value, hasMinValue=True)

    @staticmethod
    def get_minimum_float_attribute_value(node, attribute_name):
        """
        Returns the minimum value that a specific float attribute has set
        :param node: str
        :param attribute_name: str
        :return: float
        """

        return maya.cmds.attributeQuery(attribute_name, min=True, node=node)[0]

    @staticmethod
    def set_minimum_float_attribute_value(node, attribute_name, min_value):
        """
        Sets the minimum value that a specific float attribute has set
        :param node: str
        :param attribute_name: str
        :param min_value: float
        """

        return maya.cmds.addAttr('{}.{}'.format(node, attribute_name), edit=True, minValue=min_value, hasMinValue=True)

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
    def hide_attributes(node, attributes_list):
        """
        Hides given attributes in DCC UI
        :param node: str
        :param attributes_list: list(str)
        """

        return attribute.hide_attributes(node, attributes_list)

    @staticmethod
    def lock_attributes(node, attributes_list, **kwargs):
        """
        Locks given attributes in DCC UI
        :param node: str
        :param attributes_list: list(str)
        :param kwargs:
        """

        hide = kwargs.get('hide', False)

        return attribute.lock_attributes(node, attributes_list, hide=hide)

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
    def hide_translate_attributes(node):
        """
        Hides all translate transform attributes of the given node
        :param node: str
        """

        return attribute.hide_translate(node)

    @staticmethod
    def lock_translate_attributes(node):
        """
        Locks all translate transform attributes of the given node
        :param node: str
        """

        return attribute.lock_translate_attributes(node, hide=False)

    @staticmethod
    def hide_rotate_attributes(node):
        """
        Hides all rotate transform attributes of the given node
        :param node: str
        """

        return attribute.hide_rotate(node)

    @staticmethod
    def lock_rotate_attributes(node):
        """
        Locks all rotate transform attributes of the given node
        :param node: str
        """

        return attribute.lock_rotate_attributes(node, hide=False)

    @staticmethod
    def hide_scale_attributes(node):
        """
        Hides all scale transform attributes of the given node
        :param node: str
        """

        return attribute.hide_scale(node)

    @staticmethod
    def lock_scale_attributes(node):
        """
        Locks all scale transform attributes of the given node
        :param node: str
        """

        return attribute.lock_scale_attributes(node, hide=False)

    @staticmethod
    def hide_visibility_attribute(node):
        """
        Hides visibility attribute of the given node
        :param node: str
        """

        return attribute.hide_visibility(node)

    @staticmethod
    def lock_visibility_attribute(node):
        """
        Locks visibility attribute of the given node
        :param node: str
        """

        return attribute.lock_attributes(node, ['visibility'], hide=False)

    @staticmethod
    def hide_scale_and_visibility_attributes(node):
        """
        Hides scale and visibility attributes of the given node
        :param node: str
        """

        MayaDcc.hide_scale_attributes(node)
        MayaDcc.hide_visibility_attribute(node)

    @staticmethod
    def lock_scale_and_visibility_attributes(node):
        """
        Locks scale and visibility attributes of the given node
        :param node: str
        """

        MayaDcc.lock_scale_attributes(node)
        MayaDcc.lock_visibility_attribute(node)

    @staticmethod
    def hide_keyable_attributes(node):
        """
        Hides all node attributes that are keyable
        :param node: str
        """

        return attribute.hide_keyable_attributes(node)

    @staticmethod
    def lock_keyable_attributes(node):
        """
        Locks all node attributes that are keyable
        :param node: str
        """

        return attribute.lock_keyable_attributes(node, hide=False)

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

        if attribute_type == 'string':
            return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), attribute_value, type=attribute_type)
        else:
            return maya.cmds.setAttr('{}.{}'.format(node, attribute_name), attribute_value)

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
    def node_inherits_transform(node):
        """
        Returns whether or not given node inherits its parent transforms
        :param node: str
        :return: bool
        """

        return maya.cmds.getAttr('{}.inheritsTransform'.format(node))

    @staticmethod
    def set_node_inherits_transform(node, flag):
        """
        Sets whether or not given node inherits parent transforms or not
        :param node: str
        :param flag: bool
        """

        return maya.cmds.setAttr('{}.inheritsTransform'.format(node), flag)

    @staticmethod
    def reset_transform_attributes(node):
        """
        Reset all transform attributes of the given node
        :param node: str
        """

        for axis in 'xyz':
            for xform in 'trs':
                xform_attr = '{}{}'.format(xform, axis)
                if xform == 's':
                    MayaDcc.set_attribute_value(node, xform_attr, 1.0)
                else:
                    MayaDcc.set_attribute_value(node, xform_attr, 0.0)

        for shear_attr in ['shearXY', 'shearXZ', 'shearYZ']:
            MayaDcc.set_attribute_value(node, shear_attr, 0.0)

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
    def delete_user_defined_attributes(node):
        """
        Removes all attributes in the given node that have been created by a user
        :param node: str
        """

        return attribute.remove_user_defined_attributes(node)

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
    def connect_multiply(source_node, source_attribute, target_node, target_attribute, value=0.1, multiply_name=None):
        """
        Connects source attribute into target attribute with a multiply node inbetween
        :param source_node: str
        :param source_attribute: str
        :param target_node: str
        :param target_attribute: str
        :param value: float, value of the multiply node
        :param multiply_name: str
        :return: str, name of the created multiply node
        """

        return attribute.connect_multiply(
            '{}.{}'.format(source_node, source_attribute), '{}.{}'.format(target_node, target_attribute),
            value=value, name=multiply_name)

    @staticmethod
    def connect_translate(source_node, target_node):
        """
        Connects the translation of the source node into the rotation of the target node
        :param source_node: str
        :param target_node: str
        """

        return attribute.connect_translate(source_node, target_node)

    @staticmethod
    def connect_rotate(source_node, target_node):
        """
        Connets the rotation of the source node into the rotation of the target node
        :param source_node: str
        :param target_node: str
        """

        return attribute.connect_rotate(source_node, target_node)

    @staticmethod
    def connect_scale(source_node, target_node):
        """
        Connects the scale of the source node into the rotation of the target node
        :param source_node: str
        :param target_node: str
        """

        return attribute.connect_scale(source_node, target_node)

    @staticmethod
    def connect_visibility(node, attr, target_node, default_value=True):
        """
        Connect the visibility of the target node into an attribute
        :param node: str, name of a node. If it does not exists, it will ber created
        :param attr: str, attribute name of a node. If it does not exists, it will ber created
        :param target_node: str, target node to connect its visibility into the attribute
        :param default_value: bool, Whether you want the visibility on/off by default
        """

        return attribute.connect_visibility(
            '{}.{}'.format(node, attr), target_node, default_value=default_value)

    @staticmethod
    def connect_message_attribute(source_node, target_node, message_attribute, force=False):
        """
        Connects the message attribute of the input_node into a custom message attribute on target_node
        :param source_node: str, name of a node
        :param target_node: str, name of a node
        :param message_attribute: str, name of the message attribute to create and connect into. If already exists,
        just connect
        :param force, Whether or not force the connection of the message attribute
        """

        return attribute.connect_message(source_node, target_node, message_attribute, force=force)

    @staticmethod
    def get_message_attributes(node, **kwargs):
        """
        Returns all message attributes of the give node
        :param node: str
        :return: list(str)
        """

        user_defined = kwargs.get('user_defined', True)

        return attribute.get_message_attributes(node, user_defined=user_defined)

    @staticmethod
    def get_attribute_input(attribute_node, **kwargs):
        """
        Returns the input into given attribute
        :param attribute_node: str, full node and attribute (node.attribute) attribute we want to retrieve inputs of
        :param kwargs:
        :return: str
        """

        node_only = kwargs.get('node_only', False)

        return attribute.get_attribute_input(attribute_node, node_only=node_only)

    @staticmethod
    def get_message_input(node, message_attribute):
        """
        Get the input value of a message attribute
        :param node: str
        :param message_attribute: str
        :return: object
        """

        return attribute.get_message_input(node=node, message=message_attribute)

    @staticmethod
    def store_world_matrix_to_attribute(node, attribute_name='origMatrix', **kwargs):
        """
        Stores world matrix of given transform into an attribute in the same transform
        :param node: str
        :param attribute_name: str
        :param kwargs:
        """

        skip_if_exists = kwargs.get('skip_if_exists', False)

        return attribute.store_world_matrix_to_attribute(
            transform=node, attribute_name=attribute_name, skip_if_exists=skip_if_exists)

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
    def list_node_parents(node):
        """
        Returns all parent nodes of the given Maya node
        :param node: str
        :return: list(str)
        """

        return scene.get_all_parent_nodes(node)

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
    def scene_is_modified():
        """
        Returns whether or not current opened DCC file has been modified by the user or not
        :return: True if current DCC file has been modified by the user; False otherwise
        :rtype: bool
        """

        return maya.cmds.file(query=True, modified=True)

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

        nodes = maya.cmds.file(file_path, o=True, f=force, returnNewNodes=True)

        scene_ext = os.path.splitext(file_path)[-1]
        scene_type = None
        if scene_ext == '.ma':
            scene_type = 'mayaAscii'
        elif scene_ext == '.mb':
            scene_type = 'mayaBinary'
        if scene_type:
            maya.mel.eval('$filepath = "{}";'.format(file_path))
            maya.mel.eval('addRecentFile $filepath "{}";'.format(scene_type))

        return nodes

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
    def save_current_scene(force=True, **kwargs):
        """
        Saves current scene
        :param force: bool
        """

        path_to_save = kwargs.get('path_to_save', None)
        name_to_save = kwargs.get('name_to_save', None)
        extension_to_save = kwargs.get('extension_to_save', MayaDcc.get_extensions()[0])
        scene_name = MayaDcc.scene_name()
        if scene_name:
            extension_to_save = os.path.splitext(scene_name)[-1]
        if not extension_to_save.startswith('.'):
            extension_to_save = '.{}'.format(extension_to_save)
        maya_scene_type = 'mayaAscii' if extension_to_save == '.ma' else 'mayaBinary'

        if scene_name:
            if path_to_save and name_to_save:
                maya.cmds.file(rename=os.path.join(path_to_save, '{}{}'.format(name_to_save, extension_to_save)))
            return maya.cmds.file(save=True, type=maya_scene_type, f=force)
        else:
            if path_to_save and name_to_save:
                maya.cmds.file(rename=os.path.join(path_to_save, '{}{}'.format(name_to_save, extension_to_save)))
                return maya.cmds.file(save=True, type=maya_scene_type, f=force)
            else:
                if force:
                    return maya.cmds.SaveScene()
                else:
                    if MayaDcc.scene_is_modified():
                        return maya.cmds.SaveScene()
                    else:
                        return maya.cmds.file(save=True, type=maya_scene_type)

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
    def set_flat_key_frame(node, attribute_name, start_time, end_time):
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
        Match translation and rotation of the target node to the translation and rotation of the source node
        :param source_node: str
        :param target_node: str
        """

        return transform.MatchTransform(source_node, target_node).translation_rotation()

    @staticmethod
    def match_translation_to_rotate_pivot(source_node, target_node):
        """
        Matches target translation to the source transform rotate pivot
        :param source_node: str
        :param target_node: str
        :return:
        """

        return transform.MatchTransform(source_node, target_node).translation_to_rotate_pivot()

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
    def list_node_constraints(node):
        """
        Returns all constraints linked to given node
        :param node: str
        :return: list(str)
        """

        return maya.cmds.listRelatives(node, type='constraint')

    @staticmethod
    def create_point_constraint(source, constraint_to, **kwargs):
        """
        Creates a new point constraint
        :param source:
        :param constraint_to:
        :param kwargs:
        :return:
        """

        maintain_offset = kwargs.get('maintain_offset', False)

        return maya.cmds.pointConstraint(constraint_to, source, mo=maintain_offset)

    @staticmethod
    def create_orient_constraint(source, constraint_to, **kwargs):
        """
        Creates a new orient constraint
        :param source:
        :param constraint_to:
        :param kwargs:
        :return:
        """

        maintain_offset = kwargs.get('maintain_offset', False)

        return maya.cmds.orientConstraint(constraint_to, source, mo=maintain_offset)

    @staticmethod
    def create_scale_constraint(source, constraint_to, **kwargs):
        """
        Creates a new scale constraint
        :param source:
        :param constraint_to:
        :param kwargs:
        :return:
        """

        maintain_offset = kwargs.get('maintain_offset', False)

        return maya.cmds.scaleConstraint(constraint_to, source, mo=maintain_offset)

    @staticmethod
    def create_parent_constraint(source, constraint_to, **kwargs):
        """
        Creates a new parent constraint
        :param source:
        :param constraint_to:
        :param kwargs:
        :return:
        """

        maintain_offset = kwargs.get('maintain_offset', False)

        return maya.cmds.parentConstraint(constraint_to, source, mo=maintain_offset)

    @staticmethod
    def get_axis_aimed_at_child(transform_node):
        """
        Returns the axis that is pointing to the given transform
        :param transform_node: str, name of a transform node
        :return:
        """

        return transform.get_axis_aimed_at_child(transform_node)

    @staticmethod
    def create_aim_constraint(source, point_to, **kwargs):
        """
        Creates a new aim constraint
        :param source: str
        :param point_to: str
        """

        aim_axis = kwargs.pop('aim_axis', (1.0, 0.0, 0.0))
        up_axis = kwargs.pop('up_axis', (0.0, 1.0, 0.0))
        world_up_axis = kwargs.pop('world_up_axis', (0.0, 1.0, 0.0))
        # World Up type: 0: scene up; 1: object up; 2: object rotation up; 3: vector; 4: None
        world_up_type = kwargs.pop('world_up_type', 3)
        world_up_object = kwargs.pop('world_up_object', None)
        weight = kwargs.pop('weight', 1.0)
        maintain_offset = kwargs.pop('maintain_offset', False)

        if world_up_object:
            kwargs['worldUpObject'] = world_up_object

        return maya.cmds.aimConstraint(
            point_to, source, aim=aim_axis, upVector=up_axis, worldUpVector=world_up_axis,
            worldUpType=world_up_type, weight=weight, mo=maintain_offset, **kwargs)

    @staticmethod
    def create_pole_vector_constraint(control, handle):
        """
        Creates a new pole vector constraint
        :param control: str
        :param handle: str
        :return: str
        """

        return maya.cmds.poleVectorConstraint(control, handle)[0]

    @staticmethod
    def get_selection_groups(name=None):
        """
        Returns all selection groups (sets) in current DCC scene
        :param name: str or None
        :return: list(str)
        """

        if name:
            return maya.cmds.ls(name, type='objectSet')
        else:
            return maya.cmds.ls(type='objectSet')

    @staticmethod
    def node_is_selection_group(node):
        """
        Returns whether or not given node is a selection group (set)
        :param node: str
        :return: bool
        """

        return MayaDcc.node_type(node) == 'objectSet'

    @staticmethod
    def create_selection_group(name, empty=False):
        """
        Creates a new DCC selection group
        :param name: str
        :param empty: bool
        :return: str
        """

        return maya.cmds.sets(name=name, empty=empty)

    @staticmethod
    def add_node_to_selection_group(node, selection_group_name, force=True):
        """
        Adds given node to selection group
        :param node: str
        :param selection_group_name: str
        :param force: bool
        :return: str
        """

        if force:
            return maya.cmds.sets(node, edit=True, forceElement=selection_group_name)
        else:
            return maya.cmds.sets(node, edit=True, addElement=selection_group_name)

    @staticmethod
    def zero_transform_attribute_channels(node):
        """
        Sets to zero all transform attribute channels of the given node (transform rotate and scale)
        :param node: str
        """

        return transform.zero_transform_channels(node)

    @staticmethod
    def zero_scale_joint(jnt):
        """
        Sets the given scale to zero and compensate the change by modifying the joint translation and rotation
        :param jnt: str
        """

        return maya.cmds.joint(jnt, edit=True, zeroScaleOrient=True)

    @staticmethod
    def set_joint_orient(jnt, orient_axis, secondary_orient_axis=None, **kwargs):
        """
        Sets the joint orientation and scale orientation so that the axis indicated by the first letter in the
        argument will be aligned with the vector from this joint to its first child joint. For example, if the
        argument is "xyz", the x-axis will point towards the child joint. The alignment of the remaining two
        joint orient axes are dependent on whether or not the -sao/-secondaryAxisOrient flag is used.
        If the secondary_orient_axis flag is used, see the documentation for that flag for how the remaining
        axes are aligned. In the absence of a user specification for the secondary axis orientation, the rotation
        axis indicated by the last letter in the argument will be aligned with the vector perpendicular to first
        axis and the vector from this joint to its parent joint. The remaining axis is aligned according the right
        hand rule. If the argument is "none", the joint orientation will be set to zero and its effect to the
        hierarchy below will be offset by modifying the scale orientation. The flag will be ignored if: A. the
        joint has non-zero rotations when the argument is not "none". B. the joint does not have child joint, or
        the distance to the child joint is zero when the argument is not "none". C. either flag -o or -so is set.
        :param jnt: str, can be one of the following strings: xyz, yzx, zxy, zyx, yxz, xzy, none
        :param orient_axis: str, can be one of the following strings: xyz, yzx, zxy, zyx, yxz, xzy, none
        :param secondary_orient_axis: str, one of the following strings: xup, xdown, yup, ydown, zup, zdown, none. This
            flag is used in conjunction with the -oj/orientJoint flag. It specifies the scene axis that the second
            axis should align with. For example, a flag combination of "-oj yzx -sao yup" would result in the y-axis
             pointing down the bone, the z-axis oriented with the scene's positive y-axis, and the x-axis oriented
             according to the right hand rule.
         :param:
        :return:
        """

        zero_scale_joint = kwargs.get('zero_scale_joint', False)

        return maya.cmds.joint(jnt, edit=True, zso=zero_scale_joint, oj=orient_axis, sao=secondary_orient_axis)

    @staticmethod
    def attach_joints(source_chain, target_chain, **kwargs):
        """
        Attaches a chain of joints to a matching chain
        :param source_chain: list(str)
        :param target_chain: list(str)
        """

        # 0 = Constraint; 1 = Matrix
        attach_type = kwargs.get('attach_type', 0)
        create_switch = kwargs.get('create_switch', True)
        switch_attribute_name = kwargs.get('switch_attribute_name', 'switch')

        attach = joint_utils.AttachJoints(
            source_joints=source_chain, target_joints=target_chain, create_switch=create_switch)
        attach.set_attach_type(attach_type)
        if switch_attribute_name:
            attach.set_switch_attribute_name(switch_attribute_name)
        attach.create()

    @staticmethod
    def create_hierarchy(transforms, replace_str=None, new_str=None):
        """
        Creates a transforms hierarchy with the given list of joints
        :param transforms: list(str)
        :param replace_str: str, if given this string will be replace with the new_str
        :param new_str: str, if given replace_str will be replace with this string
        :return: list(str)
        """

        build_hierarchy = joint_utils.BuildJointHierarchy()
        build_hierarchy.set_transforms(transform)
        if replace_str and new_str:
            build_hierarchy.set_replace(replace_str, new_str)

        return build_hierarchy.create()

    @staticmethod
    def duplicate_hierarchy(transforms, stop_at=None, force_only_these=None, replace_str=None, new_str=None):
        """
        Duplicates given hierarchy of transform nodes
        :param transforms: list(str), list of joints to duplicate
        :param stop_at: str, if given the duplicate process will be stop in the given node
        :param force_only_these: list(str), if given only these list of transforms will be duplicated
        :param replace_str: str, if given this string will be replace with the new_str
        :param new_str: str, if given replace_str will be replace with this string
        :return: list(str)
        """

        transforms = python.force_list(transforms)

        duplicate_hierarchy = transform.DuplicateHierarchy(transforms[0])
        if stop_at:
            duplicate_hierarchy.stop_at(stop_at)
        if force_only_these:
            duplicate_hierarchy.only_these(force_only_these)
        if replace_str and new_str:
            duplicate_hierarchy.set_replace(replace_str, new_str)

        return duplicate_hierarchy.create()

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
    def move_pivot_to_zero(node):
        """
        Moves pivot of given node to zero (0, 0, 0 in the world)
        :param node: str
        """

        return maya.cmds.xform(node, ws=True, a=True, piv=(0, 0, 0))

    @staticmethod
    def combine_meshes(meshes_to_combine=None, **kwargs):
        """
        Combines given meshes into one unique mesh. If no meshes given, all selected meshes will be combined
        :param meshes_to_combine: list(str) or None
        :return: str
        """

        construction_history = kwargs.get('construction_history', True)
        if not meshes_to_combine:
            meshes_to_combine = maya.cmds.ls(sl=True, long=True)
        if not meshes_to_combine:
            return

        out, unite_node = maya.cmds.polyUnite(*meshes_to_combine)
        if not construction_history:
            MayaDcc.delete_history(out)

        return out

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
    def node_vertex_name(mesh_node, vertex_id):
        """
        Returns the full name of the given node vertex
        :param mesh_node: str
        :param vertex_id: int
        :return: str
        """

        return '{}.vtx[{}]'.format(mesh_node, vertex_id)

    @staticmethod
    def total_vertices(mesh_node):
        """
        Returns the total number of vertices of the given geometry
        :param mesh_node: str
        :return: int
        """

        return maya.cmds.polyEvaluate(mesh_node, vertex=True)

    @staticmethod
    def node_vertex_object_space_translation(mesh_node, vertex_id=None):
        """
        Returns the object space translation of the vertex id in the given node
        :param mesh_node: str
        :param vertex_id: int
        :return:
        """

        if vertex_id is not None:
            vertex_name = MayaDcc.node_vertex_name(mesh_node=mesh_node, vertex_id=vertex_id)
        else:
            vertex_name = mesh_node

        return maya.cmds.xform(vertex_name, objectSpace=True, q=True, translation=True)

    @staticmethod
    def node_vertex_world_space_translation(mesh_node, vertex_id=None):
        """
        Returns the world space translation of the vertex id in the given node
        :param mesh_node: str
        :param vertex_id: int
        :return:
        """

        if vertex_id is not None:
            vertex_name = MayaDcc.node_vertex_name(mesh_node=mesh_node, vertex_id=vertex_id)
        else:
            vertex_name = mesh_node

        return maya.cmds.xform(vertex_name, worldSpace=True, q=True, translation=True)

    @staticmethod
    def set_node_vertex_object_space_translation(mesh_node, translate_list, vertex_id=None):
        """
        Sets the object space translation of the vertex id in the given node
        :param mesh_node: str
        :param translate_list: list
        :param vertex_id: int
        :return:
        """

        if vertex_id is not None:
            vertex_name = MayaDcc.node_vertex_name(mesh_node=mesh_node, vertex_id=vertex_id)
        else:
            vertex_name = mesh_node

        return maya.cmds.xform(vertex_name, objectSpace=True, t=translate_list)

    @staticmethod
    def set_node_vertex_world_space_translation(mesh_node, translate_list, vertex_id=None):
        """
        Sets the world space translation of the vertex id in the given node
        :param mesh_node: str
        :param translate_list: list
        :param vertex_id: int
        :return:
        """

        if vertex_id is not None:
            vertex_name = MayaDcc.node_vertex_name(mesh_node=mesh_node, vertex_id=vertex_id)
        else:
            vertex_name = mesh_node

        return maya.cmds.xform(vertex_name, worldSpace=True, t=translate_list)

    @staticmethod
    def create_nurbs_sphere(name='sphere', radius=1.0, **kwargs):
        """
        Creates a new NURBS sphere
        :param name: str
        :param radius: float
        :return: str
        """

        axis = kwargs.get('axis', (0, 1, 0))
        construction_history = kwargs.get('construction_history', True)

        return maya.cmds.sphere(name=name, radius=radius, axis=axis, constructionHistory=construction_history)[0]

    @staticmethod
    def create_nurbs_cylinder(name='cylinder', radius=1.0, **kwargs):
        """
        Creates a new NURBS cylinder
        :param name: str
        :param radius: float
        :return: str
        """

        axis = kwargs.get('axis', (0, 1, 0))
        height_ratio = kwargs.get('height_ratio', 1)
        construction_history = kwargs.get('construction_history', True)

        return maya.cmds.cylinder(
            name=name, ax=axis, ssw=0, esw=360, r=radius, hr=height_ratio, d=3,
            ut=0, tol=0.01, s=8, nsp=1, ch=construction_history)[0]

    @staticmethod
    def rebuild_curve(curve, spans, **kwargs):
        """
        Rebuilds curve with given parameters
        :param curve: str
        :param spans: int
        :param kwargs:
        :return:
        """

        construction_history = kwargs.get('construction_history', True)
        replace_original = kwargs.get('replace_original', False)
        keep_control_points = kwargs.get('keep_control_points', False)
        keep_end_points = kwargs.get('keep_end_points', True)
        keep_tangents = kwargs.get('keep_tangents', True)
        # Degree: 1: linear; 2: quadratic; 3: cubic; 5: quintic; 7: hepetic
        degree = kwargs.get('degree', 3)
        # Rebuild Type: 0: uniform; 1: reduce spans; 2: match knots; 3: remove multiple knots;
        # 4: curvature; 5: rebuild ends; 6: clean
        rebuild_type = kwargs.get('rebuild_type', 0)
        # End Knots: 0: uniform end knots; 1: multiple end knots
        end_knots = kwargs.get('end_knots', 0)
        # Keep range: 0: reparametrize the resulting curve from 0 to 1; 1: keep the original curve parametrization;
        # 2: reparametrize the result from 0 to number of spans
        keep_range = kwargs.get('keep_range', 1)

        return maya.cmds.rebuildCurve(
            curve, spans=spans, rpo=replace_original, rt=rebuild_type, end=end_knots, kr=keep_range,
            kcp=keep_control_points, kep=keep_end_points, kt=keep_tangents, d=degree, ch=construction_history)

    @staticmethod
    def convert_surface_to_bezier(surface, **kwargs):
        """
        Rebuilds given surface as a bezier surface
        :param surface: str
        :return:
        """

        replace_original = kwargs.get('replace_original', True)
        construction_history = kwargs.get('construction_history', True)
        spans_u = kwargs.get('spans_u', 4)
        spans_v = kwargs.get('spans_v', 4)
        degree_u = kwargs.get('degree_u', 3)
        degree_v = kwargs.get('degree_v', 3)

        return maya.cmds.rebuildSurface(
            surface, ch=construction_history, rpo=replace_original,
            su=spans_u, sv=spans_v, rt=7, du=degree_u, dv=degree_v)

    @staticmethod
    def create_locator(name='loc'):
        """
        Creates a new locator
        :param name: str
        :return: str
        """

        return maya.cmds.spaceLocator(name=name)[0]

    @staticmethod
    def create_cluster(objects, cluster_name='cluster', **kwargs):
        """
        Creates a new cluster in the given objects
        :param objects: list(str)
        :param cluster_name: str
        :return: list(str)
        """

        relative = kwargs.pop('relative', False)

        return maya.cmds.cluster(objects, n=MayaDcc.find_unique_name(cluster_name), relative=relative, **kwargs)

    @staticmethod
    def create_decompose_matrix_node(node_name):
        """
        Creates a new decompose matrix node
        :param node_name: str
        :return: str
        """

        return maya.cmds.createNode('decomposeMatrix', name=node_name)

    @staticmethod
    def create_empty_mesh(mesh_name):
        """
        Creates a new empty mesh
        :param mesh_name:str
        :return: str
        """

        return maya.cmds.polyCreateFacet(
            name=mesh_name, ch=False, tx=1, s=1, p=[(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)])

    @staticmethod
    def create_circle_curve(name, **kwargs):
        """
        Creates a new circle control
        :param name: str
        :param kwargs:
        :return: str
        """

        construction_history = kwargs.get('construction_history', True)
        normal = kwargs.get('normal', (1, 0, 0))

        return maya.cmds.circle(n=name, normal=normal, ch=construction_history)[0]

    @staticmethod
    def create_joint(name, size=1.0, *args, **kwargs):
        """
        Creates a new joint
        :param name: str, name of the new joint
        :param size: float, size of the joint
        :return: str
        """

        pos = kwargs.pop('position', [0, 0, 0])

        return maya.cmds.joint(name=name, rad=size, p=pos)

    @staticmethod
    def orient_joint(joint, **kwargs):
        """
        Orients given joint
        :param joint: str
        :return:
        """

        # Aim At: 0: aim at world X; 1: aim at world Y; 2: aim at world Z; 3: aim at immediate child;
        # 4: aim at immediate parent; 5: aim at local parent (aiming at the parent and the reverseing the direction)
        aim_at = kwargs.get('aim_at', 3)
        # Aim Up At: 0: parent rotation:; 1: child position; 2: parent position; 3: triangle plane
        aim_up_at = kwargs.get('aim_up_at', 0)

        orient = joint_utils.OrientJointAttributes(joint)
        orient.set_default_values()
        orient = joint_utils.OrientJoint(joint)
        orient.set_aim_at(aim_at)
        orient.set_aim_up_at(aim_up_at)

        return orient.run()

    @staticmethod
    def create_ik_handle(name, start_joint, end_joint, solver_type=None, curve=None, **kwargs):
        """
        Creates a new IK handle
        :param name: str
        :param start_joint: str
        :param end_joint: str
        :param solver_type: str
        :param curve: str
        :param kwargs:
        :return: str
        """

        if solver_type is None:
            solver_type = ik_utils.IkHandle.SOLVER_SPLINE

        handle = ik_utils.IkHandle(name)
        handle.set_solver(solver_type)
        handle.set_start_joint(start_joint)
        handle.set_end_joint(end_joint)
        if curve and maya.cmds.objExists(curve):
            handle.set_curve(curve)

        return handle.create()

    @staticmethod
    def create_spline_ik_stretch(
            curve, joints, node_for_attribute=None, create_stretch_on_off=False, stretch_axis='X', **kwargs):
        """
        Makes the joints stretch on the curve
        :param curve: str, name of the curve that joints are attached via Spline IK
        :param joints: list<str>, list of joints attached to Spline IK
        :param node_for_attribute: str, name of the node to create the attributes on
        :param create_stretch_on_off: bool, Whether to create or not extra attributes to slide the stretch value on/off
        :param stretch_axis: str('X', 'Y', 'Z'), axis that the joints stretch on
        :param kwargs:
        """

        create_bulge = kwargs.get('create_bulge', True)

        return ik_utils.create_spline_ik_stretch(
            curve, joints, node_for_attribute=node_for_attribute, create_stretch_on_off=create_stretch_on_off,
            scale_axis=stretch_axis, create_bulge=create_bulge)

    @staticmethod
    def create_cluster_surface(
            surface, name, first_cluster_pivot_at_start=True, last_cluster_pivot_at_end=True, join_ends=False):
        """
        Creates a new clustered surface
        :param surface: str
        :param name: str
        :param first_cluster_pivot_at_start: str
        :param last_cluster_pivot_at_end: str
        :param join_ends: bool
        :return: list(str), list(str)
        """

        cluster_surface = deform_utils.ClusterSurface(surface, name)
        cluster_surface.set_first_cluster_pivot_at_start(first_cluster_pivot_at_start)
        cluster_surface.set_last_cluster_pivot_at_end(last_cluster_pivot_at_end)
        cluster_surface.set_join_ends(join_ends)
        cluster_surface.create()

        return cluster_surface.get_cluster_handle_list(), cluster_surface.get_cluster_list()

    @staticmethod
    def create_cluster_curve(
            curve, name, first_cluster_pivot_at_start=True, last_cluster_pivot_at_end=True, join_ends=False):
        """
        Creates a new clustered curve
        :param curve: str
        :param name: str
        :param first_cluster_pivot_at_start: str
        :param last_cluster_pivot_at_end: str
        :param last_cluster_pivot_at_end: str
        :param join_ends: bool
        :return: list(str), list(str)
        """

        cluster_curve = deform_utils.ClusterCurve(curve, name)
        cluster_curve.set_first_cluster_pivot_at_start(first_cluster_pivot_at_start)
        cluster_curve.set_last_cluster_pivot_at_end(last_cluster_pivot_at_end)
        cluster_curve.set_join_ends(join_ends)
        cluster_curve.create()

        return cluster_curve.get_cluster_handle_list(), cluster_curve.get_cluster_list()

    @staticmethod
    def create_wire(surface, curves, name='wire', **kwargs):
        """
        Creates a new wire that wires given surface/curve to given curves
        :param surface:str
        :param curves: list(str)
        :param name:str
        :param kwargs:
        :return: str, str
        """

        curves = python.force_list(curves)
        dropoff_distance = kwargs.get('dropoff_distance', [])
        group_with_base = kwargs.get('group_with_base', False)

        return maya.cmds.wire(surface, w=curves, n=name, dds=dropoff_distance, gw=group_with_base)

    @staticmethod
    def attach_transform_to_surface(transform, surface, u=None, v=None, constraint=False, attach_type=None):
        """
        Attaches a transform to given surface
        If no U an V values are given, the command will try to find the closest position on the surface
        :param transform: str, str, name of a transform to follicle to the surface
        :param surface: str, name of a surface to attach follicle to
        :param u: float, U value to attach to
        :param v: float, V value to attach to
        :param constraint: bool
        :param attach_type: bool
        :return: str, name of the follicle created
        """

        if attach_type is None:
            attach_type = 0

        # Follicle
        if attach_type == 0:
            return follicle_utils.follicle_to_surface(transform, surface, constraint=constraint)
        else:
            return rivet_utils.attach_to_surface(transform, surface, constraint=constraint)

    @staticmethod
    def create_curve(name, degree, points, knots, periodic):
        """
        Creates a new Nurbs curve
        :param name: str, name of the new curve
        :param degree: int
        :param points: list
        :param knots: list
        :param periodic: bool
        :return: str
        """

        return maya.cmds.curve(n=name, d=degree, p=points, k=knots, per=periodic)

    @staticmethod
    def create_curve_from_transforms(transforms, spans=None, description='from_transforms'):
        """
        Creates a curve from a list of transforms. Each transform will define a curve CV
        Useful when creating a curve from a joint chain (spines/tails)
        :param transforms: list<str>, list of tranfsorms to generate the curve from. Positions will be used to place CVs
        :param spans: int, number of spans the final curve should have
        :param description: str, description to given to the curve
        :return: str name of the new curve
        """

        return curve_utils.transforms_to_curve(transforms=transforms, spans=spans, description=description)

    @staticmethod
    def create_nurbs_surface_from_transforms(transforms, name, spans=-1, offset_axis='Y', offset_amount=1):
        """
        Creates a NURBS surface from a list of transforms
        Useful for creating a NURBS surface that follows a spine or tail
        :param transforms: list<str>, list of transforms
        :param name: str, name of the surface
        :param spans: int, number of spans to given to the final surface.
        If -1, the surface will have spans based on the number of transforms
        :param offset_axis: str, axis to offset the surface relative to the transform ('X', 'Y' or 'Z')
        :param offset_amount: int, amount the surface offsets from the transform
        :return: str, name of the NURBS surface
        """

        return geo_utils.transforms_to_nurbs_surface(
            transforms, name, spans=spans, offset_axis=offset_axis, offset_amount=offset_amount)

    @staticmethod
    def create_empty_follow_group(target_transform, **kwargs):
        """
        Creates a new follow group above a target transform
        :param target_transform: str, name of the transform make follow
        :param kwargs:
        :return:
        """

        return space_utils.create_empty_follow_group(target_transform, **kwargs)

    @staticmethod
    def create_follow_group(source_transform, target_transform, **kwargs):
        """
        Creates a group above a target transform that is constrained to the source transform
        :param source_transform: str, name of the transform to follow
        :param target_transform: str, name of the transform make follow
        :param kwargs:
        :return:
        """

        return space_utils.create_follow_group(source_transform, target_transform, **kwargs)

    @staticmethod
    def get_constraint_functions_dict():
        """
        Returns a dict that maps each constraint type with its function in DCC API
        :return: dict(str, fn)
        """

        return {
            'pointConstraint': maya.cmds.pointConstraint,
            'orientConstraint': maya.cmds.orientConstraint,
            'parentConstraint': maya.cmds.parentConstraint,
            'scaleConstraint': maya.cmds.scaleConstraint,
            'aimConstraint': maya.cmds.aimConstraint
        }

    @staticmethod
    def get_constraints():
        """
        Returns all constraints nodes in current DCC scene
        :return: list(str)
        """

        return maya.cmds.listRelatives(type='constraint')

    @staticmethod
    def get_constraint_targets(constraint_node):
        """
        Returns target of the given constraint node
        :param constraint_node: str
        :return: list(str)
        """

        cns = constraint_utils.Constraint()

        return cns.get_targets(constraint_node)

    @staticmethod
    def node_constraint(node, constraint_type):
        """
        Returns a constraint on the transform with the given type
        :param node: str
        :param constraint_type: str
        :return: str
        """

        cns = constraint_utils.Constraint()

        return cns.get_constraint(node, constraint_type=constraint_type)

    @staticmethod
    def node_constraints(node):
        """
        Returns all constraints a node is linked to
        :param node: str
        :return: list(str)
        """

        return maya.cmds.listRelatives(node, type='constraint')

    @staticmethod
    def node_transforms(node):
        """
        Returns all transforms nodes of a given node
        :param node: str
        :return: list(str)
        """

        return maya.cmds.listRelatives(node, type='transform')

    @staticmethod
    def node_joints(node):
        """
        Returns all oints nodes of a give node
        :param node: str
        :return: listr(str)
        """

        return maya.cmds.listRelatives(node, type='joint')

    @staticmethod
    def node_shape_type(node):
        """
        Returns the type of the given shape node
        :param node: str
        :return: str
        """

        return shape_utils.get_shape_node_type(node)

    @staticmethod
    def delete_node_constraints(node):
        """
        Removes all constraints applied to the given node
        :param node: str
        """

        return maya.cmds.delete(maya.cmds.listRelatives(node, ad=True, type='constraint'))

    @staticmethod
    def set_parent_controller(control, parent_controller):
        """
        Sets the parent controller of the given control
        :param control: str
        :param parent_controller: str
        """

        return maya.cmds.controller(control, parent_controller, p=True)

    @staticmethod
    def distance_between_nodes(source_node=None, target_node=None):
        """
        Returns the distance between 2 given nodes
        :param str source_node: first node to start measuring distance from.
            If not given, first selected node will be used.
        :param str target_node: second node to end measuring distance to.
            If not given, second selected node will be used.
        :return: distance between 2 nodes.
        :rtype: float
        """

        return mathutils.distance_between_nodes(source_node, target_node)

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
    def get_pole_vector_position(transform_init, transform_mid, transform_end, offset=1):
        """
        Given 3 transform (such as arm, elbow, wrist), returns a position where pole vector should be located
        :param transform_init: str, name of a transform node
        :param transform_mid: str, name of a transform node
        :param transform_end: str, name of a transform node
        :param offset: float, offset value for the final pole vector position
        :return: list(float, float, float), pole vector with offset
        """

        return transform.get_pole_vector(transform_init, transform_mid, transform_end, offset=offset)

    @staticmethod
    def get_control_colors():
        """
        Returns control colors available in DCC
        :return: list(float, float, float)
        """

        return maya_color.CONTROL_COLORS

    @staticmethod
    def get_all_fonts():
        """
        Returns all fonts available in DCC
        :return: list(str)
        """

        return maya.cmds.fontDialog(FontList=True) or list()

    @staticmethod
    def get_side_labelling(node):
        """
        Returns side labelling of the given node
        :param node: str
        :return: list(str)
        """

        if not MayaDcc.attribute_exists(node, 'side'):
            return 'None'

        side_index = MayaDcc.get_attribute_value(node, 'side')

        return MayaDcc.SIDE_LABELS[side_index]

    @staticmethod
    def set_side_labelling(node, side_label):
        """
        Sets side labelling of the given node
        :param node: str
        :param side_label: str
        """

        if not side_label or side_label not in MayaDcc.SIDE_LABELS or not MayaDcc.attribute_exists(node, 'side'):
            return False

        side_index = MayaDcc.SIDE_LABELS.index(side_label)

        return MayaDcc.set_attribute_value(node, 'side', side_index)

    @staticmethod
    def get_type_labelling(node):
        """
        Returns type labelling of the given node
        :param node: str
        :return: list(str)
        """

        if not MayaDcc.attribute_exists(node, 'type'):
            return 'None'

        type_index = MayaDcc.get_attribute_value(node, 'type')

        return MayaDcc.TYPE_LABELS[type_index]

    @staticmethod
    def set_type_labelling(node, type_label):
        """
        Sets type labelling of the given node
        :param node: str
        :param type_label: str
        """

        if not type_label or type_label not in MayaDcc.TYPE_LABELS or not MayaDcc.attribute_exists(node, 'type'):
            return False

        type_index = MayaDcc.TYPE_LABELS.index(type_label)

        return MayaDcc.set_attribute_value(node, 'type', type_index)

    @staticmethod
    def get_other_type_labelling(node):
        """
        Returns other type labelling of the given node
        :param node: str
        :return: list(str)
        """

        if not MayaDcc.get_type_labelling(node) == 'Other':
            return ''

        if not MayaDcc.attribute_exists(node, 'otherType'):
            return ''

        return MayaDcc.get_attribute_value(node, 'otherType')

    @staticmethod
    def set_other_type_labelling(node, other_type_label):
        """
        Sets other type labelling of the given node
        :param node: str
        :param other_type_label: str
        """

        if not MayaDcc.get_type_labelling(node) == 'Other' or not MayaDcc.attribute_exists(node, 'otherType'):
            return False

        return MayaDcc.set_attribute_value(node, 'otherType', str(other_type_label))

    @staticmethod
    def get_draw_label_labelling(node):
        """
        Returns draw label labelling of the given node
        :param node: str
        :return: list(str)
        """

        if not MayaDcc.attribute_exists(node, 'drawLabel'):
            return False

        return MayaDcc.get_attribute_value(node, 'drawLabel')

    @staticmethod
    def set_draw_label_labelling(node, draw_type_label):
        """
        Sets draw label labelling of the given node
        :param node: str
        :param draw_type_label: str
        """

        if not MayaDcc.attribute_exists(node, 'drawLabel'):
            return False

        return MayaDcc.set_attribute_value(node, 'drawLabel', bool(draw_type_label))

    @staticmethod
    def get_up_axis_name():
        """
        Returns the name of the current DCC up axis
        :return: str
        """

        return maya.cmds.upAxis(query=True, axis=True)

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

    @staticmethod
    def get_repeat_last_decorator(command_name=None):
        """
        Returns repeat last decorator for current DCC
        """

        return maya_decorators.repeat_static_command(command_name)


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
            tpDcc.logger.debug(msg)
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

    def set_progress(self, value):
        """
        Set progress bar progress value
        :param value: int
        """

        return maya.cmds.progressBar(self.progress_ui, edit=True, progress=value)

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
