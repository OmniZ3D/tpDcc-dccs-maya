#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains exceptions related with Maya API
"""

from __future__ import print_function, division, absolute_import


class MissingObjectByName(Exception):
    pass


class AttributeAlreadyExists(Exception):
    pass
