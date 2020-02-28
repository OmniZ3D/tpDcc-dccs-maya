#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains skin weights data classes for Maya
"""

from __future__ import print_function, division, absolute_import

from tpDcc.dccs.maya.data import base


class SkinWeightsData(base.MayaCustomData, object):
    def __init__(self, name=None, path=None):
        super(SkinWeightsData, self).__init__(name=name, path=path)

    def get_data_title(self):
        return 'maya_skin_weights'
