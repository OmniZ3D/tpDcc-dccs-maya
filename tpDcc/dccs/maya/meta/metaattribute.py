#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with meta attributes
"""

from __future__ import print_function, division, absolute_import

import copy
import logging

import tpDcc.dccs.maya as maya
from tpDcc.libs.python import decorators
from tpDcc.dccs.maya.meta import metautils

LOGGER = logging.getLogger()


class MetaAttribute(object):
    """
    Utility class that contains functions to work on DCC dependant node attributes
    """

    attr_types = dict(message=('message', 'msg', 'm'),
                      double=('float', 'fl', 'f', 'doubleLinear', 'doubleAngle', 'double', 'd'),
                      string=('string', 's', 'str'), long=('long', 'int', 'i', 'integer'), short=('short', 'shrt'),
                      bool=('bool', 'b', 'boolean'), enum=('enum', 'options', 'e'),
                      double3=('double3', 'd3', 'vector', 'vec', 'v'),
                      float3=('vector', 'vec'), multi=('multi', 'm'))

    def __init__(self, obj_name=None, attr_name=None, attr_type=False, value=None, enum=None, lock=None,
                 keyable=None, hidden=None, min_value=None, max_value=None, default_value=None, *args, **kwargs):
        """
        Checks the attribute existance and initializes it. If an existing attribute name of an object is called and
        the attribute type is different, the attribute type is converted automatically.
        :param obj_name: variant, str, MetaNode
        :param attr_name: str, name of the attribute we want to initialize
        :param attr_type: str, must be a valid attribute type
        :param value: variant, set value on creation
        :param enum:
        :param lock:
        :param keyable:
        :param hidden:
        :param min_value:
        :param max_value:
        :param default_value:
        :param args:
        :param kwargs:
        """

        super(MetaAttribute, self).__init__()

        self.obj = None
        self.attr = attr_name
        self.attr_type = attr_type

        try:
            obj_name.meta_node
            self.obj = obj_name
        except Exception:
            from tpRigToolkit.core.meta import metanode
            assert maya.cmds.objExists(obj_name) is True, '"{}" does not exists!'.format(obj_name)
            self.obj = metanode.MetaNode(obj_name)

        if attr_type:
            attr_type = metautils.MetaAttributeUtils.validate_attr_type_name(attr_type)
        if enum is not None:
            self.attr_type = 'enum'
        elif value and attr_type is False and not self.obj.has_attr(attr_name):
            if type(value) is list:
                for o in value:
                    if maya.cmds.objExists(o):
                        self.attr_type = 'message'
                        LOGGER.debug('MultiMessage mode!')
                        break
                    self.attr_type = 'double3'
            elif maya.cmds.objExists(value):
                self.attr_type = 'message'
            else:
                self.attr_type = metautils.MetaAttributeUtils.validate_attr_type_name(attr_type)
        else:
            self.attr_type = metautils.MetaAttributeUtils.validate_attr_type_name(attr_type)

        self.attr = attr_name

        if maya.cmds.objExists('{0}.{1}'.format(self.obj.meta_node, attr_name)):
            current_type = maya.cmds.getAttr('{0}.{1}'.format(self.obj.meta_node, attr_name), type=True)
            if not metautils.MetaAttributeUtils.validate_attr_type_match(self.attr_type,
                                                                         current_type) and self.attr_type is not False:
                if self.obj.is_referenced():
                    LOGGER.error(
                        '"{0}" is referenced. Cannot convert "{1}" to "{2}"!'.format(self.obj.meta_node, attr_name,
                                                                                     attr_type))
                self.convert(self.attr_type)
            else:
                self.attr = attr_name
                self.attr_type = current_type
        else:
            try:
                _type = self.attr_type
                if not _type:
                    _type = 'string'
                metautils.MetaAttributeUtils.add(self.obj.meta_node, attr_name, _type)
            except StandardError as e:
                LOGGER.error(
                    '|Attribute Add| >> Failed" "{0}" failed to add "{1}" | type: {2}'.format(self.obj.meta_node,
                                                                                              attr_name,
                                                                                              self.attr_type))
                raise StandardError(e)

        if enum:
            try:
                self.set_enum(enum)
            except Exception:
                LOGGER.error('Failed to set enum value of "{}"'.format(enum))

        if value is not None:
            self.set(value)

        if min_value is not None:
            try:
                self.min_value = min_value
            except Exception:
                LOGGER.error('|Attribute Add| >> min value on call failure!'.format(min_value))

        if max_value is not None:
            try:
                self.max_value = max_value
            except Exception:
                LOGGER.error('|Attribute Add| >> max value on call failure!'.format(min_value))

        if default_value is not None:
            try:
                self.default_value = default_value
            except Exception:
                LOGGER.error('|Attribute Add| >> default value on call failure!'.format(min_value))

        if keyable is not None:
            self.set_keyable(keyable)

        if hidden is not None:
            self.set_hidden(hidden)

        if lock is not None:
            self.set_locked(lock)

    def __repr__(self):
        try:
            return '{0}(node: "{1}", attr: "{2}"'.format(self.__class__, self.obj.short_name, self.attr)
        except Exception:
            return self

    def get_long_name(self):
        return metautils.MetaAttributeUtils.get_name_long(self.obj.meta_node, self.attr)

    def get_combined_name(self):
        return '{0}.{1}'.format(self.obj.meta_node, self.attr)

    def get_combined_short_name(self):
        return '{0}.{1}'.format(self.obj.get_short_name(), self.attr)

    def get_alias(self):
        """
        Return attribute alias name
        :return: str
        """

        if maya.cmds.aliasAttr(self.combined_name, query=True):
            return maya.cmds.aliasAttr(self.combined_name, query=True)

        return None

    def set_alias(self, alias):
        """
        Set the alias of an attribute
        :param alias: str, name you want to use as an attribute alias
        """

        try:
            alias = metautils.MetaAttributeValidator.string_arg(alias)
            if alias:
                try:
                    if alias != self.name_alias:
                        return maya.cmds.aliasAttr(alias, self.combined_name)
                    else:
                        LOGGER.debug('{0}.{1} already has that alias!'.format(self.obj.get_short_name(), self.attr))
                except Exception:
                    LOGGER.warning('{0}.{1} failed to set alias of {2}'.format(self.obj.meta_node, self.attr, alias))
            else:
                if self.name_alias:
                    self.attr = self.long_name
                    maya.cmds.aliasAttr(self.combined_name, remove=True)
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, alias, e]
            LOGGER.error('{0}.{1}.set_alias() | arg: {2} | error: {3}'.format(*fmt_args))

    def get_nice_name(self):
        """
        Returns attribute's nice name
        :return: str
        """

        return maya.cmds.attributeQuery(self.attr, node=self.obj.meta_node, niceName=True) or False

    def set_nice_name(self, nice_name):
        """
        Set the nice name of the attribute
        :param nice_name:
        :return:
        """
        return metautils.MetaAttributeUtils.rename_nice(self.obj.meta_node, self.attr, nice_name)

    def get(self, *args, **kwargs):
        """
        Get and store attribute value based on attribute type
        :param args:
        :param kwargs:
        :return: variant
        """

        try:
            if self.attr_type == 'message':
                return metautils.MetaAttributeUtils.get_message(self.obj.meta_node, self.attr)
            else:
                return metautils.MetaAttributeUtils.get(self.obj.meta_node, self.attr)
        except Exception as e:
            LOGGER.warning('{0} failed to get | {1}'.format(self.combined_name, e))

    def set(self, value, *args, **kwargs):
        """
        Set attribute value based on attribute type
        :param value: variant
        :param args:
        :param kwargs:
        """

        try:
            if self.obj.has_attr(self.attr):
                if self.attr_type == 'message':
                    self.store(value)
                elif self.get_children():
                    for i, c in enumerate(self.get_children()):
                        try:
                            child_attr = MetaAttribute(self.obj.meta_node, c)
                            # If we have the same length of values in our list as we have children, use them
                            if type(value) is list and len(self.get_children()) == len(value):
                                child_attr.value = value[i]
                            else:
                                metautils.MetaAttributeUtils.set(child_attr.obj.meta_node, child_attr.attr, value,
                                                                 *args, **kwargs)
                        except Exception as e:
                            fmt_args = [c, e]
                            LOGGER.error('On child: {0} | error: {1}'.format(*fmt_args))
                else:
                    metautils.MetaAttributeUtils.set(self.obj.meta_node, self.attr, value, *args, **kwargs)

            object.__setattr__(self, self.attr, self.value)
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, value, e]
            LOGGER.error('{0}.{1}.set() | arg: {2} | error: {3}'.format(*fmt_args))

    def rename(self, name):
        """
        Rename an attribute
        :param name: str, name you want to use as new name
        """

        result = metautils.MetaAttributeUtils.rename(self.obj.meta_node, self.attr, name)
        if result:
            self.attr = name
        return self.attr

    def remove(self):
        """
        Deletes an attribute
        """

        try:
            metautils.MetaAttributeUtils.delete(self.obj.meta_node, self.attr)
            LOGGER.warning('{} deleted!'.format(self.combined_name))
            del (self)
        except Exception:
            LOGGER.error('{} failed to delete!'.format(self.obj.meta_node, self.attr))

    def get_locked(self):
        """
        Get lock state of the attribute
        :param lock: bool
        :return:
        """

        return maya.cmds.getAttr(self.combined_name, lock=True)

    def set_locked(self, lock=True):
        """
        Set lock state of the attribute
        :param lock: bool
        """

        try:
            lock = metautils.MetaAttributeValidator.bool_arg(lock)
            if lock:
                if self.get_children():
                    for c in self.get_children():
                        child_attr = MetaAttribute(self.obj.meta_node, c)
                        if not child_attr.locked:
                            maya.cmds.setAttr(child_attr.obj.meta_node + '.' + child_attr.attr, edit=True, lock=True)
                elif not self.locked:
                    maya.cmds.setAttr(self.obj.meta_node + '.' + self.attr, edit=True, lock=True)
            else:
                if self.get_children():
                    for c in self.get_children():
                        child_attr = MetaAttribute(self.obj.meta_node, c)
                        if child_attr.locked:
                            maya.cmds.setAttr(child_attr.obj.meta_node + '.' + child_attr.attr, edit=True, lock=False)
                elif self.locked:
                    maya.cmds.setAttr(self.obj.meta_node + '.' + self.attr, edit=True, lock=False)
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, lock, e]
            LOGGER.error('{0}.{1}.set_locked() | arg: {2} | error: {3}'.format(*fmt_args))

    def get_keyable(self):
        """
        Get keyable state of the attribute
        :return: bool
        """

        return maya.cmds.getAttr(self.combined_name, keyable=True)

    def set_keyable(self, keyable):
        """
        Set keyable state of the attribute
        :param keyable: bool
        """

        keyable_types = ['long', 'float', 'bool', 'double', 'enum', 'double3', 'doubleAngle', 'doubleLinear']

        try:
            keyable = metautils.MetaAttributeValidator.bool_arg(keyable)

            if self.attr_type in keyable_types:
                if keyable:
                    if self.get_children():
                        for c in self.get_children():
                            child_attr = MetaAttribute(self.obj.meta_node, c)
                            if not child_attr.keyable:
                                maya.cmds.setAttr(child_attr.obj.meta_node + '.' + child_attr.attr, edit=True,
                                                  keyable=True)
                                self.hidden = False
                    elif not self.keyale:
                        maya.cmds.setAttr(self.obj.meta_node + '.' + self.attr, edit=True, keyable=True)
                        self.hidden = False
                else:
                    if self.get_children():
                        for c in self.get_children():
                            child_attr = MetaAttribute(self.obj.meta_node, c)
                            if child_attr.keyable:
                                maya.cmds.setAttr(child_attr.obj.meta_node + '.' + child_attr.attr, edit=True,
                                                  keyable=False)
                                if not maya.cmds.getAttr(child_attr.combined_name, channelBox=True):
                                    child_attr.set_hidden(False)
                    elif self.keyable:
                        maya.cmds.setAttr(self.obj.meta_node + '.' + self.attr, edit=True, keyable=False)
                        if not maya.cmds.getAttr(self.combined_name, channelBox=True):
                            self.set_hidden(False)
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, keyable, e]
            LOGGER.error('{0}.{1}.set_keyable() | arg: {2} | error: {3}'.format(*fmt_args))

    def get_hidden(self):
        """
        Get hidden state of the attribute
        :return: bool
        """

        hidden = not maya.cmds.getAttr(self.combined_name, channelBox=True)
        if self.keyable:
            hidden = maya.cmds.attributeQuery(self.long_name, node=self.obj.meta_node, hidden=True)

        return hidden

    def set_hidden(self, hide):
        """
        Set hidden state of the attribute
        :param hide: bool
        """

        try:
            hide = metautils.MetaAttributeValidator.bool_arg(hide)
            if hide:
                if self.get_children():
                    for c in self.get_children():
                        child_attr = MetaAttribute(self.obj.meta_node, c)
                        if not child_attr.hidden:
                            if child_attr.keyable:
                                child_attr.set_keyable(False)
                            maya.cmds.setAttr(child_attr.obj.meta_node + '.' + child_attr.attr, edit=True,
                                              channelBox=False)
                elif not self.hidden:
                    if self.keyable:
                        self.set_keyable(False)
                    maya.cmds.setAttr(self.obj.meta_node + '.' + self.attr, edit=True, channelBox=False)
            else:
                if self.get_children():
                    for c in self.get_children():
                        child_attr = MetaAttribute(self.obj.meta_node, c)
                        if child_attr.hidden:
                            maya.cmds.setAttr(child_attr.obj.meta_node + '.' + child_attr.attr, edit=True,
                                              channelBox=True)
                elif self.hidden:
                    maya.cmds.setAttr(self.obj.meta_node + '.' + self.attr, edit=True, channelBox=True)
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, hide, e]
            LOGGER.error('{0}.{1}.set_hidden() | arg: {2} | error: {3}'.format(*fmt_args))

    def get_default_value(self):
        """
        Returns default value of the numeric attribute
        :return: variant
        """

        if not self.is_numeric():
            return False

        try:
            default_value = maya.cmds.attributeQuery(self.long_name, node=self.obj.meta_node, listDefault=True)
            if default_value:
                return default_value[0]
            else:
                return False
        except StandardError:
            return False

    def set_default_value(self, value=None):
        """
        Set default setting value of the numeric attribute
        :param value:  value or False to reset
        """

        try:
            if self.is_numeric():
                if value is not None:
                    if self.get_children():
                        for c in self.get_children():
                            child_attr = MetaAttribute(self.obj.meta_node, c)
                            try:
                                maya.cmds.addAttr(child_attr.obj.meta_node + '.' + child_attr.attr, edit=True,
                                                  defaultValue=value)
                            except StandardError:
                                LOGGER.debug('"{}" failed to set a default value'.format(child_attr.combined_name))
                    else:
                        try:
                            maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, defaultValue=value)
                        except StandardError:
                            LOGGER.debug('"{}" failed to set a default value'.format(self.combined_name))
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, value, e]
            LOGGER.error('{0}.{1}.set_default() | value: {2} | error: {3}'.format(*fmt_args))

    def get_min_value(self):
        """
        Returns minimum value of the numeric attribute
        :return: variant
        """

        if not self.is_numeric():
            return False

        try:
            min_value = maya.cmds.attributeQuery(self.long_name, node=self.obj.meta_node, minimum=True)
            if min_value:
                return min_value[0]
            else:
                return False
        except StandardError:
            return False

    def set_min_value(self, value):
        """
        Set minimum setting value of the numeric attribute
        :param value:  value or False to reset
        """

        try:
            if self.is_numeric() and not self.get_children():
                if value is False or None:
                    try:
                        maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, hasMinValue=False)
                        LOGGER.warning('{} had its minimum value cleared'.format(self.combined_name))
                    except Exception:
                        LOGGER.error('{} failed to clear a minimum value'.format(self.combined_name))
                elif value is not None:
                    try:
                        maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, minValue=value)
                    except Exception:
                        LOGGER.error('{} failed to set a minimum value'.format(self.combined_name))

                if self.value < value:
                    self.value = value
                    LOGGER.warning('Value changed due to a new minimum. Value is now: {}'.format(value))
            else:
                LOGGER.error('"{}" is not a numeric attribute'.format(self.combined_name))
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, value, e]
            LOGGER.error('{0}.{1}.set_min_value() | value: {2} | error: {3}'.format(*fmt_args))

    def get_max_value(self):
        """
        Returns maximum value of the numeric attribute
        :return: variant
        """

        if not self.is_numeric():
            return False

        try:
            max_value = maya.cmds.attributeQuery(self.long_name, node=self.obj.meta_node, maximum=True)
            if max_value:
                return max_value[0]
            else:
                return False
        except StandardError:
            return False

    def set_max_value(self, value):
        """
        Set maximum setting value of the numeric attribute
        :param value:  value or False to reset
        """

        try:
            if self.is_numeric() and not self.get_children():
                if value is False or None:
                    try:
                        maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, hasMaxValue=False)
                        LOGGER.warning('{} had its maximum value cleared'.format(self.combined_name))
                    except Exception:
                        LOGGER.error('{} failed to clear a maximum value'.format(self.combined_name))
                elif value is not None:
                    try:
                        maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, minValue=value)
                    except Exception:
                        LOGGER.error('{} failed to set a maximum value'.format(self.combined_name))

                if self.value > value:
                    self.value = value
                    LOGGER.warning('Value changed due to a new maximum. Value is now: {}'.format(value))
            else:
                LOGGER.error('"{}" is not a numeric attribute'.format(self.combined_name))
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, value, e]
            LOGGER.error('{0}.{1}.set_max_value() | value: {2} | error: {3}'.format(*fmt_args))

    def get_soft_min_value(self):
        """
        Returns soft minimum value of the numeric attribute
        :return: variant
        """

        if not self.is_numeric():
            return False

        try:
            min_value = maya.cmds.attributeQuery(self.long_name, node=self.obj.meta_node, softMin=True)
            if min_value:
                return min_value[0]
            else:
                return False
        except StandardError:
            return False

    def set_soft_min_value(self, value):
        """
        Set soft minimum setting value of the numeric attribute
        :param value:  value or False to reset
        """

        try:
            if self.is_numeric() and not self.get_children():
                if value is False:
                    try:
                        maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, hasSoftMinValue=False)
                        LOGGER.warning('{} had its minimum value cleared'.format(self.combined_name))
                    except Exception:
                        LOGGER.error('{} failed to clear a soft minimum value'.format(self.combined_name))
                elif value is not None:
                    try:
                        maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, softMinValue=value)
                    except Exception:
                        LOGGER.error('{} failed to set a soft minimum value'.format(self.combined_name))
            else:
                LOGGER.error('"{}" is not a numeric attribute'.format(self.combined_name))
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, value, e]
            LOGGER.error('{0}.{1}.set_min_value() | value: {2} | error: {3}'.format(*fmt_args))

    def get_soft_max_value(self):
        """
        Returns soft maximum value of the numeric attribute
        :return: variant
        """

        if not self.is_numeric():
            return False

        try:
            max_value = maya.cmds.attributeQuery(self.long_name, node=self.obj.meta_node, softMax=True)
            if max_value:
                return max_value[0]
            else:
                return False
        except StandardError:
            return False

    def set_soft_max_value(self, value):
        """
        Set soft maximum setting value of the numeric attribute
        :param value:  value or False to reset
        """

        try:
            if self.is_numeric() and not self.get_children():
                if value is False:
                    try:
                        maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, hasSoftMaxValue=False)
                        LOGGER.warning('{} had its maximum value cleared'.format(self.combined_name))
                    except Exception:
                        LOGGER.error('{} failed to clear a soft maximum value'.format(self.combined_name))
                elif value is not None:
                    try:
                        maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, softMaxValue=value)
                    except Exception:
                        LOGGER.error('{} failed to set a soft maximum value'.format(self.combined_name))
            else:
                LOGGER.error('"{}" is not a numeric attribute'.format(self.combined_name))
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, value, e]
            LOGGER.error('{0}.{1}.set_max_value() | value: {2} | error: {3}'.format(*fmt_args))

    def get_enum(self):
        """
        Get the enum setting values
        :return: list<str>
        """
        return maya.cmds.attributeQuery(self.attr, node=self.obj.meta_node, listEnum=True)[0].split(':') or False

    def set_enum(self, enums):
        """
        Set the option for an enum attribute
        :param enums: str, 'off:on', 'off=0:on=2', ...
        """

        fmt_args = [self.obj.short_name, self.long_name, enums]
        base_msg = '{0}.{1}.setEnum() | enumCommand: {2}'.format(*fmt_args)
        try:
            if self.attr_type == 'enum':
                if ':'.join(self.enum) != metautils.MetaAttributeValidator.string_list_arg(enums):
                    maya.cmds.addAttr(self.obj.meta_node + '.' + self.attr, edit=True, at='enum', en=enums)
                else:
                    LOGGER.info('{} | already set'.format(base_msg))
            else:
                LOGGER.warning('{} | not an enum. Invalid call'.format(base_msg))
        except Exception as e:
            fmt_args = [base_msg, e]
            LOGGER.error('{0} | error: {1}'.format(*fmt_args))

    long_name = property(get_long_name, rename)
    combined_name = property(get_combined_name)
    combined_short_name = property(get_combined_short_name)
    alias = property(get_alias, set_alias)
    name_alias = property(get_alias, set_alias)
    nice_name = property(get_nice_name, set_nice_name)
    value = property(get, set, remove)
    locked = property(get_locked, set_locked)
    lock = property(get_locked, set_locked)
    keyable = property(get_keyable, set_keyable)
    hidden = property(get_hidden, set_hidden)
    default_value = property(get_default_value, set_default_value)
    min_value = property(get_min_value, set_min_value)
    max_value = property(get_max_value, set_max_value)
    soft_min = property(get_soft_min_value, set_soft_min_value)
    soft_min_value = property(get_soft_min_value, set_soft_min_value)
    soft_max = property(get_soft_max_value, set_soft_max_value)
    soft_max_value = property(get_soft_max_value, set_soft_max_value)
    enum = property(get_enum, set_enum)

    def store(self, info_to_store, convert_if_necessary=True):
        """
        Stores information to an object. If the info exists as an object, it stores as a message node
        :param info_to_store:  str, string information to store
        :param convert_if_necessary:  bool, whether to convert the attribute if it needs to store it
        """

        if self.attr_type == 'message':
            self.obj.store(self.attr, info_to_store=info_to_store)
        elif convert_if_necessary:
            self.convert('message')
            self.obj.store(self.attr, info_to_store=info_to_store)

    def is_multi(self):
        """
        Returns True if the attribute is a multi one or False otherwise
        :return: bool
        """

        return maya.cmds.addAttr('{0}.{1}'.format(self.obj.meta_node, self.attr), query=True, m=True)

    def is_index_matters(self):
        """
        Returns if the indices are important in a multi attribute
        :return: bool
        """

        return maya.cmds.addAttr('{0}.{1}'.format(self.obj.meta_node, self.attr), query=True, im=True)

    def is_dynamic(self):
        """
        Returns True if the attribute is a dynamic one or False otherwise
        :return: bool
        """

        if self.attr and maya.cmds.listAttr(self.obj.meta_node, userDefined=True):
            return True
        LOGGER.error('{}.is_dynamic: False'.format(self.combined_short_name))
        return False

    def is_numeric(self):
        """
        Returns True if the attribute is a numeric one or False otherwise
        :return: bool
        """

        if maya.cmds.getAttr(self.combined_name, type=True) in ['string', 'message', 'enum', 'bool']:
            return False
        return True

    def is_readable(self):
        """
        Returns True if the attribute is readable one or False otherwise
        :return: bool
        """

        if not self.is_dynamic():
            LOGGER.warning('"{}" is not a dynamic attribute. Readable is not relevant'.format(self.combined_name))
            return False
        return maya.cmds.addAttr(self.combined_name, query=True, r=True) or False

    def is_writable(self):
        """
        Returns True if the attribute is writable one or False otherwise
        :return: bool
        """

        if not self.is_dynamic():
            LOGGER.warning('"{}" is not a dynamic attribute. Writable is not relevant'.format(self.combined_name))
            return False
        return maya.cmds.addAttr(self.combined_name, query=True, w=True) or False

    def is_storable(self):
        """
        Returns True if the attribute is storable one or False otherwise
        :return: bool
        """

        if not self.is_dynamic():
            LOGGER.warning('"{}" is not a dynamic attribute. Storable is not relevant'.format(self.combined_name))
            return False
        return maya.cmds.addAttr(self.combined_name, query=True, s=True) or False

    def is_used_as_color(self):
        """
        Returns True if the attribute can be used as color or False otherwise
        :return: bool
        """

        if not self.is_dynamic():
            LOGGER.warning('"{}" is not a dynamic attribute. UsedAsColor is not relevant'.format(self.combined_name))
            return False
        return maya.cmds.addAttr(self.combined_name, query=True, usedAsColor=True) or False

    @decorators.abstractmethod
    def is_user_defined(self):
        """
        Returns True if the attribute is a user defined one or False otherwise
        :return: bool
        """

        user_defined = maya.cmds.listAttr(self.obj.meta_node, userDefined=True) or []
        if self.long_name in user_defined:
            return True
        return False

    def convert(self, attr_type):
        """
        Converts an attribute type from one to another while preserving as much data as possible
        :param attr_type: str
        :return: str
        """

        try:
            if self.obj.is_referenced():
                LOGGER.error(
                    '"{0}" is referenced. Cannot convert "{1}" to "{2}"!'.format(self.obj.meta_node, self.nice_name,
                                                                                 attr_type))
            if self.get_children():
                LOGGER.error('"{}" has children, cannot convert'.format(self.combined_name))

            keyable = copy.copy(self.keyable)
            hidden = copy.copy(self.hidden)
            locked = copy.copy(self.locked)
            stored_numeric = False
            if self.is_numeric() and not self.get_children():
                stored_numeric = True
                minimum = copy.copy(self.min_value)
                maximum = copy.copy(self.max_value)
                default = copy.copy(self.default_value)
                soft_min = copy.copy(self.soft_min)
                soft_max = copy.copy(self.soft_max)

            metautils.MetaAttributeUtils.convert_type(self.obj.meta_node, self.attr, attr_type=attr_type)

            self.set_hidden(hidden)
            self.set_keyable(keyable)
            self.set_locked(locked)

            if self.is_numeric() and not self.get_children() and stored_numeric:
                if soft_min is not False or int(soft_min) != 0:
                    self.set_soft_min_value(soft_min)
                if soft_max is not False or int(soft_max) != 0:
                    self.set_soft_max_value(soft_max)
                if minimum is not False:
                    self.set_min_value(minimum)
                if maximum is not False:
                    self.set_max_value(maximum)
                if default is not False:
                    self.set_default_value(default)
            self.attr_type = maya.cmds.getAttr(self.combined_name, type=True)
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name, attr_type, e]
            LOGGER.error('{0}.{1}.convert() | attr_type: {2} | error: {3}'.format(*fmt_args))

    def get_children(self, as_meta=False):
        """
        Returns children attributes
        :param as_meta: bool
        :return: bool
        """

        try:
            as_meta = metautils.MetaAttributeValidator.bool_arg(as_meta)
            try:
                buffer = maya.cmds.attributeQuery(self.attr, node=self.obj.meta_node, listChildren=True) or []
            except Exception:
                buffer = list()
            if as_meta:
                return [MetaAttribute(self.obj.meta_node, c) for c in buffer]
            return buffer
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name]
            fn_msg = '{0}.{1}.get_children()'.format(*fmt_args)
            fmt_args = [fn_msg, as_meta, e]
            LOGGER.error('{0} | as_meta: {1} | error: {2}'.format(*fmt_args))

    def get_parent(self, as_meta=False):
        """
        Returns parent attribute
        :param as_meta: bool
        :return: variant
        """

        try:
            as_meta = metautils.MetaAttributeValidator.bool_arg(as_meta)
            buffer = maya.cmds.attributeQuery(self.attr, node=self.obj.meta_node, listParent=True) or []
            if as_meta:
                return [MetaAttribute(self.obj.meta_node, c) for c in buffer]
            return buffer
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name]
            fn_msg = '{0}.{1}.get_parent()'.format(*fmt_args)
            fmt_args = [fn_msg, as_meta, e]
            LOGGER.error('{0} | as_meta: {1} | error: {2}'.format(*fmt_args))

    def get_siblings(self, as_meta=False):
        """
        Returns sibling attributes if exists
        :param as_meta: bool
        :return: variant
        """

        try:
            as_meta = metautils.MetaAttributeValidator.bool_arg(as_meta)
            buffer = maya.cmds.attributeQuery(self.attr, node=self.obj.meta_node, listParent=True) or []
            if as_meta:
                return [MetaAttribute(self.obj.meta_node, c) for c in buffer]
            return buffer
        except Exception as e:
            fmt_args = [self.obj.short_name, self.long_name]
            fn_msg = '{0}.{1}.get_siblings()'.format(*fmt_args)
            fmt_args = [fn_msg, as_meta, e]
            LOGGER.error('{0} | as_meta: {1} | error: {2}'.format(*fmt_args))
