#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes to work with HumanIK
"""

from __future__ import print_function, division, absolute_import

import tpDcc.dccs.maya as maya


def initialize():
    """
    Makes sure that HumanIK tool is laoded and visible
    """

    if maya.mel.eval('exists hikGetCurrentCharacter'):
        character = get_current_character()
    else:
        character = ''

    maya.mel.eval('HIKCharacterControlsTool();')

    maya.set_current_character(character)


def update_hik_tool():
    """
    Refreshes HumanIK tool UI so that fits the current HumanIK character
    """

    maya.mel.eval("""
    if (hikIsCharacterizationToolUICmdPluginLoaded())
    {
        hikUpdateCharacterList();
        hikUpdateSourceList();
        hikUpdateContextualUI();
    }
    """)


def none_string():
    """
    Returns the string that should be display when no HumanIK character is selected
    :return: str
    """
    try:
        return maya.mel.eval('hikNoneString()') or ''
    except Exception:
        return ''


def create_character(character_name):
    """
    Creates a HumanIK character and tries to use the given name to name the new character
    :param character_name: str, name of the new HumanIK character
    """

    return maya.mel.eval('hikCreateCharacter("{0}")'.format(character_name))


def rename_character(character):
    """
    Opens a dialog that allows the user to rename the given HumanIK character
    """

    maya.mel.eval('hikSetCurrentCharacter("{0}");  hikRenameDefinition();'.format(character))


def get_current_character():
    """
    Returns the name of the current HumanIK character
    :return: str
    """

    return maya.mel.eval('hikGetCurrentCharacter()') or 'None'


def set_current_character(character):
    """
    Sets the given HumanIK character as the global current HumanIK
    """

    return maya.mel.eval('hikSetCurrentCharacter("{0}");'.format(character))


def get_scene_characters():
    """
    Returns a list of names for all HumanIK characters in the current scene
    """

    return maya.mel.eval('hikGetSceneCharacters()') or []


def delete_whole_character(character):
    """
    Deletes the given HumanIK character
    It deletes its control rig (if any), its skeleton (if any) and its character definition
    """

    maya.mel.eval("""
    hikSetCurrentCharacter("{0}"); hikDeleteControlRig(); hikDeleteSkeleton_noPrompt();
    """.format(character))


def get_skeleton_generator_node(character):
    """
    Returns the name of the skeleton generator node associated with teh given HumanIK
    character if it exists, or an empty string otherwise
    :param character: str, HumanIK character name
    """

    return maya.mel.eval('hikGetSkeletonGeneratorNode("{0}")'.format(character)) or ''
