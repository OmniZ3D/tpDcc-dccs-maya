#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with spaces
"""

from __future__ import print_function, division, absolute_import

from tpPyUtils import python

import tpMayaLib as maya
from tpMayaLib.core import name as name_utils, attribute as attr_utils, transform as xform_utils


def create_follow_group(source_transform, target_transform, prefix='follow', follow_scale=False, use_duplicate=False):
    """
    Creates a group above a target transform that is constrained to the source transform
    :param source_transform: str, name of the transform to follow
    :param target_transform: str, name of the transform make follow
    :param prefix: str, prefix to add to the follow group
    :param follow_scale: bool, Whether to ad a scale constraint or not
    :param use_duplicate: bool, Whether to use a duplicate or not
    :return: str, name of the follow group
    """

    parent = maya.cmds.listRelatives(target_transform, p=True, f=True)
    target_name = python.force_list(target_transform)
    name = '{}_{}'.format(prefix, target_name[0])

    if use_duplicate:
        follow_group = maya.cmds.duplicate(target_transform, n=name_utils.find_unique_name(name), po=True)[0]
        attr_utils.remove_user_defined_attributes(follow_group)
        parent = None
    else:
        follow_group = maya.cmds.group(empty=True, n=name_utils.find_unique_name(name))

    match = xform_utils.MatchTransform(source_transform, follow_group)
    match.translation_rotation()

    if parent:
        maya.cmds.parent(follow_group, parent)

    if follow_scale:
        attr_utils.connect_scale(source_transform, follow_group)

    maya.cmds.parentConstraint(source_transform, follow_group, mo=True)

    return follow_group


def create_local_follow_group(source_transform, target_transform, prefix='followLocal', orient_only=False, connect_scale=False):
    """
    Creates a group above a target transform that is local constrained to the source transform
    This help when setting up controls that need to be parented but only affect what they constrain when the actual
    control is moved
    :param source_transform: str, transform to follow
    :param target_transform: str, transform to make follow
    :param prefix: str, prefix to add to the follow group
    :param orient_only: bool, Whether the local constraint should just be an orient constraint
    :param connect_scale: bool, Whether local constraint should constraint also scale or not
    """

    parent = maya.cmds.listRelatives(target_transform, p=True)
    name = '{}_{}'.format(prefix, target_transform)
    follow_group = maya.cmds.group(empty=True, n=name_utils.find_unique_name(name))

    match = xform_utils.MatchTransform(source_transform, follow_group)
    match.translation_rotation()

    xform_grp = xform_utils.create_buffer_group(follow_group)

    if not orient_only:
        attr_utils.connect_translate(source_transform, follow_group)
    if orient_only or not orient_only:
        attr_utils.connect_rotate(source_transform, follow_group)
    if connect_scale:
        attr_utils.connect_scale(source_transform, follow_group)

    if parent:
        maya.cmds.parent(xform_grp, parent)

    return follow_group
