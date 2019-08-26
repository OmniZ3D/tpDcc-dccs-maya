#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with joints
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya
from tpPyUtils import strings, python
from tpMayaLib.core import exceptions, decorators, mathutils, scene, attribute, transform, node, transform as xform_utils, constraint as cns_utils


class BuildJointHierarchy(object):
    def __init__(self):
        self._transforms = list()
        self._replace_old = None
        self._replace_new = None

    # region Public Functions
    def create(self):
        """
        Creates the new joint hierarchy
        :return: list<str>
        """

        new_joints = self._build_hierarchy()

        return new_joints

    def set_transforms(self, transform_list):
        """
        Set the list of transform that we need to create joint hierarchy for
        :param transform_list: list<str>
        """

        self._transforms = transform_list

    def set_replace(self, old, new):
        """
        Replace the naming in the new joints
        :param old: str, string in the duplicate name to replace
        :param new: str, string in the duplicate to replace with
        """

        self._replace_old = old
        self._replace_new = new
    # endregion

    # region Private Functions
    def _build_hierarchy(self):
        new_joints = list()
        last_transform = None

        for xform in self._transforms:
            maya.cmds.select(clear=True)
            joint = maya.cmds.joint()
            xform_utils.MatchTransform(xform, joint).translation_rotation()
            xform_utils.MatchTransform(xform, joint).world_pivots()
            new_joints.append(joint)
            if last_transform:
                maya.cmds.parent(joint, last_transform)
            last_transform = joint

        return new_joints
    # endregion


class AttachJoints(object):
    """
    Attaches a chain of joints to a matching chain using parent and scale constraints
    """

    class AttachType(object):
        CONSTRAINT = 0
        MATRIX = 1

        @staticmethod
        def get_string_list():
            """
            Returns a list with the attach types as strings
            :return: list<str>
            """

            return ['Constraint', 'Matrix']

    def __init__(self, source_joints, target_joints):
        self._source_joints = source_joints
        self._target_joints = target_joints
        self._attach_type = AttachJoints.AttachType.CONSTRAINT

    # region Public Functions
    def create(self):
        """
        Creates the attachments
        """

        self._attach_joints(self._source_joints, self._target_joints)

    def set_source_and_target_joints(self, source_joints, target_joints):
        """
        :param source_joints: list<str>, list of joint names that should move the target
        :param target_joints: list<str>, list of joint names that should be moved by the source
        """

        self._source_joints = source_joints
        self._target_joints = target_joints

    def set_attach_type(self, attach_type):
        self._attach_type = attach_type
    # endregion

    # region Private Functions
    def _hook_scale_constraint(self, node):
        cns = cns_utils.Constraint()
        scale_cns = cns.get_constraint(node, cns_utils.Constraints.SCALE)
        if not scale_cns:
            return
        cns_utils.scale_constraint_to_world(scale_cns)

    def _unhook_scale_constraint(self, scale_constraint):
        cns_utils.scale_constraint_to_local(scale_constraint)

    def _attach_joint(self, source_joint, target_joint):
        if self._attach_type == AttachJoints.AttachType.CONSTRAINT:
            self._hook_scale_constraint(target_joint)
            parent_cns = maya.cmds.parentConstraint(source_joint, target_joint, mo=True)[0]
            maya.cmds.setAttr('{}.interpType'.format(parent_cns), 2)
            scale_cns = maya.cmds.scaleConstraint(source_joint, target_joint)[0]
            cns = cns_utils.Constraint()
            cns.create_switch(self._target_joints[0], 'switch', parent_cns)
            cns.create_switch(self._target_joints[0], 'switch', scale_cns)
            self._unhook_scale_constraint(scale_cns)
        elif self._attach_type == AttachJoints.AttachType.MATRIX:
            switches = cns_utils.SpaceSwitch().get_space_switches(target_joint)
            if switches:
                cns_utils.SpaceSwitch().add_source(source_joint, target_joint, switches[0])
                cns_utils.SpaceSwitch().create_switch(self._target_joints[0], 'switch', switches[0])
            else:
                switch = cns_utils.SpaceSwitch(source_joint, target_joint)
                switch.set_use_weight(True)
                switch_node = switch.create()
                switch.create_switch(self._target_joints[0], 'switch', switch_node)

    def _attach_joints(self, source_chain, target_chain):
        for i in range(len(source_chain)):
            self._attach_joint(source_chain[i], target_chain[i])
    # endregion


