#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with meta system for rigging
"""

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode


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
