#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for Maya windows
"""

from __future__ import print_function, division, absolute_import

import os

from tpDcc.libs.python import path as path_utils
from tpDcc.libs.qt.core import dialog as core_dialog
from tpDcc.dccs.maya.core import directory


class MayaDialog(core_dialog.Dialog, object):
    def __init__(self, name='MayaDialog', parent=None, **kwargs):
        super(MayaDialog, self).__init__(name=name, parent=parent, **kwargs)


class MayaOpenFileDialog(core_dialog.OpenFileDialog, object):
    def __init__(self, name='MayaOpenFileDialog', parent=None, **kwargs):
        super(MayaOpenFileDialog, self).__init__(name=name, parent=parent, **kwargs)


class MayaSaveFileDialog(core_dialog.SaveFileDialog, object):
    def __init__(self, name='MaxSaveFileDialog', parent=None, **kwargs):
        super(MayaSaveFileDialog, self).__init__(name=name, parent=parent, **kwargs)


class MayaSelectFolderDialog(core_dialog.SelectFolderDialog, object):
    def __init__(self, name='MaxSelectFolderDialog', parent=None, **kwargs):
        super(MayaSelectFolderDialog, self).__init__(name=name, parent=parent, **kwargs)


class MayaNativeDialog(core_dialog.NativeDialog, object):

    @staticmethod
    def open_file(title='Open File', start_directory=None, filters=None):
        """
        Function that shows open file Max native dialog
        :param title: str
        :param start_directory: str
        :param filters: str
        :return: str
        """

        start_directory = start_directory if start_directory else os.path.expanduser('~')
        clean_path = path_utils.clean_path(start_directory)
        file_path = directory.select_file_dialog(title=title, start_directory=clean_path, pattern=filters)

        return file_path

    @staticmethod
    def save_file(title='Save File', start_directory=None, filters=None):
        """
        Function that shows save file Max native dialog
        :param title: str
        :param start_directory: str
        :param filters: str
        :return: str
        """

        start_directory = start_directory if start_directory else os.path.expanduser('~')
        clean_path = path_utils.clean_path(start_directory)
        file_path = directory.save_file_dialog(title=title, start_directory=clean_path, pattern=filters)

        return file_path

    @staticmethod
    def select_folder(title='Select Folder', start_directory=None):
        """
        Function that shows select folder Maya dialog
        :param title: str
        :param start_directory: str
        :return: str
        """

        start_directory = start_directory if start_directory else os.path.expanduser('~')
        clean_path = path_utils.clean_path(start_directory)
        folder_path = directory.select_folder_dialog(title=title, start_directory=clean_path)

        return folder_path