class OrientJointAttributes(object):
    """
    Creates attributes on a node that can be used with OrientAttributes
    """

    def __init__(self, joint):
        """
        Constructor
        :param joint: str, name of the joint we want to create orient attributes to
        """

        self.joint = None
        self.attributes = list()
        self.title = None

        if is_joint(joint) or xform_utils.is_transform(joint):
            self.joint = joint
            self._create_attributes()

    @staticmethod
    @decorators.undo_chunk
    def add_orient_attributes(obj):
        """
        Adds orient attributes to the given joint node
        :param obj: str, name of a valid joint node
        """

        if type(obj) is not list:
            obj = [obj]

        for o in obj:
            if not is_joint(o) and not xform_utils.is_transform(o):
                continue
            ori = OrientJointAttributes(joint=o)
            ori.set_default_values()

    @staticmethod
    def zero_orient_joint(joint):
        """
        Move orientation to orient joint attributes and zero out orient attributes from the given joint node
        :param joint: str, name of valid joint node
        """

        if type(joint) is not list:
            joint = [joint]

        for jnt in joint:
            if not is_joint(jnt):
                continue
            for axis in 'XYZ':
                rotate_value = maya.cmds.getAttr('{}.rotate{}'.format(jnt, axis))
                maya.maya.cmds.setAttr('{}.rotate{}'.format(jnt, axis), 0)
                maya.maya.cmds.setAttr('{}.jointOrient{}'.format(jnt, axis), rotate_value)

    @staticmethod
    def remove_orient_attributes(joint):
        """
        Removes orient attributes from the given joint node
        :param joint: str, name of valid joint node
        """

        if type(joint) is not list:
            joint = [joint]

        for jnt in joint:
            if not is_joint(jnt):
                continue
            ori = OrientJointAttributes(joint=jnt)
            ori.delete()

    @classmethod
    def orient_with_attributes(cls, objects_to_orient=None, force_orient_attributes=False):
        """
        Orients all joints and transforms with OrientJointAttribute added on them
        :param objects_to_orient: list<str>, if given, only given objects will be oriented
        """

        if not objects_to_orient:
            objects_to_orient = scene.get_top_dag_nodes()

        maya.logger.debug('Orienting {}'.format(objects_to_orient))

        oriented = False
        for obj in objects_to_orient:
            relatives = maya.cmds.listRelatives(obj, f=True)
            if not maya.cmds.objExists('{}.ORIENT_INFO'.format(obj)):
                if force_oriernt_attributes:
                    cls.add_orient_attributes(obj)
                else:
                    if relatives:
                        cls.orient_with_attributes(objects_to_orient=relatives, force_orient_attributes=force_orient_attributes)
                        oriented = True
                    continue

            if maya.cmds.nodeType(obj) in ['joint', 'transform']:
                orient = OrientJoint(joint_name=obj)
                orient.run()
                if relatives:
                    cls.orient_with_attributes(objects_to_orient=relatives, force_orient_attributes=force_orient_attributes)
                    oriented = True

        return oriented

    def set_joint(self, joint):
        """
        Set a joint to create attributes on
        :param joint: str, name of the joint
        """

        if not is_joint(joint):
            return

        self.joint = joint

        self._create_attributes()

    def get_values(self):
        """
        Returns all orient settings attributes as a dictionary
        :return: dict
        """

        values_dict = dict()
        for attr in self.attributes:
            values_dict[attr.get_name()] = attr.get_value()

        return values_dict

    def set_values(self, value_dict):
        """
        Set joint orient attributes by the values stored in the given dictionary (get_values() function generates that dict)
        :param value_dict: dict
        """

        for attr in self.attributes:
            attr.set_value(value_dict[attr.get_name()])

    def set_default_values(self):
        """
        Set all joint orient axis to their default values
        """

        for attr in self.attributes:
            attr.set_default_value()

    def delete(self):
        """
        Removes all joint orient attributes (created on _create_attribute() function)
        """

        if self.title:
            self.title.delete()

        for attr in self.attributes:
            attr.delete()

    def _create_attributes(self):
        """
        Internal function that creates joint orient attributes
        """

        self.title = attribute.EnumAttribute('Orient_Info'.upper())
        self.title.set_locked(True)
        self.title.create(self.joint)

        self.attributes.append(attribute.create_axis_attribute(name='aimAxis', node=self.joint, value=0))
        self.attributes.append(attribute.create_axis_attribute(name='upAxis', node=self.joint, value=1))
        self.attributes.append(attribute.create_axis_attribute(name='worldUpAxis', node=self.joint, value=1))

        aim_at_attr = attribute.EnumAttribute('aimAt', value=3)
        aim_at_attr.set_enum_names(['worldX', 'worldY', 'worldZ', 'child', 'parent', 'localParent'])
        aim_at_attr.create(self.joint)
        self.attributes.append(aim_at_attr)

        aim_up_attr = attribute.EnumAttribute('aimUpAt', value=0)
        aim_up_attr.set_enum_names(['world', 'parentRotate', 'childPosition', 'trianglePlane', '2ndChildPosition'])
        aim_at_attr.create(self.joint)
        self.attributes.append(aim_up_attr)

        self.attributes.append(attribute.create_triangle_attribute(name='triangleTop', node=self.joint, value=1))
        self.attributes.append(attribute.create_triangle_attribute(name='triangleMid', node=self.joint, value=2))
        self.attributes.append(attribute.create_triangle_attribute(name='triangleBottom', node=self.joint, value=3))

        active_attr = attribute.NumericAttribute('active', value=1)
        active_attr.set_variable_type(attribute.AttributeTypes.Bool)
        active_attr.set_keyable(True)
        active_attr.create(self.joint)
        self.attributes.append(active_attr)


