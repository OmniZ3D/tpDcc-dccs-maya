#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpMayaLib
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import inspect
import logging

from tpDcc.libs.python import importer

# =================================================================================

resource = None

# =================================================================================

try:
    # Do not remove Maya imports
    import maya.cmds as cmds
    import maya.mel as mel
    import maya.utils as utils
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaUI as OpenMayaUI
    import maya.OpenMayaAnim as OpenMayaAnim
    import maya.OpenMayaRender as OpenMayaRender
except ImportError:
    # NOTE: We use this empty try/catch to avoid errors during CI/CD
    pass


new_api = True
try:
    import maya.api.OpenMaya as OpenMayaV2
    import maya.api.OpenMayaUI as OpenMayaUIV2
    import maya.api.OpenMayaAnim as OpenMayaAnimV2
    import maya.api.OpenMayaRender as OpenMayaRenderV2
except Exception:
    new_api = False

try:
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
except Exception:
    # NOTE: We use this empty try/catch to avoid errors during CI/CD
    pass

# =================================================================================


class tpMayaLib(importer.Importer, object):
    def __init__(self, *args, **kwargs):
        super(tpMayaLib, self).__init__(module_name='tpMayaLib', *args, **kwargs)

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
                    import tpDcc.dccs.maya
                    mod_dir = tpDcc.dccs.maya.__path__[0]
                except Exception:
                    return None

        return mod_dir

    def externals_path(self):
        """
        Returns the paths where tpMayaLib externals packages are stored
        :return: str
        """

        return os.path.join(self.get_module_path(), 'externals')

    def update_paths(self):
        """
        Adds path to system paths at startup
        """

        import maya.cmds as cmds

        ext_path = self.externals_path()
        python_path = os.path.join(ext_path, 'python')
        maya_path = os.path.join(python_path, str(cmds.about(v=True)))

        paths_to_update = [self.externals_path(), maya_path]

        for p in paths_to_update:
            if os.path.isdir(p) and p not in sys.path:
                sys.path.append(p)


def create_logger_directory():
    """
    Creates artellapipe logger directory
    """

    logger_path = os.path.normpath(os.path.join(os.path.expanduser('~'), 'tpDcc', 'logs'))
    if not os.path.isdir(logger_path):
        os.makedirs(logger_path)


def get_logging_config():
    """
    Returns logging configuration file path
    :return: str
    """

    create_logger_directory()

    return os.path.normpath(os.path.join(os.path.dirname(__file__), '__logging__.ini'))


def init_dcc(do_reload=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    """

    import tpDcc.dccs.maya as maya

    from tpDcc.libs.qt.core import resource as resource_utils

    class tpMayaLibResource(resource_utils.Resource, object):
        RESOURCES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')

    logging.config.fileConfig(get_logging_config(), disable_existing_loggers=False)

    tpmayalib_importer = importer.init_importer(importer_class=tpMayaLib, do_reload=False)
    tpmayalib_importer.update_paths()
    maya.use_new_api()

    global logger
    global resource
    logger = tpmayalib_importer.logger
    resource = tpMayaLibResource

    tpmayalib_importer.import_modules()
    tpmayalib_importer.import_packages(only_packages=True)
    if do_reload:
        tpmayalib_importer.reload_all()

    maya.create_metadata_manager()


def init_ui(do_reload=False):
    import tpMayaLib as maya

    tpmayalib_importer = importer.init_importer(importer_class=tpMayaLib, do_reload=False)
    tpmayalib_importer.update_paths()
    maya.use_new_api()

    global logger
    logger = tpmayalib_importer.logger

    # tpmayalib_importer.import_modules(skip_modules=['tpMayaLib.core', 'tpMayaLib.data',
    # 'tpMayaLib.managers', 'tpMayaLib.meta'])
    # tpmayalib_importer.import_packages(only_packages=True, skip_modules=['tpMayaLib.core',
    # 'tpMayaLib.data', 'tpMayaLib.managers', 'tpMayaLib.meta'])
    tpmayalib_importer.import_modules()
    tpmayalib_importer.import_packages(only_packages=True)
    if do_reload:
        tpmayalib_importer.reload_all()

    maya.create_metadata_manager()
