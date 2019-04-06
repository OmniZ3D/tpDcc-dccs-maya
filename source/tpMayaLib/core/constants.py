#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constants definitions for tpMayaLib
"""

from __future__ import print_function, division, absolute_import

from tpPyUtils import enum


class DebugLevel(enum.Enum):
    pass


class ScriptLanguage(enum.Enum):
    pass


class DebugLevels(enum.EnumGroup):
    Disabled = DebugLevel(0)
    Low = DebugLevel()
    Mid = DebugLevel()
    High = DebugLevel()


class ScriptLanguages(enum.EnumGroup):
    Python = ScriptLanguage()
    MEL = ScriptLanguage()
    CSharp = ScriptLanguage()
    CPlusPlus = ScriptLanguage()
    Manifest = ScriptLanguage()