class OrientJoint(object):
    """
    Orient the joint using attributes created with OrientJointAttributes
    """

    def __init__(self, joint_name):
        """
        Constructor
        :param joint_name: str, name of the joint we want to orient
        """

        self.joint = joint_name
        self.orient_values = None
        self.aim_vector = [1, 0, 0]
        self.up_vector = [0, 1, 0]
        self.world_up_vector = [0, 1, 0]

        self.aim_at = 3
        self.aim_up_at = 0

        self.child = None
        self.chidl2 = None
        self.grand_child = None
        self.parent = None
        self.grand_parent = None

        self.delete_later = list()
        self.world_up_vector = self.get_vector_from_axis(1)
        self.up_space_type = 'vector'

        self._get_relatives()

    @staticmethod
    def get_vector_from_axis(axis_index):
        """
        Returns vector from the given axis type
        :param axis_index: int
        :return: list<int, int, int>
        """

        vectors = [[1, 0, 0],
                   [0, 1, 0],
                   [0, 0, 1],
                   [-1, 0, 0],
                   [0, -1, 0],
                   [0, 0, -1],
                   [0, 0, 0]]

        return vectors[axis_index]

    def set_aim_vector(self, vector_list):
        """
        Set the aim vector for the orient process
        :param vector_list: list<float, float, float>, vector that defines what axis should aim
        """

        self.aim_vector = vector_list

    def set_up_vector(self, vector_list):
        """
        Set the up vector for the orient process
        :param vector_list: list<float, float, float>, vector that defines what axis should aim up
        """

        self.up_vector = vector_list

    def set_world_up_vector(self, vector_list):
        """
        Set the world up axis for the orient process
        :param vector_list: list<float, float, float>, vector that defines what world up axis be
        """

        self.world_up_vector = vector_list

    def set_aim_at(self, index):
        """
        Defines how the joint will aim
        :param index: int, aim at index value
                                0: aim at world X
                                1: aim at world Y
                                2: aim at world Z
                                3: aim at inmediate child
                                4: aim at inmediate parent
                                5: aim at local parent (aiming at the parent and then reversing the direction)
        """

        self.aim_at = self._get_aim_at(index=index)

    def set_aim_up_at(self, index):
        """
        Defines how the will aim up
        :param index: int, aim up at index value
                                0: parent rotate
                                1: child position
                                2: parent position
                                3: triangle plane (need to be configured before)
        """

        self.aim_up_at = self._get_aim_up_at(index=index)

    def set_aim_up_at_object(self, transform_name):
        """
        Defines the object used for aim up
        :param transform_name: str, name of the object
        """

        self.aim_up_at = self._get_local_up_group(transform_name=transform_name)
        self.up_space_type = 'objectrotation'
        self.world_up_vector = [0, 1, 0]

    def run(self):
        """
        Orients joints
        """

        if maya.cmds.objExists('{}.active'.format(self.joint)):
            if not maya.cmds.getAttr('{}.active'.format(self.joint)):
                maya.logger.warning('{} has orientation attributes but is not acitve. Skipping ...'.format(self.joint))
                return

        self._freeze()
        self._get_relatives()
        self._pin()

        try:
            for axis in 'xyz':
                maya.cmds.setAttr('{}.rotateAxis{}'.format(self.joint, axis.upper()), 0)
        except Exception:
            maya.logger.warning('Could not zero our rotateAxis on {}. This can cause rig errors!'.format(self.joint))

        self.orient_values = self._get_values()

        if self.orient_values:
            self.aim_vector = self.get_vector_from_axis(self.orient_values['aimAxis'])
            self.up_vector = self.get_vector_from_axis(self.orient_values['upAxis'])
            self.world_up_vector = self.get_vector_from_axis(self.orient_values['worldUpAxis'])
            self.aim_at = self._get_aim_at(self.orient_values['aimAt'])
            self.aim_up_at = self._get_aim_up_at(self.orient_values['aimUpAt'])
        else:
            if type(self.aim_at) == int:
                self.aim_at = self._get_aim_at(self.aim_at)
            if type(self.aim_up_at) == int:
                self.aim_up_at = self._get_aim_up_at(self.aim_up_at)

        self._create_aim()
        self._cleanup()
        self._freeze()

    def _get_values(self):
        """
        Returns orient joint attributes stored in the wrapped joint node
        :return: dict<str, Attribute>
        """

        if not maya.cmds.objExists('{}.ORIENT_INFO'.format(self.joint)):
            maya.logger.warning(
                'Impossible to get orient attributes from {} because they do not exists!'.format(self.joint))
            return

        ori_attrs = OrientJointAttributes(joint=self.joint)
        return ori_attrs.get_values()

    def _get_relatives(self):
        """
        Internal function that returns all relatives joints of the given joint
        """

        # Get parent and grand parent nodes
        parent = maya.cmds.listRelatives(self.joint, p=True, f=True)
        if parent:
            self.parent = parent[0]
            grand_parent = maya.cmds.listRelatives(self.parent, p=True, f=True)
            if grand_parent:
                self.grand_parent = grand_parent[0]

        # Get children and grand children
        children = maya.cmds.listRelatives(self.joint, f=True, type='transform')
        if children:
            self.child = children[0]
            if len(children) > 1:
                self.child2 = children[1]
            grand_children = maya.cmds.listRelatives(self.child, f=True)
            if grand_children:
                self.grand_child = grand_children[0]

    def _get_aim_at(self, index):
        """
        Creates and returns the group we want to aim depending of the given index option
        :param index: int, index that defines how we want to create the aim group
        :return: str, created group positioned where lookAt constraint should aim
        """

        # World Axis (0=X, 1=Y, 2=Z)
        if index < 3:
            world_aim = maya.cmds.group(empty=True, n='world_aim')
            transform.MatchTransform(source_transform=self.joint, target_transform=world_aim).translation()

            if index == 0:
                maya.cmds.move(1, 0, 0, world_aim, r=True)
            elif index == 1:
                maya.cmds.move(0, 1, 0, world_aim, r=True)
            elif index == 2:
                maya.cmds.move(0, 0, 1, world_aim, r=True)

            self.delete_later.append(world_aim)
            return world_aim

        # Child
        elif index == 3:
            child_aim = self._get_position_group(self.child)
            return child_aim

        # Parent
        elif index == 4:
            parent_aim = self._get_position_group(self.parent)
            return parent_aim

        # Front (in X axis) of wrapped joint
        elif index == 5:
            aim = self._get_local_up_group(self.parent)
            return aim

    def _get_aim_up_at(self, index):
        """
        Creates and returns the group we want to set as up group depending of the given index option
        :param index: int, index that defines how we want to create the aim up group
        :return: str, created group positioned where lookAt up axis should look
        """

        if index == 1:
            self.up_space_type = 'objectrotation'
            return self._get_local_up_group(self.parent)

        elif index == 2:
            child_group = self._get_position_group(self.child)
            self.up_space_type = 'object'
            return child_group

        elif index == 3:
            parent_group = self._get_position_group(self.parent)
            self.up_space_type = 'object'
            return parent_group

        elif index == 4:
            top = self._get_triangle_group(self.orient_values['triangleTop'])
            mid = self._get_triangle_group(self.orient_values['triangleMid'])
            btm = self._get_triangle_group(self.orient_values['triangleBottom'])
            if not top or not mid or not btm:
                maya.logger.warning('Could not orient {} fully with current triangle plane settings'.format(self.joint))
                return

            plane_grp = xform_utils.create_group_in_plane(top, mid, btm)
            maya.cmds.move(0, 10, 0, plane_grp, r=True, os=True)
            self.delete_later.append(plane_grp)
            self.up_space_type = 'object'
            return plane_grp

        elif index == 5:
            self.up_space_type = 'object'
            child_grp = None

            if self.child2 and maya.cmds.objExists(self.child2):
                child_grp = self._get_position_group(self.child2)
            if not self.child2 or not maya.cmds.objExists(self.child2):
                maya.logger.warning(
                    'Child2 specified as up in orient attribute but {} has no 2nd child'.format(self.joint))

            return child_grp

    def _freeze(self):
        """
        Internal function that freezes wrapped joint without touching its hierarchy
        """

        children = maya.cmds.listRelatives(self.joint, f=True)

        found_children = list()
        if children:
            for child in children:
                if xform_utils.is_transform(child):
                    child_parented = maya.cmds.parent(child, w=True)[0]
                    found_children.append(child_parented)

        maya.cmds.makeIdentity(self.joint, apply=True, r=True, s=True)

        if found_children:
            maya.cmds.parent(found_children, self.joint)

    def _pin(self):
        """
        Internal function that pin joint so its children and parent does not move when transforming
        Updates list of nodes to remove so pin is removed after orienting
        """

        pin = transform.PinTransform(transform_name=self.joint)
        pin.pin()

        nodes = pin.get_pin_nodes()
        self.delete_later += nodes

    def _get_local_up_group(self, transform_name):
        """
        Creates an empty group matching give transform rotation but positioned in front of the
        current wrapped joint (moved in X axis)
        :param transform_name: str, transform we want to match position to
        :return: str, new created local up group
        """

        local_up_group = maya.cmds.group(empty=True, n='local_up_{}'.format(transform))
        transform.MatchTransform(source_transform=transform_name, target_transform=local_up_group).rotation()
        transform.MatchTransform(source_transform=self.joint, target_transform=local_up_group).translation()
        maya.cmds.move(1, 0, 0, local_up_group, relative=True, objectSpace=True)
        self.delete_later.append(local_up_group)

        return local_up_group

    def _get_position_group(self, transfrom_name):
        """
        Creates an empty group with its transformations matching the given transform node
        :param transfrom_name: str, transform we want to match new group to
        :return: str, new created position group
        """

        position_group = maya.cmds.group(empty=True, name='position_group')
        transform.MatchTransform(source_transform=transfrom_name,
                                 target_transform=position_group).translation_rotation()
        self.delete_later.append(position_group)

        return position_group

    def _get_triangle_group(self, index):
        """
        Creates an empty group positioned based on the childs/parents based on given index
        :param index: int, index that defines position of the group
        (0=grand_parent, 1=parent, 2=joint, 3=child, 4=grand_child)
        :return: str, new created triangle position group
        """

        target_transform = None
        if index == 0:
            target_transform = self.grand_parent
        elif index == 1:
            target_transform = self.parent
        elif index == 2:
            target_transform = self.joint
        elif index == 4:
            target_transform = self.child
        elif index == 4:
            target_transform = self.grand_child
        if not target_transform:
            return

        return self._get_position_group(target_transform)

    def _create_aim(self):
        """
        Create aim constraints used to orient the joint
        """

        if self.aim_up_at:
            aim = maya.cmds.aimConstraint(
                self.aim_at,
                self.joint,
                aimVector=self.aim_vector,
                upVector=self.up_vector,
                worldUpObject=self.aim_up_at,
                worldUpVector=self.world_up_vector,
                worldUpType=self.up_space_type)[0]
        else:
            aim = maya.cmds.aimConstraint(
                self.aim_at,
                self.joint,
                aimVector=self.aim_vector,
                upVector=self.up_vector,
                worldUpVector=self.world_up_vector,
                worldUpType=self.up_space_type)[0]

        self.delete_later.append(aim)

    def _cleanup(self):
        """
        Removes all extra nodes created during orient process
        """

        maya.cmds.delete(self.delete_later)


