#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
MetaNode class implementation for Maya
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya
from tpMayaLib.meta import metanode, metautils
from tpMayaLib.core import transform as transform_lib, shape as shape_lib


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

        super(MetaObject, self).__init__(node=node, name=name, name_args=name_args, name_kwargs=name_kwargs, *args, **kwargs)

        if self.cached:
            return

        if not metautils.MetaAttributeValidator.is_transform(node=self.meta_node):
            raise ValueError('[{}] not a transform! The MetaObject class only work with objects that have transforms!'.format(self.meta_node))

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

    def get_shapes(self, as_meta=False, full_path=True, intermediates=False, non_intermediates=True):
        """
        Return all the shapes of a given node where the last parent is the top of hierarchy
        :param as_meta: bool, Whether if the returned object should be returned as Meta object or as string
        :param full_path: bool, whether you want long names or not
        :param intermediates: bool, list intermediate shapes
        :param non_intermediates: bool, list non intermediate shapes
        :return: variant, list<str> || list<Meta>
        """

        result = metautils.MetaTransformUtils.get_shapes(node=self, full_path=full_path, intermediates=intermediates, non_intermediates=non_intermediates)
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

    def snap(self, target, snap_pivot=False):
        """
        Snaps transform node into target
        :param target: str
        :param snap_pivot: bool, Whether to snap pivot or not
        """

        transform_lib.snap(transform=self.meta_node, target=target, snap_pivot=snap_pivot)


