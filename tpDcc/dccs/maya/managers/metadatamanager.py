#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manager to control current scene meta data values and nodes
"""

from __future__ import print_function, division, absolute_import

import inspect

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc.dccs.maya as maya
from tpDcc.libs.python import python, decorators, name as name_utils
from tpDcc.libs.qt.core import window
from tpDcc.libs.qt.widgets import models, views

# ===================================================================================================================
METANODES_CACHE = dict()
METANODE_CLASSES_REGISTER = dict()
METANODE_TYPES_REGISTER = list()
METANODE_CLASSES_INHERITANCE_MAP = list()
# ===================================================================================================================


class MetaDataManager(window.MainWindow, object):
    def __init__(self):
        super(MetaDataManager, self).__init__(
            name='MetaDataWindow',
            title='RigLib - MetaData Manager',
            size=(350, 700),
            fixed_size=False,
            auto_run=True,
            frame_less=True,
            use_style=True
        )

    def ui(self):
        super(MetaDataManager, self).ui()

        base_layout = QHBoxLayout()
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.setSpacing(0)

        reg_mclasses_layout = QVBoxLayout()
        reg_mclasses_layout.setContentsMargins(2, 2, 2, 2)
        reg_mclasses_layout.setSpacing(2)
        reg_mclasses_lbl = QLabel('Registered MetaNodes')
        reg_mclasses_lbl.setAlignment(Qt.AlignCenter)
        reg_mclasses_list = views.ListView()
        self._reg_mclasses_model = models.ListModel()
        reg_mclasses_list.setModel(self._reg_mclasses_model)
        reg_mclasses_layout.addWidget(reg_mclasses_lbl)
        reg_mclasses_layout.addWidget(reg_mclasses_list)
        base_layout.addLayout(reg_mclasses_layout)

        curr_mnodes_layout = QVBoxLayout()
        curr_mnodes_layout.setContentsMargins(2, 2, 2, 2)
        curr_mnodes_layout.setSpacing(2)
        curr_mnodes_lbl = QLabel('Current MetaNodes')
        curr_mnodes_lbl.setAlignment(Qt.AlignCenter)
        curr_mnodes_table = QTableView()
        curr_mnodes_table.verticalHeader().hide()
        nodes_headers = ['ID', 'MetaNode']
        self._curr_mnodes_model = models.TableModel(horizontal_headers=nodes_headers)
        curr_mnodes_table.setModel(self._curr_mnodes_model)
        curr_mnodes_layout.addWidget(curr_mnodes_lbl)
        curr_mnodes_layout.addWidget(curr_mnodes_table)
        base_layout.addLayout(curr_mnodes_layout)

        self.main_layout.addLayout(base_layout)

        self._update_ui()

    @staticmethod
    def generate_uuid(meta_node=None):
        """
        Generates a unique id taking in account the current existing UUID registered
        :return: str
        """

        maya.logger.debug('Generating a new UUID')

        valid_uuid = False
        generated_uuid = None

        while not valid_uuid:
            uuid = python.generate_uuid()
            if uuid not in METANODES_CACHE.keys():
                generated_uuid = uuid
                valid_uuid = True
            else:
                if not meta_node == METANODES_CACHE[uuid]:
                    maya.logger.debug(
                        'METANODES_CACHE: {0} : UUID is registered to a different node : modifying UUID: {1}'.format(
                            uuid, meta_node.meta_node))
                else:
                    maya.logger.debug(
                        'METANODES_CACHE : UUID {0} is already registered in METANODES_CACHE'.format(uuid))

        return generated_uuid

    @staticmethod
    def register_metanode_to_cache(meta_node):
        """
        Register a new meta class and store it into the global meta class cache
        :param meta_node: dcclib.Meta
        """

        from tpDcc.dccs.maya.meta import metanode

        global METANODES_CACHE

        uuid = metanode.MetaNode.get_metanode_uuid(meta_node=meta_node)

        if METANODES_CACHE or uuid not in METANODES_CACHE.keys():
            maya.logger.debug('CACHE: Adding to MetaNode UUID Cache: {0} > {1}'.format(meta_node.meta_node, uuid))
            METANODES_CACHE[uuid] = meta_node

        meta_node._lastUUID = uuid

    @staticmethod
    def clean_metanodes_cache():
        """
        Loop through the current METANODE_CACHE and confirm that they're all still valid by testing all
        MObjectHandles
        """

        from tpDcc.dccs.maya.meta import metanode

        for k, v in METANODES_CACHE.items():
            try:
                if not metanode.MetaNode.check_metanode_validity(v):
                    METANODES_CACHE.pop(k)
                    maya.logger.debug(
                        'CACHE : {} being removed from the META NODE CACHE due to invalid MObject'.format(k))
            except Exception as e:
                maya.logger.debug('CACHE : Clean cache failed!')
                maya.logger.debug(str(e))

    @staticmethod
    def get_metanode_from_cache(meta_node):
        """
        Pull the given node from META_NODECACHE if its already be instantiated
        :param meta_node: str, name of the node from DAG
        """

        from tpDcc.dccs.maya.meta import metanode

        return metanode.MetaNode.get_meta_from_cache(meta_node=meta_node)

    @staticmethod
    def register_meta_classes():

        from tpDcc.dccs.maya.meta import metanode

        global METANODE_CLASSES_REGISTER
        METANODE_CLASSES_REGISTER = dict()
        global METANODE_CLASSES_INHERITANCE_MAP
        METANODE_CLASSES_INHERITANCE_MAP = dict()

        meta_data_name = metanode.MetaNode.__name__
        METANODE_CLASSES_REGISTER[meta_data_name] = metanode.MetaNode
        METANODE_CLASSES_INHERITANCE_MAP[meta_data_name] = dict()
        METANODE_CLASSES_INHERITANCE_MAP[meta_data_name]['full'] = [metanode.MetaNode]
        METANODE_CLASSES_INHERITANCE_MAP[meta_data_name]['short'] = meta_data_name

        for meta_class in python.itersubclasses(metanode.MetaNode):
            maya.logger.debug('Registering: {}'.format(meta_class))
            METANODE_CLASSES_REGISTER[meta_class.__name__] = meta_class
            METANODE_CLASSES_INHERITANCE_MAP[meta_class.__name__] = dict()
            METANODE_CLASSES_INHERITANCE_MAP[meta_class.__name__]['full'] = list(inspect.getmro(meta_class))
            METANODE_CLASSES_INHERITANCE_MAP[meta_class.__name__]['short'] = [
                n.__name__ for n in inspect.getmro(meta_class)]

    @staticmethod
    def register_meta_types(node_types=None):

        from tpDcc.dccs.maya.meta import metanode

        if node_types is None:
            node_types = list()

        base_types = [
            'network',
            'transform',
            'joint',
            'locator',
            'objectSet',
            'script',
            'HIKCharacterNode',
            'HIKControlSetNode'
        ]

        global METANODE_TYPES_REGISTER
        if node_types and METANODE_TYPES_REGISTER:
            base_types = METANODE_TYPES_REGISTER
        METANODE_TYPES_REGISTER = list()

        if node_types:
            node_types = python.force_list(node_types)
            [base_types.append(n) for n in node_types if n not in base_types]

        try:
            valid_dcc_metanode_types = metanode.MetaNode.get_valid_metanode_types()

            for node_type in base_types:
                if node_type not in METANODE_TYPES_REGISTER and node_type in valid_dcc_metanode_types:
                    maya.logger.debug('MetaNode type: {0} : added to METANODE_TYPES_REGISTER'.format(node_type))
                    METANODE_TYPES_REGISTER.append(node_type)
                else:
                    maya.logger.debug('MetaNode TYPE: {0} is an invalid Maya Meta type'.format(node_type))
        except Exception as e:
            maya.logger.warning('Fail when register MetaNode types: {0}'.format(str(e)))

    @staticmethod
    def register_meta_nodes():
        global METANODES_CACHE
        METANODES_CACHE = dict()

    @classmethod
    def clean_metanode_types_register(cls):
        cls.register_metanodes_types(node_types=[])

    @staticmethod
    def get_metanode_classes_registry():
        return METANODE_CLASSES_REGISTER

    @staticmethod
    def get_metanode_types_registry():
        return METANODE_TYPES_REGISTER

    @staticmethod
    def get_metanode_cache():
        return METANODES_CACHE

    @staticmethod
    def print_metanode_classes_registry():
        for m in METANODE_CLASSES_REGISTER:
            print(m)

    @staticmethod
    def print_metanode_types_registry():
        for m in METANODE_TYPES_REGISTER:
            print(m)

    @classmethod
    def print_metanodes_cache(cls):
        """
        Print the current valid cache of instantaited MetaNodes
        :return:
        """

        cls.clean_metanodes_cache()
        for k, v in METANODES_CACHE.items():
            print('{0} : {1} : {2}'.format(k, name_utils.strip_name(v.meta_node), v))

    @staticmethod
    def remove_metanodes_from_cache(meta_nodes):
        """
        Removes instantiated MetaNodes from the cache of MetaNodes
        """

        for k, v in METANODES_CACHE.items():
            if not type(meta_nodes) == list:
                meta_nodes = [meta_nodes]

            if v and v in meta_nodes:
                try:
                    METANODES_CACHE.pop(k)
                    maya.logger.debug('METANODES CACHE: {0} being removed from the MetaNodes Cache >> {1}'.format(
                        name_utils.strip_name(k), name_utils.strip_name(v.meta_node)))
                except Exception as e:
                    maya.logger.debug('METANODES CACHE: Failed to remove {0} from cache >> {1}'.format(k, v.meta_node))

    @staticmethod
    def reset_metanodes_cache():
        """
        Reset the global MetaNodes cached
        """

        global METANODES_CACHE
        METANODES_CACHE = dict()

    @classmethod
    def reset_metanode_types_cache(cls):
        cls.register_metanodes_types(node_types=None)

    @staticmethod
    def get_metanode_classes_instances(metanode_instances):
        """
        Returns a list of registered metaNodes classes that are subclassed from the given metanode classes
        This function can be useful to group meta classes by their inheritance
        :param metanode_instances: list<MetaNode>
        :return: list<str>
        """

        sub_classes = list()
        if not type(metanode_instances) == list:
            metanode_instances = [metanode_instances]
        for metanode_class in METANODE_CLASSES_REGISTER.values():
            for instance in metanode_instances:
                if issubclass(metanode_class, instance):
                    sub_classes.append(metanode_class)

        return sub_classes

    @staticmethod
    def meta_types_to_registry_key(meta_types):
        meta_types = python.force_list(meta_types)
        keys = list()

        for cls in meta_types:
            try:
                keys.append(cls.__name__)
            except Exception:
                keys.append(cls)

        # Remove unregistered keys
        return [key for key in keys if key in METANODE_CLASSES_REGISTER.keys()] or []

    @staticmethod
    def convert_node_to_metanode(nodes, meta_class):
        """
        Converts given node to MetaNode, assuming that the node type is registered in the MetaNodeTypesRegistry
        :param nodes: list, nodes to cast to MetaNode instance
        :param meta_class: MetaNode class to convert them to
        NOTE: Always use convert_meta_class_to_type function because it checks if the given nodes
        are or not already instantiated or bound to Meta system
        """

        from tpDcc.dccs.maya.meta import metanode

        if not type(nodes) == list:
            nodes = [nodes]
        for n in nodes:
            maya.logger.debug('Converting node {0} >> to {1} MetaNode'.format(name_utils.strip_name(n), meta_class))
            meta_node = metanode.MetaNode(n)
            meta_node.add_attribute('meta_class', value=MetaDataManager.meta_types_to_registry_key(meta_class)[0])
            meta_node.add_attribute('meta_node_id', value=name_utils.strip_name(n))
            meta_node.attr_set_locked('meta_class', True)
            meta_node.attr_set_locked('meta_node_id', True)

        return [metanode.MetaNode(n) for n in nodes]

    # endregion

    @classmethod
    @decorators.timer
    def get_meta_nodes(cls, meta_types=[], meta_instances=[], meta_classes_grps=[], meta_attrs=None,
                       data_type='MetaNode', node_types=None, **kwargs):
        """
        Get all MetaNode nodes in the current scene and return as MetaNode objects if possible
        :param meta_types: list(str), if given, only will return the meta nodes of the given type
        :param meta_instances: list(str), if given the meta inheritance will be checked and child classes
            will be returned
        :param meta_classes_grps:
        :param meta_attrs:
        :param data_type:
        :param node_types:
        :param kwargs:
        :return:
        """

        from tpDcc.dccs.maya.meta import metanode

        meta_nodes = list()

        if not node_types:
            nodes = maya.cmds.ls(type=cls.get_metanode_types_registry(), long=True)
        else:
            nodes = maya.cmds.ls(type=node_types, long=True)
        if not nodes:
            return meta_nodes

        for node in nodes:
            meta_node = False
            if not meta_instances:
                if metanode.MetaNode.is_meta_node(node=node, meta_types=meta_types):
                    meta_node = True
            else:
                if metanode.MetaNode.is_meta_node_inherited(node=node, meta_instances=meta_instances):
                    meta_node = True
            if meta_node:
                if meta_classes_grps:
                    if not hasattr(meta_classes_grps, '__iter__'):
                        meta_classes_grps = [meta_classes_grps]
                    if metanode.MetaNode.is_meta_node_class_grp(node, meta_classes_grps):
                        meta_nodes.append(node)
                else:
                    meta_nodes.append(node)

        if not meta_nodes:
            return meta_nodes

        if meta_attrs:
            raise NotImplementedError('not implemented yet')

        if data_type == 'MetaNode':
            return [metanode.MetaNode(node, **kwargs) for node in meta_nodes]
        else:
            return meta_nodes

    def _update_ui(self):

        global METANODE_CLASSES_INHERITANCE_MAP
        classes = METANODE_CLASSES_INHERITANCE_MAP
        self._reg_mclasses_model.set_items(classes)

        global METANODES_CACHE
        nodes = METANODES_CACHE

        if nodes:
            items = list()
            ids = list(METANODES_CACHE.keys())
            nodes = list(METANODES_CACHE.values())
            for id, node in zip(ids, nodes):
                items.append([id, node.__class__.__name__])
            self._curr_mnodes_model.set_items(items)


def run():
    win = MetaDataManager()
    win.show()
    return win
