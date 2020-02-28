#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with custom Maya Python contexts
"""

from __future__ import print_function, division, absolute_import

import contextlib

import tpDcc.dccs.maya as maya


@contextlib.contextmanager
def maya_no_undo():
    """
    Disable undo functionality during the context
    """

    try:
        maya.cmds.undoInfo(stateWithoutFlush=False)
        yield
    finally:
        maya.cmds.undoInfo(stateWithoutFlush=True)