def check_joint(joint):
    """
    Checks if a node is a valid joint and raise and exception if the joint is not valid
    :param joint: str, name of the node to be checked
    :return: bool, True if the give node is a joint node or False otherwise
    """

    if not is_joint(joint):
        raise exceptions.JointException(joint)


def is_joint(joint):
    """
    Checks if the given object is a joint
    :param joint: str, object to query
    :return: bool, True if the given object is a valid joint or False otherwise
    """

    if not maya.cmds.objExists(joint):
        return False

    if not maya.cmds.ls(type='joint').count(joint):
        return False

    return True


def is_end_joint(joint):
    """
    Returns True if the given joint is an end joint (last child of hierarchy) or False otherwise
    :param joint: str, name of the joint to check
    :return: bool
    """

    check_joint(joint)

    joint_descendants = maya.cmds.ls(maya.cmds.listRelatives(joint, ad=True) or [], type='joint')
    if not joint_descendants:
        return True

    return False


def get_end_joint(start_joint, include_transforms=False):
    """
    Find the end joint of a chain from the given start joint
    :param start_joint: str, joint to find end joint from
    :param include_transforms: bool, Include non-joint transforms in the chain
    :return: str
    """

    check_joint(start_joint)

    end_joint = None
    next_joint = start_joint
    while next_joint:
        child_list = maya.cmds.listRelatives(next_joint, c=True) or []
        child_joints = maya.cmds.ls(child_list, type='joint') or []
        if include_transforms:
            child_joints = list(set(child_joints + maya.cmds.ls(child_list, transforms=True) or []))
        if child_joints:
            next_joint = child_joints[0]
        else:
            end_joint = next_joint
            next_joint = None

    return end_joint


