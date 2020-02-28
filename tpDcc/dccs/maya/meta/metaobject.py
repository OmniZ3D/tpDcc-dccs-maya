#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
MetaNode class implementation for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode, metautils
from tpDcc.dccs.maya.core import transform as transform_lib, shape as shape_lib, attribute as attr_utils


class MetaObject(metanode.MetaNode, object):
    def __init__(self, node=None, name='object', name_args=None, name_kwargs=None, *args, **kwargs):
        if kwargs and kwargs.get('node_type') == 'joint':
            if node is None:
                maya.cmds.select(clear=True)
                # TODO: This breaks the auto nomenclature system :( CHANGE
                node = maya.cmds.joint(name=name)

        # By default, if not node_type is given, we create a transform node
        if kwargs.get('node_type') is None:
            kwargs['node_type'] = 'transform'

        super(MetaObject, self).__init__(
            node=node, name=name, name_args=name_args, name_kwargs=name_kwargs, *args, **kwargs)

        if self.cached:
            return

        if not metautils.MetaAttributeValidator.is_transform(node=self.meta_node):
            raise ValueError(
                '[{}] not a transform! The MetaObject class only work with objects that have transforms!'.format(
                    self.meta_node))

    # =============================================================================================
    # HIERARCHY
    # =============================================================================================

    def get_parent(self, as_meta=False, full_path=True):
        """
        Return MetaNode parent node
        :param as_meta: bool, Whether if the returned object should be returned as Meta object or as string
        :param full_path: bool, whether you want long names or not
        :return: variant, str || MetaNode
        """

        result = metautils.MetaTransformUtils.get_parent(self, full_path=full_path)
        if result and as_meta:
            return metanode.validate_obj_arg(result, 'MetaObject')

        return result

    def set_parent(self, target=False):
        """
        Parent a Maya instanced object while maintaining a correct object instance
        :param target:
        :return:
        """

        return metautils.MetaTransformUtils.set_parent(self.meta_node, target)

    parent = property(get_parent, set_parent)

    def get_children(self, as_meta=False, full_path=True):
        """
        Returns children of the MetaNode
        :param as_meta: bool, Whether to return children as meta or not
        :param full_path: bool, whether you want long names or not
        :return: list
        """

        result = metautils.MetaTransformUtils.get_children(self, full_path)
        if result and as_meta:
            return metanode.valid_obj_list_arg(result)

        return result

    # =============================================================================================
    # ATTRIBUTES
    # =============================================================================================

    def hide_attributes(self, attributes=None):
        """
        Lock and hide the given attributes on the control.
        If no attributes given, hide translate, rotate, scale and visibility
        :param attributes: list<str>, list of attributes to hide and lock (['translateX', 'translateY'])
        """

        if attributes:
            attr_utils.hide_attributes(self.meta_node, attributes)
        else:
            self.hide_translate_attributes()
            self.hide_rotate_attributes()
            self.hide_scale_attributes()
            self.hide_visibility_attribute()

    def hide_translate_attributes(self):
        """
        Lock and hide the translate attributes on the control
        """

        attr_utils.lock_translate_attributes(self.meta_node)

    def hide_rotate_attributes(self):
        """
        Lock and hide the rotate attributes on the control
        """

        attr_utils.lock_rotate_attributes(self.meta_node)

    def hide_scale_attributes(self):
        """
        Lock and hide the scale attributes on the control
        """

        attr_utils.lock_scale_attributes(self.meta_node)

    def hide_visibility_attribute(self):
        """
        Lock and hide the visibility attribute on the control
        """

        attr_utils.lock_attributes(self.meta_node, ['visibility'], hide=True)

    def hide_scale_and_visibility_attributes(self):
        """
        lock and hide the visibility and scale attributes on the control
        """

        self.hide_scale_attributes()
        self.hide_visibility_attribute()

    def hide_keyable_attributes(self):
        """
        Lock and hide all keyable attributes on the control
        """

        attr_utils.hide_keyable_attributes(self.meta_node)

    def show_translate_attributes(self):
        """
        Unlock and set keyable the control translate attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.translate{}'.format(self.meta_node, axis), long=False, k=True)

    def show_rotate_attributes(self):
        """
        Unlock and set keyable the control rotate attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.rotate{}'.format(self.meta_node, axis), long=False, k=True)

    def show_scale_attributes(self):
        """
        Unlock and set keyable the control scale attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.scale{}'.format(self.meta_node, axis), long=False, k=True)

    # =============================================================================================
    # SHAPES
    # =============================================================================================

    def get_shapes(self, as_meta=False, full_path=True, intermediates=False, non_intermediates=True):
        """
        Return all the shapes of a given node where the last parent is the top of hierarchy
        :param as_meta: bool, Whether if the returned object should be returned as Meta object or as string
        :param full_path: bool, whether you want long names or not
        :param intermediates: bool, list intermediate shapes
        :param non_intermediates: bool, list non intermediate shapes
        :return: variant, list<str> || list<Meta>
        """

        result = metautils.MetaTransformUtils.get_shapes(
            node=self, full_path=full_path, intermediates=intermediates, non_intermediates=non_intermediates)
        if result and as_meta:
            return metanode.validate_obj_list_arg(result)

        return result

    def get_shapes_components(self):
        """
        Returns shapes components of the MetaNode shapes
        :return: list<str>
        """

        shapes = self.get_shapes(as_meta=False, full_path=True)
        return shape_lib.get_components_from_shapes(shapes)

    # =============================================================================================
    # TRANSFORM
    # =============================================================================================

    def get_position(self, *args, **kwargs):
        """
        Returns the position of the object
        :param args:
        :param kwargs:
        :return:
        """

        # TODO: Improve this to handle all scenarios

        return transform_lib.get_translation(self.meta_node)

    def snap(self, target, snap_pivot=False):
        """
        Snaps transform node into target
        :param target: str
        :param snap_pivot: bool, Whether to snap pivot or not
        """

        transform_lib.snap(transform=self.meta_node, target=target, snap_pivot=snap_pivot)
