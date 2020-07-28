#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility module that contains classes and functions to work with Maya callbacks
"""

from __future__ import print_function, division, absolute_import

from tpDcc import register
from tpDcc.abstract import callback

import tpDcc.dccs.maya as maya


class MayaCallback(object):

    class TickCallback(callback.ICallback, object):
        """
        Callback that handles TickCallback notifications for 3ds Max
        """

        Interval = 0.001            # Tick interval (seconds)

        @classmethod
        def filter(cls, *args):
            """
            Function that processes given arguments during an execution of addTimerCallback
            :param args: Variable list of arguments pass from the callback function to be evaluated
            :return: tuple<...> that is (True, Valid Data, ...) if notification should be passed to the listener
                or (False, None) otherwise
            """

            elapsed_time = args[0]
            last_time = args[1]
            client_data = args[2]

            return True, elapsed_time, last_time, client_data

        @classmethod
        def register(cls, fn, owner=None):
            """
            Function that abstracts addTimerCallback
            :param fn: Python function to register
            :param owner:
            :return: Token of inderminant type to later unregister the function
            """

            return maya.OpenMaya.MTimerMessage.addTimerCallback(cls.Interval, fn, "")

        @classmethod
        def unregister(cls, token):
            """
            Function that abstracts removeCallback
            :param token: token provided by the register function
            """

            if token:
                maya.OpenMaya.MTimerMessage.removeCallback(token)

    class NodeAddedCallback(callback.ICallback, object):
        """
        Callback that handles NodeAdded notifications for Maya
        """

        @classmethod
        def filter(cls, *args):
            mobj = args[0]
            try:
                node = maya.OpenMaya.MFnDagNode(mobj)
                path = node.fullPathName()
                name = node.name()
                valid = True
            except Exception:
                path = None
                name = None
                valid = False

            return valid, path, name

        @classmethod
        def register(cls, fn, owner=None):
            return maya.OpenMaya.MDGMessage.addNodeCallback(fn, 'transform', 'dagNode')

        @classmethod
        def unregister(cls, token):
            if token:
                maya.OpenMaya.MDGMessage.removeCallback(token)

    class NodeDeletedCallback(callback.ICallback, object):
        """
        Callback that handles NodeRemoved notifications for Maya
        """

        @classmethod
        def filter(cls, *args):
            mobj = args[0]
            try:
                node = maya.OpenMaya.MFnDagNode(mobj)
                path = node.fullPathName()
                name = node.name()
                valid = True
            except Exception:
                path = None
                name = None
                valid = False

            return valid, path, name

        @classmethod
        def register(cls, fn, owner=None):
            return maya.OpenMaya.MDGMessage.addNodeRemovedCallback(fn, 'transform', 'dagNode')

        @classmethod
        def unregister(cls, token):
            if token:
                maya.OpenMaya.MDGMessage.removeCallback(token)

    class NodeSelectCallback(callback.ICallback, object):
        """
        Callback that handles NodeSelect notifications for Maya
        """

        @classmethod
        def filter(cls, *args):
            return True, None

        @classmethod
        def register(cls, fn, owner=None):
            MayaCallback.NodeSelectCallback._callback = staticmethod(fn)
            return maya.cmds.scriptJob(e=[
                'SelectionChanged', 'import tpDcc; tpDcc.Callbacks.NodeSelectCallback._callback()'])

        @classmethod
        def unregister(cls, token):
            if token:
                MayaCallback.NodeSelectCallback._callback = None
                maya.cmds.scriptJob(kill=token, force=True)

    class SceneCreatedCallback(callback.ICallback, object):
        """
        Callback that handles SceneCreation notifications for Maya
        """

        _codes = [maya.OpenMaya.MSceneMessage.kBeforeNew, maya.OpenMaya.MSceneMessage.kBeforeOpen]

        @classmethod
        def filter(cls, *args):
            return True, args

        @classmethod
        def register(cls, fn, owner=None):
            return [maya.OpenMaya.MSceneMessage.addCallback(c, fn) for c in cls._codes]

        @classmethod
        def unregister(cls, token):
            for t in token:
                maya.OpenMaya.MSceneMessage.removeCallback(t)

    class ShutdownCallback(callback.ICallback, object):
        """
        Callback that handles Shutdown notifications for Maya
        """

        @classmethod
        def filter(cls, *args):
            return True, args

        @classmethod
        def register(cls, fn, owner=None):
            return maya.OpenMaya.MSceneMessage.addCallback(maya.OpenMaya.MSceneMessage.kMayaExiting, fn)

        @classmethod
        def unregister(cls, token):
            if token:
                maya.OpenMaya.MSceneMessage.removeCallback(token)
