#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya Deformer nodes
"""

from __future__ import print_function, division, absolute_import

import re
import logging

import tpDcc.dccs.maya as maya
from tpDcc.libs.python import python, mathlib, name as name_utils
from tpDcc.dccs.maya.core import node, attribute, exceptions, name as name_lib, decorators
from tpDcc.dccs.maya.core import geometry as geo_utils, shape as shape_utils

ALL_DEFORMERS = (
    'blendShape',
    'skinCluster',
    'cluster',
    'softMod',
    'sculpt',
    'ffd',
    'wrap',
    'nonLinear',
    'wire',
    'sculpt',
    'jiggle'
)


class ClusterObject(object):
    """
    Util class for clustering objects
    """

    def __init__(self, geometry, name):
        super(ClusterObject, self).__init__()

        self._geo = geometry
        self._join_ends = False
        self._name = name
        self._cvs = list()
        self._cv_count = 0
        self._clusters = list()
        self._handles = list()

    def create(self):
        """
        Creates the clusters
        """

        self._create()

    def get_cluster_list(self):
        """
        Returns the names of cluster deformers
        :return: list<str>
        """

        return self._clusters

    def get_cluster_handle_list(self):
        """
        Returns the name of cluster handles
        :return: list<str>
        """

        return self._handles

    def _create(self):
        """
        Internal function that creates the custer
        Override in child classes
        """

        return

    def _create_cluster(self, cvs):
        return create_cluster(cvs, self._name)


class ClusterSurface(ClusterObject, object):
    """
    Util class for clustering a surface
    """

    def __init__(self, geometry, name):
        super(ClusterSurface, self).__init__(geometry, name)

        self._join_ends = False
        self._join_both_ends = False
        self._first_cluster_pivot_at_start = True
        self._last_cluster_pivot_at_end = True
        self._maya_type = None

        if shape_utils.has_shape_of_type(self._geo, 'nurbsCurve'):
            self._maya_type = 'nurbsCurve'
        elif shape_utils.has_shape_of_type(self._geo, 'nurbsSurface'):
            self._maya_type = 'nurbsSurface'

        self._cluster_u = True

    def _create(self):
        self._cvs = maya.cmds.ls('{}.cv[*]'.format(self._geo, flatten=True))
        if self._maya_type == 'nurbsCurve':
            self._cv_count = len(self._cvs)
        elif self._maya_type == 'nurbsSurface':
            if self._cluster_u:
                index = '[0][*]'
            else:
                index = '[*][0]'

            self._cv_count = len(maya.cmds.ls('{}.cv{}'.format(self._geo, index), flatten=True))

        start_index = 0
        cv_count = self._cv_count
        if self._join_ends:
            if self._join_both_ends:
                self._create_start_and_end_joined_cluster()
            else:
                last_cluster, last_handle = self._create_start_and_end_clusters()
            cv_count = len(self._cvs[2:self._cv_count])
            start_index = 2

        for i in range(start_index, cv_count):
            if self._maya_type == 'nurbsCurve':
                cv = '{}.cv[{}]'.format(self._geo, i)
            elif self._maya_type == 'nurbsSurface':
                if self._cluster_u:
                    index = '[*][{}]'.format(i)
                else:
                    index = '[{}][*]'.format(i)
                cv = '{}.cv{}'.format(self._geo, index)
            else:
                maya.logger.warning('Given NURBS Maya type "{}" is not valid!'.format(self._maya_type))
                return

            cluster, handle = self._create_cluster(cv)
            self._clusters.append(cluster)
            self._handles.append(handle)

        if self._join_ends and not self._join_both_ends:
            self._clusters.append(last_cluster)
            self._handles.append(last_handle)

        return self._clusters

    def set_join_ends(self, flag):
        """
        Sets whether clusters on the end of the surface take up 2 CVs or 1 CV
        :param flag: bool
        """

        self._join_ends = flag

    def set_join_both_ends(self, flag):
        """
        Sets whether clusters on the ends of the surface are joined together or not
        :param flag: bool
        """

        self._join_both_ends = flag

    def set_last_cluster_pivot_at_end(self, flag):
        """
        Sets whether move the last cluster pivot to the end of the curve
        :param flag: bool
        """

        self._last_cluster_pivot_at_end = flag

    def set_first_cluster_pivot_at_start(self, flag):
        """
        Sets whether move the first cluster pivot to the start of the curve
        :param flag: bool
        """

        self._first_cluster_pivot_at_start = flag

    def set_cluster_u(self, flag):
        """
        Sets whether cluster u should be used
        :param flag: bool
        """

        self._cluster_u = flag

    def _create_start_and_end_clusters(self):
        """
        Internal function used to create start and end clusters
        """

        start_cvs = None
        end_cvs = None
        start_pos = None
        end_pos = None

        if self._maya_type == 'nurbsCurve':
            start_cvs = '{}.cv[0:1]'.format(self._geo)
            end_cvs = '{}.cv[{}:{}]'.format(self._geo, self._cv_count - 2, self._cv_count - 1)
            start_pos = maya.cmds.xform('{}.cv[0]'.format(self._geo), q=True, ws=True, t=True)
            end_pos = maya.cmds.xform('{}.cv[{}]'.format(self._geo, self._cv_count - 1), q=True, ws=True, t=True)
        elif self._maya_type == 'nurbsSurface':
            if self._cluster_u:
                cv_count_u = len(maya.cmds.ls('{}.cv[*][0]'.format(self._geo), flatten=True))
                index1 = '[0:*][0:1]'
                index2 = '[0:*][{}:{}]'.format(self._cv_count - 2, self._cv_count - 1)
                index3 = '[{}][0]'.format(cv_count_u - 1)
                index4 = '[0][{}]'.format(self._cv_count - 1)
                index5 = '[{}][{}]'.format(cv_count_u, self._cv_count - 1)
            else:
                cv_count_v = len(maya.cmds.ls('%s.cv[0][*]' % self._geo, flatten=True))
                index1 = '[0:1][0:*]'
                index2 = '[{}:{}][0:*]'.format(self._cv_count - 2, self._cv_count - 1)
                index3 = '[0][{}]'.format(cv_count_v - 1)
                index4 = '[{}][0]'.format(self._cv_count - 1)
                index5 = '[{}][{}]'.format(self._cv_count - 1, cv_count_v)

            start_cvs = '{}.cv{}'.format(self._geo, index1)
            end_cvs = '{}.cv{}'.format(self._geo, index2)

            p1 = maya.cmds.xform('{}.cv[0][0]'.format(self._geo), q=True, ws=True, t=True)
            p2 = maya.cmds.xform('{}.cv{}'.format(self._geo, index3), q=True, ws=True, t=True)
            start_pos = mathlib.get_mid_point(p1, p2)

            p1 = maya.cmds.xform('{}.cv{}'.format(self._geo, index4), q=True, ws=True, t=True)
            p2 = maya.cmds.xform('{}.cv{}'.format(self._geo, index5), q=True, ws=True, t=True)
            end_pos = mathlib.get_mid_point(p1, p2)

        cluster, handle = self._create_cluster(start_cvs)

        self._clusters.append(cluster)
        self._handles.append(handle)

        if self._first_cluster_pivot_at_start:
            maya.cmds.xform(handle, ws=True, rp=start_pos, sp=start_pos)

        last_cluster, last_handle = self._create_cluster(end_cvs)
        if self._last_cluster_pivot_at_end:
            maya.cmds.xform(last_handle, ws=True, rp=end_pos, sp=end_pos)

        return last_cluster, last_handle

    def _create_start_and_end_joined_cluster(self):
        start_cvs = None
        end_cvs = None

        if self._maya_type == 'nurbsCurve':
            start_cvs = '{}.cv[0:1]'.format(self._geo)
            end_cvs = '{}.cv[{}:{}]'.format(self._geo, self._cv_count - 2, self._cv_count - 1)
        elif self._maya_type == 'nurbsSurface':
            if self._cluster_u:
                index_1 = '[0:*][0]'
                index_2 = '[0:*][{}]'.format(self._cv_count - 1)
            else:
                index_1 = '[0][0:*}'
                index_2 = '[{}][0:*]'.format(self._cv_count - 1)

            start_cvs = '{}.cv{}'.format(self._geo, index_1)
            end_cvs = '{}.cv{}'.format(self._geo, index_2)

        maya.cmds.select([start_cvs, end_cvs])
        cvs = maya.cmds.ls(sl=True)

        cluster, handle = self._create_cluster(cvs)
        self._clusters.append(cluster)
        self._handles.append(handle)


class ClusterCurve(ClusterSurface, object):
    """
    Util class for clustering a curve
    """

    def _create(self):
        self._cvs = maya.cmds.ls('{}.cv[*]'.format(self._geo), flatten=True)
        self._cv_count = len(self._cvs)
        start_index = 0
        cv_count = self._cv_count

        if self._join_ends:
            last_cluster, last_handle = self._create_start_and_end_clusters()
            cv_count = len(self._cvs[2:self._cv_count])
            start_index = 2

        for i in range(start_index, cv_count):
            cluster, handle = self._create_cluster('{}.cv[{}]'.format(self._geo, i))
            self._clusters.append(cluster)
            self._handles.append(handle)

        if self._join_ends:
            self._clusters.append(last_cluster)
            self._handles.append(last_handle)

        return self._clusters

    def _create_start_and_end_clusters(self):
        cluster, handle = self._create_cluster('{}.cv[0:1]'.format(self._geo))

        self._clusters.append(cluster)
        self._handles.append(handle)

        pos = maya.cmds.xform('{}.cv[0]'.format(self._geo), q=True, ws=True, t=True)
        maya.cmds.xform(handle, ws=True, rp=pos, sp=pos)

        last_cluster, last_handle = self._create_cluster(
            '{}.cv[{}:{}]'.format(self._geo, self._cv_count - 2, self._cv_count - 1))
        pos = maya.cmds.xform('{}.cv[{}]'.format(self._geo, self._cv_count - 1), q=True, ws=True, t=True)
        maya.cmds.xform(last_handle, ws=True, rp=pos, sp=pos)

        return last_cluster, last_handle

    def set_cluster_u(self, flag):
        """
        Override because cluster u is not available on curves
        :param flag: bool
        """

        maya.logger.warning('Cannot set cluster U, there is only one direction for spans on a curve.')


def is_deformer(deformer):
    """
    Checks if a node is a valid deformer
    :param deformer: str, name of the node to be checked
    """

    if not maya.cmds.objExists(deformer):
        return False

    # NOTE: Geometry filter is the base type for all deformers
    node_type = maya.cmds.nodeType(deformer, i=True)
    if not node_type.count('geometryFilter'):
        return False

    return True


def check_deformer(deformer):
    """
    Checks if a node is a valid deformer and raises and exception if the node is not valid
    :param deformer: str
    :return: bool, True if the given deformer is valid
    """

    if not maya.cmds.objExists(deformer):
        exceptions.NodeExistsException(deformer)
    if not is_deformer(deformer):
        raise exceptions.DeformerException(deformer)


def get_deformer_list(node_type='geometryFilter', affected_geometry=[], regex_filter=''):
    """
    Returns a list of deformers that match the input criteria
    You can list deformers connected to a specific geometry, by type and filer the results using regular expressions
    :param node_type: str, Deformer type as string. Optional arg, only return deformers of specified type
    :param affected_geometry: list(str), Affected geometry list. Optional arg, will list deformers connected to the
        specific geometry
    :param regex_filter: str, Regular expression as string. Optional arg, will filter results
    """

    deformer_nodes = maya.cmds.ls(type=node_type)

    # Filter by affected geometry
    if affected_geometry:
        if type(affected_geometry) == str:
            affected_geometry = [affected_geometry]
        history_nodes = maya.cmds.listHistory(affected_geometry, groupLevels=True, pruneDagObjects=True)
        deformer_nodes = maya.cmds.ls(history_nodes, type=node_type)

    # Remove duplicated, tweak and transferAttributes nodes
    deformer_nodes = python.remove_dupes(deformer_nodes)
    tweak_nodes = maya.cmds.ls(deformer_nodes, type='tweak')
    if tweak_nodes:
        deformer_nodes = [x for x in deformer_nodes if x not in tweak_nodes]
    transfer_attr_nodes = maya.cmds.ls(deformer_nodes, type='transferAttributes')
    if transfer_attr_nodes:
        deformer_nodes = [x for x in deformer_nodes if x not in transfer_attr_nodes]

    # Filter results
    if regex_filter:
        reg_filter = re.compile(regex_filter)
        deformer_nodes = filter(reg_filter.search, deformer_nodes)

    return deformer_nodes


def get_deformer_fn(deformer):
    """
    Initializes and returns an MFnWeightGeometryFilter function set attached to the specific deformer
    :param deformer: str, name of the deformer to create function set for
    :return: str
    """

    if maya.use_new_api():
        maya.logger.warning('MFnWeightGeometryFilter does not exists in OpenMayaAnim 2.0 yet! Using OpenMaya 1.0 ...')
        maya.use_new_api(False)

    if not maya.cmds.objExists(deformer):
        raise Exception('Deformer {} does not exists!'.format(deformer))

    deformer_obj = node.get_mobject(deformer)
    try:
        deformer_fn = maya.OpenMayaAnim.MFnWeightGeometryFilter(deformer_obj)
    except Exception as e:
        print(str(e))
        raise Exception('Could not get a geometry filter for deformer "{}"!'.format(deformer))

    return deformer_fn


def get_deformer_set(deformer):
    """
    Returns the deformer set name associated with the given deformer
    :param deformer: str, name of deformer to return the deform set for
    :return: str
    """

    check_deformer(deformer)

    deformer_obj = node.get_mobject(node_name=deformer)
    deformer_fn = maya.OpenMayaAnim.MFnGeometryFilter(deformer_obj)
    deformer_set_obj = deformer_fn.deformerSet()
    if deformer_set_obj.isNull():
        raise exceptions.DeformerSetExistsException(deformer)

    return maya.OpenMaya.MFnDependencyNode(deformer_set_obj).name()


def get_deformer_set_fn(deformer):
    """
    Initializes and return an MFnSet function set attached to the deformer set of the given deformer
    :param deformer: str, name of the deformer attached to the deformer set to create function set for
    :return: str
    """

    check_deformer(deformer)

    deformer_set = get_deformer_set(deformer=deformer)

    deformer_set_obj = node.get_mobject(node_name=deformer_set)
    deformer_set_fn = maya.OpenMaya.MFnSet(deformer_set_obj)

    return deformer_set_fn


def get_geo_index(geometry, deformer):
    """
    Returns the geometry index of a shape to a given deformer
    :param geometry: str, name of shape or parent transform to query
    :param deformer: str, name of deformery to query
    """

    check_deformer(deformer)

    geo = geometry
    if maya.cmds.objectType(geometry) == 'transform':
        try:
            geometry = maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True)[0]
        except Exception:
            raise exceptions.GeometryException(geo)
    geo_obj = node.get_mobject(node_name=geometry)

    deformer_obj = node.get_mobject(node_name=deformer)
    deformer_fn = maya.OpenMayaAnim.MFnGeometryFilter(deformer_obj)
    try:
        geo_index = deformer_fn.indexForOutputShape(geo_obj)
    except Exception:
        raise exceptions.NotAffectByDeformerException(geometry, deformer)

    return geo_index


def get_deformer_set_members(deformer, geometry=''):
    """
    Returns the deformer set members of the given deformer
    You can specify a shape name to query deformer membership for, otherwise, membership for the first affected
    geometry will be returned
    :param deformer: str, deformer to query set membership for
    :param geometry: str, geometry to query deformer set membership for (optional)
    :return: str
    """

    deformer_set_fn = get_deformer_set_fn(deformer=deformer)

    if geometry:
        geo_index = get_geo_index(geometry, deformer)
    else:
        geo_index = 0

    if maya.is_new_api():
        deformer_set_sel = deformer_set_fn.getMembers(True)
        deformer_set_len = len(deformer_set_sel)
        if geo_index >= deformer_set_len:
            raise exceptions.GeometryIndexOutOfRange(deformer, geometry, geo_index, deformer_set_len)
        geo_index, deformer_set_path, deformer_set_comp = deformer_set_sel.getDagPath()
    else:
        deformer_set_sel = maya.OpenMaya.MSelectionList()
        deformer_set_fn.getMembers(deformer_set_sel, True)
        deformer_set_path = maya.OpenMaya.MDagPath()
        deformer_set_comp = maya.OpenMaya.MObject()
        deformer_set_len = deformer_set_sel.length()
        if geo_index >= deformer_set_len:
            raise exceptions.GeometryIndexOutOfRange(deformer, geometry, geo_index, deformer_set_len)
        deformer_set_sel.getDagPath(geo_index, deformer_set_path, deformer_set_comp)

    return [deformer_set_path, deformer_set_comp]


def get_deformer_set_member_str_list(deformer, geometry=''):
    """
    Returns the deformer set members of the given deformer as a list of strings
    You can specify a shape name to query deformer membership for, otherwise, membership for the first affected
    geometry will be returned
    :param deformer: str, deformer to query set membership for
    :param geometry: str, geometry to query deformer set membership for (optional)
    :return: list<str>
    """

    deformer_set_fn = get_deformer_set_fn(deformer)

    if maya.is_new_api():
        deformer_set_sel = deformer_set_fn.getMembers(True)
        set_member_str = str(deformer_set_sel)
    else:
        deformer_set_sel = maya.OpenMaya.MSelectionList()
        deformer_set_fn.getMembers(deformer_set_sel, True)
        set_member_str = list()
        deformer_set_sel.getSelectionStrings(set_member_str)

    set_member_str = maya.cmds.ls(set_member_str, fl=True)

    return set_member_str


def get_deformer_set_member_indices(deformer, geometry=''):
    """
    Returns a list of deformer set member vertex indices
    :param deformer: str, deformer to set member indices for
    :param geometry: str, geometry to query deformer set membership for
    :return: str
    """

    geo = geometry
    if maya.cmds.objectType(geometry) == 'transform':
        try:
            geometry = maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True)[0]
        except Exception:
            exceptions.GeometryException(geo)

    geometry_type = maya.cmds.objectType(geometry)
    deformer_set_mem = get_deformer_set_members(deformer=deformer, geometry=geometry)

    member_id_list = list()

    # Single Index
    if geometry_type == 'mesh' or geometry_type == 'nurbsCurve' or geometry_type == 'particle':
        single_index_comp_fn = maya.OpenMaya.MFnSingleIndexedComponent(deformer_set_mem[1])
        if maya.is_new_api():
            member_indices = single_index_comp_fn.getElements()
        else:
            member_indices = maya.OpenMaya.MIntArray()
            single_index_comp_fn.getElements(member_indices)
        member_id_list = list(member_indices)

    # Double Index
    if geometry_type == 'nurbsSurface':
        double_index_comp_fn = maya.OpenMaya.MFnDoubleIndexedComponent(deformer_set_mem[1])
        if maya.is_new_api():
            member_indices_U, member_indices_V = double_index_comp_fn.getElements()
        else:
            member_indices_U = maya.OpenMaya.MIntArray()
            member_indices_V = maya.OpenMaya.MIntArray()
            double_index_comp_fn.getElements(member_indices_U, member_indices_V)
        array_length = member_indices_U.length() if hasattr(member_indices_U, 'length') else len(member_indices_U)
        for i in range(array_length):
            member_id_list.append([member_indices_U[i], member_indices_V[i]])

    # Triple Index
    if geometry_type == 'lattice':
        triple_index_comp_fn = maya.OpenMaya.MFnTripleIndexedComponent(deformer_set_mem[1])
        if maya.is_new_api():
            member_indices_S, member_indices_T, member_indices_U = triple_index_comp_fn.getElements()
        else:
            member_indices_S = maya.OpenMaya.MIntArray()
            member_indices_T = maya.OpenMaya.MIntArray()
            member_indices_U = maya.OpenMaya.MIntArray()
            triple_index_comp_fn.getElements(member_indices_S, member_indices_T, member_indices_U)
        array_length = member_indices_S.length() if hasattr(member_indices_S, 'length') else len(member_indices_S)
        for i in range(array_length):
            member_id_list.append([member_indices_S[i], member_indices_T[i], member_indices_U[i]])

    return member_id_list


def get_affected_geometry(deformer, return_shapes=False, full_path_names=False):
    """
    Returns a dictionary containing information about geometry affected by a given deformer
    Dict keys corresponds to affected geometry names and values indicate geometry index to deformer
    :param deformer: str, name of the deformer to query geometry from
    :param return_shapes: bool, Whether shape names should be returned instead of transform names
    :param full_path_names: bool, Whether full path names of affected objects should be returned
    :return: dict
    """

    check_deformer(deformer=deformer)

    affected_objects = dict()

    deformer_obj = node.get_mobject(node_name=deformer)
    geo_filter_fn = maya.OpenMayaAnim.MFnGeometryFilter(deformer_obj)

    if maya.is_new_api():
        output_object_array = geo_filter_fn.getOutputGeometry()
    else:
        output_object_array = maya.OpenMaya.MObjectArray()
        geo_filter_fn.getOutputGeometry(output_object_array)

    array_length = output_object_array.length() if hasattr(output_object_array, 'length') else len(output_object_array)
    for i in range(array_length):
        output_index = geo_filter_fn.indexForOutputShape(output_object_array[i])
        output_node = maya.OpenMaya.MFnDagNode(output_object_array[i])

        if not return_shapes:
            output_node = maya.OpenMaya.MFnDagNode(output_node.parent(0))

        if full_path_names:
            affected_objects[output_node.fullPathName()] = output_index
        else:
            affected_objects[output_node.partialPathName()] = output_index

    return affected_objects


def find_input_shape(shape):
    """
    Returns the input shape ('...ShapeOrig') for the given shape node
    This function assumes that the specified shape is affected by at least one valid deformer
    :param shape: The shape node to find the corresponding input shape for
    :return: str
    """

    if not maya.cmds.objExists(shape):
        raise exceptions.ShapeException(shape)

    # Get inMesh connection
    in_mesh_cnt = maya.cmds.listConnections(shape + '.inMesh', source=True, destination=False, shapes=True)
    if not in_mesh_cnt:
        return shape

    # Check direct mesh (outMesh --> inMesh) connection
    if str(maya.cmds.objectType(in_mesh_cnt[0])) == 'mesh':
        return in_mesh_cnt[0]

    # Find connected deformer
    deformer_obj = node.get_mobject(in_mesh_cnt[0])
    if not deformer_obj.hasFn(maya.OpenMaya.MFn.kGeometryFilt):
        deformer_hist = maya.cmds.listHistory(shape, type='geometryFilter')
        if not deformer_hist:
            maya.logger.warning(
                'Shape node "{0}" has incoming inMesh connections but is not affected by any valid deformers! '
                'Returning "{0}"!'.format(shape))
            return shape
        else:
            deformer_obj = node.get_mobject(deformer_obj[0])

    deformer_fn = maya.OpenMayaAnim.MFnGeometryFilter(deformer_obj)

    shape_obj = node.get_mobject(shape)
    geo_index = deformer_fn.indexForOutputShape(shape_obj)
    input_shape_obj = deformer_fn.inputShapeAtIndex(geo_index)

    return maya.OpenMaya.MFnDependencyNode(input_shape_obj).name()


def rename_deformer_set(deformer, deformer_set_name=''):
    """
    Rename the deformer set connected to the given deformer
    :param deformer: str, name of the deformer whose deformer set you want to rename
    :param deformer_set_name: str, new name for the deformer set. If left as default, new name will be (deformer+"Set")
    :return: str
    """

    check_deformer(deformer)

    if not deformer_set_name:
        deformer_set_name = deformer + 'Set'

    deformer_set = maya.cmds.listConnections(deformer + '.message', type='objectSet')[0]
    if deformer_set != deformer_set_name:
        deformer_set_name = maya.cmds.rename(deformer_set, deformer_set_name)

    return deformer_set_name


def get_weights(deformer, geometry=None):
    """
    Get the weights for the given deformer. Weights returned as a Python list object
    :param deformer: str, deformer to get weights for
    :param geometry: str, target geometry to get weights from
    :return: list<float>
    """

    use_new_api = False
    if maya.is_new_api():
        maya.logger.warning(
            'get_weights function is dependant of MFnWeightGeometryFilter which is not available in OpenMaya 2.0 yet! '
            'Using OpenMaya 1.0 ...')
        maya.use_new_api(False)
        use_new_api = True

    check_deformer(deformer)

    if not geometry:
        geometry = get_affected_geometry(deformer=deformer).keys()[0]

    geo_shape = geometry
    if geometry and maya.cmds.objectType(geo_shape) == 'transform':
        geo_shape = maya.cmds.listRelatives(geometry, s=True, ni=True)[0]

    deformer_fn = get_deformer_fn(deformer)
    deformer_set_mem = get_deformer_set_members(deformer=deformer, geometry=geo_shape)

    weight_list = maya.OpenMaya.MFloatArray()
    deformer_fn.getWeights(deformer_set_mem[0], deformer_set_mem[1], weight_list)

    if use_new_api:
        maya.use_new_api(True)

    return list(weight_list)


def set_weights(deformer, weights, geometry=None):
    """
    Set the weights for the give ndeformer using the input value list
    :param deformer: str, deformer to set weights for
    :param weights: list<float>, input weight value list
    :param geometry: str, target geometry to apply weights to. If None, use first affected geometry
    """

    use_new_api = False
    if maya.is_new_api():
        maya.logger.warning(
            'set_weights function is dependant of MFnWeightGeometryFilter which is not available in OpenMaya 2.0 yet! '
            'Using OpenMaya 1.0 ...')
        maya.use_new_api(False)
        use_new_api = True

    check_deformer(deformer)

    if not geometry:
        geometry = get_affected_geometry(deformer).keys()[0]

    geo_shape = geometry
    geo_obj = node.get_mobject(geometry)
    if geometry and geo_obj.hasFn(maya.OpenMaya.MFn.kTransform):
        geo_shape = maya.cmds.listRelatives(geometry, s=True, ni=True)[0]

    deformer_fn = get_deformer_fn(deformer)
    deformer_set_mem = get_deformer_set_members(deformer=deformer, geometry=geo_shape)

    weights_list = maya.OpenMaya.MFloatArray()
    [weights_list.append(i) for i in weights]

    deformer_fn.setWeight(deformer_set_mem[0], deformer_set_mem[1], weights_list)

    if use_new_api:
        maya.use_new_api(True)


def bind_pre_matrix(deformer, bind_pre_matrix='', parent=True):
    """
    Creates a bindPreMatrix transform for the given deformer
    :param deformer: str, deformer to create bind pre matrix transform for
    :param bind_pre_matrix: str, specify existing transform for bind pre matrix connec tion.
        If empty, create a new transform
    :param parent: bool, parent the deformer handle to the bind pre matrix transform
    :return: str
    """

    check_deformer(deformer)

    deformer_handle = maya.cmds.listConnections(deformer + '.matrix', s=True, d=False)
    if deformer_handle:
        deformer_handle = deformer_handle[0]
    else:
        raise exceptions.DeformerHandleExistsException()

    if bind_pre_matrix:
        if not maya.cmds.objExists(bind_pre_matrix):
            bind_pre_matrix = maya.cmds.createNode('transform', n=bind_pre_matrix)
    else:
        prefix = deformer_handle.replace(deformer_handle.split('_')[-1], '')
        bind_pre_matrix = maya.cmds.createNode('transform', n=prefix + 'bindPreMatrix')

    # Match transform and pivot
    maya.cmds.xform(bind_pre_matrix, ws=True, matrix=maya.cmds.xform(deformer_handle, query=True, ws=True, matrix=True))
    maya.cmds.xform(bind_pre_matrix, ws=True, piv=maya.cmds.xform(deformer_handle, query=True, ws=True, rp=True))

    # Connect inverse matrix to deformer
    maya.cmds.connectAttr(bind_pre_matrix + '.worldInverseMatrix[0]', deformer + '.bindPreMatrix', f=True)

    if parent:
        maya.cmds.parent(deformer_handle, bind_pre_matrix)

    return bind_pre_matrix


def prune_weights(deformer, geo_list=None, threshold=0.001):
    """
    Set deformer component weights to 0.0 if the original weight value is below the given threshold
    :param deformer: str, name of the deformer to removed components from
    :param geo_list: list<str>, geometry objects whose components are checked for weight pruning
    :param threshold: float, weight threshold for removal
    """

    check_deformer(deformer)

    geo_list = [] if geo_list is None else python.force_list(geo_list)
    if not geo_list:
        geo_list = maya.cmds.deformer(deformer, q=True, g=True)
    if not geo_list:
        raise Exception('No geometry to prune weights for!')
    for geo in geo_list:
        if not maya.cmds.objExists(geo):
            raise exceptions.GeometryExistsException(geo)

    for geo in geo_list:
        weight_list = get_weights(deformer=deformer, geometry=geo)
        weight_list = [wt if wt > threshold else 0.0 for wt in weight_list]
        set_weights(deformer=deformer, weights=weight_list, geometry=geo)


def prune_membership_by_weights(deformer, geo_list=None, threshold=0.001):
    """
    Removes components from a given deformer set if there are weights values below the given threshold
    :param deformer: str, name of the deformer to removed components from
    :param geo_list: list<str>, geometry objects whose components are checked for weight pruning
    :param threshold: float, weight threshold for removal
    """

    use_new_api = False
    if maya.is_new_api():
        maya.logger.warning(
            'prune_membership_by_weights function is dependant of MFnWeightGeometryFilter which is not available in '
            'OpenMaya 2.0 yet! Using OpenMaya 1.0 ...')
        maya.use_new_api(False)
        use_new_api = True

    check_deformer(deformer)

    geo_list = [] if geo_list is None else python.force_list(geo_list)
    if not geo_list:
        geo_list = maya.cmds.deformer(deformer, q=True, g=True)
    if not geo_list:
        raise Exception('No geometry to prune weights for!')
    for geo in geo_list:
        if not maya.cmds.objExists(geo):
            raise exceptions.GeometryExistsException(geo)

    deformer_set = get_deformer_set(deformer)
    all_prune_list = list()

    for geo in geo_list:
        geo_type = geo_utils.component_type(geo)
        member_index_list = get_deformer_set_member_indices(deformer=deformer, geometry=geo)
        weight_list = get_weights(deformer=deformer, geometry=geo)

        prune_list = [member_index_list[i] for i in range(len(member_index_list)) if weight_list[i] <= threshold]
        for i in range(len(prune_list)):
            if type(prune_list[i]) == str or type(prune_list[i]) == unicode or type(prune_list[i]) == int:
                prune_list[i] = '[{}]'.format(str(prune_list[i]))
            elif type(prune_list[i]) == list:
                prune_list[i] = [str(p) for p in prune_list[i]]
                prune_list[i] = '[' + ']['.join(prune_list[i]) + ']'
            prune_list[i] = geo + '.' + geo_type + str(prune_list[i])
        all_prune_list.extend(prune_list)

        if prune_list:
            maya.cmds.sets(prune_list, rm=deformer_set)

    if use_new_api:
        maya.use_new_api(True)

    return all_prune_list


def clean(deformer, threshold=0.001):
    """
    Clean given deformer by pruning weights and membership under the given tolerance
    :param deformer: str, deformer to clean
    :param threshold: float, weight value tolerance for prune operations
    """

    check_deformer(deformer)

    maya.logger.debug('Cleaning deformer: {}!'.format(deformer))

    prune_weights(deformer=deformer, threshold=threshold)
    prune_membership_by_weights(deformer=deformer, threshold=threshold)


def check_multiple_outputs(deformer, print_result=True):
    """
    Check the  given deformer to check for multiple output connections from a single plug
    :param deformer: str, deformer to check for multiple output connections
    :param print_result: bool, Whether if the results should be printed or not
    :return: dict
    """

    check_deformer(deformer)

    out_geo_plug = attribute.get_attr_mplug(deformer + '.outputGeometry')
    if not out_geo_plug.isArray():
        raise Exception('Attribute ""{}".outputGeometry is not array" attribute!'.format(deformer))

    if maya.use_new_api():
        index_list = out_geo_plug.getExistingArrayAttributeIndices()
        num_index = len(index_list)
    else:
        index_list = maya.OpenMaya.MIntArray()
        num_index = out_geo_plug.getExistingArrayAttributeIndices(index_list)

    return_dict = dict()
    for i in range(num_index):
        plug_cnt = maya.cmds.listConnections(
            deformer + '.outputGeometry[' + str(index_list[i]) + ']', s=False, d=True, p=True)
        if len(plug_cnt) > 1:
            return_dict[deformer + '.outputGeometry[' + str(index_list[i]) + ']'] = plug_cnt
            if print_result:
                maya.logger.debug(
                    'Deformer output "' + deformer + '.outputGeometry[' + str(
                        index_list[i]) + ']" has ' + str(len(plug_cnt)) + ' outgoing connections:')
                for cnt in plug_cnt:
                    maya.logger.debug('\t- ' + cnt)

    return return_dict


def create_cluster(points, name):
    """
    Creates a cluster on the given points
    :param points: list<str>, names of points to cluster
    :param name: str, name of the cluster
    :return: list<str, st>, [cluster, handle]
    """

    cluster, handle = maya.cmds.cluster(points, n=name_lib.find_unique_name(name))
    return cluster, handle


def get_deformer_history(geo_obj):
    """
    Returns the history of the geometry object
    :param geo_obj: str, name of the geometry
    :return: list<str>, list of deformers in the deformation history
    """

    scope = maya.cmds.listHistory(geo_obj, pruneDagObjects=True)
    if not scope:
        return

    found = list()
    for obj in scope:
        inherited = maya.cmds.nodeType(obj, inherited=True)
        if 'geometryFilter' in inherited:
            found.append(obj)
        if maya.cmds.objectType(obj, isAType='shape') and not maya.cmds.nodeType(obj) == 'lattice':
            return found

    if not found:
        return None

    return found


def find_all_deformers(geo_obj):
    """
    Returns a list of all deformers in the given geometry deformation history
    :param geo_obj: st,r name of the geometry
    :return: list<str>, list of deformers in the given geometry object deformation history
    """

    history = get_deformer_history(geo_obj)
    found = list()
    if not history:
        return found

    for obj in history:
        if maya.cmds.objectType(obj, isAType='geometryFilter'):
            found.append(obj)

    return found


def find_deformer_by_type(geo_obj, deformer_type, return_all=False):
    """
    Given a mesh object find a deformer with deformer_type in its history
    :param geo_obj: str, name of a mesh
    :param deformer_type: str, correspnds to the Maya deformer type (skinCluster, blendShape, etc)
    :param return_all: bool, Whether to return all the deformer found of the given type or just the first one
    :return: list<names of deformers of type found in the history>
    """

    found = list()
    history = get_deformer_history(geo_obj)
    if not history:
        return None

    for obj in history:
        if obj and maya.cmds.nodeType(obj) == deformer_type:
            if not return_all:
                return obj
            found.append(obj)

    if not found:
        return None

    return found


def get_skin_weights(skin_deformer, vertices_ids=None):
    """
    Get the skin weights of the given skinCluster deformer
    :param skin_deformer: str, name of a skin deformer
    :param vertices_ids:
    :return: dict<int, list<float>, returns a dictionary where the key is the influence id and the
    value is the list of weights of the influence
    """

    mobj = node.get_mobject(skin_deformer)

    mf_skin = maya.OpenMayaAnim.MFnSkinCluster(mobj)

    weight_list_plug = mf_skin.findPlug('weightList', 0)
    weights_plug = mf_skin.findPlug('weights', 0)
    weight_list_attr = weight_list_plug.attribute()
    weights_attr = weights_plug.attribute()

    weights = dict()

    vertices_count = weight_list_plug.numElements()
    if not vertices_ids:
        vertices_ids = list(range(vertices_count))

    for vertex_id in vertices_ids:
        weights_plug.selectAncestorLogicalIndex(vertex_id, weight_list_attr)

        if maya.is_new_api():
            weight_influence_ids = weights_plug.getExistingArrayAttributeIndices()
        else:
            weight_influence_ids = maya.OpenMaya.MIntArray()
            weights_plug.getExistingArrayAttributeIndices(weight_influence_ids)

        influence_plug = maya.OpenMaya.MPlug(weights_plug)
        for influence_id in weight_influence_ids:
            influence_plug.selectAncestorLogicalIndex(influence_id, weights_attr)
            if influence_id not in weights:
                weights[influence_id] = [0] * vertices_count

            try:
                value = influence_plug.asDouble()
                weights[influence_id][vertex_id] = value
            except KeyError:
                # Assumes a removed influence
                pass

    return weights


def get_skin_envelope(geo_obj):
    """
    Returns envelope value of the skinCluster in the given geometry object
    :param geo_obj: str, name of the geometry
    :return: float
    """

    skin_deformer = find_deformer_by_type(geo_obj, 'skinCluster')
    if skin_deformer:
        return maya.cmds.getAttr('{}.envelope'.format(skin_deformer))

    return None


def set_skin_envelope(geo_obj, envelope_value):
    """
    Sets the envelope value of teh skinCluster in the given geometry object
    :param geo_obj: str, name of the geometry
    :param envelope_value: float. envelope value
    """

    skin_deformer = find_deformer_by_type(geo_obj, 'skinCluster')
    if skin_deformer:
        return maya.cmds.setAttr('{}.envelope'.format(skin_deformer), envelope_value)


def get_skin_influence_weights(influence_name, skin_deformer):
    """
    Returns weights of the influence in the given skinCluster deformer
    :param influence_name: str, name of the influence
    :param skin_deformer: str, skinCluster deformer name
    :return: list<float>, influences values
    """

    influence_index = get_index_at_skin_influence(influence_name, skin_deformer)
    if influence_index is None:
        return

    weights_dict = get_skin_weights(skin_deformer)
    if influence_index in weights_dict:
        weights = weights_dict[influence_index]
    else:
        indices = attribute.get_indices('{}.weightList'.format(skin_deformer))
        index_count = len(indices)
        weights = [0] * index_count

    return weights


def get_index_at_skin_influence(influence, skin_deformer):
    """
    Given an influence name, find at what index it connects to the skinCluster
    This corresponds to the matrix attribute.
    For example, skin_deformer.matrix[0] is the connection of the first influence
    :param influence: str, name of an influence
    :param skin_deformer: str, name of a skinCluster affected by the influence
    :return: int, index of the influence
    """

    connections = maya.cmds.listConnections('{}.worldMatrix'.format(influence), p=True, s=True)
    if not connections:
        return

    good_connection = None
    for cnt in connections:
        if cnt.startswith(skin_deformer):
            good_connection = cnt
            break

    if good_connection is None:
        return

    search = name_utils.search_last_number(good_connection)
    found_string = search.group()

    index = None
    if found_string:
        index = int(found_string)

    return index


def get_skin_influence_at_index(index, skin_deformer):
    """
    Returns which influence connect to the skinCluster at the given index
    :param index: int, index of an influence
    :param skin_deformer: str, name of the skinCluster to check the index
    :return: str, name of the influence at the given index
    """

    influence_slot = '{}.matrix[{}]'.format(skin_deformer, index)
    connection = attribute.get_attribute_input(influence_slot)
    if connection:
        connection = connection.split('.')
        return connection[0]

    return None


def get_skin_influence_names(skin_deformer, short_name=False):
    """
    Returns the names of the connected influences in the given skinCluster
    :param skin_deformer: str, name of the skinCluster
    :param short_name: bool, Whether to return full name of the influence or not
    :return: list<str>
    """

    mobj = node.get_mobject(skin_deformer)
    mf_skin = maya.OpenMayaAnim.MFnSkinCluster(mobj)
    influence_dag_paths = mf_skin.influenceObjects()

    influence_names = list()
    for i in range(len(influence_dag_paths)):
        if not short_name:
            influence_path_name = influence_dag_paths[i].fullPathName()
        else:
            influence_path_name = influence_dag_paths[i].partialPathName()
        influence_names.append(influence_path_name)

    return influence_names


def get_skin_influence_indices(skin_deformer):
    """
    Returns the indices of the connected influences in the given skinCluster
    This corresponds to the matrix attribute.
    For example, skin_deformer.matrix[0] is the connection of the first influence
    :param skin_deformer: str, name of a skinCluster
    :return: list<int>, list of indices
    """

    mobj = node.get_mobject(skin_deformer)
    mf_skin = maya.OpenMayaAnim.MFnSkinCluster(mobj)
    influence_dag_paths = mf_skin.influenceObjects()

    influence_ids = list()
    for i in range(len(influence_dag_paths)):
        influence_id = int(mf_skin.indexForInfluenceObject(influence_dag_paths[i]))
        influence_ids.append(influence_id)

    return influence_ids


def get_skin_influences(skin_deformer, short_name=True, return_dict=False):
    """
    Returns the influences connected to the skin cluster
    Returns a dictionary with the keys being the name of the influences being the value at the
    key index where the influence connects to the skinCluster
    :param skin_deformer: str, name of a skinCluster
    :param short_name: bool, Whether to return full name of the influence or not
    :param return_dict: bool, Whether to return a dictionary or not
    :return: variant<dict, list>
    """

    mobj = node.get_mobject(skin_deformer)
    mf_skin = maya.OpenMayaAnim.MFnSkinCluster(mobj)

    if maya.is_new_api():
        influence_dag_paths = mf_skin.influenceObjects()
        total_paths = len(influence_dag_paths)
    else:
        influence_dag_paths = maya.OpenMaya.MDagPathArray()
        mf_skin.influenceObjects(influence_dag_paths)
        total_paths = influence_dag_paths.length()

    influence_ids = dict()
    influence_names = list()
    for i in range(total_paths):
        influence_path = influence_dag_paths[i]
        if not short_name:
            influence_path_name = influence_dag_paths[i].fullPathName()
        else:
            influence_path_name = influence_dag_paths[i].partialPathName()
        influence_id = int(mf_skin.indexForInfluenceObject(influence_path))
        influence_ids[influence_path_name] = influence_id
        influence_names.append(influence_path_name)

    if return_dict:
        return influence_ids
    else:
        return influence_names


def get_non_zero_influences(skin_deformer):
    """
    Returns influences that have non zero weights in the skinCluster
    :param skin_deformer: str, name of a skinCluster deformer
    :return: list<str>, list of influences found in the skinCluster that have influence
    """

    influences = maya.cmds.skinCluster(skin_deformer, query=True, weightedInfluence=True)

    return influences


def add_missing_influences(skin_deformer1, skin_deformer2):
    """
    Make sure used influences in skin1 are added to skin2
    :param skin_deformer1: str, name of skinCluster
    :param skin_deformer2: str, name of skinCluster
    """

    influences1 = get_non_zero_influences(skin_deformer1)
    influences2 = get_non_zero_influences(skin_deformer2)

    for influence1 in influences1:
        if influence1 not in influences2:
            maya.cmds.skinCluster(skin_deformer2, edit=True, addInfluence=True, weight=0.0, normalizeWeights=1)


def get_skin_blend_weights(skin_deformer):
    """
    Returns the blendWeight values on the given skinCluster
    :param skin_deformer: str, name of a skinCluster deformer
    :return: list<float>, blend weight values corresponding to point order
    """

    indices = attribute.get_indices('{}.weightList'.format(skin_deformer))
    blend_weights = attribute.get_indices('{}.blendWeights'.format(skin_deformer))
    blend_weights_dict = dict()

    if blend_weights:
        for blend_weight in blend_weights:
            blend_weights_dict[blend_weight] = maya.cmds.getAttr(
                '{}.blendWeights[{}]'.format(skin_deformer, blend_weight))

    values = list()
    for i in range(len(indices)):
        if i in blend_weights_dict:
            value = blend_weights_dict[i]
            if type(value) < 0.000001:
                value = 0.0
            if isinstance(value, float):
                value = 0.0
            if value != value:
                value = 0.0

            values.append(value)
            continue
        else:
            values.append(0.0)
            continue

    return values


def set_skin_blend_weights(skin_deformer, weights):
    """
    Sets the blendWeights on the skinCluster given a list of weights
    :param skin_deformer: str, name of a skinCluster deformer
    :param weights: list<float>, list of weight values corresponding to point order
    """

    indices = attribute.get_indices('{}.weightList'.format(skin_deformer))

    new_weights = list()
    for weight in weights:
        if weight != weight:
            weight = 0.0
        new_weights.append(weight)

    for i in range(len(indices)):
        if maya.cmds.objExists('{}.blendWeights[{}]'.format(skin_deformer, i)):
            try:
                maya.cmds.setAttr('{}.blendWeights[{}]'.format(skin_deformer, i), weights[i])
            except Exception:
                pass


def set_skin_weights_to_zero(skin_deformer):
    """
    Sets all the weights on the given skinCluster to zero
    :param skin_deformer: str, name of a skinCluster deformer
    """

    weights = maya.cmds.ls('{}.weightList[*]'.format(skin_deformer))
    for weight in weights:
        weight_attrs = maya.cmds.listAttr('{}.weights'.format(weight), multi=True)
        if not weight_attrs:
            continue
        for weight_attr in weight_attrs:
            attr = '{}.{}'.format(skin_deformer, weight_attr)
            maya.cmds.setAttr(attr, 0)


@decorators.undo_chunk
def skin_mesh_from_mesh(source_mesh, target_mesh, exclude_joints=None, include_joints=None, uv_space=False):
    """
    Skins a mesh based on the skinning of another mesh
    Source mesh must be skinned and the target mesh will be skinned with the joints in the source mesh
    The skinning from the source mesh will be projected onto the target mesh
    :param source_mesh: str, name of a mesh
    :param target_mesh: str, name of a mesh
    :param exclude_joints: list<str>, exclude the named joint from the skinCluster
    :param include_joints: list<str>, include the named joints from the skinCluster
    :param uv_space: bool, Whether to copy the skin weights in UV space rather than point space
    """

    maya.logger.debug('Skinning {} using weights from {}'.format(target_mesh, source_mesh))

    skin = find_deformer_by_type(source_mesh, 'skinCluster')
    if not skin:
        maya.logger.warning('{} has no skin. No skinning to copy!'.lformat(source_mesh))
        return

    target_skin = find_deformer_by_type(target_mesh, 'skinCluster')
    if target_skin:
        maya.logger.warning('{} already has a skinCluster. Deleting existing one ...'.format(target_mesh))
        maya.cmds.delete(target_skin)
        target_skin = None

    influences = get_non_zero_influences(skin)

    if exclude_joints:
        for exclude in exclude_joints:
            if exclude in influences:
                influences.remove(exclude)
    if include_joints:
        found = list()
        for include in include_joints:
            if include in influences:
                found.append(include)
        influences = found

    # TODO: skinCluster should be renamed using NameIt lib
    if target_skin:
        if uv_space:
            maya.cmds.copySkinWeights(
                sourceSkin=skin,
                destinationSkin=target_skin,
                noMirror=True,
                surfaceAssociation='closestPoint',
                influenceAssociation=['name'],
                uvSpace=['map1', 'map1'],
                normalize=True
            )
        else:
            maya.cmds.copySkinWeights(
                sourceSkin=skin,
                destinationSkin=target_skin,
                noMirror=True,
                surfaceAssociation='closestPoint',
                influenceAssociation=['name'],
                normalize=True
            )
        skinned = maya.cmds.skinCluster(target_skin, query=True, weightedInfluence=True)
        unskinned = set(influences) ^ set(skinned)
        for jnt in unskinned:
            maya.cmds.skinCluster(target_skin, edit=True, removeInfluence=jnt)
    else:
        skin_name = name_lib.get_basename(target_mesh)
        target_skin = maya.cmds.skinCluster(
            influences, target_mesh, tsb=True, n=name_lib.find_unique_name('skin_{}'.format(skin_name)))[0]

    return target_skin