def get_joint_list(start_joint, end_joint):
    """
    Get list of joints between and including given start and end joint
    :param start_joint: str, start joint of joint list
    :param end_joint: str, end joint of joint list
    :return: list<str>
    """

    check_joint(start_joint)
    check_joint(end_joint)

    if start_joint == end_joint:
        return [start_joint]

    # Check hierarchy
    descendant_list = maya.cmds.ls(maya.cmds.listRelatives(start_joint, ad=True), type='joint')
    if not descendant_list.count(end_joint):
        raise Exception('End joint "{}" is not a descendant of start joint "{}"'.format(end_joint, start_joint))

    joint_list = [end_joint]
    while joint_list[-1] != start_joint:
        parent_jnt = maya.cmds.listRelatives(joint_list[-1], p=True, pa=True)
        if not parent_jnt:
            raise Exception('Found root joint while searching for start joint "{}"'.format(start_joint))
        joint_list.append(parent_jnt[0])

    joint_list.reverse()

    return joint_list


def get_length(joint):
    """
    Returns the length of a given joint
    :param joint: str, joint to query length from
    :return: str
    """

    check_joint(joint)

    child_joints = maya.cmds.ls(maya.cmds.listRelatives(joint, c=True, pa=True) or [], type='joint')
    if not child_joints:
        return 0.0

    max_length = 0.0
    for child_jnt in child_joints:
        pt1 = transform.get_position(joint)
        pt2 = transform.get_position(child_jnt)
        offset = mathutils.offset_vector(pt1, pt2)
        length = mathutils.magnitude(offset)
        if length > max_length:
            max_length = length

    return max_length


