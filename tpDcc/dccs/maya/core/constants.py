#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains constants definitions for tpDcc.dccs.maya
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.python import python

if python.is_python2():
    from tpDcc.libs.python.enum import Enum
else:
    from enum import Enum


class DebugLevels(Enum):
    Disabled = 0
    Low = 1
    Mid = 2
    High = 3


class ScriptLanguages(Enum):
    Python = 0
    MEL = 1
    CSharp = 2
    CPlusPlus = 3
    Manifest = 4
