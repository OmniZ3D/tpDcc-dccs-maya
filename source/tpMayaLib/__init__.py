#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpMayaLib
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import inspect

# Do not remove Maya imports
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMayaAnim as OpenMayaAnim

new_api = True
try:
    import maya.api.OpenMaya as OpenMayaV2
    import maya.api.OpenMayaUI as OpenMayaUIV2
    import maya.api.OpenMayaAnim as OpenMayaAnimV2
except Exception:
    new_api = False

from tpPyUtils import importer

# =================================================================================

logger = None

# =================================================================================

api = {
    'OpenMaya': OpenMaya,
    'OpenMayaUI': OpenMayaUI,
    'OpenMayaAnim': OpenMayaAnim
}

if new_api:
    api2 = {
        'OpenMaya': OpenMayaV2,
        'OpenMayaUI': OpenMayaUIV2,
        'OpenMayaAnim': OpenMayaAnimV2
    }
else:
    api2 = api

OpenMaya = OpenMaya
OpenMayaUI = OpenMayaUI
OpenMayaAnim = OpenMayaAnim

# =================================================================================


class tpMayaLib(importer.Importer, object):
    def __init__(self):
        super(tpMayaLib, self).__init__(module_name='tpMayaLib')

    def get_module_path(self):
        """
        Returns path where tpMayaLib module is stored
        :return: str
        """

        try:
            mod_dir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)
        except Exception:
            try:
                mod_dir = os.path.dirname(__file__)
            except Exception:
                try:
                    import tpDccLib
                    mod_dir = tpDccLib.__path__[0]
                except Exception:
                    return None

        return mod_dir

    def externals_path(self):
        """
        Returns the paths where tpPyUtils externals packages are stored
        :return: str
        """

        return os.path.join(self.get_module_path(), 'externals')

    def update_paths(self):
        """
        Adds path to system paths at startup
        """

        ext_path = self.externals_path()
        python_path = os.path.join(ext_path, 'python')
        maya_path = os.path.join(python_path, str(cmds.about(v=True)))

        paths_to_update = [self.externals_path(), maya_path]

        for p in paths_to_update:
            if os.path.isdir(p) and p not in sys.path:
                sys.path.append(p)


def init(do_reload=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    """

    tpmayalib_importer = importer.init_importer(importer_class=tpMayaLib, do_reload=False)
    tpmayalib_importer.update_paths()
    use_new_api()

    global logger
    logger = tpmayalib_importer.logger

    tpmayalib_importer.import_modules(skip_modules=['tpMayaLib.core'])
    tpmayalib_importer.import_packages(only_packages=True, order=['tpMayaLib.core'])
    if do_reload:
        tpmayalib_importer.reload_all()

    create_metadata_manager()


def create_metadata_manager():
    """
    Creates MetaDataManager for Maya
    """

    from tpMayaLib.managers import metadatamanager
    metadatamanager.MetaDataManager.register_meta_classes()
    metadatamanager.MetaDataManager.register_meta_types()
    metadatamanager.MetaDataManager.register_meta_nodes()


def use_new_api(flag=False):
    """
    Enables new Maya API usage
    """

    global OpenMaya
    global OpenMayaUI
    global OpenMayaAnim

    if new_api:
        if flag:
            OpenMaya = api2['OpenMaya']
            OpenMayaUI = api2['OpenMayaUI']
            OpenMayaAnim = api2['OpenMayaAnim']
        else:
            OpenMaya = api['OpenMaya']
            OpenMayaUI = api['OpenMayaUI']
            OpenMayaAnim = api['OpenMayaAnim']
    else:
        OpenMaya = api['OpenMaya']
        OpenMayaUI = api['OpenMayaUI']
        OpenMayaAnim = api['OpenMayaAnim']


def is_new_api():
    """
    Returns whether new Maya API is used or not
    :return: bool
    """

    return not OpenMaya == api['OpenMaya']
