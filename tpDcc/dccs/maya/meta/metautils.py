#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with meta system
"""

import copy
import pprint
import logging

import tpDcc.dccs.maya as maya
from tpDcc.libs.python import decorators
from tpDcc.dccs.maya.core import common, attribute as attr_utils, name as name_utils, shape as shape_utils

LOGGER = logging.getLogger()


class MetaAttributeValidator(attr_utils.AttributeValidator):
    """
    Utility class that contains functions to check if a DCC node attributes are valid or not
    """

    @staticmethod
    def meta_node_string(arg):
        """
        Returns given argument meta node if possible
        :return: arg
        """

        try:
            arg = arg.meta_node
        except Exception:
            pass

        return arg

    @staticmethod
    def meta_node_string_list(string_list):
        """
        Returns  list of arguments with their meta nodes if possible
        :param string_list:
        :return:
        """

        string_list = MetaAttributeValidator.list_arg(string_list)
        result = list()
        for obj in string_list:
            try:
                obj = obj.meta_node
            except Exception:
                pass
            result.append(obj)

        return result

    @staticmethod
    def shape_arg(node=None, types=None, single_return=False):
        """
        Returns arg if args is a Maya shape node else returns shapes of given node
        :param node: variant, value to valid as a Maya shape node
        :param types: valid types if you want validation
        :param single_return: True if you only want to return first
        :return: bool
        """

        try:
            node = node.meta_node
        except Exception:
            pass

        return attr_utils.AttributeValidator.shape_arg(node=node, types=types, single_return=single_return)

    @staticmethod
    def is_component(arg=None):
        """
        Returns whether given node is a component or not
        :param node: str
        :return: bool
        """

        arg = MetaAttributeValidator.meta_node_string(arg)
        return attr_utils.AttributeValidator.is_component(arg)


class MetaAttributeUtils(object):
    """
    Utility class that contains functions to work with meta nodes attributes
    """

    attr_types = dict(message=('message', 'msg', 'm'),
                      double=('float', 'fl', 'f', 'doubleLinear', 'doubleAngle', 'double', 'd'),
                      string=('string', 's', 'str'), long=('long', 'int', 'i', 'integer'), short=('short', 'shrt'),
                      bool=('bool', 'b', 'boolean'), enum=('enum', 'options', 'e'),
                      double3=('double3', 'd3', 'vector', 'vec', 'v'),
                      float3=('vector', 'vec'), multi=('multi', 'm'))

    # region Public Functions
    @classmethod
    def validate_attr_type_name(cls, attr_type):
        """
        Validates an attribute type by converting the given attribute type to a valid one if possible
        :param attr_type: str, attribute type
        :return: variant, str(validated type) || bool
        """

        for option in cls.attr_types.keys():
            if attr_type == option:
                return option
            if attr_type in cls.attr_types.get(option):
                return option

        return False

    @classmethod
    def validate_attr_type_match(cls, type_a, type_b):
        """
        Returns True if bot attribute types given match or False otherwise
        :param type_a: str
        :param type_b: str
        :return:  bool
        """

        if type_a == type_b:
            return True

        for o in cls.attr_types.keys():
            if type_a in cls.attr_types.get(o) and type_b in cls.attr_types.get(o):
                return True

        return False

    # endregion

    # region Abstract Functions
    @staticmethod
    @decorators.abstractmethod
    def validate_attribute(*args):
        """
        Validates given attribute and check if the given attributes is valid or not
        :param args:
        """

        if len(args) == 1:
            # LOGGER.debug('|Attribute Validation| >> single argument')
            if issubclass(type(args[0]), dict):
                # LOGGER.debug('|Attribute Validation| >> dict argument')
                if args[0].get('combined'):
                    # LOGGER.debug('|Attribute Validation| >> passed validating arg, returning it ...')
                    return args[0]
                raise ValueError('Given argument is not a valid dictionary: {}'.format(args[0]))
            elif type(args[0]) in [list, tuple] and len(args[0]) == 2:
                # LOGGER.debug('|Attribute Validation| >> list argument')
                if hasattr(args[0][0], 'meta_node'):
                    obj = args[0][0].meta_node
                else:
                    obj = args[0][0]
                attr = args[0][1]
                combined = '{0}.{1}'.format(obj, attr)
            elif '.' in args[0]:
                # LOGGER.debug('|Attribute Validation| >> string argument')
                obj = args[0].split('.')[0]
                attr = '.'.join(args[0].split('.')[1:])
                combined = args[0]
            else:
                raise ValueError('Invalid attribute argument: {}'.format(args))
        else:
            # LOGGER.debug('|Attribute Validation| >> multi argument')

            if hasattr(args[0], 'meta_node'):
                args[0] = args[0].meta_node

            combined = '{0}.{1}'.format(args[0], args[1])
            obj = args[0]
            attr = args[1]

        return {'node': obj, 'obj': obj, 'attr': attr, 'combined': combined}

    @staticmethod
    @decorators.abstractmethod
    def get_type(*args):
        """
        Returns given attribute type
        :param args: dict, validated argument
        :return: str
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            return maya.cmds.getAttr(attr_dict['combined'], type=True)
        except Exception as e:
            LOGGER.error('|Attribute Type Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

    @staticmethod
    @decorators.abstractmethod
    def convert_type(node=None, attr=None, attr_type=None, *args):
        """
        Attempts to convert an existing attribute type from one type to another
        Enums are stored to string as 'option1;option2'
        Strings with a ';' will split to enum options during conversion
        :param node: str
        :param attr: str
        :param attr_type: str
        :return: bool
        """

        _attr_type = attr_type
        if '.' in node or issubclass(type(node), dict):
            attr_dict = MetaAttributeUtils.validate_attribute(*args)
            _attr_type = attr
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(node, attr)
        combined = attr_dict['combined']

        _attr_type = MetaAttributeUtils.validate_attr_type_name(_attr_type)
        _type_current = MetaAttributeUtils.validate_attr_type_name(MetaAttributeUtils.get_type(attr_dict))

        LOGGER.debug(
            '|Convert Attribute Type| >> attr: {0} | type: {1} | target_type: {2}'.format(
                combined, _type_current, _attr_type))

        if _attr_type == _type_current:
            LOGGER.debug('|Convert Attribute Type| >> {} already target type'.format(combined))
            return True

        # ============================================== Data Gathering
        lock = False
        if MetaAttributeUtils.is_locked(attr_dict):
            lock = True
            maya.cmds.setAttr(combined, lock=False)

        _driver = MetaAttributeUtils.get_driver(attr_dict, skip_conversion_nodes=True)
        _driven = MetaAttributeUtils.get_driven(attr_dict, skip_conversion_nodes=True)
        _enum = 'off', 'on'

        if _type_current == 'enum':
            _enum = MetaAttributeUtils.get_enum(attr_dict).split(':')
        if _type_current == 'message':
            _data = MetaAttributeUtils.get_message(attr_dict)
        elif _type_current == 'enum':
            _data = MetaAttributeUtils.get_enum(attr_dict)
        else:
            _data = MetaAttributeUtils.get(attr_dict)

        MetaAttributeUtils.delete(attr_dict)

        # ============================================== Data Rebuild

        if _attr_type == 'enum':
            if _data:
                if MetaAttributeValidator.string_arg(_data):
                    for o in [":", ",", ";"]:
                        if o in _data:
                            _enum = _data.split(o)
                            break

        MetaAttributeUtils.add(attr_dict, attr_type, enum_options=_enum)

        if _data is not None:
            LOGGER.debug('|Convert Attribute Type| >> Data Setting: {}'.format(_data))
            try:
                if _attr_type == 'string':
                    if _type_current == 'message':
                        _data = ','.join(_data)
                    else:
                        _data = str(_data)
                elif _attr_type == 'double':
                    _data = float(_data)
                elif _attr_type == 'long':
                    _data = int(_data)
            except Exception as e:
                LOGGER.error(
                    '|Convert Attribute Type| >> Failed to convert data: {0} | type: {1} | err: {2}'.format(
                        _data, _attr_type, e))

            try:
                MetaAttributeUtils.set(attr_dict, value=_data)
            except Exception as e:
                LOGGER.error(
                    '|Convert Attribute Type| >> Failed to set back data buffer {0} | data: {1} | err: {2}'.format(
                        combined, _data, e))

        if _driver and _type_current != 'message':
            LOGGER.debug('|Convert Attribute Type| >> Driver: {}'.format(_driver))
            try:
                MetaAttributeUtils.connect(_driver, combined)
            except Exception as e:
                LOGGER.debug(
                    '|Convert Attribute Type| >> Failed to connect {0} >> {1} | err: {2}'.format(_driver, combined, e))

        if _driven:
            LOGGER.debug('|Convert Attribute Type| >> Driven: {}'.format(_driven))
            for c in _driven:
                LOGGER.debug('|Convert Attribute Type| >> driven: {}'.format(c))
                try:
                    MetaAttributeUtils.connect(combined, c)
                except Exception as e:
                    LOGGER.debug(
                        '|Convert Attribute Type| >> Failed to connect {0} >> {1} | err: {2}'.format(combined, c, e))

        if lock:
            maya.cmds.setAttr(combined, lock=True)

        return True

    @staticmethod
    @decorators.abstractmethod
    def get(*args, **kwargs):
        """
        Get attribute for the given DCC node
        :param args: dict, validated argument
        :param kwargs:
        :return:
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        combined = attr_dict['combined']
        obj = attr_dict['obj']
        attr = attr_dict['attr']

        if kwargs:
            if not kwargs.get('sl') or not kwargs.get('silent'):
                kwargs['sl'] = True

        LOGGER.debug('|Attribute Getter| >> arg: {}'.format(args))
        if kwargs:
            LOGGER.debug('|Attribute Getter| >> kwargs: {}'.format(kwargs))

        if '[' in attr:
            LOGGER.debug('|Attribute Getter| >> Indexed Attribute')
            return maya.cmds.listConnections(combined)

        try:
            attr_type = maya.cmds.getAttr(combined, type=True)
        except Exception as e:
            LOGGER.debug(
                '|Attribute Getter| >> {0} failed to return type. Exists: {1}'.format(combined, maya.cmds.objExists(
                    combined)))
            return None

        if attr_type in ['TdataCompound']:
            return maya.cmds.listConnections(combined)

        if maya.cmds.attributeQuery(attr, node=obj, msg=True):
            return MetaAttributeUtils.get_message(message_attr=attr_dict)
        elif attr_type == 'double3':
            return [maya.cmds.getAttr(obj + '.' + arg) for arg in
                    maya.cmds.attributeQuery(attr, node=obj, listChildren=True)]
        else:
            return maya.cmds.getAttr(combined, **kwargs)

    @staticmethod
    @decorators.abstractmethod
    def get_driver(node, attr=None, get_node=False, skip_conversion_nodes=False, long_names=True):
        """
        Get the driver of an attribute if exists
        :param node: str
        :param attr: str
        :param get_node: bool, True if you want the DAG node or the attribute(s) or False otherwise
        :param skip_conversion_nodes: bool, True if you want conversion nodes included in query or False otherwise
        :param long_names: bool, True if you want the data returned name wise
        :return: str, driver attr
        """

        if attr is None:
            attr_dict = MetaAttributeUtils.validate_attribute(node)
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(node, attr)
        combined = attr_dict['combined']

        if not MetaAttributeUtils.is_connected(attr_dict):
            return False

        if get_node:
            connections = maya.cmds.listConnections(combined, skipConversionNodes=skip_conversion_nodes,
                                                    destination=False, source=True, plugs=False)
            if not connections:
                parent = MetaAttributeUtils.get_parent(attr_dict)
                if parent:
                    LOGGER.debug('|Driver Attribute Getter| >> Parent Attribute Check: {}'.format(parent))
                    return MetaAttributeUtils.get_driver(attr_dict['node'], parent, get_node=get_node,
                                                         skip_conversion_nodes=skip_conversion_nodes,
                                                         long_names=long_names)
                return False
            if long_names:
                return name_utils.get_long_name(obj=connections[0])
            else:
                return name_utils.get_short_name(obj=connections[0])
        else:
            if maya.cmds.connectionInfo(combined, isDestination=True):
                connections = maya.cmds.listConnections(combined, skipConversionNodes=skip_conversion_nodes,
                                                        destination=False, source=True, plugs=True)
                if not connections:
                    connections = [maya.cmds.connectionInfo(combined, sourceFromDestination=True)]
                if connections:
                    if skip_conversion_nodes and MetaAttributeValidator.get_maya_type(
                            node=connections) == 'unitConversion':
                        parent = MetaAttributeUtils.get_parent(attr_dict)
                        if parent:
                            LOGGER.debug('|Driver Attribute Getter| >> Parent Attribute Check: {}'.format(parent))
                            return MetaAttributeUtils.get_driver(attr_dict['node'], parent, get_node=get_node,
                                                                 skip_conversion_nodes=skip_conversion_nodes,
                                                                 long_names=long)
                    if long_names:
                        return name_utils.get_long_name(obj=connections[0])
                    else:
                        return name_utils.get_short_name(obj=connections[0])
                return False

        return False

    @staticmethod
    @decorators.abstractmethod
    def get_driven(node, attr=None, get_node=False, skip_conversion_nodes=False, long_names=True):
        """
        Get attributes driven by an attribute
        :param node: str
        :param attr: str
        :param get_node: bool, True if you want the DAG node or the attribute(s) or False otherwise
        :param skip_conversion_nodes: bool, True if you want conversion nodes included in query or False otherwise
        :param long_names: bool, True if you want the data returned name wise
        :return: str, driven attrs
        """

        if attr is None:
            attr_dict = MetaAttributeUtils.validate_attribute(node)
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(node, attr)
        combined = attr_dict['combined']

        if get_node:
            connections = maya.cmds.listConnections(combined, skipConversionNodes=skip_conversion_nodes,
                                                    destination=True, source=False, plugs=False)
            if not connections:
                return False
            if long_names:
                return [name_utils.get_long_name(o) for o in connections]
            else:
                return [name_utils.get_short_name(o) for o in connections]
        else:
            if maya.cmds.connectionInfo(combined, isSource=True):
                connections = maya.cmds.listConnections(combined, skipConversionNodes=skip_conversion_nodes,
                                                        destination=True, source=False, plugs=True)
                if not connections:
                    connections = maya.cmds.connectionInfo(combined, destinationFromSource=True)
                if connections:
                    connections_list = list()
                    for cnt in connections:
                        if long_names:
                            connections_list.append(name_utils.get_long_name(cnt))
                        else:
                            connections_list.append(name_utils.get_short_name(cnt))
                    return connections_list
                return False

        return False

    @staticmethod
    @decorators.abstractmethod
    def add(obj, attr=None, attr_type=None, enum_options=['off', 'on'], *args, **kwargs):
        """
        Add a new attribute to the given object
        :param obj: str, object to add attribute to
        :param attr: str, attribute name
        :param attr_type: str, valid type
        :param enum_options: list<str>, list of option for enum attribute types
        :return: str, added attribute name
        """

        try:
            if enum_options is None:
                enum_options = ['off', 'on']

            if '.' in obj or issubclass(type(obj), dict):
                attr_dict = MetaAttributeUtils.validate_attribute(obj)
                attr_type = attr
            else:
                attr_dict = MetaAttributeUtils.validate_attribute(obj, attr)

            combined = attr_dict['combined']
            node = attr_dict['node']
            attr_name = attr_dict['attr']
            if maya.cmds.objExists(combined):
                raise ValueError('{} already exists!'.format(combined))

            _type = MetaAttributeUtils.validate_attr_type_name(attr_type=attr_type)
            assert _type is not False, '"{}" is not a valid attribute type'.format(attr_type)

            if _type == 'string':
                maya.cmds.addAttr(node, ln=attr_name, dt='string', *args, **kwargs)
            elif _type == 'double':
                maya.cmds.addAttr(node, ln=attr_name, at='float', *args, **kwargs)
            elif _type == 'long':
                maya.cmds.addAttr(node, ln=attr_name, at='long', *args, **kwargs)
            elif _type == 'double3':
                maya.cmds.addAttr(node, ln=attr_name, at='double3', *args, **kwargs)
                maya.cmds.addAttr(node, ln=(attr_name + 'X'), p=attr_name, at='double', *args, **kwargs)
                maya.cmds.addAttr(node, ln=(attr_name + 'Y'), p=attr_name, at='double', *args, **kwargs)
                maya.cmds.addAttr(node, ln=(attr_name + 'Z'), p=attr_name, at='double', *args, **kwargs)
            elif _type == 'enum':
                if type(enum_options) in [list, tuple]:
                    enum_options = '%s' % (':'.join(enum_options))
                maya.cmds.addAttr(node, ln=attr_name, at='enum', en=enum_options, *args, **kwargs)
                maya.cmds.setAttr((node + '.' + attr_name), e=True, keyable=True)
            elif _type == 'bool':
                maya.cmds.addAttr(node, ln=attr_name, at='bool', *args, **kwargs)
                maya.cmds.setAttr((node + '.' + attr_name), edit=True, channelBox=True)
            elif _type == 'message':
                maya.cmds.addAttr(node, ln=attr_name, at='message', *args, **kwargs)
            elif _type == 'float3':
                maya.cmds.addAttr(node, ln=attr_name, at='float3', *args, **kwargs)
                maya.cmds.addAttr(node, ln=(attr_name + 'X'), p=attr_name, at='float', *args, **kwargs)
                maya.cmds.addAttr(node, ln=(attr_name + 'Y'), p=attr_name, at='float', *args, **kwargs)
                maya.cmds.addAttr(node, ln=(attr_name + 'Z'), p=attr_name, at='float', *args, **kwargs)
            else:
                raise ValueError('Unknown attribute type: {}'.format(attr_type))

            return combined
        except Exception as e:
            LOGGER.error(str(e))

    @staticmethod
    def set(node, attr=None, value=None, lock=False, **kwargs):
        """
        Sets an existing attribute of the given object
        :param node: str, object to set attribute of
        :param attr: str, attribute name
        :param value: variant
        :param lock: bool, True if the attribute must be locke after setting it or False otherwise
        :param kwargs:
        :return: value
        """

        if '.' in node or issubclass(type(node), dict):
            attr_dict = MetaAttributeUtils.validate_attribute(node)
            if value is None and attr is not None:
                value = attr
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(node, attr)

        combined = attr_dict['combined']
        obj = attr_dict['node']
        attr_name = attr_dict['attr']
        was_locked = False

        LOGGER.debug('|Attribute Setter| >> attr: {0} | value: {1} | lock: {2}'.format(combined, value, lock))
        if kwargs:
            LOGGER.debug('|Attribute Setter| >> kwargs: {0}'.format(kwargs))

        attr_type = maya.cmds.getAttr(combined, type=True)
        valid_type = MetaAttributeUtils.validate_attr_type_name(attr_type=attr_type)

        if MetaAttributeUtils.is_locked(combined):
            was_locked = True
            maya.cmds.setAttr(combined, lock=False)

        if not MetaAttributeUtils.is_keyed(attr_dict):
            if MetaAttributeUtils.break_connection(attr_dict):
                LOGGER.warning('|Attribute Setter| >> Broken connection: {}'.format(combined))

        current = MetaAttributeUtils.get(combined)
        if current == value:
            LOGGER.debug('|Attribute Setter| >> Already has a value: {}'.format(combined))
            if was_locked:
                MetaAttributeUtils.set_lock(attr_dict, True)
                return

        children = MetaAttributeUtils.get_children(attr_dict)
        if children:
            if MetaAttributeValidator.is_list_arg(value):
                if len(children) != len(value):
                    raise ValueError(
                        'Must have matching len for value and children. Children: {0} | Value: {1}'.format(
                            children, value))
            else:
                value = [value for i in range(len(children))]

            for i, child in enumerate(children):
                maya.cmds.setAttr('{0}.{1}'.format(obj, child), value[i], **kwargs)
        elif valid_type == 'long':
            maya.cmds.setAttr(combined, int(float(value)), **kwargs)
        elif valid_type == 'string':
            maya.cmds.setAttr(combined, str(value), type='string', **kwargs)
        elif valid_type == 'double':
            maya.cmds.setAttr(combined, float(value), **kwargs)
        elif valid_type == 'message':
            MetaAttributeUtils.set_message(obj, attr_name, value)
        elif valid_type == 'enum':
            if MetaAttributeValidator.string_arg(value) and ':' in value:
                maya.cmds.addAttr(combined, edit=True, en=value, **kwargs)
            else:
                enum_values = MetaAttributeUtils.get_enum(attr_dict).split(':')
                if value in enum_values:
                    maya.cmds.setAttr(combined, enum_values.index(value), **kwargs)
                elif value is not None and value <= len(enum_values):
                    maya.cmds.setAttr(combined, value, **kwargs)
                else:
                    maya.cmds.setAttr(combined, value, **kwargs)
        else:
            maya.cmds.setAttr(combined, value, **kwargs)

        if was_locked or lock:
            maya.cmds.setAttr(combined, lock=True)

        return

    @staticmethod
    @decorators.abstractmethod
    def delete(*args):
        """
        Deletes given attribute from the given node
        :param args: dict, validated argument
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        combined = attr_dict['combined']

        try:
            if maya.cmds.objExists(combined):
                if MetaAttributeUtils.get_parent(attr_dict):
                    raise ValueError('{0} is a child attribute, try deleting parent attr first: {1}'.format(
                        combined, MetaAttributeUtils.get_parent(attr_dict)))
                try:
                    maya.cmds.setAttr(combined, lock=False)
                except Exception:
                    pass

                try:
                    MetaAttributeUtils.break_connection(combined)
                except Exception:
                    pass

                driven_attr = MetaAttributeUtils.get_driven(attr_dict) or []
                for plug in driven_attr:
                    LOGGER.warning('|Attribute Deletion| >> [{0}] | Breaking out plug: {1}'.format(combined, plug))
                    MetaAttributeUtils.disconnect(combined, plug)

                maya.cmds.deleteAttr(combined)
                return True

            return False
        except Exception as e:
            pprint.pprint(vars())
            raise Exception(e)

    @staticmethod
    @decorators.abstractmethod
    def get_children(*args):
        """
        Get children of a given attribute
        :param args: dict, validated argument
        :return: list, children attrs || status (bool)
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        try:
            return maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], listChildren=True) or []
        except Exception as e:
            LOGGER.error('|Attribute Children Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

    @staticmethod
    @decorators.abstractmethod
    def get_parent(*args):
        """
        Get parent of a given attribute
        :param args: dict, validated argument
        :return: list, parent attrs || status (bool)
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        try:
            parents = maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], listParent=True) or []
            if parents:
                return parents[0]
            return parents
        except Exception as e:
            LOGGER.error('|Attribute Parent Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

    @staticmethod
    @decorators.abstractmethod
    def get_siblings(*args):
        """
        Get siblings of a given attribute
        :param args: dict, validated argument
        :return: list, sibling attrs || status (bool)
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        try:
            return maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], listSiblings=True) or []
        except Exception as e:
            LOGGER.error('|Attribute Siblings Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

    @staticmethod
    @decorators.abstractmethod
    def get_family_dict(*args):
        """
        Gets family dictionary of a given attribute
        :param args: dict, validated argument
        :return: dict
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        obj = attr_dict['obj']
        attr = attr_dict['attr']

        return_dict = {}
        attrs = maya.cmds.attributeQuery(attr, node=obj, listParent=True)
        if attrs is not None:
            return_dict['parent'] = attrs[0]
        attrs = maya.cmds.attributeQuery(attr, node=obj, listChildren=True)
        if attrs is not None:
            return_dict['children'] = attrs
        attrs = maya.cmds.attributeQuery(attr, node=obj, listSiblings=True)
        if attrs is not None:
            return_dict['siblings'] = attrs

        if return_dict:
            return return_dict

        return False

    @staticmethod
    def get_numeric_attribute_state(*args):
        """
        Returns a dictionary of max, min, range, soft and default settings of a given numeric attribute
        :param args: dict, validated argument
        :return: dict
            default
            min
            max
            softMin
            softMax
            range
            softRange
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        combined = attr_dict['combined']
        obj = attr_dict['obj']
        attr = attr_dict['attr']

        data_dict = dict()

        numeric = MetaAttributeUtils.is_numeric(attr_dict)
        if not numeric and MetaAttributeUtils.get_children(attr_dict):
            return {}
        else:
            try:
                data_dict['min'] = MetaAttributeUtils.get_min(attr_dict)
            except Exception:
                data_dict['min'] = False
                LOGGER.debug('{0}.{1} failed to query min value'.format(obj, attr))
            try:
                data_dict['max'] = MetaAttributeUtils.get_max(attr_dict)
            except Exception:
                data_dict['max'] = False
                LOGGER.debug('{0}.{1} failed to query max value'.format(obj, attr))
            try:
                data_dict['default'] = MetaAttributeUtils.get_default(attr_dict)
            except Exception:
                data_dict['default'] = False
                LOGGER.debug('{0}.{1} failed to query default value'.format(obj, attr))
            try:
                data_dict['softMax'] = MetaAttributeUtils.get_soft_max(attr_dict)
            except Exception:
                data_dict['softMax'] = False
                LOGGER.debug('{0}.{1} failed to query soft max value'.format(obj, attr))
            try:
                data_dict['softMin'] = MetaAttributeUtils.get_soft_min(attr_dict)
            except Exception:
                data_dict['softMin'] = False
                LOGGER.debug('{0}.{1} failed to query soft min value'.format(obj, attr))
            try:
                data_dict['range'] = MetaAttributeUtils.get_range(attr_dict)
            except Exception:
                data_dict['range'] = False
                LOGGER.debug('{0}.{1} failed to query range value'.format(obj, attr))
            try:
                data_dict['softRange'] = MetaAttributeUtils.get_soft_range(attr_dict)
            except Exception:
                data_dict['softRange'] = False
                LOGGER.debug('{0}.{1} failed to query soft range value'.format(obj, attr))

        return attr_dict

    @staticmethod
    def get_attribute_state(*args):
        """
        Returns a dictionary of locked, keyable and hidden states of the given attribute
        :param args: dict, validated argument
        :return: dict
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        combined = attr_dict['combined']
        obj = attr_dict['obj']
        attr = attr_dict['attr']

        obj_attrs = maya.cmds.listAttr(obj, userDefined=True) or []
        data_dict = {'type': maya.cmds.getAttr(combined, type=True),
                     'locked': maya.cmds.getAttr(combined, lock=True),
                     'keyable': maya.cmds.getAttr(combined, keyable=True)
                     }

        dynamic = False
        if attr in obj_attrs:
            dynamic = True
        data_dict['dynamic'] = dynamic

        hidden = not maya.cmds.getAttr(combined, channelBox=True)
        if data_dict.get('keyable'):
            hidden = maya.cmds.attributeQuery(attr, node=obj, hidden=True)
        data_dict['hidden'] = hidden

        if data_dict.get('type') == 'enum' and dynamic is True:
            data_dict['enum'] = maya.cmds.addAttr(combined, query=True, en=True)

        numeric = True
        if data_dict.get('type') in ['string', 'message', 'enum', 'bool']:
            numeric = False
        data_dict['numeric'] = numeric
        if numeric:
            numeric_dict = MetaAttributeUtils.get_numeric_attribute_state(attr_dict)
            data_dict.update(numeric_dict)

        if dynamic:
            data_dict['readable'] = maya.cmds.addAttr(combined, query=True, r=True)
            data_dict['writable'] = maya.cmds.addAttr(combined, query=True, w=True)
            data_dict['storable'] = maya.cmds.addAttr(combined, query=True, s=True)
            data_dict['usedAsColor'] = maya.cmds.addAttr(combined, query=True, usedAsColor=True)

        return data_dict

    @staticmethod
    @decorators.abstractmethod
    def copy_to(from_object, from_attr, to_object=None, to_attr=None, convert_to_match=True, values=True,
                in_connection=False, out_connections=False, keep_source_connections=True, copy_settings=True,
                driven=None):
        """
        Copy attributes from one object to another. If the attribute already exists, it'll cpy the values
        If it does not, it will be created.
        :param from_object: str, object with attributes to copy
        :param from_attr: str, source attribute
        :param to_object: str, object where we want to copy attributes to
        :param to_attr: str, name of the attribute to copy. If None, it will create an attribute of the
        from_attr name on the to_object if it does not exists
        :param convert_to_match: bool, whether to automatically convert attribute if they need to be
        :param values:
        :param in_connection: bool
        :param out_connections: bool
        :param keep_source_connections: bool, keeps connections on source
        :param copy_settings: bool, copy the attribute state of the from_attr (keyable, lock, and hidden)
        :param driven: str, whether to connect source>target or target>source
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(from_object, from_attr)
        combined = attr_dict['combined']
        node = attr_dict['node']
        to_obj = to_object
        to_attr_name = to_attr

        if to_obj is None:
            LOGGER.debug('|Attributes Copy| >> No to_object specified. Using from_object:{}'.format(from_object))
            to_obj = from_object
        if to_attr_name is None:
            LOGGER.debug('|Attributes Copy| >> No to_attr specified. Using from-attr:{}'.format(from_attr))
            to_attr_name = from_attr
        attr_dict_target = MetaAttributeUtils.validate_attribute(to_obj, to_attr_name)

        if combined == attr_dict_target['combined']:
            raise ValueError('Cannot copy to itself')

        LOGGER.debug('|Attributes Copy| >> source: {}'.format(combined))
        LOGGER.debug('|Attributes Copy| >> target: {0} | {1}'.format(to_obj, to_attr_name))

        dict_source_flags = MetaAttributeUtils.get_attribute_state(attr_dict)

        if values and not MetaAttributeUtils.validate_attr_type_name(dict_source_flags['type']):
            LOGGER.warning(
                '|Attributes Copy| >> {0} is a {1} attribute and not valid for copying'.format(attr_dict['combined'],
                                                                                               dict_source_flags[
                                                                                                   'type']))
            return False

        _driver = MetaAttributeUtils.get_driver(attr_dict, skip_conversion_nodes=True)
        _driven = MetaAttributeUtils.get_driven(attr_dict, skip_conversion_nodes=True)
        _data = MetaAttributeUtils.get(attr_dict)

        LOGGER.debug('|Attributes Copy| >> data: {}'.format(_data))
        LOGGER.debug('|Attributes Copy| >> driver: {}'.format(_driver))
        LOGGER.debug('|Attributes Copy| >> driven: {}'.format(_driven))

        if maya.cmds.objExists(attr_dict_target['combined']):
            dict_target_flags = MetaAttributeUtils.get_attribute_state(attr_dict_target)

            if not MetaAttributeUtils.validate_attr_type_name(dict_target_flags['type']):
                LOGGER.warning('|Attributes Copy| >> {0} may not copy correctly. Type did not validate'.format(
                    attr_dict_target['combined']))

            if not MetaAttributeUtils.validate_attr_type_match(dict_source_flags['type'], dict_target_flags['type']):
                if dict_target_flags['dynamic'] and convert_to_match:
                    LOGGER.debug('Attributes Copy| >> {} not the correct type, trying to convert it'.format(
                        attr_dict_target['combined']))
                    MetaAttributeUtils.convert_type(attr_dict_target, dict_source_flags['type'])
                else:
                    raise Exception(
                        '|Attributes Copy| >> {} not the correct type. Conversion is necessary '
                        'and convert_to_match is disabled'.format(
                            attr_dict_target['combined']))
        else:
            MetaAttributeUtils.add(attr_dict_target, dict_source_flags['type'])

        if _data is not None:
            try:
                MetaAttributeUtils.set(attr_dict_target, value=_data)
            except Exception as e:
                LOGGER.debug('|Attributes Copy| >> Failed to set back data buffer {0} | data: {1} | err: {2}'.format(
                    attr_dict_target['combined'], _data, e))

        if _driver and in_connection:
            if dict_source_flags['type'] != 'message':
                LOGGER.debug('|Attributes Copy| >> Current Driver: {}'.format(_driver))
                try:
                    MetaAttributeUtils.connect(_driver, attr_dict_target['combined'])
                except Exception as e:
                    LOGGER.error(
                        '|Attributes Copy| >> Failed to connect {0} >> {1} | err: {2}'.format(
                            _driver, attr_dict_target['combined'], e))

        if _driven and out_connections:
            LOGGER.debug('|Attributes Copy| >> Current Driven: {}'.format(_driven))
            for c in _driven:
                dict_driven = MetaAttributeUtils.validate_attribute(c)
                if dict_driven['combined'] != attr_dict_target['combined']:
                    LOGGER.debug('|Attributes Copy| >> driven: {}'.format(c))
                    try:
                        MetaAttributeUtils.connect(attr_dict_target['combined'], c)
                    except Exception as e:
                        LOGGER.error(
                            '|Attributes Copy| >> Failed to connect {0} >> {1} | err: {2}'.format(
                                _driven, attr_dict_target['combined'], e))

        if copy_settings:
            if dict_source_flags.get('enum'):
                maya.cmds.addAttr(attr_dict_target['combined'], e=True, at='enum', en=dict_source_flags['enum'])
            if dict_source_flags['numeric']:
                children = MetaAttributeUtils.get_children(attr_dict)
                if children:
                    for child in children:
                        dict_child = MetaAttributeUtils.get_attribute_state(node, child)
                        _buffer = '{0}.{1}'.format(attr_dict_target['node'], child)
                        if dict_child['default']:
                            maya.cmds.addAttr(_buffer, edit=True, dv=dict_child['default'])
                        if dict_child['max']:
                            maya.cmds.addAttr(_buffer, edit=True, maxValue=dict_child['max'])
                        if dict_child['min']:
                            maya.cmds.addAttr(_buffer, edit=True, minValue=dict_child['min'])
                        if dict_child['softMax']:
                            maya.cmds.addAttr(_buffer, edit=True, softMaxValue=dict_child['softMax'])
                        if dict_child['softMin']:
                            maya.cmds.addAttr(_buffer, edit=True, softMinValue=dict_child['softMin'])
                else:
                    if dict_source_flags['default']:
                        maya.cmds.addAttr(attr_dict_target['combined'], edit=True, dv=dict_source_flags['default'])
                    if dict_source_flags['max']:
                        maya.cmds.addAttr(attr_dict_target['combined'], edit=True, maxValue=dict_source_flags['max'])
                    if dict_source_flags['min']:
                        maya.cmds.addAttr(attr_dict_target['combined'], edit=True, minValue=dict_source_flags['min'])
                    if dict_source_flags['softMax']:
                        maya.cmds.addAttr(attr_dict_target['combined'], edit=True,
                                          softMaxValue=dict_source_flags['softMax'])
                    if dict_source_flags['softMin']:
                        maya.cmds.addAttr(attr_dict_target['combined'], edit=True,
                                          softMinValue=dict_source_flags['softMin'])

            maya.cmds.setAttr(attr_dict_target['combined'], edit=True, channelBox=not dict_source_flags['hidden'])
            maya.cmds.setAttr(attr_dict_target['combined'], edit=True, keyable=dict_source_flags['keyable'])
            maya.cmds.setAttr(attr_dict_target['combined'], edit=True, lock=dict_source_flags['locked'])

        if driven == 'target':
            try:
                MetaAttributeUtils.connect(attr_dict, attr_dict_target)
            except Exception as e:
                LOGGER.error(
                    '|Attributes Copy| >> Failed to connect source to target {0} >> {1} | err: {2}'.format(
                        combined, attr_dict_target['combined'], e))
        elif driven == 'source':
            try:
                MetaAttributeUtils.connect(attr_dict_target, attr_dict)
            except Exception as e:
                LOGGER.error('|Attributes Copy| >> Failed to connect target to source {0} >> {1} | err: {2}'.format(
                    attr_dict_target['combined'], combined, e))

        if dict_source_flags['locked']:
            maya.cmds.setAttr(attr_dict_target['combined'], lock=True)

        return True

    @staticmethod
    @decorators.abstractmethod
    def is_connected(*args):
        """
        Returns true if a given attribute is connected to another one
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        combined = attr_dict['combined']

        if maya.cmds.connectionInfo(combined, isDestination=True):
            return True

        return False

    @staticmethod
    def connect(from_attr, to_attr, lock=False, **kwargs):
        """
        Connects attributes. Handles locks on source or end automatically
        :param from_attr: str
        :param to_attr: str
        :param lock: bool
        :param kwargs:
        :return: bool
        """

        from_attr_dict = MetaAttributeUtils.validate_attribute(from_attr)
        from_combined = from_attr_dict['combined']

        to_attr_dict = MetaAttributeUtils.validate_attribute(to_attr)
        to_combined = to_attr_dict['combined']

        LOGGER.debug('|Attribute Connection| >> Connecting {0} to {1}'.format(from_combined, to_combined))
        assert from_combined != to_combined, 'Cannot connect an attribute to itself'

        was_locked = False
        if maya.cmds.objExists(to_combined):
            if maya.cmds.getAttr(to_combined, lock=True):
                was_locked = True
                maya.cmds.setAttr(to_combined, lock=False)

            MetaAttributeUtils.break_connection(to_attr_dict)
            maya.cmds.connectAttr(from_combined, to_combined, **kwargs)

        if was_locked or lock:
            maya.cmds.setAttr(to_combined, lock=True)

        return True

    @staticmethod
    def disconnect(from_attr, to_attr):
        """
        Disconnects attributes. Handles locks on source or end automatically
        :param from_attr: str, node.attribute
        :param to_attr: attribute type dependant
        :return: bool
        """

        from_attr_dict = MetaAttributeUtils.validate_attribute(from_attr)
        from_combined = from_attr_dict['combined']

        to_attr_dict = MetaAttributeUtils.validate_attribute(to_attr)
        to_combined = to_attr_dict['combined']

        driven_lock = False
        if maya.cmds.getAttr(to_combined, lock=True):
            driven_lock = True
            maya.cmds.setAttr(to_combined, lock=False)

        source_lock = False
        if maya.cmds.getAttr(from_combined, lock=True):
            source_lock = True
            maya.cmds.setAttr(from_combined, lock=False)

        maya.cmds.disconnectAttr(from_combined, to_combined)

        if driven_lock:
            maya.cmds.setAttr(to_combined, lock=True)
        if source_lock:
            maya.cmds.setAttr(from_combined, lock=True)

        return True

    @staticmethod
    @decorators.abstractmethod
    def break_connection(*args):
        """
        Breaks connection of a given attributes. Handles locks on source or end automatically
        :param args: dict, validated argument
        :return: broken connection || status (bool)
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        combined = attr_dict['combined']
        obj = attr_dict['obj']
        attr = attr_dict['attr']
        driven_attr = combined

        family = dict()

        if MetaAttributeUtils.get_type(attr_dict) == 'message':
            LOGGER.debug('|Attribute Break Connection| >> message')
            dst = maya.cmds.listConnections(
                combined, skipConversionNodes=False, destination=True, source=False, plugs=True)
            if dst:
                for child_attr in dst:
                    LOGGER.debug('|Attribute Break Connection| >> Disconnecting attr {}'.format(child_attr))
                    MetaAttributeUtils.disconnect(driven_attr, child_attr)

        if maya.cmds.connectionInfo(combined, isDestination=True):
            source_connections = maya.cmds.listConnections(
                combined, skipConversionNodes=False, destination=False, source=True, plugs=True)
            if not source_connections:
                family = MetaAttributeUtils.get_family_dict(attr_dict)
                source_connections = maya.cmds.connectionInfo(combined, sourceFromDestination=True)
            else:
                source_connections = source_connections[0]

            if not source_connections:
                LOGGER.warning('|Attribute Break Connection| >> No source for "{0}.{1}" found!'.format(obj, attr))
                return False

            LOGGER.debug('|Attribute Break Connection| >> Source Connections: {}'.format(source_connections))
            if family and family.get('parent'):
                LOGGER.debug('|Attribute Break Connection| >> Attribute Family: {}'.format(family))
                driven_attr = '{0}.{1}'.format(obj, family.get('parent'))

            LOGGER.debug(
                '|Attribute Break Connection| >> Breaking {0} >>> to >>> {1}'.format(source_connections, driven_attr))
            MetaAttributeUtils.disconnect(from_attr=source_connections, to_attr=driven_attr)

            return source_connections

        return False

    @staticmethod
    @decorators.abstractmethod
    def has_attr(*args):
        """
        Returns True if the given attribute exists or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            if maya.cmds.objExists(attr_dict['combined']):
                return True
            return False
        except Exception as e:
            LOGGER.error('|Has Attribute| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

        return False

    @staticmethod
    def get_name_long(*args):
        """
        Get the long name of an attribute
        :param args: dict, validated argument
        :return: str
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            return maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], longName=True) or False
        except Exception:
            if maya.cmds.objExists(attr_dict['combined']):
                return attr_dict['attr']
            else:
                raise RuntimeError(
                    '|Long Attribute Name Getter| >> Attribute does nost exists: {}'.format(attr_dict['combined']))

    @staticmethod
    @decorators.abstractmethod
    def is_locked(*args):
        """
        Returns True if the given attribute is locked or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            return maya.cmds.getAttr(attr_dict['combined'], lock=True)
        except Exception as e:
            LOGGER.error('|Attribute Locker| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

    @staticmethod
    @decorators.abstractmethod
    def set_lock(node, attr=None, arg=None):
        """
        Set the lock status of an attribute
        :param node: str
        :param attr: str
        :param arg: bool
        :return:
        """

        if '.' in node or issubclass(type(node), dict):
            attr_dict = MetaAttributeUtils.validate_attribute(node)
            if attr_dict is None and attr is not None:
                attr_dict = attr
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(node, attr)

        combined = attr_dict['combined']
        obj = attr_dict['node']

        children = MetaAttributeUtils.get_children(attr_dict)
        if children:
            for i, child in enumerate(children):
                maya.cmds.setAttr('{0}.{1}'.format(obj, child), lock=arg)
        else:
            maya.cmds.setAttr(combined, lock=arg)

    @staticmethod
    @decorators.abstractmethod
    def is_hidden(*args):
        """
        Returns True if the given attribute is hidden or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        hidden = not maya.cmds.getAttr(attr_dict['combined'], channelBox=True)
        if MetaAttributeUtils.is_keyed(attr_dict):
            hidden = maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], hidden=True)

        return hidden

    @staticmethod
    def set_hidden(node, attr=None, arg=None):
        """
        Set the hidden status of the given attribute
        :param node: str
        :param attr: str
        :param arg: bool
        """

        if '.' in node or issubclass(type(node), dict):
            attr_dict = MetaAttributeUtils.validate_attribute(node)
            if arg is None and attr is not None:
                arg = attr
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(node, attr)

        combined = attr_dict['combined']
        obj = attr_dict['node']

        children = MetaAttributeUtils.get_children(attr_dict)

        if arg:
            if children:
                for child in children:
                    child_attr_dict = MetaAttributeUtils.validate_attribute(node, child)
                    if not MetaAttributeUtils.is_hidden(child_attr_dict):
                        if MetaAttributeUtils.is_keyed(child_attr_dict):
                            MetaAttributeUtils.set_keyable(child_attr_dict, arg=False)
                        maya.cmds.setAttr(child_attr_dict['combined'], e=True, channelBox=False)
            elif not MetaAttributeUtils.is_hidden(attr_dict):
                if MetaAttributeUtils.is_keyed(attr_dict):
                    MetaAttributeUtils.set_keyable(attr_dict, arg=False)
                maya.cmds.setAttr(combined, e=True, channelBox=False)
        else:
            if children:
                for child in children:
                    child_attr_dict = MetaAttributeUtils.validate_attribute(node, child)
                    if MetaAttributeUtils.is_hidden(child_attr_dict):
                        maya.cmds.setAttr(child_attr_dict['combined'], e=True, channelBox=True)
            elif MetaAttributeUtils.is_hidden(attr_dict):
                maya.cmds.setAttr(combined, e=True, channelBox=True)

    @staticmethod
    @decorators.abstractmethod
    def get_keyed(node):
        """
        Returns list of keyed attributes
        :param node: dict, validated argument
        :return: list<attributes>
        """

        result = list()
        for attr in maya.cmds.listAttr(node, keyable=True):
            if MetaAttributeUtils.is_keyed(node, attr):
                result.append(attr)

        return result

    @staticmethod
    @decorators.abstractmethod
    def is_keyed(*args):
        """"
        Returns True if the given attribute is keyable or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        if maya.cmds.keyframe(attr_dict['combined'], query=True):
            return True

        return False

    @staticmethod
    @decorators.abstractmethod
    def set_keyable(node, attr=None, arg=None):
        """
        Set the lock of status of the given attribute
        :param node: str
        :param attr: str
        :param arg: bool
        """

        if '.' in node or issubclass(type(node), dict):
            attr_dict = MetaAttributeUtils.validate_attribute(node)
            if arg is None and attr is not None:
                arg = attr
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(node, attr)

        combined = attr_dict['combined']
        obj = attr_dict['node']

        children = MetaAttributeUtils.get_children(attr_dict)
        if children:
            for i, child in enumerate(children):
                if not arg:
                    hidden = MetaAttributeUtils.is_hidden(obj, child)
                    maya.cmds.setAttr('{0}.{1}'.format(obj, child), e=True, keyable=arg)
                    if not arg and MetaAttributeUtils.is_hidden(obj, child) != hidden:
                        MetaAttributeUtils.set_hidden(obj, child, hidden)
        else:
            if not arg:
                hidden = MetaAttributeUtils.is_hidden(attr_dict)
                maya.cmds.setAttr(combined, e=True, keyable=arg)
                if not arg and MetaAttributeUtils.is_hidden(attr_dict) != hidden:
                    MetaAttributeUtils.set_hidden(attr_dict, hidden)

    @staticmethod
    @decorators.abstractmethod
    def get_enum(*args):
        """
        Returns enum attribute
        :param args: dict, validated argument
        :return: variant, str || bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        if MetaAttributeUtils.get_type(attr_dict) == 'enum':
            return maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], listEnum=True)[0]

        return False

    @staticmethod
    @decorators.abstractmethod
    def is_multi(*args):
        """
        :Check if the given attribute is a valid Maya multi attribute
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            if not MetaAttributeUtils.is_dynamic(attr_dict):
                return False
            return maya.cmds.addAttr(attr_dict['combined'], query=True, m=True)
        except Exception as e:
            LOGGER.error(('|Is Multi Attribute| >> {0} | {1}'.format(attr_dict['combined'], e)))
            return False

    @staticmethod
    @decorators.abstractmethod
    def is_dynamic(*args):
        """
        Returns True if the given attribute is dynamic or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        user_defined = maya.cmds.listAttr(attr_dict['obj'], userDefined=True) or []
        if attr_dict['attr'] in user_defined:
            return True

        return False

    @staticmethod
    @decorators.abstractmethod
    def is_numeric(*args):
        """
        Returns if an attribute is numeric or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        if maya.cmds.getAttr(attr_dict['combined'], type=True) in ['string', 'message', 'enum', 'bool']:
            return False

        return True

    @staticmethod
    @decorators.abstractmethod
    def is_readable(*args):
        """
        Returns if an attribute is readable or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        if not MetaAttributeUtils.is_dynamic(attr_dict):
            return False

        return maya.cmds.addAttr(attr_dict['combined'], query=True, r=True) or False

    @staticmethod
    @decorators.abstractmethod
    def is_writable(*args):
        """
        Returns if an attribute is writable or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        if not MetaAttributeUtils.is_dynamic(attr_dict):
            return False

        return maya.cmds.addAttr(attr_dict['combined'], query=True, w=True) or False

    @staticmethod
    @decorators.abstractmethod
    def is_storable(*args):
        """
        Returns True if an attribute is storable or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        if not MetaAttributeUtils.is_dynamic(attr_dict):
            return False

        return maya.cmds.addAttr(attr_dict['combined'], query=True, s=True) or False

    @staticmethod
    @decorators.abstractmethod
    def is_used_as_color(*args):
        """
        Returns True if an attribute is used as color or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        if not MetaAttributeUtils.is_dynamic(attr_dict):
            return False

        return maya.cmds.addAttr(attr_dict['combined'], query=True, usedAsColor=True) or False

    @staticmethod
    @decorators.abstractmethod
    def is_user_defined(*args):
        """
        Returns True if an attribute is user defined or False otherwise
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        if MetaAttributeUtils.get_name_long(attr_dict) in maya.cmds.listAttr(attr_dict['node'], userDefined=True):
            return True

        return False

    @staticmethod
    @decorators.abstractmethod
    def get_default(*args):
        """
        Returns the default value of the given integer attribute
        :param args: dict, validated argument
        :return: dict
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)
        combined = attr_dict['combined']
        node = attr_dict['node']
        attr = attr_dict['attr']

        if not MetaAttributeUtils.is_dynamic(attr_dict):
            long_attr = MetaAttributeUtils.get_name_long(attr_dict)
            if long_attr in ['translateX', 'translateY', 'translateZ', 'translate',
                             'rotateX', 'rotateY', 'rotateZ', 'rotate',
                             'scaleX', 'scaleY', 'scaleZ', 'scale']:
                if 'scale' in long_attr:
                    if long_attr == 'scale':
                        return [1.0, 1.0, 1.0]
                    return 1.0
                else:
                    if long_attr in ['rotate', 'translate']:
                        return [0.0, 0.0, 0.0]
                    return 0.0

            return False

        if type(maya.cmds.addAttr(combined, query=True, defaultValue=True)) is int or float:
            result = maya.cmds.attributeQuery(attr, node=node, listDefault=True)
            if result is not False:
                if len(result) == 1:
                    return result[0]
                return result

        return False

    @staticmethod
    @decorators.abstractmethod
    def get_max(*args):
        """
        Returns the maximum value of the given integer attribute
        :param args: dict, validated argument
        :return: variant, float || bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            if maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], maxExists=True):
                result = maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], maximum=True)
                if result is not False:
                    if len(result) == 1:
                        return result[0]
                    return result
        except Exception as e:
            LOGGER.error('|Max Attribute Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

        return False

    @staticmethod
    @decorators.abstractmethod
    def get_min(*args):
        """
        Returns the minimum value of the given integer attribute
        :param args: dict, validated argument
        :return: variant, float || bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            if maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], minExists=True):
                result = maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], minimum=True)
                if result is not False:
                    if len(result) == 1:
                        return result[0]
                    return result
        except Exception as e:
            LOGGER.error('|Min Attribute Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

        return False

    @staticmethod
    @decorators.abstractmethod
    def get_range(*args):
        """
        Returns the range of the given integer attribute
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            return maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], range=True) or False
        except Exception as e:
            LOGGER.error('|Integer Range Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

    @staticmethod
    @decorators.abstractmethod
    def get_soft_range(*args):
        """
        Returns the soft range of the given integer attribute
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            return maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], softRange=True) or False
        except Exception as e:
            LOGGER.error('|Integer Range Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

    @staticmethod
    @decorators.abstractmethod
    def get_soft_max(*args):
        """
        Returns the soft maximum value of the given integer attribute
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            result = maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], softMin=True)
            if result is not False:
                if len(result) == 1:
                    return result[0]
                return result
        except Exception as e:
            LOGGER.error('|Integer Soft Max Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

        return False

    @staticmethod
    @decorators.abstractmethod
    def get_soft_min(*args):
        """
        Returns the soft minimum value of the given integer attribute
        :param args: dict, validated argument
        :return: bool
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        try:
            result = maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], softMax=True)
            if result is not False:
                if len(result) == 1:
                    return result[0]
                return result
        except Exception as e:
            LOGGER.error('|Integer Soft Max Getter| >> {0} | {1}'.format(attr_dict['combined'], e))
            return False

        return False

    @staticmethod
    def get_nice_name(*args):
        """
        Returns the nice name of the given attribute
        :param args: dict, validated argument
        :return: str
        """

        attr_dict = MetaAttributeUtils.validate_attribute(*args)

        return maya.cmds.attributeQuery(attr_dict['attr'], node=attr_dict['node'], niceName=True) or False

    @staticmethod
    def rename_nice_name(node=None, attr=None, name=None):
        """
        Set the nice name of the given attribute
        :param ndoe: str
        :param attr: str
        :param name: str, new name. If None, assumes obj argument is combined and uses attr. If False, clears the nice
        name
        :return: bool
        """

        if name is None:
            name = attr
            attr_dict = MetaAttributeUtils.validate_attribute(node)
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(node, attr)

        lock = MetaAttributeUtils.is_locked(attr_dict)
        if lock:
            MetaAttributeUtils.set_lock(attr_dict, False)

        if name:
            maya.cmds.addAttr(attr_dict['combined'], edit=True, niceName=name)
        elif not name:
            maya.cmds.addAttr(attr_dict['combined'], edit=True, niceName=attr_dict['attr'])
        if lock:
            MetaAttributeUtils.set_lock(attr_dict, True)

        return MetaAttributeUtils.get_nice_name(attr_dict)

    @staticmethod
    def get_message(message_holder, message_attr=None, data_attr=None, data_key=None, simple=False):
        """
        :param message_holder:
        :param message_attr:
        :param data_attr:
        :param data_key:
        :param simple:
        :return:
        """

        from tpDcc.dccs.maya.meta import metanode

        data = data_attr

        if '.' in message_holder or issubclass(type(message_holder), dict):
            attr_dict = MetaAttributeUtils.validate_attribute(message_holder)
            data = message_attr
        else:
            attr_dict = MetaAttributeUtils.validate_attribute(message_holder, message_attr)
        combined = attr_dict['combined']

        if data_key is None:
            data_key = message_attr
        else:
            data_key = unicode(data_key)

        LOGGER.debug('|Message Getter| >> {0} || data_attr: {1} | data_Key: {2}'.format(combined, data, data_key))

        if not maya.cmds.objExists(combined):
            LOGGER.debug('|Message Getter| >> {0} | No attribute exists'.format(combined))
            return False

        dict_type = MetaAttributeUtils.get_type(attr_dict)
        if dict_type in ['string']:
            LOGGER.debug('|Message Getter| >> Special Message Attr ...')
            msg_buffer = maya.cmds.listConnections(combined, p=True)
            if msg_buffer and len(msg_buffer) == 1:
                msg_buffer = [msg_buffer[0].split('.')[0]]
            else:
                raise ValueError('Invalid message {}'.format(msg_buffer))
        else:
            msg_buffer = maya.cmds.listConnections(combined, destination=True, source=True, shapes=True)

            if msg_buffer and maya.cmds.objectType(msg_buffer[0]) == 'reference':
                msg_buffer = maya.cmds.listConnections(combined, destination=True, source=True)

        if MetaAttributeUtils.is_multi(attr_dict):
            LOGGER.debug('|Message Getter| >> Multimessage')
            if msg_buffer:
                return msg_buffer
            return False
        else:
            LOGGER.debug('|Message Getter| >> Single Message')
            if simple:
                return msg_buffer

            data = 'MsgData'
            if data_attr:
                data = data_attr

            if '.' in data or issubclass(type(data), dict):
                attr_dict_data = MetaAttributeUtils.validate_attribute(data)
            else:
                attr_dict_data = MetaAttributeUtils.validate_attribute(message_holder, data)

            if msg_buffer is not None:
                if maya.cmds.objExists(msg_buffer[0]) and not maya.cmds.objectType(msg_buffer[0]) == 'reference':
                    meta_node = metanode.MetaNode(attr_dict['node'])
                    if meta_node.has_attr(attr_dict_data['attr']):
                        dict_buffer = meta_node.__getattribute__(attr_dict_data['attr']) or {}
                        if dict_buffer.get(data_key):
                            LOGGER.debug('|Message Getter| >> Extra Message Data Found')
                            return [msg_buffer[0] + '.' + dict_buffer.get(data_key)]
                    return msg_buffer
                else:
                    return attr_utils.repair_message_to_reference_target(combined)
                    # return repairMessageToReferencedTarget(storageObject, messageAttr)

        return False

    @staticmethod
    def set_message(message_holder, message_attr, message, data_attr=None, data_key=None, simple=False,
                    connect_back=None):
        """
        :param message_holder:
        :param message_attr:
        :param message:
        :param data_attr:
        :param data_key:
        :param simple:
        :param connect_back:
        :return:
        """

        from tpDcc.dccs.maya.meta import metanode

        try:
            attr_dict = MetaAttributeUtils.validate_attribute(message_holder, message_attr)
            combined = attr_dict['combined']

            mode = 'reg'
            messaged_node = None
            messaged_extra = None
            dict_data_attr = None

            if data_attr is None:
                data_attr = '{}_datdict'.format(message_attr)

            multi = False
            if maya.cmds.objExists(combined) and maya.cmds.addAttr(combined, query=True, m=True):
                multi = True
                if not message:
                    LOGGER.debug('|Message Setter| >> MultiMessage delete')
                    MetaAttributeUtils.delete(combined)
                    MetaAttributeUtils.add(combined, 'message', m=True, im=False)
                    return True

            if issubclass(type(message), list) or multi:

                def store_message_multi(message_nodes, holder_dict):
                    for n in message_nodes:
                        try:
                            MetaAttributeUtils.connect((n + '.message'), holder_dict['combined'], next_available=True)
                        except Exception as e:
                            LOGGER.warning('|Message Setter| >> {0} failed: {1}'.format(n, e))

                if len(message) > 1 or multi:
                    if maya.cmds.objExists(combined):
                        if not MetaAttributeUtils.get_type(combined) == 'message':
                            LOGGER.warning('|Message Setter| >> Not a message attribute. Converting ...')
                            MetaAttributeUtils.delete(attr_dict)
                            MetaAttributeUtils.add(message_holder, message_attr, 'message', m=True, im=False)
                            store_message_multi(message, attr_dict)
                            return True

                        _buffer = MetaAttributeUtils.get_message(combined, data_attr)
                        if not maya.cmds.addAttr(combined, query=True, m=True):
                            LOGGER.warning(('|Message Setter| >> Not a multi message attribute. Converting ...'))
                            MetaAttributeUtils.delete(attr_dict)
                            MetaAttributeUtils.add(message_holder, message_attr, 'message', m=True, im=False)
                            store_message_multi(message, attr_dict)
                            return True
                        else:
                            LOGGER.debug('|Message Setter| >> Multimesssage')
                            message_long = [name_utils.get_long_name(m) for m in message]
                            if _buffer and [name_utils.get_long_name(m) for m in _buffer] == message_long:
                                LOGGER.debug('|Message Setter| >> Message match. Good to go')
                                return True
                            else:
                                LOGGER.debug('|Message Setter| >> Messages do not match')
                                connections = MetaAttributeUtils.get_driven(combined)
                                if connections:
                                    for c in connections:
                                        MetaAttributeUtils.break_connection(c)

                                MetaAttributeUtils.delete(attr_dict)
                                MetaAttributeUtils.add(message_holder, message_attr, 'message', m=True, im=False)
                                store_message_multi(message, attr_dict)
                    else:
                        LOGGER.debug('|Message Setter| >> New Attribute ...')
                        MetaAttributeUtils.add(message_holder, message_attr, 'message', m=True, im=False)
                        store_message_multi(message, attr_dict)
                    return True
                else:
                    message = message[0]

            if not message:
                MetaAttributeUtils.break_connection(attr_dict)
                return True
            elif '.' in message:
                if MetaAttributeValidator.is_component(message):
                    list_msg = MetaAttributeValidator.get_component(message)
                    messaged_node = list_msg[1]
                    if simple:
                        message = list_msg[1]
                        LOGGER.debug('|Message Setter| >> Simle. Using {0} | {1}'.format(message, list_msg))
                    else:
                        mode = 'comp'
                        LOGGER.debug('|Message Setter| >> ComponentMessage: {}'.format(list_msg))
                        messaged_extra = list_msg[0]
                else:
                    dict_msg = MetaAttributeUtils.validate_attribute(message)
                    messaged_node = dict_msg['node']
                    if simple:
                        message = dict_msg['node']
                        LOGGER.debug('|Message Setter| >> Simle. Using {0} | {1}'.format(message, dict_msg))
                    else:
                        mode = 'attr'
                        LOGGER.debug('|Message Setter| >> AttrMessage: {}'.format(dict_msg))
                        messaged_extra = dict_msg['attr']
            elif MetaAttributeValidator.is_shape(message):
                mode = 'shape'
                messaged_node = message
            else:
                messaged_node = message

            message_long = name_utils.get_long_name(message)

            _data_attr = 'MsgData_'
            if data_attr is not None:
                _data_attr = data_attr

            if data_key is None:
                data_key = message_attr
            else:
                data_key = unicode(data_key)

            LOGGER.debug(
                '|Message Setter| >> mode: {0} | data_attr: {1} | data_key: {2}'.format(mode, _data_attr, data_key))
            LOGGER.debug(
                '|Message Setter| >> message_holder: {0} | message_attr: {1}'.format(message_holder, message_attr))
            LOGGER.debug(
                '|Message Setter| >> messaged_node: {0} | messaged_extra: {1} | message_long: {2}'.format(
                    messaged_node, messaged_extra, message_long))

            if messaged_extra:
                if '.' in _data_attr:
                    dict_data_attr = MetaAttributeUtils.validate_attribute(data_attr)
                else:
                    dict_data_attr = MetaAttributeUtils.validate_attribute(message_holder, _data_attr)

            def store_message(msg_node, msg_extra, holder_dict, data_attr_dict=None, data_key=None, mode=None):
                if mode not in ['shape']:
                    MetaAttributeUtils.connect((msg_node + '.message'), holder_dict['combined'])

                if msg_extra:
                    LOGGER.debug('|Message Setter| >> {0}.{1} stored to: {2}'.format(
                        msg_node, msg_extra, holder_dict['combined']))

                    if not maya.cmds.objExists(data_attr_dict['combined']):
                        MetaAttributeUtils.add(data_attr_dict['node'], data_attr_dict['attr'], 'string')

                    if MetaAttributeUtils.get_type(data_attr_dict['combined']) != 'string':
                        raise ValueError(
                            'DataAttr must be string. {0} is type {1}'.format(
                                data_attr_dict['combined'], MetaAttributeUtils.get_type(data_attr_dict['combined'])))

                    meta_node = metanode.MetaNode(attr_dict['node'])
                    dict_buffer = meta_node.__getattribute__(data_attr_dict['attr']) or {}
                    dict_buffer[data_key] = messaged_extra
                    LOGGER.debug('|Message Setter| >> buffer: {}'.format(dict_buffer))
                    meta_node.__setattr__(data_attr_dict['attr'], dict_buffer)

                    return True

                LOGGER.debug('|Message Setter| >> "{0}" stored to: "{1}"'.format(msg_node, combined))
                return True

            if mode == 'shape':
                MetaAttributeUtils.copy_to(messaged_node, 'viewName', message_holder, message_attr, driven='target')
                store_message(messaged_node, messaged_extra, attr_dict, dict_data_attr, 'shape')
                return True

            if maya.cmds.objExists(combined):
                if not MetaAttributeUtils.get_type(combined) == 'message':
                    LOGGER.warning('|Message Setter| >> Not a message attribute. Converting ...')
                    MetaAttributeUtils.delete(attr_dict)
                    MetaAttributeUtils.add(message_holder, message_attr, 'message', m=False)
                    store_message(messaged_node, messaged_extra, attr_dict, dict_data_attr, data_key)
                    return True

                _buffer = MetaAttributeUtils.get_message(combined, data_attr, data_key=data_key, simple=simple)
                if not maya.cmds.addAttr(combined, query=True, m=True):
                    LOGGER.debug('|Message Setter| >> MessageSimple')
                    if _buffer and name_utils.get_long_name(_buffer[0]) == message_long:
                        LOGGER.debug('|Message Setter| >> Message match. Good to go')
                        return True
                    else:
                        MetaAttributeUtils.break_connection(attr_dict)
                        store_message(messaged_node, messaged_extra, attr_dict, dict_data_attr, data_key)
                else:
                    LOGGER.debug('|Message Setter| >> MultiMessage')
                    if _buffer and name_utils.get_long_name(_buffer[0]) == message_long:
                        LOGGER.ebug('|Message Setter| >> Message match. Good to go')
                        return True
                    else:
                        connections = MetaAttributeUtils.get_driven(combined)
                        if connections:
                            for c in connections:
                                MetaAttributeUtils.break_connection(c)

                        MetaAttributeUtils.delete(attr_dict)
                        MetaAttributeUtils.add(message_holder, message_attr, 'message', m=False)
                        store_message(messaged_node, messaged_extra, attr_dict, dict_data_attr, data_key)
            else:
                LOGGER.debug('|Message Setter| >> New Attribute')
                MetaAttributeUtils.add(message_holder, message_attr, 'message', m=False)
                store_message(messaged_node, messaged_extra, attr_dict, dict_data_attr, data_key)

            return True
        except Exception as e:
            raise StandardError(e)


