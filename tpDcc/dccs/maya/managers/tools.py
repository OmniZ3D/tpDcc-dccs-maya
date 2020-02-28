#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Maya Tools manager
"""

from __future__ import print_function, division, absolute_import

from tpDcc import register
from tpDcc.managers import tools
from tpDcc.libs.python import decorators


class MayaToolsManager(tools.ToolsManager, object):
    def __init__(self):

        self._shelf_layout = dict()

        super(MayaToolsManager, self).__init__()


@decorators.Singleton
class MayaToolsManagerSingleton(MayaToolsManager, object):
    """
    Singleton class that holds preferences manager instance
    """

    def __init__(self):
        MayaToolsManager.__init__(self)


register.register_class('ToolsMgr', MayaToolsManagerSingleton)
