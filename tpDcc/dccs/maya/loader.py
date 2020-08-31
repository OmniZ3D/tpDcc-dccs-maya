#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpDcc.dccs.maya
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import inspect
import logging

import tpDcc.register as core_register
from tpDcc.dccs.maya import register

# =================================================================================

PACKAGE = 'tpDcc.dccs.maya'

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
except Exception:
    # NOTE: We use this empty try/catch to avoid errors during CI/CD
    pass


def use_new_api(flag=False):
    """
    Enables new Maya API usage
    """

    from tpDcc.dccs.maya import register

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

    register.register_class('OpenMaya', OpenMaya)
    register.register_class('OpenMayaUI', OpenMayaUI)
    register.register_class('OpenMayaAnim', OpenMayaAnim)
    register.register_class('OpenMayaRender', OpenMayaRender)


def is_new_api():
    """
    Returns whether new Maya API is used or not
    :return: bool
    """

    return not OpenMaya == api['OpenMaya']


def register_maya_classes():
    register.register_class('is_new_api', is_new_api)
    register.register_class('use_news_api', use_new_api)
    register.register_class('cmds', cmds)
    register.register_class('mel', mel)
    register.register_class('utils', utils)
    register.register_class('OpenMaya', OpenMaya)
    register.register_class('OpenMayaUI', OpenMayaUI)
    register.register_class('OpenMayaAnim', OpenMayaAnim)
    register.register_class('OpenMayaRender', OpenMayaRender)


register_maya_classes()


# =================================================================================

from tpDcc.dccs.maya.core import dcc, callback, menu, shelf
from tpDcc.dccs.maya.ui import completer, dialog, window

# =================================================================================


def get_module_path():
    """
    Returns path where tpDcc.dccs.maya module is stored
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


def externals_path():
    """
    Returns the paths where tpDcc.dccs.maya externals packages are stored
    :return: str
    """

    return os.path.join(get_module_path(), 'externals')


def update_paths():
    """
    Adds path to system paths at startup
    """

    import maya.cmds as cmds

    ext_path = externals_path()
    python_path = os.path.join(ext_path, 'python')
    maya_path = os.path.join(python_path, str(cmds.about(v=True)))

    paths_to_update = [externals_path(), maya_path]

    for p in paths_to_update:
        if os.path.isdir(p) and p not in sys.path:
            sys.path.append(p)


def create_logger(dev=False):
    """
    Returns logger of current module
    """

    logger_directory = os.path.normpath(os.path.join(os.path.expanduser('~'), 'tpDcc', 'logs'))
    if not os.path.isdir(logger_directory):
        os.makedirs(logger_directory)

    logging_config = os.path.normpath(os.path.join(os.path.dirname(__file__), '__logging__.ini'))

    logging.config.fileConfig(logging_config, disable_existing_loggers=False)
    logger = logging.getLogger(PACKAGE.replace('.', '-'))
    if dev:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    return logger


def init_dcc(dev=False):
    """
    Initializes module
    :param dev: bool, Whether to launch code in dev mode or not
    """

    if dev:
        register.cleanup()
        register_classes()
        register_maya_classes()

    update_paths()
    register_resources()

    logger = create_logger(dev=dev)
    register.register_class('logger', logger)

    use_new_api()

    create_metadata_manager()


# def init_ui():
#     from tpDcc.libs.python import importer
#
#     update_paths()
#     skip_modules = ['{}.{}'.format(PACKAGE, name) for name in ['loader', 'core', 'data', 'managers', 'meta']]
#     importer.init_importer(package=PACKAGE, skip_modules=skip_modules)
#     use_new_api()
#
#     create_metadata_manager()


def create_metadata_manager():
    """
    Creates MetaDataManager for Maya
    """

    from tpDcc.dccs.maya.managers import metadatamanager

    metadatamanager.MetaDataManager.register_meta_classes()
    metadatamanager.MetaDataManager.register_meta_types()
    metadatamanager.MetaDataManager.register_meta_nodes()


def register_resources():
    """
    Registers tpDcc.libs.qt resources path
    """

    import tpDcc

    resources_manager = tpDcc.ResourcesMgr()
    resources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    resources_manager.register_resource(resources_path, key=tpDcc.Dccs.Maya)


def register_classes():
    core_register.register_class('Dcc', dcc.MayaDcc)
    core_register.register_class('DccProgressBar', dcc.MayaProgessBar)
    core_register.register_class('Callbacks', callback.MayaCallback)
    core_register.register_class('Menu', menu.MayaMenu)
    core_register.register_class('Shelf', shelf.MayaShelf)
    core_register.register_class('Completer', completer.MayaCompleter)
    core_register.register_class('Dialog', dialog.MayaDialog)
    core_register.register_class('OpenFileDialog', dialog.MayaOpenFileDialog)
    core_register.register_class('SaveFileDialog', dialog.MayaSaveFileDialog)
    core_register.register_class('SelectFolderDialog', dialog.MayaSelectFolderDialog)
    core_register.register_class('NativeDialog', dialog.MayaNativeDialog)
    core_register.register_class('Window', window.MayaWindow)
    core_register.register_class('DockWindow', window.MayaWindow)
    core_register.register_class('SubWindow', window.MayaWindow)


register_classes()
