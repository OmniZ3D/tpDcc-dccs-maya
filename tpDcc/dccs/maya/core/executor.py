#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base implementation for Maya commands executor
"""


from __future__ import print_function, division, absolute_import

from tpDcc import register
from tpDcc.core import executor


class MayaExecutor(executor.DccExecutor, object):
    def __init__(self):
        super(MayaExecutor, self).__init__()


register.register_class('Executor', MayaExecutor)