def duplicate_joint(joint, name=None):
    """
    Duplicates a given joint
    :param joint: str, joint to duplicate
    :param name: variant, str || None, new name for duplicated joint. If None, leave as default
    :return: str
    """

    check_joint(joint)
    if not name:
        name = joint+'_dup'
    if maya.cmds.objExists(str(name)):
        raise Exception('Joint "{}" already exists!'.format(name))

    dup_joint = maya.cmds.duplicate(joint, po=True)[0]
    if name:
        dup_joint = maya.cmds.rename(dup_joint, name)

    # Unlock transforms
    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v', 'radius']:
        maya.cmds.setAttr(dup_joint+'.'+attr, l=False, cb=True)

    return dup_joint


def duplicate_chain(start_jnt, end_jnt=None, parent=None, skip_jnt=None, prefix=None):
    """
    Duplicats a joint chain based on start and en joint
    :param start_jnt: str, start joint of chain
    :param end_jnt: str, end joint of chain. If None, use end of current chain
    :param parent: str, parent transform for new chain
    :param skip_jnt: variant, str ||None, skip joints in chain that match name pattern
    :param prefix: variant, str ||None, new name prefix
    :return: list<str>, list of duplicate joints
    """

    if not maya.cmds.objExists(start_jnt):
        raise Exception('Start joint "{}" does not exists!'.format(start_jnt))
    if end_jnt and not maya.cmds.objExists(str(end_jnt)):
        raise Exception('End joint "{}" does not exists!'.format(end_jnt))

    if parent:
        if not maya.cmds.objExists(parent):
            raise Exception('Given parent transform "{}" does not eixsts!'.format(parent))
        if not transform.is_transform(parent):
            raise Exception('Parent object "{}" is not a valid transform!'.format(parent))

    if not end_jnt:
        end_jnt = get_end_joint(start_jnt=start_jnt)
    joints = get_joint_list(start_joint=start_jnt, end_joint=end_jnt)

    skip_joints = maya.cmds.ls(skip_jnt) if skip_jnt else list()

    dup_chain = list()
    for i in range(len(joints)):
        if joints[i] in skip_joints:
            continue

        name = None
        if prefix:
            jnt_index = strings.get_alpha(i, capital=True)
            if i == (len(joints)-1):
                jnt_index = 'End'
            name = prefix+jnt_index+'_jnt'

        jnt = duplicate_joint(joint=joints[i], name=name)

        if not i:
            if not parent:
                if maya.cmds.listRelatives(jnt, p=True):
                    try:
                        maya.cmds.parent(jnt, w=True)
                    except Exception:
                        pass
            else:
                try:
                    maya.cmds.parent(jnt, parent)
                except Exception:
                    pass
        else:
            try:
                maya.cmds.parent(jnt, dup_chain[-1])
                if not maya.cmds.isConnected(dup_chain[-1]+'.scale', jnt+'.inverseScale'):
                    maya.cmds.connectAttr(dup_chain[-1]+'.scale', jnt+'.inverseScale', f=True)
            except Exception as e:
                raise Exception('Error while duplicating joint chain! - {}'.format(str(e)))

        dup_chain.append(jnt)

    return dup_chain


