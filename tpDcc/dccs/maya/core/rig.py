#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig utils functions for Maya
"""

import logging

from tpDcc.libs.python import python

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import constraint as cns_utils, attribute as attr_utils, transform as transform_utils

LOGGER = logging.getLogger()


class RigSwitch(object):
    """
    Creates a switch between differetn rigs on a buffer joint
    """

    def __init__(self, switch_joint):
        """
        Constructor
        :param switch_joint: str, name of a buffer joint with switch attribute
        """

        self._switch_joint = switch_joint
        if not maya.cmds.objExists('{}.switch'.format(switch_joint)):
            LOGGER.warning('{} is most likely not a buffer joint with switch attribute'.format(switch_joint))

        self._groups = dict()

        weight_count = self.get_weight_count()
        if not weight_count:
            LOGGER.warning('{} has no weights!'.format(weight_count))

        for i in range(weight_count):
            self._groups[i] = None

        self._control_name = None
        self._attribute_name = 'switch'

    def create(self):
        if self._control_name and maya.cmds.objExists(self._control_name):
            weight_count = self.get_weight_count()
            var = attr_utils.NumericAttribute(self._attribute_name)
            var.set_min_value(0)
            max_value = weight_count - 1
            if max_value > var._get_max_value():
                max_value = var._get_max_value()
            var.set_max_value(max_value)
            var.set_keyable(True)
            var.create(self._control_name)
            attr_name = var.get_name()
            maya.cmds.connectAttr(attr_name, '{}.switch'.format(self._switch_joint))
        elif not self._control_name or not maya.cmds.objExists(self._control_name):
            attr_name = '{}.switch'.format(self._switch_joint)
        else:
            LOGGER.error('Impossible to create RigSwitch Attribute ...')
            return

        for key in self._groups.keys():
            groups = self._groups[key]
            if not groups:
                continue
            for group in groups:
                attr_utils.connect_equal_condition(attr_name, '{}.visibility'.format(group), key)

    def get_weight_count(self):
        edit_cns = cns_utils.Constraint()
        cns = edit_cns.get_constraint(self._switch_joint, 'parentConstraint')
        if cns:
            weight_count = edit_cns.get_weight_count(cns)
        else:
            switch_nodes = cns_utils.SpaceSwitch().get_space_switches(self._switch_joint)
            if switch_nodes:
                sources = cns_utils.SpaceSwitch().get_source(switch_nodes[0])
                weight_count = len(sources)
            else:
                weight_count = 0

        return weight_count

    def add_groups_to_index(self, index, groups):
        """
        A switch joint is meant to switch visibility between rigs
        By adding groups you define their visibility when switch attributes changes
        An index 0 means the group will be visible when the switch is 0 and invisible when is 1
        :param index: int, index on the switch. Need sto be an integer value event though switch is a float
        :param groups: list<str>, list of groups that should be have visibility attached to the given index
        """

        groups = python.force_list(groups)
        if not self._switch_joint or not maya.cmds.objExists(self._switch_joint):
            LOGGER.warning('Swtich joint {} does not exists!'.format(self._switch_joint))
            return

        weight_count = self.get_weight_count()
        if weight_count < (index + 1):
            LOGGER.warning(
                'Adding groups to index {} is undefined. {}.switch does not have that many inputs'.format(
                    index, self._switch_joint))

        self._groups[index] = groups

    def set_attribute_control(self, transform):
        """
        Set where the switch attribute should be stored
        :param transform: str, name of a transform
        """

        self._control_name = transform

    def set_attribute_name(self, attr_name):
        """
        Sets the name of the switch attribute on the attribute control
        :param attr_name: str, name for the switch attribute
        """

        self._attribute_name = attr_name


def get_all_rig_modules():
    """
    Returns all rig modules in the scene
    :return: list<str>
    """

    modules = maya.cmds.ls(type='network')
    found = list()
    for module in modules:
        attrs = maya.cmds.listAttr(module)
        if 'parent' in attrs:
            found.append(module)

    return found


def get_character_module(character_name, character_meta_class='RigCharacter'):
    """
    Return root module of the given character name
    :param character_name: str
    :return: str
    """

    modules = maya.cmds.ls(type='network')
    for module in modules:
        attrs = maya.cmds.listAttr(module)
        if 'meta_class' in attrs and 'meta_node_id' in attrs:
            meta_class = maya.cmds.getAttr('{}.meta_class'.format(module))
            module_name = maya.cmds.getAttr('{}.meta_node_id'.format(module))
            if meta_class == character_meta_class and module_name == character_name:
                return metanode.validate_obj_arg(module, character_meta_class)

    return None


def parent_shape_in_place(transform, shape_source, keep_source=True, replace_shapes=False, snap_first=False):
    """
    Parents a curve shape in place into a the transform of a given node
    :param transform: str, object to we want to parent shape into
    :param shape_source: str, curve shape to parent
    :param keep_source: bool, Whether to keep the curve shape parented also
    :param replace_shapes: bool, Whether to remove the objects original shapes or not
    :param snap_first: bool, Whether to snap shape to transform before parenting
    :return: bool, Whether the operation was successful or not
    """

    # TODO: Finish

    shape_source = python.force_list(shape_source)

    for shape in shape_source:
        maya.cmds.parent(shape, transform, add=True, shape=True)


def create_follow_fade(source_guide, drivers, skip_lower=0.0001):
    """
    Creates a multiply divide for each transform in drivers with a weight value based on the distance from source guide
    :param source_guide: str, name of a transform in maya to calculate distance from
    :param drivers: list(str), list of drivers to apply fade based in the distance from source guide
    :param skip_lower: float, distance below which multiplyDivide no fading stops
    :return: list(str), list of multiplyDivide nodes created
    """

    distance_list, distance_dict, original_distance_order = transform_utils.get_ordered_distance_and_transform(
        source_guide, drivers)
    multiplies = list()

    if not distance_list[-1] > 0:
        return multiplies

    for dst in original_distance_order:
        scaler = 1.0 - (dst / distance_list[-1])
        if scaler <= skip_lower:
            continue
        multi = attr_utils.MultiplyDivideNode(source_guide)
        multi.set_input2(scaler, scaler, scaler)
        multi.input1X_in('{}.translateX'.format(source_guide))
        multi.input1Y_in('{}.translateY'.format(source_guide))
        multi.input1Z_in('{}.translateZ'.format(source_guide))

        for driver in distance_dict[dst]:
            multi.outputX_out('{}.translateX'.format(driver))
            multi.outputY_out('{}.translateY'.format(driver))
            multi.outputZ_out('{}.translateZ'.format(driver))

        multi_dict = dict()
        multi_dict['node'] = multi
        multi_dict['source'] = source_guide
        multi_dict['target'] = driver           # ???
        multiplies.append(multi_dict)

    return multiplies
