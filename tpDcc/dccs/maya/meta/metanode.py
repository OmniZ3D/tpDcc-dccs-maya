#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
MetaNode class implementation for Maya
"""

# NOTE: maya.cmds.addAttr gives some problem with string formatting when unpack attributes from keywords attributes
# So we do not use unicode laterals
from __future__ import print_function, division, absolute_import

import sys
import json
import time
import types
import traceback
from functools import wraps

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metautils
from tpDcc.dccs.maya.core import exceptions, helpers, name as name_utils, attribute as attr_utils
from tpDcc.dccs.maya.managers import metadatamanager


def node_lock_manager(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        res = None
        err = None
        locked = False
        try:
            locked = False
            meta_node = args[0]
            maya.logger.debug(
                'NodeLockManager > fn : {0} : MetaNode / self: {1}'.format(fn.__name__, meta_node.meta_node))
            if meta_node.meta_node and meta_node._lockState:
                locked = True
                maya.logger.debug('NodeLockManager > fn : {0} : node being unlocked'.format(fn.__name))
                maya.cmds.lockNode(meta_node.meta_node, lock=False)
            res = fn(*args, **kwargs)
        except StandardError as e:
            err = e
        finally:
            if locked:
                maya.logger.debug('NodeLockManager > fn : {0} : node being relocked'.format(fn.__name__))
                maya.cmds.lockNode(meta_node.meta_node, lock=True)
            if err:
                traceback = sys.exc_info()[2]  # Get full traceback
                raise StandardError(StandardError(err), traceback)
            return res

    return wrapper


class MetaNode(object):

    UNMANAGED = [
        'meta_node',
        'meta_node_id',
        '_MObject',
        '_MObjectHandle',
        '_MFnDependencyNode',
        '_lockState', 'lockState',
        '_forceAsMeta',
        '_lastDagPath',
        '_lastUUID',
        'cached'
    ]

    cached = None

    def __new__(cls, *args, **kwargs):

        # A DCC native object is passed and if it has the meta_class attribute, we pass that class into the
        # the super(__new__) and an object of that class will be instantiated and returned

        meta_class = None
        MetaNode.cached = None

        if args:
            meta_node = args[0]
            if meta_node:

                # If the meta node is in the cache we do not create a new one
                cache_instance = metadatamanager.MetaDataManager.get_metanode_from_cache(meta_node=meta_node)
                maya.logger.debug('Cache instance: {0}'.format(cache_instance))
                if cache_instance:
                    MetaNode.cached = True
                    cache_instance.cached = True
                    return cache_instance

            # If the given node is already a MetaNode we return it
            if issubclass(type(meta_node), MetaNode):
                maya.logger.debug('The passed node is already an instantiated MetaNode!!')
                MetaNode.cached = True
                meta_node.cached = True
                return meta_node

            meta_class = cls.is_meta_node(node=meta_node, check_instance=False, return_meta_class=True)

        if meta_class:
            maya.logger.debug('MetaClass derived from MayaNode Attr : {0}'.format(meta_class))
            if meta_class in metadatamanager.METANODE_CLASSES_REGISTER:
                registered_meta_class = metadatamanager.METANODE_CLASSES_REGISTER[meta_class]
                try:
                    maya.logger.debug('### Instantiating existing MetaClass : {0} >> {1}'.format(
                        meta_class, registered_meta_class))
                    return super(cls.__class__, cls).__new__(registered_meta_class)
                except Exception:
                    maya.logger.debug('Failed to initialize MetaClass : {0}'.format(registered_meta_class))
                    pass
            else:
                raise StandardError('Node has an unregistered MetaClass attr set: "{}"'.format(meta_class))
        else:
            maya.logger.debug('MetaClass "{}" not found, given or registered!'.format(meta_class))
            return super(cls.__class__, cls).__new__(cls)

    def __init__(self, node=None, name=None, node_type='network', *args, **kwargs):

        maya.logger.debug(
            'Meta => __init__ => main args :: node={0}, name={1}, node_type={2}'.format(node, name, node_type))

        if node and MetaNode.cached:
            self.cached = True
            maya.logger.debug('Meta Cache => Aborting __init__ on pre-cached MetaNode object!')
            return

        # Data that will be passed to the Maya node and it is stored on the Python object
        # We use __setattr__ to avoid data serialization on Maya node
        object.__setattr__(self, 'cached', False)
        object.__setattr__(self, '_MObject', '')
        object.__setattr__(self, '_MObjectHandle', '')
        object.__setattr__(self, '_MDagPath', '')
        object.__setattr__(self, '_lastDagPath', '')
        object.__setattr__(self, '_lastUUID', '')
        object.__setattr__(self, '_lockState', False)
        object.__setattr__(self, '_forceAsMeta', False)

        if not node:
            if not node_type == 'network' and node_type not in metadatamanager.METANODE_TYPES_REGISTER:
                maya.logger.debug(
                    'node_type : "{0}" : is not registered yet! Use metadatamanager.register_meta_types to '
                    'register the class before instantiating it'.format(node_type))
                if not name:
                    name = node_type
            if not name:
                name = self.__class__.__name__

            self.meta_node, full_management = self.__create_node__(node_type, name=name)

            if full_management:
                # MetaClass
                self.add_attribute('meta_class', value=str(self.__class__.__name__), attr_type='string')
                self.meta_node_id = name
                # Use to identify system base classes
                self.add_attribute('meta_class_group', value='MetaClass', attr_type='string', hidden=True)
                # Indicates this node if a system root MetaNode
                self.add_attribute('meta_system_root', value=False, attr_type='bool', hidden=True)

                if helpers.get_maya_version() <= 2016:
                    self.add_attribute('UUID', value='')

                maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, 'meta_class'), edit=True, lock=True)
                maya.cmds.setAttr('{0}.{1}'.format(self.meta_node_id, 'meta_class'), edit=True, lock=True)

            maya.logger.debug('New MetaData node {0} created!'.format(name))
            self.register_metanode_to_cache(self)

        else:
            self.meta_node = node

            if self.is_meta_node(node=node):
                maya.logger.debug('MetaNode passed in : {0}'.format(node))
                self.register_metanode_to_cache(self)
            else:
                maya.logger.debug('Standard Maya Node being managed')

        self.lockState = False
        self.__bind_data__(*args, **kwargs)

        auto_fill = kwargs.get('autofill', False)
        if auto_fill == 'all' or auto_fill == 'messageOnly':
            self.__fill_attr_cache__(auto_fill)

    def __getattribute__(self, attr):
        data = None
        object_attr = False

        try:
            data = object.__getattribute__(self, attr)
            object_attr = True
        except Exception as exc:
            maya.logger.debug('{} attr not yet seen - function call probably generated by Maya directly'.format(attr))

        if data:
            if isinstance(data, types.MethodType):
                return data

        try:
            if attr in MetaNode.UNMANAGED:
                return data

            meta_node = object.__getattribute__(self, 'meta_node')
            if not meta_node or not maya.cmds.objExists(meta_node):
                return data
            else:
                try:
                    attr_type = maya.cmds.getAttr('{0}.{1}'.format(meta_node, attr), type=True)
                    if attr_type == 'message':
                        return self.__get_message_attr__(attr)

                    attr_val = maya.cmds.getAttr('{0}.{1}'.format(meta_node, attr), silent=True)
                    if attr_type == 'string':
                        try:
                            attr_val = deserialize_json_attr(attr_val)
                            if type(attr_val) == dict:
                                return attr_val
                        except Exception:
                            # maya.logger.debug('string is not JSON deserializable')
                            pass
                        return attr_val
                    elif attr_type == 'double3' or attr_type == 'float3':
                        return attr_val[0]
                    return attr_val
                except Exception:
                    if object_attr:
                        return data
                    else:
                        raise AttributeError(
                            'Object instance "{}" : {} has no attribute : {}'.format(self.meta_node, self, attr))
        except StandardError as e:
            raise StandardError('{} | {}'.format(e, traceback.format_exc()))

    def __create_node__(self, node_type, name):
        """
        Function that can be override to manage custom creation functionality for specific node types
        :param node_type: str, type of node to create
        :param name: str, name of the new node
        :return: str, bool, name of the created node and bool that manages which controls the bindings of the base
            attributes. If False, we do not bind up the meta_node_id, meta_class attributes, instead we rely on
            the node_type.lower() being a key in the metadata manager register as a class
        """

        return maya.cmds.createNode(node_type, name=name), True

    def __bind_data__(self, *args, **kwargs):
        """
        This should be override in new MetaClasses. Is intended to be used as an entry point to bind attrs or
        extras you need at a class level. It's called in the __init__
        NOTE: When subclassing __bind_data__ will run BEFORE your subclasses __init__
        - To bind a new attr and serialize it --> self.addAttr('attr', attr_type='string')
        - To bind a new attr to the Python object only, not serialized --> self.attr =
            None or self.__setattr__('attr', None)
        """

        pass

    def __get_message_attr__(self, attr):
        msg_links = maya.cmds.listConnections('{0}.{1}'.format(
            self.meta_node, attr), destination=True, source=True, sh=True)
        if msg_links:
            msg_links = maya.cmds.ls(msg_links, long=True)
            if not maya.cmds.attributeQuery(attr, node=self.meta_node, m=True):
                if self.is_meta_node(node=msg_links[0]):
                    return MetaNode(msg_links[0])
            for i, link in enumerate(msg_links):
                if self.is_meta_node(link) or self._forceAsMeta:
                    msg_links[i] = maya.logger.Meta(link)
                    maya.logger.debug('{}: Connect data is a MetaClass object, returning the class'.format(link))
            return msg_links
        else:
            maya.logger.debug('Nothing connected to msgLink {0}.{1}'.format(self.meta_node, attr))
            return []

    def __fill_attr_cache__(self, level):
        """
        Loop through all attributes on the node and cast each one of the into the main object.__dict__.
        This will allow to show them in the script editor and have auto complete for free
        :param level:
        :return:
        """

        if level == 'messageOnly':
            attrs = self.list_attrs_of_type(attr_type='message')
        else:
            attrs = maya.cmds.listAttr(self.meta_node)
        for attr in attrs:
            try:
                object.__setattr__(self, attr, None)
            except Exception:
                maya.logger.debug('Unable to bind attribute: {} to initial Python object'.format(attr))

    def __set_enum_attr__(self, attr, value):
        if attribute_data_type(value) in ['string', 'unicode']:
            maya.logger.debug('Set Enum attribute by string : {0}'.format(value))
            enums = maya.cmds.attributeQuery(attr, node=self.meta_node, listEnum=True)[0].split(':')
            try:
                value = enums.index(value)
            except Exception:
                exc_msg = 'Invalid enum string passed in: strig is not in enum keys'
                maya.logger.debug(exc_msg)
                raise ValueError(exc_msg)
        maya.logger.debug('Set Enum attribute by index: {0}'.format(value))
        maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, attr), value)

    def __set_message_attr__(self, attr, value, force=True, ignore_overload=False):
        """
        By default, the nodes you pass will be the only connections to the message.
        Other connections will be deleted
        """

        try:
            if ignore_overload:
                if not maya.cmds.attributeQuery(attr, node=self.meta_node, multi=True):
                    if attribute_data_type(value) == 'complex':
                        exc_msg = 'You cannot connect multiple nodes to a single message plug via __setattr__'
                        maya.logger.debug(exc_msg)
                        raise ValueError(exc_msg)
                    maya.logger.debug('Set Single message attribute connection: {0}'.format(value))
                    self.connect_child(value, attr, clean_current=True, force=force)
                else:
                    maya.logger.debug('Set Multi-Message attribute connection: {0}'.format(value))
                    self.connect_children(value, attr, clean_current=True, force=force)
            else:
                if value:
                    if issubclass(type(value), list):
                        value = [metautils.MetaAttributeValidator.meta_node_string(o) for o in value]
                    else:
                        value = metautils.MetaAttributeValidator.meta_node_string(value)
                metautils.MetaAttributeUtils.set_message(self.meta_node, attr, value)
        except Exception as e:
            raise Exception(e)

    @node_lock_manager
    def __setattr__(self, attr, value, force=True, **kwargs):
        object.__setattr__(self, attr, value)

        if attr not in MetaNode.UNMANAGED and not attr == 'UNMANAGED':
            if self.has_attr(attr):
                locked = False
                if self.attr_is_locked(attr) and force:
                    self.attr_set_locked(attr, False)
                    locked = True
                meta_node = self.meta_node
                attr_type = self.attr_type(attr)

                if attr_type == 'enum':
                    self.__set_enum_attr__(attr=attr, value=value)
                elif attr_type == 'message':
                    self.__set_message_attr__(attr=attr, value=value, force=force)
                else:
                    attr_string = '{0}.{1}'.format(meta_node, attr)
                    value_type = attribute_data_type(value)
                    if attr_type == 'string':
                        if value_type == 'string' or value_type == 'unicode':
                            maya.cmds.setAttr(attr_string, value, type='string')
                            maya.logger.debug('setAttr: {0} : type : "string" to value : {1}'.format(attr, value))
                        elif value_type == 'complex':
                            maya.logger.debug('setAttr : {0} : type : "complex_string" to value : {1}'.format(
                                attr, serialize_json_attr(value)[0]))
                            maya.cmds.setAttr(attr_string, serialize_json_attr(value)[0], type='string')
                    elif attr_type in ['double3', 'float3'] and value_type == 'complex':
                        try:
                            maya.cmds.setAttr(attr_string, value[0], value[1], value[2])
                        except ValueError as e:
                            raise ValueError(e)
                    elif attr_type == 'doubleArray':
                        maya.cmds.setAttr(attr_string, value, type='doubleArray')
                    elif attr_type == 'matrix':
                        maya.cmds.setAttr(attr_string, value, type='matrix')
                    else:
                        try:
                            maya.cmds.setAttr(attr_string, value)
                        except StandardError as e:
                            maya.logger.debug('Failed to setAttr {0} - might be connected'.format(attr_string))
                            raise StandardError(e)

                    maya.logger.debug('setAttr : {0} : type : {1} to value : {2}'.format(attr, attr_type, value))
                if locked:
                    self.attr_set_locked(attr, True)
            else:
                maya.logger.debug('attr : {0} does not exist on MayaNode > class attr only'.format(attr))

    @node_lock_manager
    def __delattr__(self, attr):
        try:
            maya.logger.debug('Atribute delete : {0}, {1}'.format(self, attr))
            object.__delattr__(self, attr)
            if self.has_attr(attr):
                maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, attr), lock=False)
                maya.cmds.deleteAttr('{0}.{1}'.format(self.meta_node, attr))
        except StandardError as e:
            raise StandardError(e)

    def __repr__(self):
        try:
            if self.has_attr('meta_class'):
                return '{0}(meta_class: "{1}", node: "{2}")'.format(self.__class__, self.meta_class,
                                                                    self.meta_node.split('|')[-1])
            else:
                return '{0}(Wrapped Standard MayaNode, node: "{1}")'.format(self.__class__,
                                                                            self.meta_node.split('|')[-1])
        except Exception:
            try:
                metadatamanager.METANODES_CACHE.pop(object.__getattribute__(self, '_lastUUID'))
                maya.logger.debug(
                    'Dead MetaNode {0} removed from cache ...'.format(object.__getattribute__(self, '_lastDagPath')))
            except Exception:
                pass
            try:
                return (
                    'Dead MetaNode : Last good Dag Path was: {0}'.format(object.__getattribute__(self, '_lastDagPath')))
            except Exception:
                return "METANODE REMOVED BY HAND"

    def __eq__(self, obj):
        if not self._MObjectHandle.isValid():
            try:
                metadatamanager.METANODES_CACHE.pop(object.__getattribute__(self, '_lastUUID'))
                maya.logger.debug(
                    'Dead MetaNode "{0}" removed from cache...'.format(object.__getattribute__(self, '_lastDagPath')))
            except Exception:
                pass
            return False

        if isinstance(obj, self.__class__):
            if obj._MObject and self._MObject:
                if obj._MObject == self._MObject:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def __fill_attr_cache__(self, level):
        """
        Loops through all the attributes of a given node and cast each one of them into the main object.__dict__
        so all of them will show in the scriptEditor with auto-completion
        :param level: str, 'all' || 'messageOnly'
        """

        if level == 'messageOnly':
            attrs = self.list_attrs_of_type(attr_type='message')
        else:
            attrs = maya.cmds.listAttr(self.meta_node)

        for attr in attrs:
            try:
                object.__setattr__(self, attr, None)
            except Exception:
                maya.logger.debug('Unable to bind attr : {0} to initial Python object!'.format(attr))

    def __verify__(self, *args, **kwargs):
        """
        Function that checks that MetaNode is valid and can be used as post constructor
        Override in child classes
        :return: pass
        """

        return True

    @property
    def lockState(self):
        """
        Returns the lock state of the native node
        :return: bool
        """

        return self._lockState

    @lockState.setter
    def lockState(self, state):
        try:
            maya.cmds.lockNode(self.meta_node, lock=state)
            self._lockState = state
        except Exception:
            maya.logger.debug('Cannot set the nodeState for : {0}'.format(self.meta_node))

    @property
    def meta_node_id(self):
        if not self.has_attr('meta_node_id'):
            return self.meta_node.split('|')[-1].split(':')[-1]
        else:
            return maya.cmds.getAttr('{0}.{1}'.format(self.meta_node, 'meta_node_id'))

    @meta_node_id.setter
    @node_lock_manager
    def meta_node_id(self, value):
        if not self.has_attr('meta_node_id'):
            maya.cmds.addAttr(self.meta_node, longName='meta_node_id', dt='string')
        maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, 'meta_node_id'), edit=True, lock=False)
        maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, 'meta_node_id'), value, type='string')
        maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, 'meta_node_id'), edit=True, lock=True)

    @property
    def meta_node_mobj(self):
        """
        Exposed wrapper to return the MObject directly, this passes via MObjectHandle to ensure that
        the MObject cached is still valid
        """

        mobj_handle = object.__getattribute__(self, '_MObjectHandle')
        if mobj_handle:
            try:
                if not mobj_handle.isValid():
                    maya.logger.info(
                        'MetaNode : MObject is no longer valid - {0} - object may have been deleted or'
                        ' the scene reloaded?'.format(object.__getattribute__(self, 'meta_node_id')))
                    return
                # If we have a DagNode, we return the full path
                return object.__getattribute__(self, '_MObject')
            except StandardError as e:
                raise StandardError(e)

    @property
    def meta_node(self):
        """
        meta_node is the pointer to the Maya object itself and it's retrieved via MObject Maya API under the hood
        which ensures that it's always synchronized with Maya
        """

        try:
            mobj_handle = object.__getattribute__(self, '_MObjectHandle')
        except AttributeError:
            mobj_handle = None

        # maya.logger.debug('Getting Maya Node MObject Handle: {}'.format(mobj_handle))

        if mobj_handle:
            try:
                if not mobj_handle.isValid():
                    last_dag_path = object.__getattribute__(self, '_lastDagPath')
                    raise exceptions.MObjectNotValidException(mobj=mobj_handle, last_dag_path=last_dag_path)

                mobj = object.__getattribute__(self, '_MObject')

                if maya.OpenMaya.MObject.hasFn(mobj, maya.OpenMaya.MFn.kDagNode):
                    dag_path = maya.OpenMaya.MDagPath()
                    maya.OpenMaya.MDagPath.getAPathTo(mobj, dag_path)
                    # maya.logger.debug(' --- Maya Node DAG --- \n\tPath: {}'.format(dag_path.fullPathName()))
                    _result = dag_path.fullPathName()
                else:
                    dep_node_func = maya.OpenMaya.MFnDependencyNode(mobj)
                    # maya.logger.debug(' --- Maya Node DG --- \n\tName: {}'.format(dep_node_func.name()))
                    _result = dep_node_func.name()

                # Cache the DAG path on the object as a backup for error reporting
                # maya.logger.debug('Updating _lastDagPath of {} to: \n\tLast DAG path: {}'.format(mobj, _result))
                object.__setattr__(self, '_lastDagPath', _result)
                return _result
            except StandardError as e:
                raise StandardError(e)

    @meta_node.setter
    def meta_node(self, node):
        if node:
            try:
                mobj = maya.OpenMaya.MObject()
                sel = maya.OpenMaya.MSelectionList()
                sel.add(node)
                sel.getDependNode(0, mobj)

                maya.logger.debug(
                    'Updating Meta Node: \n\tMObject=>{} \n\tMObjectHandle=>{} \n\tMFnDependencyNode=>{}'.format(
                        mobj, maya.OpenMaya.MObjectHandle(mobj), maya.OpenMaya.MFnDependencyNode(mobj)))

                object.__setattr__(self, '_MObject', mobj)
                object.__setattr__(self, '_MObjectHandle', maya.OpenMaya.MObjectHandle(mobj))
                object.__setattr__(self, '_MFnDependencyNode', maya.OpenMaya.MFnDependencyNode(mobj))
            except StandardError as e:
                raise StandardError(e)
        else:
            maya.logger.debug('Setting meta node to None ...')

    @property
    def short_name(self):
        return name_utils.get_short_name(self.meta_node)

    @property
    def long_name(self):
        return name_utils.get_short_name(self.meta_node)

    @property
    def base_name(self):
        return name_utils.get_short_name(self.meta_node)

    @staticmethod
    def check_metanode_validity(meta_node):
        """
        Check is the given meta_node is still valid
        :param meta_node: MetaNode
        :return: bool, True if the given meta node is valid or False otherwise
        """

        return meta_node.is_valid_mobject()

    @staticmethod
    def get_metanode_uuid(meta_node):
        """
        Returns a UUID (unique identifier) for the given meta node
        :param meta_node: MetaNode
        :return: str
        """

        if type(meta_node) == MetaNode or issubclass(type(meta_node), MetaNode) or hasattr(meta_node, 'meta_node'):
            if helpers.get_maya_version() >= 2016:
                return maya.cmds.ls(meta_node.meta_node, uuid=True)[0]
            else:
                return metadatamanager.MetaDataManager.generate_uuid(meta_node=meta_node)
        else:
            if helpers.get_maya_version() >= 2016:
                return maya.cmds.ls(meta_node, uuid=True)[0]
            else:
                return maya.cmds.getAttr('{0}.UUID'.format(meta_node))

    @staticmethod
    def get_valid_metanode_types():
        """
        Check is the given meta_node is still valid
        :param meta_node: MetaNode
        :return: bool, True if the given meta node is valid or False otherwise
        """

        return maya.cmds.allNodeTypes()

    @staticmethod
    def is_meta_node(node, meta_types=None, check_instance=True, return_meta_class=False):
        """
        Returns True if the node is a meta node or False otherwise
        :param node: str, node to test
        :param meta_types: str | class, check only given meta classes
        :param check_instance: bool
        :param return_meta_class:  bool, if True return the str(meta_class) that this node is bound too
        :return: bool
        """

        meta_types = meta_types if meta_types is not None else list()
        meta_class_instance = False
        if not node:
            return False

        if check_instance:
            if issubclass(type(node), MetaNode):
                node = node.meta_node
                meta_class_instance = True

        meta_class = MetaNode.get_meta_class_from_node(node, check_instance=check_instance)
        if meta_class:
            if meta_class in metadatamanager.METANODE_CLASSES_REGISTER:
                if meta_types:
                    if meta_class in metadatamanager.MetaDataManager.meta_types_to_registry_key(meta_types=meta_types):
                        if return_meta_class:
                            return meta_class
                        return True
                    else:
                        return False
                else:
                    if return_meta_class:
                        return meta_class
                    return True
            else:
                maya.logger.debug('IsMetaNode >> Invalid MetaClass attr : {0}'.format(meta_class))
                return False
        else:
            if meta_class_instance:
                maya.logger.debug('IsMetaNode= True : node is a wrapped Native Node MetaClass instance')
                if return_meta_class:
                    return meta_class_instance.meta_class
                return True
            else:
                return False

    @classmethod
    def is_meta_node_inherited(cls, node, meta_instances=[], mode='short'):
        """
        Checks if the node is inherited from or a subclass of a given Meta base class
        :param node:  str, node to test
        :param meta_instances: list of instances we want to validate against
        :param mode: str, 'short' or 'full', how we dtermine the inheritance, either full class inheritance or
        META_INHERITANCE_MAP[key] (string)
        """

        if not node:
            return False

        if issubclass(type(node), MetaNode):
            node = node.meta_node

        meta_class = cls.get_meta_class_from_node(node)
        if meta_class and meta_class in metadatamanager.METANODE_CLASSES_REGISTER:
            for inst in metadatamanager.MetaDataManager.meta_types_to_registry_key(meta_types=meta_instances):
                if mode == 'full':
                    if metadatamanager.METANODE_CLASSES_REGISTER[inst] in \
                            metadatamanager.METANODE_CLASSES_INHERITANCE_MAP[meta_class]['full']:
                        maya.logger.debug('MetaNode {0} is subclass >> {1}'.format(meta_class, inst))
                        return True
                else:
                    if issubclass(metadatamanager.METANODE_CLASSES_REGISTER[meta_class],
                                  metadatamanager.METANODE_CLASSES_REGISTER[inst]):
                        maya.logger.debug('MetaNode {0} is subclass >> {1}'.format(meta_class, inst))
                        return True

        return False

    @classmethod
    def is_meta_node_class_grp(cls, node, meta_class_grps=[]):
        """
        Check the meta class group to see if it matches the given one
        :param node: str, node to check
        :param meta_class_grps: list<str>
        :return: bool
        """

        if not node:
            return False

        if issubclass(type(node), MetaNode):
            node = node.meta_node
        if not hasattr(meta_class_grps, '__iter__'):
            meta_class_grps = [meta_class_grps]
        for grp in meta_class_grps:
            maya.logger.debug('metaGroup testing: {0}'.format(node))
            try:
                # TODO: Finish
                pass
            except Exception:
                pass

        return False

    @staticmethod
    def register_metanode_to_cache(meta_node):
        """
        Add a given meta_node to the global META_NODE_CACHE cache of currently instantiated MetaNode objects
        :param meta_node: instantiated meta node to tadd
        """

        metadatamanager.MetaDataManager.register_metanode_to_cache(meta_node=meta_node)

    def hide(self):
        """
        Hide wrapped node
        """

        maya.cmds.hide(self.meta_node)

    def is_valid(self):
        """
        A MetaNode is valid if it has connections, otherwise is invalid
        """

        try:
            if not self.is_valid_mobject():
                return False
            if self.has_attr('meta_class') and not maya.cmds.listRelatives(self.meta_node):
                return False
        except Exception:
            # raise exceptions.InvalidMetaNodeException(meta_node=self.meta_node)
            print('MetaNode {} is not valid!'.format(self.meta_node))
            return False
        return True

    def is_valid_mobject(self):
        """
        Validates teh current MObject associated to the meta node, we need to do this check because without this,
        Maya will crash if the pointer is no longer valid
        TODO: thinking of storing the dagPath when we fill in the mNode to start with and
        TODO: if this test fails, ie the scene has been reloaded, then use the dagPath to refind
        TODO: and refil the mNode property back in.... maybe??
        """

        try:
            mobj_handle = object.__getattribute__(self, '_MObjectHandle')
            return mobj_handle.isValid()
        except Exception as e:
            maya.logger.info('_MObjectHandle not setup yet!')
            maya.logger.debug(str(e))

    def add_attribute(self, attr, value=None, attr_type=None, hidden=False, **kwargs):
        """
        Adds a new attribute to the meta node
        :param attr: str, name of the attribute
        :param value: variant, value of the attribute
        :param attr_type: str, attribute type as string
        :param hidden: bool, True if the attribute should be hidden in the channel box or False otherwise
        :param kwargs:
        :return: bool, True if the attribute was added successfully or False otherwise
        """

        maya.logger.debug(
            '|Adding Attribute| >> node: {0} | attr: {1} | attrType: {2}'.format(self.meta_node, attr, attr_type))

        added = False

        if attr_type and attr_type == 'enum' and 'enumName' not in kwargs:
            raise ValueError('enum attribute type must be passed with "enumName" keyword in args')

        DataTypeKwargs = {
            'string': {'longName': attr, 'dt': 'string'},
            'unicode': {'longName': attr, 'dt': 'string'},
            'int': {'longName': attr, 'at': 'long'},
            'bool': {'longName': attr, 'at': 'bool'},
            'float': {'longName': attr, 'at': 'double'},
            'float3': {'longName': attr, 'at': 'float3'},
            'double3': {'longName': attr, 'at': 'double3'},
            'doubleArray': {'longName': attr, 'dt': 'doubleArray'},
            'enum': {'longName': attr, 'at': 'enum'},
            'complex': {'longName': attr, 'dt': 'string'},
            'message': {'longName': attr, 'at': 'message', 'm': True, 'im': True},
            'messageSimple': {'longName': attr, 'at': 'message', 'm': False}
        }
        keyable = ['int', 'float', 'bool', 'enum', 'double3']
        add_cmd_edit_flags = ['min', 'minValue', 'max', 'maxValue', 'defaultValue', 'dv', 'softMinValue', 'smn',
                              'softMaxValue', 'smx', 'enumName']
        set_cmd_edit_flags = ['keyable', 'k', 'lock', 'l', 'channelBox', 'cb']
        add_kwargs_to_edit = dict()
        set_kwargs_to_edit = dict()
        if kwargs:
            for kw, v in kwargs.items():
                if kw in add_cmd_edit_flags:
                    add_kwargs_to_edit[kw] = v
                elif kw in set_cmd_edit_flags:
                    set_kwargs_to_edit[kw] = v

        # ===================================================================  IF ATTR EXISTS, EDIT ATTR
        if self.has_attr(attr):
            maya.logger.debug('"{0}" : Attr already exists on the node'.format(attr))
            try:
                if kwargs:
                    if add_kwargs_to_edit:
                        maya.cmds.addAttr('{0}.{1}'.format(self.meta_Node, attr), edit=True, **add_kwargs_to_edit)
                        maya.logger.debug('addAttr Edit flags run : {0} = {1}'.format(attr, add_kwargs_to_edit))
                    if set_kwargs_to_edit:
                        try:
                            if not self.is_referenced():
                                maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, attr), **set_kwargs_to_edit)
                                maya.logger.debug('setAttr Edit flags run : {0} = {1}'.format(attr, set_kwargs_to_edit))
                        except Exception:
                            maya.logger.debug(
                                'MetaNode is referenced and the setEditFlags are therefore'
                                ' invalid (lock, keyable, channelBox)')
            except Exception:
                if self.is_referenced():
                    maya.logger.debug('{0} : Trying to modify an attr on a reference node'.format(attr))
            return

        # ===================================================================  IF ATTR NOT EXISTS, CREATE ATTR
        else:
            try:
                if not attr_type:
                    attr_type = attribute_data_type(value)
                DataTypeKwargs[attr_type].update(add_kwargs_to_edit)
                maya.logger.debug('addAttr : {0} : value_type : {1} > data_type keywords: {2}'.format(
                    attr, attr_type, DataTypeKwargs[attr_type]))
                maya.cmds.addAttr(self.meta_node, **DataTypeKwargs[str(attr_type)])

                if attr_type == 'double3' or attr_type == 'float3':
                    if attr_type == 'double3':
                        sub_type = 'double'
                    else:
                        sub_type = 'float'
                    attr_list = []
                    for i, axis in enumerate(['X', 'Y', 'Z']):
                        attr_list.append('{0}{1}'.format(attr, axis))
                        maya.cmds.addAttr(self.meta_node, longName=attr_list[i], at=sub_type, parent=attr, **kwargs)
                        object.__setattr__(self, attr_list[i], None)
                    if attr_type in keyable and not hidden:
                        for at in attr_list:
                            maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, at), edit=True, keyable=True)
                elif attr_type == 'doubleArray':
                    maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, attr), [], type='doubleArray')
                else:
                    if attr_type in keyable and not hidden:
                        maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, attr), edit=True, keyable=True)
                if value:
                    self.__setattr__(attr, value, force=False)
                else:
                    object.__setattr__(self, attr, None)

                # Allow add_attribute to set any secondary kwargs via the setAttr call
                if set_kwargs_to_edit:
                    maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, attr), **set_kwargs_to_edit)
                    maya.logger.debug('setAttr Edit flags run : {0} = {1}'.format(attr, set_kwargs_to_edit))

                added = True
            except StandardError:
                maya.logger.error(traceback.format_exc())

        return added

    @node_lock_manager
    def delete_attribute(self, attr):
        """
        Deletes a given attribute
        :param attr: str
        """

        if self.has_attr(attr):
            try:
                maya.cmds.deleteAttr(self.meta_node, at=attr)
            except StandardError as e:
                raise StandardError('Failed to delete given attributes : {0} : {1}'.format(attr, e))

    @node_lock_manager
    def rename_attr(self, attr, new_attr_name):
        """
        Renames the given attribute
        :param attr: s tr
        :param new_attr_name: str
        """

        maya.cmds.renameAttr('{0}.{1}'.format(self.meta_node, attr), new_attr_name)

    def do_store(self, *args, **kwargs):
        """
        Stores information to an attribute
        :param args:
        :param kwargs:
        :return:
        """

        return metautils.MetaDataListUtils.store_info(self.meta_node, *args, **kwargs)

    def get_attr(self, attr, as_attr=True):
        """
        Returns attribute if exists
        :param attr: str, attribute name we want to query
        :param as_attr: bool, If True, Attribute object will be returned instead of attribute value
        :return: variant
        """

        try:
            a = self.__getattribute__(attr)
        except Exception:
            return None

        if as_attr:
            return attr_utils.Attribute(attr, self.meta_node)
        else:
            return a

    def has_attr(self, attr):
        """
        Simple wrapper check for attributs on the MetaNode itself
        :param attr: str
        :return: bool
        """

        if self.is_valid_mobject():
            try:
                result = self._MFnDependencyNode.hasAttribute(attr)
                if not result:
                    # Must rewrap the mobj, if you don't it kills the existing mNode and corrupts its cache entry
                    # 2011 bails because it lacks the api call anyway, 2012 and up work with this
                    mobj = maya.OpenMaya.MObject()
                    sel_list = maya.OpenMaya.MSelectionList()
                    sel_list.add(self._MObject)
                    sel_list.getDependNode(0, mobj)
                    result = self._MFnDependencyNode.findAlias(attr, mobj)
                return result
            except Exception as e:
                for arg in e.args:
                    maya.logger.error(arg)
                return maya.cmds.objExists('{0}.{1}'.format(self.meta_node, attr))

    def attr_type(self, attr):
        """
        Returns the MetaNode native API attribute type
        :param attr: str
        :return: variant
        """

        return maya.cmds.getAttr('{0}.{1}'.format(self.meta_node, attr), type=True)

    def list_attrs_of_type(self, attr_type='message'):
        """
        Lists all attrs of type on the MetaNode
        :param attr_type: str
        :return: list<str>
        """

        dep_node_fn = maya.OpenMaya.MFnDependencyNode(self.meta_node_mobj)
        attr_count = dep_node_fn.attributeCount()
        ret = list()
        for i in range(attr_count):
            attr_object = dep_node_fn.attribute(i)
            if attr_type:
                if attr_type == 'message':
                    if not attr_object.hasFn(maya.OpenMaya.MFn.kMessageAttribute):
                        continue
            mplug = dep_node_fn.findPlug(attr_object)
            ret.append(mplug.name().split('.')[1])
        return ret

    def attr_is_locked(self, attr):
        """
        Checks if the attribute on the MetaNode is locked
        :param attr: list<str>
        NOTE: This method receives a list of attributes and returns the overall state of the, ie, if any of the attrs
        in the list are locked then it will return True otherwise it will return False
        :return: bool
        """

        if hasattr(attr, '__iter__'):
            locked = False
            for a in attr:
                if maya.cmds.getAttr('{0}.{1}'.format(self.meta_node, attr), lock=True):
                    locked = True
                    break
            return locked
        return maya.cmds.getAttr('{0}.{1}'.format(self.meta_node, attr), lock=True)

    def attr_set_locked(self, attr, state):
        """
        Set the LockState of a given attr on the MetaNode
        :param attr: attr to ock, this now also takes a list of attributes
        :param state: lock state
        :return:
        """

        try:
            if not hasattr(attr, '__iter__'):
                attr = [attr]
            if not self.is_referenced():
                for a in attr:
                    maya.cmds.setAttr('{0}.{1}'.format(self.meta_node, a), lock=state)
        except StandardError as e:
            maya.logger.debug(str(e))

    @node_lock_manager
    def convert_meta_class_to_type(self, node_to_convert, new_meta_class):
        """
        Change the current meta class type of the given class instance
        NOTE: If you are converting a StandardWrapped Maya node to a MetaNode then you also need to ensure
        that the Maya node type is registered in the MetaData Manager
        :param new_meta_class:
        :param kwargs:
        """

        new_meta_class = metadatamanager.MetaDataManager.meta_types_to_registry_key(new_meta_class)[0]
        if new_meta_class in metadatamanager.METANODE_CLASSES_REGISTER:
            try:
                metadatamanager.MetaDataManager.remove_metanodes_from_cache(node_to_convert)
                if not node_to_convert.has_attr('meta_class'):
                    maya.logger.debug('Converting StandardWrapped Maya Node to a fully fledge MetaNode instance')
                    metadatamanager.MetaDataManager.convert_node_to_metanode(node_to_convert.meta_node, new_meta_class)
                else:
                    node_to_convert.meta_class = new_meta_class
            except StandardError as e:
                maya.logger.debug('Failed to convert self to new MetaClass type: {}'.format(new_meta_class))
                raise StandardError(StandardError(e), sys.exc_info()[2])
        else:
            raise StandardError('Given class it not in the MetaClass Registry: {}'.format(new_meta_class))

    def is_component(self):
        """
        Returns whether stored data are components or not
        :return: bool
        """

        if self._componentMode and self._component:
            cmp = '{}.{}'.format(self.meta_node, self._component)
            if maya.cmds.objExists(cmp):
                return True
            else:
                maya.logger.warning('Component no longer exists: {}'.format(self._component))

        return False

    def get_component(self):
        if self._componentMode and self._component:
            cmp = '{}.{}'.format(self.meta_node, self._component)
            if maya.cmds.objExists(cmp):
                return cmp
            else:
                maya.logger.warning('Component no longer exists: {}'.format(self._component))

        return self.meta_node

    def get_components(self, arg=False, flatten=True):
        """
        Query comnponents of given type in our node
        :param arg:str
        :param flatten: bool
        :return:list(str)
        """

        return maya.cmds.ls(['{}.{}[*]'.format(self.meta_node, arg)], flatten=flatten)

    def is_referenced(self):
        """
        Returns if the native MetaNode is referenced or not
        :return: bool
        """

        return maya.cmds.referenceQuery(self.meta_node, inr=True)

    def short_name(self):
        """
        Returns short name of the wrapped node
        :return:  str
        """

        return self.meta_node.split('|')[-1].split(':')[-1]

    def node_type(self):
        """
        Returns node type of the wrapped node
        :return: str
        """

        return maya.cmds.nodeType(self.meta_node)

    def select(self, *args, **kwargs):
        """
        Selects Maya node in viewport
        """

        maya.cmds.select(self.meta_node, *args, **kwargs)

    @node_lock_manager
    def rename(self, name, rename_child_links=False, *args, **kwargs):
        """
        Rename the Maya wrapped node (we work with MObject handlers so managed node will be updated properly)
        :param name: str, new name of the node
        :param rename_child_links: bool, Will rename connections back to the MetaNode from children who are connected
        directly to it, via an attribute that matches the current MetaNode name. These connected attributes
        will be renamed to reflect the change in node name
        """

        current_name = self.short_name
        maya.cmds.rename(self.meta_node, name)
        if rename_child_links:
            plugs = maya.cmds.listConnections(self.meta_node, s=True, d=True, p=True)
            for plug in plugs:
                split = plug.split('.')
                attr = split[-1].split('[')[0]
                child = split[0]
                if attr == current_name:
                    try:
                        child = MetaNode(child)
                        child.rename_attr(attr, name)
                        maya.logger.debug(
                            'Renamed Child attribute to match new MetaNode name: {}.{}'.format(child.meta_node, attr))
                    except Exception:
                        maya.logger.warning('Failed to rename attribute: {} on node: {}'.format(attr, child.meta_node))

        return name

    def delete(self):
        """
        Delete the meta node and this class instance
        NOTE: If you delete a 'network' node, by default Maya will delete all connected child nodes
        unless they are wired. To prevent this, set self.lockState=True in your classes __init__ function
        """

        if maya.cmds.lockNode(self.meta_node, query=True):
            maya.cmds.lockNode(self.meta_node, lock=False)

        metadatamanager.MetaDataManager.remove_metanodes_from_cache([self])

        maya.cmds.delete(self.meta_node)
        del (self)

    @staticmethod
    def get_meta_class_from_node(node, check_instance=True):
        """
        Get the meta class to instantiate from the node
        :param node:  str, node to retrieve the meta class binding from
        :param check_instance: bool
        :return:
        """

        if check_instance:

            # If the given node is already a MetaNode we return the MetaClass of the MetaNode
            if issubclass(type(node), MetaNode):
                maya.logger.debug('get_meta_class_from_node was given an already instantiated MNode')
                return node.meta_class

        try:
            meta_class = maya.cmds.getAttr('{0}.{1}'.format(node, 'meta_class'))
            if meta_class in metadatamanager.METANODE_CLASSES_REGISTER:
                return meta_class
            else:
                meta_class = maya.cmds.getAttr('{0}.{1}'.format(node, 'meta_class_group'))
                if meta_class in metadatamanager.METANODE_CLASSES_REGISTER:
                    return meta_class
        except Exception:
            node_type = maya.cmds.nodeType(node)
            if 'Meta{0}'.format(node_type) in metadatamanager.METANODE_CLASSES_REGISTER.keys():
                return 'Meta{0}'.format(node_type)
            else:
                for key in metadatamanager.METANODE_CLASSES_REGISTER.keys():
                    if key.lower() == node_type:
                        return key

    @staticmethod
    def get_meta_from_cache(meta_node):
        """
        Pull the given node from META_NODECACHE if its already be instantiated
        :param meta_node: str, name of the node from DAG
        """

        maya.logger.debug('Getting Meta From Cache ...')

        try:
            uuid = MetaNode.get_metanode_uuid(meta_node=meta_node)
            maya.logger.debug('MetaNode {} - UUID => {}'.format(meta_node, uuid))
            maya.logger.debug('MetaNode UUID Cache => {}'.format(metadatamanager))

            if uuid in metadatamanager.METANODES_CACHE.keys():
                try:
                    if MetaNode.check_metanode_validity(metadatamanager.METANODES_CACHE[uuid]):
                        maya.logger.debug('CACHE: Cached MetaNode {} has a valid MObject'.format(
                            metadatamanager.METANODES_CACHE[uuid]))
                        if not metadatamanager.METANODES_CACHE[uuid]._MObject == get_mobject(meta_node):
                            maya.logger.debug(
                                'CACHE: {} : UUID is already registered but to a different node: {}'.format(
                                    uuid, meta_node))
                            return

                        maya.logger.debug(
                            'CACHE : {} : Returning MetaNode from UUID cache! => {}'.format(meta_node, uuid))
                        return metadatamanager.METANODES_CACHE[uuid]
                    else:
                        maya.logger.debug('{} being removed from the cache due to invalid MObject'.format(meta_node))
                        metadatamanager.MetaDataManager.clean_metanodes_cache()
                except StandardError as e:
                    maya.logger.debug('CACHE: insepction fail!')
                    maya.logger.debug(str(e))
        except Exception:
            if meta_node in metadatamanager.METANODES_CACHE.keys():
                try:
                    if MetaNode.check_metanode_validity(metadatamanager.METANODES_CACHE[meta_node]):
                        if not metadatamanager.METANODES_CACHE[uuid]._MObject == get_mobject(meta_node):
                            maya.logger.debug(
                                'CACHE: {} : UUID is already registered but to a different node: {}'.format(
                                    uuid, meta_node))
                            return
                        maya.logger.debug('CACHE: {0} : Returning MetaNode from nameBased cache!'.format(meta_node))
                        return metadatamanager.METANODES_CACHE[meta_node]
                    else:
                        maya.logger.debug('{} being removed from the cache due to invalid MObject'.format(meta_node))
                        metadatamanager.MetaDataManager.clean_metanodes_cache()
                except Exception as e:
                    maya.logger.debug('CACHE: inspection fail!')
                    maya.logger.debug(str(e))

    @node_lock_manager
    def disconnect_current_attr_plugs(self, attr):
        """
        From a given attribute on the MetaNode disconnect any current connections and clean up
        the plugs by deleting the existing attributes
        :param attr: str
        """

        current_connects = self.__getattribute__(attr)
        if current_connects:
            if not isinstance(current_connects, list):
                current_connects = [current_connects]
            for cnt in current_connects:
                try:
                    maya.logger.debug('Disconnecting {0}.{1} >> from: {2}'.format(self.meta_node, attr, cnt))
                    self.disconnect_child(cnt, attr=attr, delete_source_plug=True, delete_dst_plug=False)
                except Exception:
                    maya.logger.warning('Failed to disconnect current message link')

    def get_next_array_index(self, node, attr):
        """
        Get the next available index in a multi message array
        :param node: str
        :param attr: str
        :return: int
        """

        index = maya.cmds.getAttr('{0}.{1}'.format(node, attr), multiIndices=True)
        if not index:
            return 0
        else:
            for i in index:
                if not maya.cmds.listConnections('%s.%s[%i]' % (node, attr, i)):
                    return i
            return index[-1] + 1

    def uplift_message(self, node, attr):
        """
        If attribute is a single, non-multi message attribute and it's already connected to something then
        convert it to a multi, non-indexed managed message attribute and cast any current connections to
        the newly created attribute
        :param node: str, node with the attribute on it
        :param attr: str, attribute to uplift
        :return: bool, If the attribute is a multi or not
        """

        if not maya.cmds.attributeQuery(attr, node=node, exists=True):
            maya.logger.debug('{} : message attribute does not exists!'.format(attr))
            return

        if maya.cmds.attributeQuery(attr, node=node, multi=True):
            maya.logger.debug('{} : message attribute is already multi - aborting uplift'.format(attr))
            return True

        connections = maya.cmds.listConnections('{0}.{1}'.format(node, attr), source=True, destination=False,
                                                plugs=True)
        if connections:
            maya.logger.debug('{} : attribute is already connected - uplift to multi-message'.format(attr))
            maya.cmds.deleteAttr('{0}.{1}'.format(node, attr))
            maya.cmds.addAttr(node, longName=attr, at='message', m=True, im=True)
            for cnt in connections:
                maya.cmds.connectAttr(cnt, '%s.%s[%i]' % (node, attr, self.get_next_array_index(node, attr)))

            return True

    def is_child_node(self, node, attr=None, source_attr=None):
        """
        Checks if a node is already connected to the MetaNode via a given attribute link
        :param node: str, native node
        :param attr: str
        :param source_attr: str
        :return: bool
        """

        if issubclass(type(node), MetaNode):
            node = node.meta_node

        if attr:
            connections = maya.cmds.ls(
                maya.cmds.listConnections('{0}.{1}'.format(self.meta_node, attr), source=False, destination=True,
                                          plugs=True), long=True)
        else:
            connections = maya.cmds.ls(
                maya.cmds.listConnections(self.meta_node, source=False, destination=True, plugs=True), long=True)
        if connections:
            for cnt in connections:
                if source_attr:
                    if '{0}.{1}'.format(maya.cmds.ls(node, long=True)[0], source_attr) in cnt:
                        return True
                else:
                    if '{0}.'.format(maya.cmds.ls(node, long=True))[0] in cnt:
                        return True

        return False

    @node_lock_manager
    def connect_child(self, node, attr, source_attr=None, clean_current=True, force=True, allow_multi=False, **kwargs):
        """
        Connects a node to the Metanode via a message attribute link
        This call generates a none-multi message on both sides of the connection and is designed for simple
        parent-child relationships
        By default, this call manages the attribute to only one child. To avoid this behaviour, use clean_current=False
        :param node: str, node to connect to this MetaNode
        :param attr: str, name of the message attribute
        :param source_attr: if given, this becomes the attribute on the child node which connect it to the MetaNode.
        If not given, this attribute is set to self.meta_node_id
        :param clean_current: bool, Disconnect and clean any currently connected nodes to this attribute
        :param force: bool, Force the connection of the nodes
        :param allow_multi: bool, Allows the same node to connect back to this metaNode under multiple wires
        By default, only allows a single wire from a MetaNode to a child
        If True, index is not used and a a single simple wire on the source attribute is used (the child)
        :param kwargs:
        """

        # Make sure that the given attribute exists on the MetaNode
        self.add_attribute(attr, attr_type='message')

        try:
            if clean_current:
                self.disconnect_current_attr_plugs(attr=attr)
            if not source_attr:
                source_attr = self.meta_node_id
            if not node:
                # this allows 'None' to be passed into the set attr calls and in turn, allow self.mymessagelink=None
                #  to clear all current connections
                return

            # add and manage the attr on the child node
            if self.is_meta_node(node):
                if not issubclass(type(node), MetaNode):
                    MetaNode(node).add_attribute(source_attr, attr_type='messageSimple')
                else:
                    node.add_attribute(source_attr, attr_type='messageSimple')
                    node = node.meta_node
            elif not maya.cmds.objExists('{0}.{1}'.format(node, source_attr)):
                maya.cmds.addAttr(node, longName=source_attr, at='message', m=False)

            # uplift to multi-message index managed if needed
            if allow_multi:
                source_is_multi = self.uplift_message(node, source_attr)

            if not self.is_child_node(node, attr, source_attr):
                try:
                    maya.logger.debug('Connecting child via multi-message')
                    maya.cmds.connectAttr(
                        '{0}.{1}'.format(self.meta_node, attr), '%s.%s[%i]' % (
                            node, source_attr, self.get_next_array_index(node, source_attr)), f=force)
                except Exception:
                    maya.logger.debug('Connecting child vai single-message')
                    maya.cmds.connectAttr('{0}.{1}'.format(
                        self.meta_node, attr), '{0}.{1}'.format(node, source_attr), f=force)
            else:
                raise StandardError('{} is already connected to MetaNode'.format(node))
        except StandardError as e:
            maya.logger.warning(e)

    @node_lock_manager
    def connect_children(self, nodes, attr, source_attr=None, clean_current=False, force=True, allow_incest=True,
                         source_simple=False, **kwargs):
        """
        Connects multiple nodes to the Metanode via a message attribute link
        :param nodes: list<str>, list of native nodes to connect to this MetaNode
        :param attr: str, name of the message attribute
        :param source_attr: if given, this becomes the attribute on the child node which connect it to the MetaNode.
            If not given, this attribute is set to self.meta_node_id
        :param clean_current: bool, Disconnect and clean any currently connected nodes to this attribute
        :param force: bool, Force the connection of the nodes
        :param allow_incest: bool, Overrides the behaviour when dealing with child nodes that are standard native
            nodes not MetaNodes.
        :param source_simple: bool, By default when child are wired we expect arrays, so plugs in source and
            destination are index managed.
        If True, index is not used and a a single simple wire on the source attribute is used (the child)
        :param kwargs:
        """

        # Make sure that the given attribute exists on the MetaNode
        self.add_attribute(attr, attr_type='message')

        if not issubclass(type(nodes), list):
            nodes = [nodes]
        if clean_current:
            self.disconnect_current_attr_plugs(attr)  # disconnect/cleanup current plugs to this attr
        if not source_attr:
            source_attr = self.meta_node_id  # attr on the nodes source side for the child connection
        if not nodes:
            # this allows 'None' to be passed into the set attr calls and in turn, allow
            # self.mymessagelink=None to clear all current connections
            return

        for node in nodes:
            is_meta = False
            if self.is_meta_node(node=node):
                is_meta = True
                if not issubclass(type(node), MetaNode):
                    MetaNode(node).add_attribute(source_attr, attr_type='message')
                else:
                    node.add_attribute(source_attr, attr_type='message')
                    node = node.meta_node
            elif not maya.cmds.objExists('{0}.{1}'.format(node, source_attr)):
                if allow_incest:
                    MetaNode(node).add_attribute(source_attr, attr_type='message')
                else:
                    maya.cmds.addAttr(node, longName=source_attr, at='message', m=True, im=False)

            try:
                if not self.is_child_node(node=node, attr=attr, source_attr=source_attr):
                    try:
                        if is_meta or allow_incest:
                            if is_meta:
                                maya.logger.debug(
                                    'Connecting MeatNode nodes via indices: {0}.{1} >> {2}.{3}'.format(
                                        self.meta_node, attr, node, source_attr))
                            elif allow_incest:
                                maya.logger.debug(
                                    'Connecting Standard Maya nodes via indices: {0}.{1} >> {2}.{3}'.format(
                                        self.meta_node, attr, node, source_attr))
                            if not source_simple:
                                maya.cmds.connectAttr(
                                    '%s.%s[%i]' % (
                                        self.meta_node, attr, self.get_next_array_index(self.meta_node, attr)),
                                    '%s.%s[%i]' % (node, source_attr, self.get_next_array_index(node, source_attr)),
                                    f=force)
                            else:
                                maya.cmds.connectAttr('%s.%s[%i]' % (
                                    self.meta_node, attr, self.get_next_array_index(
                                        self.meta_node, attr)), '%s.%s' % (node, source_attr), f=force)
                        else:
                            maya.logger.debug(
                                'Connecting {0}.{1} >> {2}.{3}'.format(self.meta_node, attr, node, source_attr))
                            maya.cmds.connectAttr('{0}.{1}'.format(node, source_attr), f=force)
                    except Exception:
                        # If the add was originally a messageSimple, then this exception is a
                        # back-up for the previous behaviour
                        maya.cmds.connectAttr('{0}.{1}'.format(self.meta_node, attr),
                                              '{0}.{1}'.format(node, source_attr), f=force)
                else:
                    raise StandardError('"{0}" is already connected to MetaNode "{1}"'.format(node, self.meta_node))
            except StandardError as e:
                maya.logger.warning(e)

    @node_lock_manager
    def disconnect_child(self, node, attr=None, delete_source_plug=True, delete_dst_plug=True):
        """
        Disconnects a given child node from teh MetaNode. By default, it removes the connection attribute
        in the process, cleaning up both sides of the connection.
        NOTE: Attributes only are removed if nothing else is connected to it
        :param node: str, native node to disconnect from the metaNode
        :param attr: str
        :param delete_source_plug: bool, If True, delete source side attribute after disconnection but only
        if it's no longer connected to anything else
        :param delete_dst_plug: bool, If True, delete the destination side attribute after disconnection but only
        if it's no longer connected to anything else
        :return:
        """

        source_plug = None
        dst_plug = None
        source_plug_meta = None
        return_data = list()

        search_connection = '%s.' % self.meta_node.split('|')[-1]
        if attr:
            search_connection = '%s.%s' % (self.meta_node.split('|')[-1], attr)

        if self.is_meta_node(node=node):
            source_plug_meta = node
            node = node.meta_node

        connections = maya.cmds.listConnections(node, source=True, destination=False, plugs=True, connections=True)
        if not connections:
            raise StandardError('{0} is not connected to the MetaNode {1}'.format(node, self.meta_node))

        for source_plug, dst_plug in zip(connections[0::2], connections[1::2]):
            maya.logger.debug('Attribute Connection Inspected: {0} << {1}'.format(source_plug, dst_plug))
            if (attr and search_connection == dst_plug.split('[')[0]) or (not attr and search_connection in dst_plug):
                maya.logger.debug('Disconnecting {0} >> {1} as {2} found in destination plug'.format(
                    dst_plug, source_plug, search_connection))
                maya.cmds.disconnectAttr(dst_plug, source_plug)
                return_data.append((dst_plug, source_plug))

        if delete_source_plug:
            try:
                allow_delete = True
                attr = source_plug.split('[')[0]  # split any multi-indexing from the plug ie node.attr[0]
                if maya.cmds.listConnections(attr):
                    allow_delete = False
                    maya.logger.debug(
                        'SourceAttr connections remaining: {0}'.format(','.join(maya.cmds.listConnections(attr))))
                if allow_delete:
                    maya.logger.debug('Deleting SourcePlug Attr {}'.format(attr))
                    if source_plug_meta:
                        delattr(source_plug_meta, attr.split('.')[-1])
                    else:
                        maya.cmds.deleteAttr(attr)
                else:
                    maya.logger.debug('Deleting SourcePlug Attr aborted as node still has connections!')
            except StandardError as e:
                maya.logger.warning('Failed to remove MetaNode Connection Attribute')
                maya.logger.debug(e)

        if delete_dst_plug:
            try:
                allow_delete = True
                attr = source_plug.split('[')[0]  # split any multi-indexing from the plug ie node.attr[0]
                if maya.cmds.listConnections(attr):
                    allow_delete = False
                    maya.logger.debug(
                        'DstPlug connections remaining: {0}'.format(','.join(maya.cmds.listConnections(attr))))
                if allow_delete:
                    maya.logger.debug('Deleting DstPug Attr {}'.format(attr))
                    delattr(source_plug_meta, attr.split('.')[-1])
                else:
                    maya.logger.debug('Deleting SourcePlug Attr aborted as node still has connections!')
            except StandardError as e:
                maya.logger.warning('Failed to remove MetaNode Connection Attribute')
                maya.logger.debug(e)

        return return_data

    def connect_parent(self):
        pass

    def connect_parent_node(self, node, attr, connect_back=None, source_attr=None):
        """
        Alternative connect parent method that support the connection of message connections
        Used to connect message links to Meta Nodes as parents
        :param node: Maya node to connect to this MetaNode
        :param attr: str, name for the message attribute to connect to the parent
        :param connect_back: bol
        :param source_attr: str, If given, this becomes the attribute on the node which connects to the
        parent. If not given, the connection attribute is the parent.message attribute
        :return: bool
        """

        if issubclass(type(node), MetaNode):
            node = node.meta_node

        metautils.MetaAttributeUtils.set_message(self.meta_node, attr, node)

        if connect_back is not None:
            metautils.MetaAttributeUtils.set_message(node, connect_back, self.meta_node)

        return True

    def get_message(self, attr, full_path=True, as_meta=False, data_attr=None, data_key=None, simple=True, *args,
                    **kwargs):
        """
        Standard nodes are treated as regular message connections but sometimes you want a message like connection
        to an attribute. To do this, we devised a method of creating a compatible attr on the object to receive
        the message, connecting the attribute you want to connect to that attribute and then when you call an attribute
        as getMessage, if it is not a message attr it tries to trace back that connection to an attribute.
        simple MUST be True by default
        :param attr:
        :param full_path:
        :param as_meta:
        :param data_attr:
        :param data_key:
        :param simple:
        :param args:
        :param kwargs:
        :return:
        """

        result = metautils.MetaAttributeUtils.get_message(
            self.meta_node, attr, data_attr=data_attr, data_key=data_key, simple=simple)

        if as_meta and result:
            return validate_obj_list_arg(result)
        if result and full_path:
            return [name_utils.get_long_name(o) for o in result]

        return result

    def message_list_get_message(self, *args, **kwargs):
        """
        Returns messageList
        :param args:
        :param kwargs:
        :return:
        """

        return metautils.MetaMessageListUtils.message_list_get(self.meta_node, *args, **kwargs)

    def message_list_get(self, *args, **kwargs):
        """
        Returns messageList
        :param args:
        :param kwargs:
        :return:
        """

        return metautils.MetaMessageListUtils.message_list_get(self.meta_node, *args, **kwargs)

    def message_list_connect(self, *args, **kwargs):
        """
        Append node to messageList
        :param args:
        :param kwargs:
        :return:
        """

        return metautils.MetaMessageListUtils.message_list_connect(self.meta_node, *args, **kwargs)

    def message_list_append(self, *args, **kwargs):
        """
        Append node to messageList
        :param args:
        :param kwargs:
        :return:
        """

        return metautils.MetaMessageListUtils.message_list_append(self.meta_node, *args, **kwargs)

    def message_list_index(self, *args, **kwargs):
        """
        Returns the index of a node if its on a messageList
        :param args:
        :param kwargs:
        :return: int
        """

        return metautils.MetaMessageListUtils.message_list_index(self.meta_node, *args, **kwargs)

    def message_list_exists(self, *args, **kwargs):
        """
        Checks if we have data on this attribute list
        :param args:
        :param kwargs:
        :return: bool
        """

        return metautils.MetaMessageListUtils.message_list_exists(self.meta_node, *args, **kwargs)

    def message_list_remove(self, *args, **kwargs):
        """
        Removes an index from the messageList
        :param args:
        :param kwargs:
        :return: bool
        """

        return metautils.MetaMessageListUtils.message_list_remove(self.meta_node, *args, **kwargs)

    def message_list_clean(self, *args, **kwargs):
        """
        Removes empty entries and pushes back
        :param args:
        :param kwargs:
        :return: bool
        """
        return metautils.MetaMessageListUtils.message_list_clean(self.meta_node, *args, **kwargs)

    def message_list_purge(self, *args, **kwargs):
        """
        Purges all the attributes of a msgList
        :param args:
        :param kwargs:
        :return:
        """

        return metautils.MetaMessageListUtils.message_list_purge(self.meta_node, *args, **kwargs)

    def get_sequential_attr_dict(self, attr=None):
        """
        Returns a sequential attr dict
        :param attr: jstr
        :return: list<str>
        """

        return metautils.MetaDataListUtils.get_sequential_attr_dict(node=self.meta_node, attr=attr)

    def get_components_by_type(self, component_type=False, flatten=True):
        """
        Returns components of the given type
        :param component_type: str, component type to query (vtx, face, edge, etc)
        :param flatten: bool, Whether to flatten the list or not
        :return: list<str>
        """

        return maya.cmds.ls(['{}.{}'.format(self.meta_node, component_type)], flatten=flatten)

    def get_maya_attr(self, *args, **kwargs):
        """
        Returns Maya attribute of the current node
        :param args: list
        :param kwargs: dict
        :return:
        """

        return metautils.MetaAttributeUtils.get(self.meta_node, *args, **kwargs)

    def get_maya_attr_string(self, attr=None, name_call='long'):
        """
        Returns Mata attribute in string form
        :param attr:
        :param name_call:
        :return: str
        """

        from tpDcc.dccs.maya.core import name

        return '{}.{}'.format(getattr(name, name_call)(self.meta_node), attr)

    def connect_out_attribute(self, attr=None, target=None, lock=False):
        """
        Connects attribute to given targets attributes on our node
        :param attr: str
        :param target: str or list
        :param lock: bool
        :return: bool
        """

        if not metautils.MetaAttributeValidator.is_list_arg(target):
            target = [target]

        result = list()
        for t in target:
            if '.' in t:
                result.append(metautils.MetaAttributeUtils.connect(self.get_maya_attr_string(attr), t, lock))
            else:
                result.append(
                    metautils.MetaAttributeUtils.connect(
                        self.get_maya_attr_string(attr), self.get_maya_attr_string(t), lock))

        return result


# ==============================================================================================================


def get_mobject(meta_node):
    """
    Base method to get the MObject from node
    """

    mobj = maya.OpenMaya.MObject()
    sel = maya.OpenMaya.MSelectionList()
    sel.add(meta_node)
    sel.getDependNode(0, mobj)
    return mobj


def attribute_data_type(value):
    """
    Validates the attribute type
    :param value: variant, value to check type for
    :return: str, type string
    """

    python_types = [str, unicode, bool, int, float, dict, list, tuple]
    valid_types = ['string', 'unicode', 'bool', 'int', 'float', 'complex', 'complex', 'complex']
    for py_type, valid_type in zip(python_types, valid_types):
        if issubclass(type(value), py_type):
            maya.logger.debug('Value {0} is a "{1}" attribute'.format(py_type, valid_type))
            return valid_type


def serialize_json_attr(data):
    """
    Serializes data such as dicts to a JSON string
    :param data: variant
    :return: str, bool, serialized data and True if the data has a size over 32000 or False otherwise
    If the data has a size bigger than 32000 (16 bit) the attr must be locked to avoid Maya to delete
    data when the attr is selected on Maya attribute editor
    """

    if len(data) > 32700:
        return json.dumps(data), True
    else:
        return json.dumps(data), False


def deserialize_json_attr(data):
    """
    Deserialize data from a JSON string back to it's original data
    :param data: str
    :return: str
    """

    if type(data) == unicode:
        return json.loads(str(data))
    return json.loads(data)


def validate_obj_arg(node, meta_class, none_valid=False, default_meta_type=None, maya_type=None, update_class=False):
    """
    Validates a given node to be able to get an instance of the object
    :param node: variant, MetaNode || str
    :param meta_class: str, what type of meta class we are looking for
    :param none_valid: bool, Whether None is a valid argument or not
    :param default_meta_type: MetaClass - What type to initialize if no MetaClass is set
    :param maya_type: variant, str || ist, If the object needs to be a certain object type
    :param update_class: bool, True to update the class of the given node if necessary
    """

    meta_classes_register = metadatamanager.METANODE_CLASSES_REGISTER

    # Check if given MetaClass is valid
    if meta_class is not None:
        t1 = time.clock()
        if not type(meta_class) in [unicode, str]:
            try:
                meta_class = meta_class.__name__
            except Exception as e:
                raise ValueError('MetaClass not a string and is not a usable MetaClass name: {}'.format(meta_class))

        if meta_class not in meta_classes_register:
            raise ValueError('Given class it not in the MetaClass Registry: {}'.format(meta_class))
        t2 = time.clock()
        maya.logger.debug('Initial meta_class ... %0.6f' % (t2 - t1))

    # Check if given node is a valid node
    node_arg = type(node)
    if node_arg in [list, tuple]:
        if len(node) == 1:
            node = node[0]
        elif node == []:
            node = None
        else:
            raise ValueError('Node cannot be list or tuple or longer than 1 length: {}'.format(node))

    # Check node None validity
    if not none_valid:
        if node in [None, False]:
            raise ValueError('Invalid node({}). none_valid = False'.format(node))
    else:
        if node in [None, False]:
            return False

    try:
        node.meta_node
        meta_node = node
        _node = node.meta_node
        maya.logger.debug('Node {} is already a MetaNode instance'.format(node))
    except Exception:
        maya.logger.debug('Node {} is not a MetaNode instance yet'.format(node))
        try:
            _node = name_utils.get_long_name(obj=node)
        except Exception as e:
            return False
    if not _node:
        if none_valid:
            return False
        else:
            raise ValueError('{} is not valid node. Validated to {}'.format(node, _node))

    _node_short = name_utils.get_short_name(obj=_node)
    maya.logger.debug('Checking: {0} | MetaClass: {1}'.format(_node, meta_class))
    new_meta_class = meta_classes_register.get(meta_class)

    # Check if we need to force Maya type
    if maya_type is not None and len(maya_type):
        t1 = time.clock()
        maya.logger.debug('Checking Maya Type ...')
        if type(maya_type) not in [tuple, list]:
            maya_types_list = [maya_type]
        else:
            maya_types_list = maya_type
        str_type = metautils.MetaAttributeValidator.get_maya_type(_node)
        if str_type not in maya_types_list:
            if none_valid:
                maya.logger.warning('"{}" maya_type: "{}" not in "{}"'.format(_node_short, str_type, maya_types_list))
                return False
            raise StandardError('"{}" maya_type: "{}" not in "{}"'.format(_node_short, str_type, maya_types_list))
        t2 = time.clock()
        maya.logger.debug('maya_type not None time ... % 0.6f' % (t2 - t1))

    node_meta_class = metautils.MetaAttributeUtils.get(_node_short, 'meta_class')

    newUUID = False
    uuid = False
    try:
        newUUID = maya.cmds.ls(_node_short, uuid=True)[0]
    except Exception:
        pass

    if newUUID:
        maya.logger.debug('>2016 UUID: {}'.format(uuid))
        uuid = newUUID
        try:
            metautils.MetaAttributeUtils.delete(_node_short, 'UUID')
            maya.logger.debug('Clearing UUID attr ...')
        except Exception:
            pass
    else:
        uuid = metautils.MetaAttributeUtils.get(_node_short, 'UUID')

    maya.logger.debug('Cache Keys || UUID: {0} | MetaClass: {1}'.format(uuid, node_meta_class))
    was_cached = False

    current_metaclases_keys = metadatamanager.METANODES_CACHE.keys()
    cache_key = None
    cached = None
    unicode_node = unicode(_node)

    if uuid in current_metaclases_keys:
        cache_key = uuid
        cached = metadatamanager.METANODES_CACHE.get(uuid)
    elif unicode_node in current_metaclases_keys:
        cache_key = unicode_node
        cached = metadatamanager.METANODES_CACHE.get(unicode_node)

    maya.logger.debug('Cached Key: {}'.format(cache_key))

    if cached is not None:
        maya.logger.debug('Given Node is already cached!')
        cached_meta_class = metautils.MetaAttributeUtils.get(_node, 'meta_class') or False
        cached_type = type(cached)
        maya.logger.debug('Cached MetaNode: {}'.format(cached.meta_node))
        maya.logger.debug('Cached MetaClass: {}'.format(cached_meta_class))
        maya.logger.debug('Cached Type: {}'.format(cached_type))
        change = False
        redo = False

        if _node != cached.meta_node:
            maya.logger.debug('MetaNodes do not match! Need new UUID ...')
            maya.logger.debug('Clearing current UUID ...')
            try:
                metautils.MetaAttributeUtils.set(_node_short, 'UUID', '')
            except Exception:
                pass
            redo = True
        elif cached_type == new_meta_class:
            maya.logger.debug(
                'Cached Type ({0}) match with new given MetaClass ({1})'.format(cached_type, new_meta_class))
            if update_class and not cached_meta_class:
                maya.logger.debug('Trying to update given node with UUID and meta_class attributes')
                try:
                    metautils.MetaAttributeUtils.add(_node_short, 'meta_class', 'string')
                except Exception:
                    pass
                try:
                    metautils.MetaAttributeUtils.add(_node_short, 'UUID', 'string')
                except Exception:
                    pass
                metautils.MetaAttributeUtils.set(_node_short, 'meta_class', meta_class, True)
            return cached
        elif cached_meta_class:
            if meta_class is not None:
                if cached_type != new_meta_class:
                    maya.logger.debug('Cached Type does not match ({})'.format(new_meta_class))
                    change = True
                elif cached_meta_class != meta_class:
                    maya.logger.debug(
                        'Cached Type ({0}) does not match with new given MetaClass ({1})'.format(
                            cached_meta_class, meta_class))
                    change = True
        elif new_meta_class:
            maya.logger.debug('No cached MetaClass or type')
            try:
                if issubclass(type(cached), new_meta_class):
                    maya.logger.debug('Subclass match')
                    change = False
                    if update_class:
                        maya.logger.debug('SubClass match not good enough')
                        change = True
            except Exception as e:
                maya.logger.warning('Cached subclass check failed | {}'.format(e))
                change = True

        if change:
            try:
                if issubclass(cached_type, new_meta_class) and not update_class:
                    change = False
            except Exception as e:
                maya.logger.warning('Cached Type: {}'.format(cached_type))
                maya.logger.warning('New Meta Class: {}'.format(new_meta_class))
                maya.logger.warning('Change cached subclass check failed | {}'.format(e))

        if not change and not redo:
            return cached
        elif change:
            if not update_class:
                return False

            maya.logger.debug('Cleaning current MetaNode Data from {}'.format(node))
            was_cached = True
            if cached_meta_class:
                maya.logger.debug('Clearing current node MetaClass ...')
                metautils.MetaAttributeUtils.delete(_node_short, 'meta_class')
            if uuid:
                maya.logger.debug('Clearing current node UUID ...')
                metautils.MetaAttributeUtils.delete(_node_short, 'UUID')
            maya.logger.debug('Removing MetaNode UUID from MetaNodes register!')
            metadatamanager.METANODES_CACHE.pop(cache_key)

    if meta_class:
        if update_class or was_cached:
            maya.logger.debug('Updating current MetaClass ({0}) to new MetaClass ({1})'.format(
                node_meta_class, new_meta_class.__name__))
            try:
                metautils.MetaAttributeUtils.add(_node_short, 'meta_class', 'string')
            except Exception:
                pass
            try:
                if not newUUID:
                    metautils.MetaAttributeUtils.add(_node_short, 'UUID', 'string')
            except Exception:
                pass
            metautils.MetaAttributeUtils.set(_node_short, 'meta_class', meta_class, True)

        node_meta_class = metautils.MetaAttributeUtils.get(_node_short, 'meta_class')
        if node_meta_class and node_meta_class not in meta_classes_register:
            raise ValueError('Stored MetaClass not found in MetaClass registry. MetaClass: {}'.format(node_meta_class))
        meta_node = new_meta_class(_node_short)
    else:
        if node_meta_class:
            if node_meta_class not in meta_classes_register:
                raise ValueError(
                    'Stored MetaClass not found in MetaClass registry. MetaClass: {}'.format(node_meta_class))
            new_meta_class = meta_classes_register.get(node_meta_class)
            maya.logger.debug('MetaClass registered: {0} | {1}'.format(_node_short, node_meta_class))
            meta_node = new_meta_class(_node_short)
        else:
            if default_meta_type:
                if not type(default_meta_type) in [unicode, str]:
                    try:
                        default_meta_type = default_meta_type.__name__
                    except Exception as e:
                        raise ValueError(
                            'Meta Type is not a string and is not a usable class name. Default MetaType: {}'.format(
                                default_meta_type))
                try:
                    meta_node = meta_classes_register.get(default_meta_type)(_node_short)
                except Exception as e:
                    raise Exception('Default MetaType ({0}) initialization failed | {1}'.format(default_meta_type, e))
            elif metautils.MetaAttributeValidator.is_transform(_node_short):
                try:
                    from tpDcc.dccs.maya.meta import metaobject
                    meta_node = metaobject.MetaObject(_node_short)
                except Exception as e:
                    raise Exception('MetaObject initialized failed | {}'.format(e))
            else:
                try:
                    meta_node = MetaNode(_node_short)
                except Exception as e:
                    raise Exception('MetaNode initialization failed | {}'.format(e))

    maya.logger.debug('Returning {}'.format(meta_node))
    return meta_node


def validate_obj_list_arg(list_arg=None, meta_class=None, none_valid=False, default_meta_type=None, maya_type=None,
                          update_class=False):
    if type(list_arg) not in [list, tuple]:
        list_arg = [list_arg]

    return_list = list()
    kwargs = {'meta_class': meta_class, 'none_valid': none_valid, 'default_meta_type': default_meta_type,
              'maya_type': maya_type, 'update_class': update_class}
    for arg in list_arg:
        buffer = validate_obj_arg(arg, **kwargs)
        if buffer:
            return_list.append(buffer)

    return return_list


# ===================================================================================================================


# CUSTOM META DATA EXAMPLE
class CustomMetaNode(MetaNode, object):
    def __init__(self, *args, **kwargs):
        super(CustomMetaNode, self).__init__(*args, **kwargs)

        if self.cached:
            print('Using cached version ...')
            return

        print('This is from CustomMetaClass : {0}'.format(self))

    @staticmethod
    def count_to(value=1):
        for i in range(value):
            print(i)
        return 'Done'

    def __bind_data__(self):
        print('In bind ...')
        self.add_attribute(attr='really_important_stuff', value=77)