def joint_buffer(joint, index_str=0):
    """
    Creates a joint buffer group in the given joint
    :param joint: str, name of the joint we want to create buffer for
    :param index_str: int, string index
    :return: str, name of the joint buffer group created
    """

    if not maya.cmds.objExists(joint):
        raise Exception('Joint "{}" does not exists!'.format(joint))

    if not index_str:
        result = maya.cmds.promptDialog(
            title='Index String',
            message='Joint Group Index',
            text='0',
            button=['Create', 'Cancel'],
            defaultButton='Create',
            cancelButton='Cancel',
            dismissString='Cancel'
        )

        if result == 'Create':
            index_str = maya.cmds.promptDialog(q=True, text=True)
        else:
            maya.logger.warning('User canceled joint group creation ...')
            return

        # Get joint prefix and create joint buffer group
        prefix = strings.strip_suffix(joint)
        grp = maya.cmds.duplicate(joint, po=True, n=prefix+'Buffer'+index_str+'_jnt')[0]
        maya.cmds.parent(joint, grp)

        if maya.cmds.getAttr(grp+'.radius', se=True):
            try:
                maya.cmds.setAttr(grp+'.radius', 0)
            except Exception:
                pass

        # Connect inverse scale
        inverse_scale_cnt = maya.cmds.listConnections(joint+'.inverseScale', s=True, d=False)
        if not inverse_scale_cnt:
            inverse_scale_cnt = list()
        if not inverse_scale_cnt.count(grp):
            try:
                maya.cmds.connectAttr(grp+'.scale', joint+'.inverseScale', f=True)
            except Exception:
                pass

        # Delete user attributes
        user_attrs = maya.cmds.listAttr(grp, ud=True)
        if user_attrs:
            for attr in user_attrs:
                if maya.cmds.objExists(grp+'.'+attr):
                    maya.cmds.setAttr(grp+'.'+attr, l=False)
                    maya.cmds.deleteAttr(grp+'.'+attr)

        node.display_override(obj=joint, override_enabled=True, override_lod=0)
        node.display_override(obj=grp, override_enabled=True, override_display=2, override_lod=1)


