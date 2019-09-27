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
import maya.OpenMayaRender as OpenMayaRender

new_api = True
try:
    import maya.api.OpenMaya as OpenMayaV2
    import maya.api.OpenMayaUI as OpenMayaUIV2
    import maya.api.OpenMayaAnim as OpenMayaAnimV2
    import maya.api.OpenMayaRender as OpenMayaRenderV2
except Exception:
    new_api = False

from tpPyUtils import importer

# =================================================================================

logger = None

# =================================================================================

api = {
    'OpenMaya': OpenMaya,
    'OpenMayaUI': OpenMayaUI,
    'OpenMayaAnim': OpenMayaAnim,
    'OpenMayaRender': OpenMayaRender
}

if new_api:
    api2 = {
        'OpenMaya': OpenMayaV2,
        'OpenMayaUI': OpenMayaUIV2,
        'OpenMayaAnim': OpenMayaAnimV2,
        'OpenMayaRender': OpenMayaRenderV2
    }
else:
    api2 = api

OpenMaya = OpenMaya
OpenMayaUI = OpenMayaUI
OpenMayaAnim = OpenMayaAnim
OpenMayaRender = OpenMayaRender

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


def init_dcc(do_reload=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    """

    tpmayalib_importer = importer.init_importer(importer_class=tpMayaLib, do_reload=False)
    tpmayalib_importer.update_paths()
    use_new_api()

    global logger
    logger = tpmayalib_importer.logger

    tpmayalib_importer.import_modules()
    tpmayalib_importer.import_packages(only_packages=True)
    if do_reload:
        tpmayalib_importer.reload_all()

    create_metadata_manager()


def init_ui(do_reload=False):
    tpmayalib_importer = importer.init_importer(importer_class=tpMayaLib, do_reload=False)
    tpmayalib_importer.update_paths()
    use_new_api()

    global logger
    logger = tpmayalib_importer.logger

    tpmayalib_importer.import_modules(skip_modules=['tpMayaLib.core', 'tpMayaLib.data', 'tpMayaLib.managers', 'tpMayaLib.meta'])
    tpmayalib_importer.import_packages(only_packages=True, skip_modules=['tpMayaLib.core', 'tpMayaLib.data', 'tpMayaLib.managers', 'tpMayaLib.meta'])
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
            OpenMayaRender = api2['OpenMayaRender']
        else:
            OpenMaya = api['OpenMaya']
            OpenMayaUI = api['OpenMayaUI']
            OpenMayaAnim = api['OpenMayaAnim']
            OpenMayaRender = api['OpenMayaRender']
    else:
        OpenMaya = api['OpenMaya']
        OpenMayaUI = api['OpenMayaUI']
        OpenMayaAnim = api['OpenMayaAnim']
        OpenMayaRender = api['OpenMayaRender']


def is_new_api():
    """
    Returns whether new Maya API is used or not
    :return: bool
    """

    return not OpenMaya == api['OpenMaya']
