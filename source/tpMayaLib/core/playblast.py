#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with playblasts
"""

import os
import glob

import tpMayaLib as maya


def get_playblast_formats():
    """
    Returns all formats available for Maya playblast
    :return: list<str>
    """

    maya.cmds.currentTime(maya.cmds.currentTime(query=True))
    return maya.cmds.playblast(query=True, format=True)


def get_playblast_compressions(format='avi'):
    """
    Returns playblast compression for the given format
    :param format: str, format to check compressions for
    :return: list<str>
    """

    maya.cmds.currentTime(maya.cmds.currentTime(query=True))
    return maya.mel.eval('playblast -format "{0}" -query -compression'.format(format))


def fix_playblast_output_path(file_path):
    """
    Workaround a bug in maya.maya.cmds.playblast to return a correct playblast
    When the `viewer` argument is set to False and maya.maya.cmds.playblast does not
    automatically open the playblasted file the returned filepath does not have
    the file's extension added correctly.
    To workaround this we just glob.glob() for any file extensions and assume
    the latest modified file is the correct file and return it.
    :param file_path: str
    :return: str
    """

    if file_path is None:
        maya.logger.warning('Playblast did not result in output path. Maybe it was interrupted!')
        return

    if not os.path.exists(file_path):
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        parts = filename.split('.')
        if len(parts) == 3:
            query = os.path.join(directory, '{}.*.{}'.format(parts[0], parts[-1]))
            files = glob.glob(query)
        else:
            files = glob.glob('{}.*'.format(file_path))

        if not files:
            raise RuntimeError('Could not find playblast from "{}"'.format(file_path))

        file_path = max(files, key=os.path.getmtime)

    return file_path