def set_draw_style(joints, draw_style='bone'):
    """
    Set joint draw style for the given joints
    :param joints: list<str>, list of joints to set draw style for
    :param draw_style: str, draw style to apply to the given joints ("bone", "box", "none")
    :return: list<str>, list of joints which draw styles have been changed
    """

    if not joints:
        raise Exception('No joints given!')

    draw_style = draw_style.lower()
    if not draw_style in ['bone', 'box', 'none']:
        raise Exception('Invalid draw style ("{}")! Accepted values are "bone", "box", "none"'.format(draw_style))

    if type(joints) not in [list, tuple]:
        joints = [joints]

    for jnt in joints:
        if not is_joint(jnt):
            continue
        if draw_style == 'bone':
            maya.cmds.setAttr('{}.drawStyle'.format(jnt), 0)
        elif draw_style == 'box':
            maya.cmds.setAttr('{}.drawStyle'.format(jnt), 1)
        elif draw_style == 'none':
            maya.cmds.setAttr('{}.drawStyle'.format(jnt), 2)

    return joints


def create_from_point_list(point_list, orient=False, side='c', part='chain', suffix='jnt'):
    """
    Create joint chain from a list of point positions
    :param point_list: list<tuple>, list of points to create joint chain from
    :param orient: bool, Whether to orient or not the joints
    :param side: str, joint side name prefix
    :param part: str, joint part name
    :param suffix: str, joint suffix name
    :return: list<str>, list of new created joints
    """

    maya.cmds.select(cl=True)

    joint_list = list()
    for i in range(len(point_list)):
        jnt = maya.cmds.joint(p=point_list[i], n='{}_{}{}_{}'.format(side, part, str(i+1), suffix))
        if i and orient:
            maya.cmds.joint(joint_list[-1], e=True, zso=True, oj='xyz', sao='yup')
        joint_list.append(jnt)

    return joint_list


def orient(joint, aim_axis='x', up_axis='y', up_vec=(0,1,0)):
    """
    Orient joints based on user defined vectors
    :param joint: str, joints to orient
    :param aim_axis: str, axis to be aligned down the length of the joint
    :param up_axis: str, axis to be aligned with the world vector given by up vector
    :param up_vec: tuple<int>, world vector to align up axis to
    """

    pass


def start_joint_tool():
    """
    Initializes Maya joint creation tool
    """

    maya.cmds.JointTool()


def set_joint_local_rotation_axis_visibility(joints=None, bool_value=None):
    """
    Sets the joint visibility of the given node or given nodes
    :param joints: list<str>, list of joints to set axis visibility of. If None, given, all joints of the scene will be used
    :param bool_value: bool, value of the local rotation axis visibility. If None given, current joint visibility will be toggled
    :return:
    """

    if joints is None:
        joints = maya.cmds.ls(type='joint')
    else:
        joints = python.force_list(joints)

    for jnt in joints:
        if bool_value is None:
            new_value = not maya.cmds.getAttr('{}.displayLocalAxis'.format(jnt))
        else:
            new_value = bool_value
        maya.cmds.setAttr('{}.displayLocalAxis'.format(jnt), new_value)

    return True