class MetaDataListUtils(object):

    @staticmethod
    def get_sequential_attr_dict(node, attr=None):
        """
        Returns a dictionary of sequential user defined attributes
        :param node: str, name of the node we want to get attributes of
        :param attr:
        :return: dict
        """

        result = dict()
        user_attrs = maya.cmds.listAttr(node, userDefined=True) or list()
        for a in user_attrs:
            if '_' in a:
                split_attr = a.split('_')
                split_index = split_attr[-1]
                split_str = ('_').join(split_attr[:-1])
                if str(attr) == split_str:
                    try:
                        result[int(split_index)] = a
                    except Exception:
                        LOGGER.debug('|get_sequential_attr_dict| >> {}.{} failed to int | int: {}'.format(
                            name_utils.get_short_name(node), attr, split_index))

        return result

    @staticmethod
    def get_next_available_sequential_attr_index(node, attr=None):
        """
        Returns next available attribute in sequence
        :param node: str
        :param attr:
        :return: int
        """

        exists = False
        count = 0

        while not exists and count < 100:
            a = '{}_{}'.format(attr, count)
            LOGGER.debug('|get_next_available_sequential_attr_index| >> {}'.format(a))
            if MetaAttributeUtils.has_attr(node, a):
                count += 1
            else:
                exists = True
                return count

        return False

    @staticmethod
    def data_list_purge(node=None, attr=None, data_attr=None):
        """
        Purges a messageList if it exists in the given node
        :param node: str
        :param attr:  str, name of the messageList attribute
        :param data_attr:
        :return: bool
        """

        from tpDcc.dccs.maya.meta import metanode

        fn_name = 'data_list_purge'

        attrs_dict = MetaDataListUtils.get_sequential_attr_dict(node, attr)
        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        for k in attrs_dict.keys():
            str_attr = attrs_dict[k]
            MetaAttributeUtils.delete(node, str_attr)
            LOGGER.debug('|{}| >> Removed: {}.{}'.format(fn_name, node, str_attr))

        try:
            mn = metanode.MetaNode(node)
            if mn.has_attr(data_attr):
                MetaAttributeUtils.delete(node, data_attr)
                LOGGER.debug('|{}| >> Removed: {}.{}'.format(fn_name, node, data_attr))
        except Exception:
            pass

        return True

    @staticmethod
    def data_list_exists(node=None, attr=None, mode=None, data_attr=None):
        """
        Checks if messageList attr exists in given node
        :param node:
        :param attr:
        :param mode:
        :param data_attr:
        :return:
        """

        attrs_dict = MetaDataListUtils.get_sequential_attr_dict(node, attr)
        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        for i, k in enumerate(attrs_dict.keys()):
            str_attr = attrs_dict[k]
            if mode == 'message':
                if MetaAttributeUtils.get_message(node, str_attr, data_attr):
                    return True
            elif MetaAttributeUtils.get(node, str_attr) is not None:
                return True

        return False

    @staticmethod
    def data_list_connect(node=None, attr=None, data=None, mode=None, data_attr=None):
        """
        Multimessage data is not ordered by default. Using this function we can add handle multiMessage lists
        through indexes
        :param node: str, node to add messageList attr
        :param attr: str, name of the messageList attribute
        :param data:
        :param mode:
        :param data_attr:
        :return: bool
        """

        from tpDcc.dccs.maya.meta import metanode

        fn_name = 'data_list_connect'

        data_list = MetaAttributeValidator.list_arg(data)
        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        LOGGER.info("|{0}| >> node: {1} | attr: {2} | mode: {3}".format(fn_name, node, attr, mode))
        LOGGER.info("|{0}| >> data | len: {1} | list: {2}".format(fn_name, len(data_list), data_list))

        attrs_list = MetaDataListUtils.data_list_get_attrs(node=node, attr=attr)
        driven_dict = dict()
        for i, a in enumerate(attrs_list):
            driven = MetaAttributeUtils.get_driven(node=node, attr=a)
            if driven:
                driven_dict[i] = driven
            else:
                driven_dict[i] = False

        MetaDataListUtils.data_list_purge(node=node, attr=attr)

        meta_node = metanode.MetaNode(node)

        if mode == 'message':
            MetaMessageListUtils.message_list_connect(node=node, attr=attr, data=data_list, data_attr=data_attr)
        else:
            for i, d in enumerate(data_list):
                attr_str = '{}_{}'.format(attr, i)
                MetaDataListUtils.store_info(node, attr_str, data, mode)
                plug = driven_dict.get(i)
                if plug:
                    for p in plug:
                        try:
                            MetaAttributeUtils.connect('{}.{}'.format(node, attr_str), p)
                        except Exception as e:
                            LOGGER.warning(
                                "|{0}| >> Failed to reconnect {1} | driven: {2} | err: {3}".format(fn_name, attr_str, p,
                                                                                                   e))

        return True

    @staticmethod
    def data_list_get(node=None, attr=None, mode=None, data_attr=None, cull=False, as_meta=True):
        """
        Return messageList
        :param node:
        :param attr:
        :param mode:
        :param data_attr:
        :param cull:
        :param as_meta: bool
        :return:
        """

        from tpDcc.dccs.maya.meta import metanode

        fn_name = 'data_list_get'

        if mode is not None:
            _mode = MetaAttributeUtils.validate_attr_type_name(mode)
        else:
            _mode = mode
        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        LOGGER.debug('|{}| >> node: {} | attr: {} | mode: {} | cull: {}'.format(fn_name, node, attr, _mode, cull))

        attrs_dict = MetaDataListUtils.get_sequential_attr_dict(node, attr)

        return_list = list()

        for k in attrs_dict.keys():
            if _mode == 'message':
                res = MetaAttributeUtils.get_message(node, attrs_dict[k], data_attr, k) or False
                if res:
                    res = res[0]
            else:
                try:
                    res = MetaAttributeUtils.get(node, attrs_dict[k])
                except Exception as e:
                    LOGGER.warning('|{}| >> {}.{} failed" || err: {}'.format(fn_name, node, attrs_dict[k], e))
                    res = None

            if issubclass(type(res), list):
                if _mode == 'message' or maya.cmds.objExists(res[0]):
                    return_list.extend(res)
                else:
                    return_list.append(res)
            else:
                return_list.append(res)

        if cull:
            return_list = [o for o in return_list if o]
        if return_list.count(False) == len(return_list):
            return list()

        if as_meta:
            return_list = metanode.validate_obj_list_arg(return_list, none_valid=True)

        return return_list

    @staticmethod
    def data_list_get_attrs(node=None, attr=None):
        """
        Get the attributes of a dataList
        :param node: str
        :param attr: str, base name for the data list (becomes attr_0, attr_1, etc)
        :return: bool
        """

        attrs_dict = MetaDataListUtils.get_sequential_attr_dict(node=node, attr=attr)
        return [attrs_dict[i] for i in attrs_dict.keys()]

    @staticmethod
    def data_list_index(node=None, attr=None, data=None, mode=None, data_attr=None):
        """
        Index a value in a given dataList
        :param node: str
        :param attr: str, base name for the dataList
        :param data: str, data to index
        :param mode: str, what kind of data to be looking for
        :param data_attr:
        :return: bool
        """

        fn_name = 'data_list_index'

        LOGGER.debug('|{}| >> node: {} | attr: {} | data: {} | mode: {}'.format(fn_name, node, attr, data, mode))

        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        data_list = MetaDataListUtils.data_list_get(node=node, attr=attr, mode=mode, data_attr=data_attr, cull=False)
        index = None

        if mode == 'message':
            long_list = [name_utils.get_long_name(o) for o in data_list]
            long_str = name_utils.get_long_name(data)
            if long_str in long_list:
                index = long_list.index(long_str)
        elif data in data_list:
            if data_list.count(data) > 1:
                raise ValueError('More that one entry!')
            else:
                index = data_list.index(data)

        if index is None:
            LOGGER.info(
                '|{}| >> Data not found! node: {} | attr: {} | data: {} | mode: {}'.format(fn_name, node, attr, data,
                                                                                           mode))
            LOGGER.info('|{}| >> values ....'.format(fn_name))
            for i, v in enumerate(data_list):
                LOGGER.info('idx: {} | {}'.format(i, v))
            raise ValueError('Data not found!')

        return index

    @staticmethod
    def data_list_append(node=None, attr=None, data=None, mode=None, data_attr=None):
        """
        Append node to dataList
        :param node:
        :param attr:
        :param data:
        :param data:
        :param mode:
        :param data_attr:
        :return: bool
        """

        fn_name = 'data_list_append'

        LOGGER.debug('|{}| >> node: {} | attr: {} | data: {} | mode: {}'.format(fn_name, node, attr, data, data_attr))

        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        data_list = MetaDataListUtils.data_list_get(node, attr, mode, data_attr, False)
        data_len = len(data_list)
        index = data_len

        if mode == 'message':
            MetaAttributeUtils.set_message(node, '{}_{}'.format(attr, index), data, data_attr, data_key=index)
        else:
            MetaDataListUtils.store_info(node, '{}_{}'.format(attr, index), data)

        return index

    @staticmethod
    def data_list_remove(node=None, attr=None, data=None, mode=None, data_attr=None):
        """
        Returns node from dataList
        :param node:
        :param attr:
        :param data:
        :param mode:
        :param data_attr:
        :return: bool
        """

        fn_name = 'data_list_remove'

        LOGGER.debug('|{}| >> node: {} | attr: {} | data: {} | mode: {}'.format(fn_name, node, attr, data, data_attr))

        data = MetaAttributeValidator.list_arg(data)
        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        attrs_dict = MetaDataListUtils.get_sequential_attr_dict(node=node, attr=attr)

        action = False
        if mode == 'message':
            data = MetaAttributeValidator.obj_string_list(args_list=data, called_from=fn_name)
            data_long_list = [name_utils.get_long_name(o) for o in data]
            for i in attrs_dict.keys():
                o_msg = MetaAttributeUtils.get_message(node, attrs_dict[i], '{}_datdict'.format(attr), data_key=i)
                if o_msg and name_utils.get_long_name(o_msg) in data_long_list:
                    LOGGER.debug(
                        '|{}| >> removing | idx: {} | attr: {} | value: {}'.format(fn_name, i, attrs_dict[i], o_msg))
                    MetaAttributeUtils.delete(node, attrs_dict[i])
                    action = True
        else:
            attrs_dict = MetaDataListUtils.get_sequential_attr_dict(node=node, attr=attr)
            for i in attrs_dict.keys():
                value = MetaAttributeUtils.get(node, attrs_dict[i])
                if value in data:
                    LOGGER.debug(
                        '|{}| >> removing | idx: {} | attr: {} | value: {}'.format(fn_name, i, attrs_dict[i], value))
                    MetaAttributeUtils.delete(node, attrs_dict[i])
                    action = True

        return action

    @staticmethod
    def data_list_remove_by_index(node=None, attr=None, indices=None):
        """
        Removes dataList message elements by their indices
        :param node: str
        :param attr: str, base name for the dataList attribute
        :param indices: list<int>, indices you want to remove
        :return: bool
        """

        fn_name = 'data_list_remove_by_index'
        indices = MetaAttributeValidator.list_arg(indices)
        attrs_dict = MetaDataListUtils.get_sequential_attr_dict(node=node, attr=attr)

        LOGGER.debug('|{}| >> node: {} | attr: {} | indices: {}'.format(fn_name, node, attr, indices))

        for i in attrs_dict.keys():
            if i in indices:
                LOGGER.warning('|{}| >> removing... | idx: {} | attr: {}'.format(fn_name, i, attrs_dict[i]))
                MetaAttributeUtils.delete(node, attrs_dict[i])

        return True

    @staticmethod
    def data_list_clean(node=None, attr=None, mode=None, data_attr=None):
        """
        Removes dead data from a dataList and reconnect if the data is the data continue in the scene
        :param node: str
        :param attr: str, bae name for the dataList attribute
        :param mode: str, what kind of data to be looking for
        :param data_attr:
        :return: bool
        """

        fn_name = 'data_list_remove'

        LOGGER.debug('|{}| >> node: {} | attr: {} | mode: {}'.format(fn_name, node, attr, data_attr))

        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        data_list = MetaDataListUtils.data_list_get(node=node, attr=attr, mode=mode, data_attr=data_attr, cull=True)

        if mode == 'message':
            return MetaMessageListUtils.message_list_connect(node=node, attr=attr, data=data_list, data_attr=data_attr)
        else:
            return MetaDataListUtils.data_list_connect(node=node, attr=attr, data=data_list, mode=mode,
                                                       data_attr=data_attr)

    @staticmethod
    def store_info(node=None, attr=None, data=None, attr_type=None, lock=True):
        """
        Stores information to an attribute (supports: message, doubleArray, json dicts, etc)
        :param node: str
        :param attr: str, base name for the dataList
        :param data: data to add
        :param attr_type: variant (if not given, will be picked best guess)
        :param lock: bool
        :return: bool
        """

        from tpDcc.dccs.maya.meta import metanode

        try:
            fn_name = 'store_info'
            data = MetaAttributeValidator.list_arg(data)
            if attr_type is None:
                _meta_node = False
                try:
                    data = [o.meta_node for o in data]
                    _meta_node = True
                    attr_type = 'message'
                    LOGGER.debug('|{}| >> meta node no art passed...'.format(fn_name))
                except Exception:
                    pass

                if not _meta_node:
                    if len(data) == 3:
                        attr_type = 'double3'
                    elif len(data) > 3:
                        attr_type = 'doubleArray'

            LOGGER.debug(
                "|{}| >> node: {} | attr: {} | data: {} | attrType: {}".format(fn_name, node, attr, data, attr_type))

            # STORE DATA
            if attr_type == ['message', 'msg', 'messageSimple']:
                LOGGER.debug('|{}| >> message...'.format(fn_name))
                MetaAttributeUtils.set_message(message_holder=node, message_attr=attr, message=data)
            elif attr_type in ['double3']:
                LOGGER.debug('|{}| >> list...'.format(fn_name))
                meta_node = metanode.MetaNode(node=node)
                if meta_node.has_attr(attr=attr):
                    try:
                        MetaAttributeUtils.set(node=node, attr=attr, value=data)
                    except Exception:
                        LOGGER.warning(
                            '|{}| >> removing... | node: {} | attr: {} | value: {}'.format(fn_name, node, attr,
                                                                                           meta_node.__getattribute__(
                                                                                               attr)))
                        MetaAttributeUtils.delete(node=node, attr=attr)
                        meta_node.add_attribute(attr=attr, value=data, attr_type=attr_type)
                else:
                    meta_node.add_attribute(attr=attr, value=data, attr_type=attr_type)
            else:
                LOGGER.debug('|{}| >> default...'.format(fn_name))
                meta_node = metanode.MetaNode(node=node)
                if meta_node.has_attr(attr=attr):
                    try:
                        MetaAttributeUtils.set(node=node, attr=attr, value=data[0])
                    except Exception:
                        LOGGER.warning(
                            '|{}| >> removing... | node: {} | attr: {} | value: {}'.format(fn_name, node, attr,
                                                                                           meta_node.__getattribute__(
                                                                                               attr)))
                        MetaAttributeUtils.delete(node=node, attr=attr)
                        meta_node.add_attribute(attr=attr, value=data[0], attr_type=attr_type)
                else:
                    meta_node.add_attribute(attr=attr, value=data[0], attr_type=attr_type)

            if lock:
                MetaAttributeUtils.set_lock(node, attr, lock)

            return True
        except Exception as e:
            raise Exception(e)


