#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility module that contains classes and functions to work with Maya callbacks
"""

from __future__ import print_function, division, absolute_import

import tpDccLib
from tpDccLib.abstract import callback

import tpMayaLib as maya


class MayaCallback(callback.AbstractCallback, object):
    """
    Wrapper class to handle cleaning up of MCallbackIds from registered MMessages
    """

    def __init__(self, fn=None, parent=None):
        super(MayaCallback, self).__init__(fn=fn, parent=parent)

    @staticmethod
    def remove_callback(callback_id):
        try:
            maya.OpenMaya.MEventMessage.removeCallback(callback_id)
            return
        except Exception:
            pass
        try:
            maya.OpenMaya.MDGMessage.removeCallback(callback_id)
            return
        except Exception:
            pass


class MayaSelectionChangedCallback(MayaCallback, object):
    def __init__(self, fn=None, parent=None):
        super(MayaSelectionChangedCallback, self).__init__(fn=fn, parent=parent)

    def create_callback(self, fn, parent):
        return maya.OpenMaya.MEventMessage.addEventCallback('SelectionChanged', fn, parent)


tpDccLib.Callback = MayaCallback
tpDccLib.Callbacks.SelectionChanged = MayaSelectionChangedCallback
