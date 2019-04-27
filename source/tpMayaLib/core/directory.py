#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with directories and files in Maya
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya


def get_file(caption='Select File', file_mode=1, filters='*', start_directory=''):
    result = maya.cmds.fileDialog2(caption=caption, fileMode=file_mode, fileFilter=filters, startingDirectory=start_directory)
    if result:
        result = result[0]
        return result

    return None