class MetaMessageListUtils(object):

    @staticmethod
    def message_list_purge(node=None, attr=None, data_attr=None):
        """
        Purges a messageList if it exists in the given node
        :param node: str
        :param attr:  str, name of the messageList attribute
        :param data_attr:
        :return: bool
        """

        return MetaDataListUtils.data_list_purge(node=node, attr=attr, data_attr=data_attr)

    @staticmethod
    def message_list_exists(node=None, attr=None, data_attr=None):
        """
        Checks if messageList attr exists in given node
        :param node:
        :param attr:
        :param data_attr:
        :return:
        """

        return MetaDataListUtils.data_list_exists(node=node, attr=attr, mode='message', data_attr=data_attr)

    @staticmethod
    def message_list_get(node=None, attr=None, data_attr=None, cull=False, as_meta=True):
        """
        Return messageList
        :param node:
        :param attr:
        :param data_attr:
        :param cull:
        :return:
        """

        return MetaDataListUtils.data_list_get(node=node, attr=attr, mode='message', data_attr=data_attr, cull=cull,
                                               as_meta=as_meta)

    @staticmethod
    def message_list_connect(node=None, attr=None, data=None, connect_back=None, data_attr=None):
        """
        Multimessage data is not ordered by default. Using this function we can add handle multiMessage lists
        through indexes
        :param node: str, node to add messageList attr
        :param attr: str, name of the messageList attribute
        :param data:
        :param connect_back:
        :param data_attr:
        :return: bool
        """

        from tpDcc.dccs.maya.meta import metanode

        fn_name = 'message_list_connect'

        data = MetaAttributeValidator.meta_node_string_list(data)
        if data_attr is None:
            data_attr = '{}_datdict'.format(attr)

        LOGGER.debug(
            '|{}| >> node: {} | attr: {} | connect_back: {} | data_attr: {}'.format(fn_name, node, attr, connect_back,
                                                                                    data_attr))
        LOGGER.debug('|{}| >> data | len: {} | list: {}'.format(fn_name, len(data), data))

        MetaMessageListUtils.message_list_purge(node, attr)

        # TODO: Doing this call we force that Instanced meta nodes have same number of arguments
        # TODO: as MetaNode class. Find a fix to this
        meta_node = metanode.MetaNode(node)

        for i, k in enumerate(data):
            str_attr = '{}_{}'.format(attr, i)
            MetaAttributeUtils.set_message(node, str_attr, k, data_attr, i)
            if connect_back is not None:
                if '.' in k:
                    n = k.split('.')[0]
                else:
                    n = k
                MetaAttributeUtils.set_message(n, connect_back, node, simple=True)

        return True

    @staticmethod
    def message_list_set(node=None, attr=None, data=None, connect_back=None, data_attr=None):
        return MetaMessageListUtils.message_list_connect(node=node, attr=attr, data=data, connect_back=connect_back,
                                                         data_attr=data_attr)

    @staticmethod
    def message_list_get_attrs(node=None, attr=None):
        return MetaDataListUtils.data_list_get_attrs(node=node, attr=attr)

    @staticmethod
    def message_list_index(node=None, attr=None, data=None, data_attr=None):
        return MetaDataListUtils.data_list_index(node=node, attr=attr,
                                                 data=MetaAttributeValidator.meta_node_string(data), mode='message',
                                                 data_attr=data_attr)

    @staticmethod
    def message_list_append(node=None, attr=None, data=None, connect_back=None, data_attr=None):
        data = MetaAttributeValidator.meta_node_string(data)
        result = MetaDataListUtils.data_list_append(node=node, attr=attr, data=data, mode='message',
                                                    data_attr=data_attr)
        if connect_back is not None:
            MetaAttributeUtils.set_message(data, connect_back, node, data_attr)

        return result

    @staticmethod
    def message_list_remove(node=None, attr=None, data=None, data_attr=None):
        return MetaDataListUtils.data_list_remove(node=node, attr=attr,
                                                  data=MetaAttributeValidator.meta_node_string(data), mode='message',
                                                  data_attr=data_attr)

    @staticmethod
    def message_list_remove_by_index(node=None, attr=None, indices=None):
        return MetaDataListUtils.data_list_remove_by_index(node=node, attr=attr, indices=indices)

    @staticmethod
    def message_list_clean(node=None, attr=None, data_attr=None):
        return MetaDataListUtils.data_list_clean(node=node, attr=attr, mode='message', data_attr=data_attr)


