#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility module that contains classes and functions to work with Maya callbacks
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya


class MCallbackIdWrapper(object):
    """
    Wrapper class to handle cleaning up of MCallbackIds from registered MMessages
    """

    def __init__(self, callback_id):
        super(MCallbackIdWrapper, self).__init__()
        self.callback_id = callback_id
        maya.logger.debug('Adding Callback: %s' % self.callback_id)

    def __del__(self):
        try:
            maya.OpenMaya.MDGMessage.removeCallback(self.callback_id)
        except Exception:
            pass
        try:
            maya.OpenMaya.MMessage.removeCallback(self.callback_id)
        except Exception:
            pass
        maya.logger.debug('Removing Callback: %s' % self.callback_id)

    def __repr__(self):
        return 'MCallbackIdWrapper(%r)' % self.callback_id


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
