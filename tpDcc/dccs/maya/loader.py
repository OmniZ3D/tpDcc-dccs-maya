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

import maya.cmds

from tpDcc.core import dcc
from tpDcc.managers import resources
from tpDcc.libs.python import path as path_utils

# =================================================================================

PACKAGE = 'tpDcc.dccs.maya'

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

    ext_path = externals_path()
    python_path = os.path.join(ext_path, 'python')
    maya_path = os.path.join(python_path, str(maya.cmds.about(v=True)))

    paths_to_update = [externals_path(), maya_path]

    for p in paths_to_update:
        if os.path.isdir(p) and p not in sys.path:
            sys.path.append(p)

    # Update custom tpDcc.dccs.maya plugins path
    tpdcc_maya_plugins_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'plugins')
    if not os.path.isdir(tpdcc_maya_plugins_path):
        return False
    tpdcc_maya_plugins_path = path_utils.clean_path(tpdcc_maya_plugins_path)

    maya_plugin_path = os.getenv('MAYA_PLUG_IN_PATH', None)
    if not maya_plugin_path:
        os.environ['MAYA_PLUG_IN_PATH'] = tpdcc_maya_plugins_path
    else:
        current_plugin_paths = os.environ['MAYA_PLUG_IN_PATH'].split(os.pathsep)
        for current_plugin_path in current_plugin_paths:
            if path_utils.clean_path(current_plugin_path) == tpdcc_maya_plugins_path:
                return True
        os.environ['MAYA_PLUG_IN_PATH'] = '{}{}{}'.format(
            os.environ['MAYA_PLUG_IN_PATH'], os.pathsep, tpdcc_maya_plugins_path)


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
    dev = os.getenv('TPDCC_DEV', dev)
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

    update_paths()
    register_resources()

    create_logger(dev=dev)

    register_commands()
    load_plugins()
    create_metadata_manager()


def get_tpdcc_maya_plugins_path():
    """
    Returns path where tpdcc Maya plugins are located
    :return: str
    """

    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'plugins')


def get_tpdcc_maya_api_commands_path():
    """
    Returns path where tpdcc Maya plugins are located
    :return: str
    """

    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'api', 'commands')


def load_plugins(do_reload=True):
    from tpDcc.dccs.maya.core import helpers

    plugins_path = get_tpdcc_maya_plugins_path()
    if not os.path.isdir(plugins_path):
        return False

    for plugin_file in os.listdir(plugins_path):
        if not plugin_file:
            continue
        plugin_ext = os.path.splitext(plugin_file)[-1]
        if not plugin_ext == '.py':
            continue
        plugin_path = path_utils.clean_path(os.path.join(plugins_path, plugin_file))
        if do_reload:
            if helpers.is_plugin_loaded(plugin_path):
                helpers.unload_plugin(plugin_path)
        helpers.load_plugin(plugin_path)


def register_commands():
    from tpDcc.core import command

    commands_path = get_tpdcc_maya_api_commands_path()
    if not os.path.isdir(commands_path):
        return False

    runner = command.CommandRunner()
    if not runner:
        return False

    runner.manager().register_path(commands_path, package_name='tpDcc')

    return True


def create_metadata_manager():
    """
    Creates MetaDataManager for Maya
    """

    from tpDcc.dccs.maya.managers import metadatamanager

    metadatamanager.register_meta_classes()
    metadatamanager.register_meta_types()
    metadatamanager.register_meta_nodes()


def register_resources():
    """
    Registers tpDcc.dccs.maya resources path
    """

    resources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    resources.register_resource(resources_path, key=dcc.Dccs.Maya)