class MetaTransformUtils(object):

    @staticmethod
    def get_rotate_pivot(node=None):
        """
        Returns the world space rotate pivot of a given node
        :param node: str, node to query
        :return: variant, list | euclid.Vector3
        """

        node = MetaAttributeValidator.meta_node_string(node)
        result = maya.cmds.xform(node, query=True, ws=True, rp=True)
        LOGGER.debug('|{}| >> [{}] = {}'.format('get_rotate_pivot', node, result))

        return result

    @staticmethod
    def get_scale_pivot(node=None):
        """
        Returns the world space scale pivot of a given node
        :param node: str, node to query
        :return: list | euclid.Vector3
        """

        node = MetaAttributeValidator.meta_node_string(node)
        result = maya.cmds.xform(node, query=True, ws=True, sp=True)
        LOGGER.debug('|{}| >> [{}] = {}'.format('get_scale_pivot', node, result))

        return result

    @staticmethod
    def get_parent(node=None, full_path=True):
        """
        Get parent of the given node
        :param node: str, object to get parents of
        :param full_path: bool, whether you want long names or not
        :return: list<str>
        """

        node = MetaAttributeValidator.meta_node_string(node)

        LOGGER.debug('|Parent Getter| >> node: {}'.format(node))
        parents = maya.cmds.listRelatives(node, parent=True, type='transform', fullPath=full_path) or False
        if parents:
            return parents[0]

        return False

    @staticmethod
    def set_parent(node=None, parent=False):
        """
        Parente transform and returns new names
        :param node: str, object to modify hierarhcy
        :param parent: str, parent node or False/None for parent to world (unparent)
        :return: str, new name
        """

        node = MetaAttributeValidator.meta_node_string(node)
        if parent:
            parent = MetaAttributeValidator.meta_node_string(parent)

        LOGGER.debug('|Parent Setter| >> node: {}'.format(node))
        LOGGER.debug('|Parent Setter| >> parent: {}'.format(parent))

        parents = maya.cmds.listRelatives(node, parent=True, type='transform')
        if parent:
            try:
                return maya.cmds.parent(node, parent)[0]
            except Exception as e:
                LOGGER.debug('|Parent Setter| >> Failed to parent "{}" to "{}" | error: {}'.format(node, parent, e))
                return node
        else:
            if parents:
                return maya.cmds.parent(node, world=True)[0]
            else:
                return node

    @staticmethod
    def get_parents(node=None, full_path=True):
        """
        Get all parents of a given node where the last parent is the top of the hierarchy
        :param node: str, object to check
        :param full_path: bool, whether you want long names or not
        :return: list<str>
        """

        node = MetaAttributeValidator.meta_node_string(node)

        list_parents = list()
        tmp_obj = node
        no_parent = False
        while not no_parent:
            tmp_parent = maya.cmds.listRelatives(tmp_obj, allParents=True, fullPath=True)
            if tmp_parent:
                if len(tmp_parent) > 1:
                    raise ValueError(
                        'Do not know what to do with multiple parents ... {0} | {1}'.format(node, tmp_parent))
                list_parents.append(tmp_parent[0])
                tmp_obj = tmp_parent[0]
            else:
                no_parent = True

        if not full_path:
            return [name_utils.get_short_name(o) for o in list_parents]

        return list_parents

    @staticmethod
    def get_children(node=None, full_path=False):
        """
        Get the immediate children of a given node
        :param node: object to check
        :param full_path: bool, whether you want long names or not
        :return: list<str>
        """

        node = MetaAttributeValidator.meta_node_string(node)

        return maya.cmds.listRelatives(node, children=True, type='transform', fullPath=full_path) or []

    @staticmethod
    def get_descendents(node=None, full_path=False):
        """
        Get all children of a given node
        :param node: str, object to check
        :param full_path: bool, whether you want long names or not
        :return: list<str>
        """

        node = MetaAttributeValidator.meta_node_string(node)

        return maya.cmds.listRelatives(node, allDescendents=True, type='transform', fullPath=full_path) or []

    @staticmethod
    def get_shapes(node=None, full_path=False, intermediates=False, non_intermediates=True):
        """
        Get shapes of a given node
        :param node: object to check
        :param full_path: bool, whether you want long names or not
        :param intermediates: bool, list intermediate shapes
        :param non_intermediates: bool, list non intermediate shapes
        :return: list<str>
        """

        node = MetaAttributeValidator.meta_node_string(node)

        return shape_utils.get_shapes(node, intermediates=intermediates, non_intermediates=non_intermediates,
                                      full_path=full_path) or []

    def snap(self, node=None, target=None, position=True, rotation=True, rotate_axis=False, rotate_order=False,
             scale_pivot=False, pivot='rp', space='w', mode='xform'):
        """
        Function that snaps source object to target
        :param source:
        :param target:
        :param position:
        :param rotation:
        :param rotate_axis:
        :param rotate_order:
        :param scale_pivot:
        :param pivot:
        :param space:
        :param mode:
        :return:
        """

        fn_name = 'snap'

        node = node.meta_node
        node = MetaAttributeValidator.meta_node_string(node)
        target = MetaAttributeValidator.meta_node_string(target)

        pivot = MetaAttributeValidator.kwargs_from_dict(pivot, common.PIVOT_ARGS, none_valid=False,
                                                        called_from=__name__ + fn_name + '>> validate pivot')
        space = MetaAttributeValidator.kwargs_from_dict(space, common.SPACE_ARGS, none_valid=False,
                                                        called_from=__name__ + fn_name + '>> validate space')
        LOGGER.debug(
            '|{}| >> obj: {} | target: {} | pivot: {} | space: {} | mode: {}'.format(fn_name, node, target, pivot,
                                                                                     space, mode))
        LOGGER.debug(
            '|{}| >> position: {} | rotation: {} | rotate_axis: {} | rotate_order: {}'.format(fn_name, position,
                                                                                              rotation, rotate_axis,
                                                                                              rotate_order))

        kwargs = {'ws': False, 'os': False}
        if space == 'world':
            kwargs['ws'] = True
        else:
            kwargs['os'] = True

        if position:
            kwargs_move = copy.copy(kwargs)
            if pivot == 'sp':
                kwargs_move['spr'] = True
            else:
                kwargs_move['rpr'] = True

            if pivot == 'closestPoint':
                LOGGER.debug('|{}| <<< closestPoint >>>'.format(fn_name))
                target_type = MetaAttributeValidator.get_maya_type(target)
                dst = None
