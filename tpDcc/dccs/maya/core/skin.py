#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with skins
"""

from __future__ import print_function, division, absolute_import

import cStringIO

import tpDcc.dccs.maya as maya
from tpDcc.libs.python import python, mathlib
from tpDcc.dccs.maya.core import decorators, exceptions, api, node as node_utils, mesh as mesh_utils
from tpDcc.dccs.maya.core import joint as jnt_utils, transform as xform_utils, shape as shape_utils


class ShowJointInfluence(object):
    """
    Displays affected vertices for selected joint
    """

    def __init__(self, joint):
        """
        Constructor
        :param joint: str, name of the joint we want to show vertex skin influences of
        """

        self.joint = None
        self.select_vertices = True
        self.show_weights = True
        self.delete_later = list()

        if jnt_utils.is_joint(joint) or xform_utils.is_transform(joint):
            self.joint = joint

        if jnt_utils.is_joint(joint) or xform_utils.is_transform(joint):
            self.joint = joint
            self.enable()

    @decorators.undo_chunk
    def enable(self):
        """
        Enables show vertex skin influences of the wrapped joint
        """

        self._cleanup()
        self._display_weighted_verts()

    @decorators.undo_chunk
    def disable(self):
        """
        Internal function used to unshow the weighted vertices of the wrapped joint
        """

        self._cleanup()
        maya.cmds.select(clear=True)

    def set_select_vertices(self, select_vertices):
        """
        Set if the influenced vertices should be selected or not
        :param select_vertices: bool
        """

        self.select_vertices = select_vertices

    def set_show_weights(self, show_weights):
        """
        Set if the weights of the influenced weights should be showed or not
        :param show_weights: bool
        """

        self.show_weights = show_weights

    @decorators.ShowMayaProgress('Showing influences')
    def _display_weighted_verts(self):
        """
        Internal function used to show the weighted vertices of the wrapped joint
        """

        affected_verts = list()
        affected_value = list()

        connections = list(set(maya.cmds.listConnections(self.joint, type='skinCluster')))
        if len(connections) <= 0:
            maya.logger.warning('Wrapped joint "{}" has no skinCluster!'.format(self.joint))
            return

        for skin_cluster in connections:
            skin_cluster_set = None
            tree_connections = maya.cmds.listConnections(
                skin_cluster, destination=True, source=False, plugs=False, connections=False)
            for branch in tree_connections:
                node_type = maya.cmds.nodeType(branch)
                if node_type == 'objectSet':
                    skin_cluster_set = branch
                    break

            if skin_cluster_set <= 0:
                maya.logger.warning(
                    'Wrapped joint "{}" with skinCluster "{}" has no valid SkinClusterSet'.format(
                        self.joint, skin_cluster))
                return

            obj = maya.cmds.listConnections(
                skin_cluster_set, destination=True, source=False, plugs=False, connections=False)
            vertex_num = maya.cmds.polyEvaluate(obj, vertex=True)
            for vtx in range(vertex_num):
                self._display_weighted_verts.step()
                vtx_name = '{0}.vtx[{1}]'.format(obj[0], str(vtx))
                weights = maya.cmds.skinPercent(skin_cluster, vtx_name, query=True, value=True)
                influences = maya.cmds.skinPercent(skin_cluster, vtx_name, query=True, transform=None)
                for i in range(len(influences)):
                    if influences[i] == self.joint and weights[i] > 0:
                        affected_verts.append(vtx_name)
                        affected_value.append(weights[i])
                        break

        if self.show_weights:
            maya.cmds.select(clear=True)
            grp = maya.cmds.group(empty=True, n='annotations_{}'.format(self.joint))
            for i in range(len(affected_verts)):
                pos = maya.cmds.pointPosition(affected_verts[i], world=True)
                loc = maya.cmds.spaceLocator()[0]
                maya.cmds.setAttr('{}.t'.format(loc), pos[0], pos[1], pos[2])
                maya.cmds.setAttr('{}.v'.format(loc), 0)
                maya.cmds.select(loc, replace=True)
                annotation_node = maya.cmds.annotate(loc, text=str(affected_value[i]), point=(pos[0], pos[1], pos[2]))
                annotation_xform = maya.cmds.listRelatives(annotation_node, parent=True, fullPath=True)
                maya.cmds.parent(annotation_xform, grp)
                maya.cmds.parent(loc, grp)
                self.delete_later.append(annotation_node)
                self.delete_later.append(loc)
            self.delete_later.append(grp)

        if self.select_vertices:
            maya.cmds.select(affected_verts, replace=True)

    def _cleanup(self):
        """
        Cleans objects created by the class
        """

        for obj in self.delete_later:
            maya.cmds.delete(obj)
        self.delete_later = list()

        if maya.cmds.objExists('annotations_{}'.format(self.joint)):
            maya.cmds.delete('annotations_{}'.format(self.joint))


class StoreSkinWeight(object):

    def __init__(self):
        self._do_run = False

    def run_store(self):
        self._do_run = True
        self._dag_skin_id_dict = dict()
        self.get_all_mesh_vertices()
        self.get_skin_weight()

    def get_mesh_node_list(self):
        """
        Returns list of meshes that belongs to the stored skin info
        :return: list(str)
        """

        if not self._do_run:
            return

        return self._mesh_node_list

    def get_all_influences(self):
        """
        Returns a list with all the influences that belongs to the stored skin info
        :return: list(str)
        """

        if not self._do_run:
            return

        return self._all_influences

    def get_all_skin_clusters(self):
        """
        Returns a list of all skin clusters that belongs to the stored skin info
        :return: dict(str, str)
        """

        if not self._do_run:
            return

        return self._all_skin_clusters

    def get_influences_dict(self):
        """
        Returns dictionary of influences that belongs to the stored skin info
        :return: dict
        """

        if not self._do_run:
            return

        return self._influences_dict

    def get_node_vertices_dict(self):
        """
        Returns dictionary of vertices that belongs to the stored skin info
        :return: dict
        """

        if not self._do_run:
            return

        return self._node_vertices_dict

    def get_node_weight_dict(self):
        """
        Returns dictionary of weights that belongs to the stored skin info
        :return: dict
        """

        if not self._do_run:
            return

        return self._node_weight_dict

    def get_node_skinfn_dict(self):
        """
        Returns dictionary of skinfn objects that belongs to the stored skin info
        :return: dict
        """

        if not self._do_run:
            return

        return self._node_skinfn_dict

    def get_show_dict(self):
        """
        Returns dictionary of weights that can be useful to show info of
        :return: dict
        """

        return self._show_dict

    def get_all_mesh_vertices(self):
        """
        Returns a dictionary containing all vertex IDs list and information of the meshes
        :return: list
        """

        selection_list = api.get_active_selection_list()
        selection_list_iter = api.SelectionListIterator(selection_list)

        loop = 0
        add_nodes = list()

        while not selection_list_iter.is_done():
            loop += 1
            if loop >= 10000:
                maya.logger.warning('Too many loops while retrieving vertices from mesh node!')
                return list()

            try:
                mesh_dag = selection_list_iter.get_dag_path()
            except Exception as e:
                maya.logger.error('Get Dag Path error : {}'.format(e.message))
                selection_list_iter.next()
                continue

            mesh_path_name = mesh_dag.full_path_name()
            add_nodes += [mesh_path_name]
            selection_list_iter.next()

        add_nodes = [maya.cmds.listRelatives(
            node, p=True, f=True)[0] if maya.cmds.nodeType(node) == 'mesh' else node for node in add_nodes]

        if maya.cmds.selectMode(query=True, component=True):
            self._hilite_nodes = maya.cmds.ls(hilite=True, long=True)
            self._hilite_nodes = mesh_utils.get_meshes_from_nodes(
                nodes=self._hilite_nodes, full_path=True, search_child_node=True)
            add_node = mesh_utils.get_meshes_from_nodes(
                maya.cmds.ls(slong=True, long=True, tr=True), full_path=True, search_child_node=True)
            if add_node:
                self._hilite_nodes += add_node
            if add_nodes:
                self._hilite_nodes += add_nodes
        else:
            self._hilite_nodes = maya.cmds.ls(
                slong=True, long=True, tr=True) + maya.cmds.ls(hlong=True, long=True, tr=True)
            self._hilite_nodes = mesh_utils.get_meshes_from_nodes(
                nodes=self._hilite_nodes, full_path=True, search_child_node=True)
            if add_nodes:
                self._hilite_nodes += add_nodes

        self._hilite_nodes = list(set(self._hilite_nodes))

        for n in self._hilite_nodes[:]:
            sel_list = api.SelectionList()
            sel_list.add(n)

            try:
                mesh_dag, component = selection_list.get_component(0)
            except Exception as e:
                maya.logger.erro('Get Dag Path error : {}'.format(e.message))
                continue

            skin_fn, vertex_array, skin_name = self._adjust_to_vertex_list(mesh_dag, component)
            if skin_fn is None:
                continue

            self._dag_skin_id_dict[mesh_dag.full_path_name()] = [
                skin_fn.get_api_object(), vertex_array.get_api_object(), skin_name, mesh_dag.get_api_object()
            ]

    def get_selected_mesh_vertices(self, node):
        """
        Returns selected vertices on the given mesh node
        :param node:
        :return:
        """

        selection_list = api.get_active_selection_list()
        selection_list_iter = api.SelectionListIterator(selection_list)

        selected_objs = dict()
        loop = 0
        vertex_arrays = list()

        while not selection_list_iter.is_done():
            loop += 1
            if loop >= 10000:
                maya.logger.warning('Too many loops while retrieving vertices from mesh node!')
                return vertex_arrays
            try:
                mesh_dag, component = selection_list_iter.get_component()
            except Exception as e:
                maya.logger.error('Get current vertex error : {}'.format(e.message))
                selection_list_iter.next()
                continue

            mesh_path_name = mesh_dag.full_path_name()
            if maya.cmds.nodeType(mesh_path_name) == 'mesh':
                mesh_path_name = maya.cmds.listRelatives(mesh_path_name, p=True, f=True)[0]
            if node != mesh_path_name:
                selection_list_iter.next()
                continue

            skin_fn, vertex_array, skin_name = self._adjust_to_vertex_list(mesh_dag, component, force=True)
            vertex_arrays += sorted(vertex_array)
            selection_list_iter.next()

        return vertex_arrays

    def get_skin_cluster(self, dag_path=None):
        """
        Loops through the DAG hierarchy of the given DAG path finding a skin cluster
        :param dag_path: variant, api.DagPath
        :return:
        """

        if not dag_path:
            return None, None

        skin_cluster = maya.cmds.ls(maya.cmds.listHistory(dag_path.full_path_name()), type='skinCluster')
        if not skin_cluster:
            return None, None

        cluster_name = skin_cluster[0]
        selection_list = api.SelectionList()
        selection_list.create_by_name(cluster_name)

        skin_node = selection_list.get_depend_node(0)
        skin_fn = api.SkinCluster(skin_node)

        return skin_fn, cluster_name

    def get_skin_weight(self):

        self._node_weight_dict = dict()
        self._node_vertices_dict = dict()
        self._influences_id_list = list()
        self._influences_dict = dict()
        self._all_influences = list()
        self._all_skin_clusters = dict()
        self._mesh_node_list = list()
        self._show_dict = dict()
        self._node_skinfn_dict = dict()

        for mesh_path_name, skin_vtx in self._dag_skin_id_dict.items():
            skin_fn = skin_vtx[0]
            vertex_array = skin_vtx[1]
            skin_name = skin_vtx[2]
            mesh_path = skin_vtx[3]

            self._node_skinfn_dict[mesh_path_name] = skin_fn
            if maya.cmds.nodeType(mesh_path_name) == 'mesh':
                mesh_path_name = maya.cmds.listRelatives(mesh_path_name, p=True, f=True)[0]

            single_id_comp = api.SingleIndexedComponent()
            vertex_component = single_id_comp.create(maya.OpenMaya.MFn.kMeshVertComponent)
            single_id_comp.add_elements(vertex_array)

            api_skin_fn = api.SkinCluster(skin_fn)
            influence_dags = api_skin_fn.influence_objects()
            influence_indices = api.IntArray(len(influence_dags), 0)
            for i in range(len(influence_dags)):
                influence_indices[i] = int(api_skin_fn.index_for_influence_object(influence_dags[i]))

            try:
                weights = api_skin_fn.get_weights(mesh_path, vertex_component)
            except Exception as e:
                maya.logger.error('Get Skin Weight error : {}'.format(e.message))
                continue

            weights = self._convert_shape_weights(len(influence_indices), weights)

            influence_list = [api.DagPath(influence_dags[i]).full_path_name() for i in range(len(influence_indices))]

            self._node_vertices_dict[mesh_path_name] = vertex_array
            self._all_skin_clusters[mesh_path_name] = skin_name
            self._mesh_node_list.append(mesh_path_name)
            self._influences_id_list.append(influence_indices)
            self._node_weight_dict[mesh_path_name] = weights
            self._influences_dict[mesh_path_name] = influence_list
            self._all_influences += influence_list
            self._show_dict[mesh_path_name] = vertex_array

        self._all_influences = sorted(list(set(self._all_influences)))

    def _adjust_to_vertex_list(self, mesh_dag, component, force=False):

        skin_fn, skin_name = self.get_skin_cluster(mesh_dag)

        if not force:
            if not skin_fn or not skin_name:
                return None, None, None
            if not mesh_dag.has_fn(maya.OpenMaya.MFn.kMesh) or skin_name == '':
                return None, None, None

        sel_id = dict()
        component_type = None

        if component.has_fn(maya.OpenMaya.MFn.kMeshVertComponent):
            component_type = 'vtx'
        elif component.has_fn(maya.OpenMaya.MFn.kMeshEdgeComponent):
            component_type = 'edge'
        elif component.has_fn(maya.OpenMaya.MFn.kMeshPolygonComponent):
            component_type = 'face'
        if component_type:
            component_fn = api.SingleIndexedComponent(component)

        mesh_fn = api.MeshFunction(mesh_dag)

        if 'vtx' == component_type:
            pass
        elif 'edge' == component_type:
            pass
        elif 'face' == component_type:
            pass
        else:
            vertex_ids = range(mesh_fn.get_number_of_vertices())
            vertex_array = api.IntArray()
            vertex_array.set(vertex_ids)

        return skin_fn, vertex_array, skin_name

    def _convert_shape_weights(self, shape, weights):
        """
        Converts given shape weights into a 2D array of vertices
        :param shape:
        :param weights:
        :return:
        """

        return [[weights[i + j * shape] for i in range(shape)] for j in range(int(len(weights) / shape))]


def check_skin(skin_cluster):
    """
    Checks if a node is valid skin cluster and raise and exception if the node is not valid
    :param skin_cluster: str, name of the node to be checked
    :return: bool, True if the given node is a skin cluster node
    """

    if not is_skin_cluster(skin_cluster):
        raise exceptions.SkinClusterException(skin_cluster)


def is_skin_cluster(skin_cluster):
    """
    Checks if the given node is a valid skinCluster
    :param skin_cluster:  str, name of the node to be checked
    :return: bool, True if the given node is a skin cluster node
    """

    if not maya.cmds.objExists(skin_cluster):
        maya.logger.error('SkinCluster "{}" does not exists!'.format(skin_cluster))
        return False
    if maya.cmds.objectType(skin_cluster) != 'skinCluster':
        maya.logger.error('Object "{}" is not a valid skinCluster node!'.format(skin_cluster))
        return False

    return True


def find_related_skin_cluster(geo):
    """
    Returns the skinCluster node attached to the specified geometry
    :param geo: str, geometry
    :return: variant, None || str
    """

    node_utils.check_node(node=geo)

    shape_node = node_utils.get_shape(node=geo)
    if not shape_node:
        return None

    skin_cluster = maya.mel.eval('findRelatedSkinCluster("{}")'.format(shape_node))
    if not skin_cluster:
        skin_cluster = maya.cmds.ls(maya.cmds.listHistory(shape_node), type='skinCluster')
        if skin_cluster:
            skin_cluster = skin_cluster[0]
    if not skin_cluster:
        return None

    return skin_cluster


@decorators.undo
def average_vertex(selection, use_distance):
    """
    Generates an average weight from all selected vertices to apply to the last selected vertex
    :param selection: list<Vertex>, list of vertices to average
    :param use_distance:
    :return:
    """

    total_vertices = len(selection)
    if total_vertices < 2:
        maya.logger.warning('Not enough vertices selected! Select a minimum of 2 vertices')
        return

    obj = selection[0]
    if '.' in selection[0]:
        obj = selection[0].split('.')[0]

    is_edge_selection = False
    if '.e[' in selection[0]:
        is_edge_selection = True

    skin_cluster_name = find_related_skin_cluster(obj)
    maya.cmds.setAttr('{0}.envelope'.format(skin_cluster_name), 0)
    succeeded = True

    try:
        maya.cmds.skinCluster(obj, edit=True, normalizeWeights=True)
        if total_vertices == 2 or is_edge_selection:
            base_list = [selection]
            if is_edge_selection:
                base_list = mesh_utils.edges_to_smooth(edges_list=selection)

            percentage = 99.0 / len(base_list)
        else:
            last_selected = selection[-1]
            point_list = [x for x in selection if x != last_selected]
            mesh_name = last_selected.split('.')[0]

            list_joint_influences = maya.cmds.skinCluster(mesh_name, query=True, weightedInfluence=True)
            influence_size = len(list_joint_influences)

            temp_vertex_joints = list()
            temp_vertex_weights = list()
            for pnt in point_list:
                for jnt in range(influence_size):
                    point_weights = maya.cmds.skinPercent(
                        skin_cluster_name, pnt, transform=list_joint_influences[jnt], query=True, value=True)
                    if point_weights < 0.000001:
                        continue
                    temp_vertex_joints.append(list_joint_influences[jnt])
                    temp_vertex_weights.append(point_weights)

            total_values = 0.0
            average_values = list()
            clean_list = list()
            for i in temp_vertex_joints:
                if i not in clean_list:
                    clean_list.append(i)

            for i in range(len(clean_list)):
                working_value = 0.0
                for j in range(len(temp_vertex_joints)):
                    if not temp_vertex_joints[j] == clean_list[i]:
                        continue
                    working_value += temp_vertex_weights[j]
                num_points = len(point_list)
                average_values.append(working_value / num_points)
                total_values += average_values[i]

            summary = 0
            for value in range(len(average_values)):
                temp_value = average_values[value] / total_values
                average_values[value] = temp_value
                summary += average_values[value]

            cmd = cStringIO.StringIO()
            cmd.write('maya.cmds.skinPercent("%s","%s", transformValue=[' % (skin_cluster_name, last_selected))

            for count, skin_joint in enumerate(clean_list):
                cmd.write('("%s", %s)' % (skin_joint, average_values[count]))
                if not count == len(clean_list) - 1:
                    cmd.write(', ')
            cmd.write('])')
            eval(cmd.getvalue())
    except Exception as e:
        maya.logger.warning(str(e))
        succeeded = False
    finally:
        maya.cmds.setAttr('{0}.envelope'.format(skin_cluster_name), 1)

    return succeeded


class SkinJointObject(object):
    """
    Class to manage skinning objects easily
    """

    def __init__(self, geometry, name, joint_radius=1.0):
        self._geometry = geometry
        self._name = name
        self._joint_radius = joint_radius
        self._join_ends = False
        self._cvs = list()
        self._cvs_count = 0
        self._skin_cluster = None
        self._joints = list()
        self._cvs_dict = dict()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def create(self):
        """
        Function that creates skinning
        :return:
        """

        self._create()

    def get_joints_list(self):
        """
        Returns the names of the joints in the skinning
        :return: list(str)
        """

        return self._joints

    def get_skin(self):
        """
        Returns skin deformer name
        :return: str
        """

        return self._skin_cluster

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create(self):
        """
        Internal function that MUST be override for custom skinning
        """

        raise NotImplementedError()

    def _create_joint(self, cvs):
        """
        Internal function that creates a new joint in the given CV
        :param cvs: list(str)
        :return:  str, name of the created joint
        """

        joint = jnt_utils.create_joint_at_points(cvs, self._name, joint_radius=self._joint_radius)
        cvs = python.force_list(cvs)
        self._cvs_dict.setdefault(joint, list()).append(cvs)

        return joint


class SkinJointSurface(SkinJointObject, object):
    """
    Class to manage skinning for surfaces
    """

    def __init__(self, geometry, name, joint_radius=1.0):
        super(SkinJointSurface, self).__init__(geometry, name, joint_radius)

        self._join_ends = False
        self._join_both_ends = False
        self._first_joint_pivot_at_start = True
        self._last_joint_pivot_at_end = True
        self._maya_type = None
        self._joint_u = True

        if shape_utils.has_shape_of_type(self._geometry, 'nurbsCurve'):
            self._maya_type = 'nurbsCurve'
        elif shape_utils.has_shape_of_type(self._geometry, 'nurbsSurface'):
            self._maya_type = 'nurbsSurface'

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def _create(self):
        self._cvs = maya.cmds.ls('{}.cv[*]'.format(self._geometry), flatten=True)
        if self._maya_type == 'nurbsCurve':
            self._cvs_count = len(self._cvs)
        elif self._maya_type == 'nurbsSurface':
            index = '[0][*]' if self._joint_u else '[*][0]'
            self._cvs_count = len(maya.cmds.ls('{}.cv{}'.format(self._geometry, index), flatten=True))

        start_index = 0
        cvs_count = self._cvs_count

        if self._join_ends:
            if self._join_both_ends:
                self._create_start_and_end_joined_joints()
            else:
                last_joint = self._create_start_and_end_joints()
            cvs_count = len(self._cvs[2:self._cvs_count])
            start_index = 2

        for i in range(start_index, cvs_count):
            if self._maya_type == 'nurbsCurve':
                cv = '{}.cv[{}]'.format(self._geometry, i)
            elif self._maya_type == 'nurbsSurface':
                index = '[*][{}]'.format(i) if self._joint_u else '[{}][*]'.format(i)
                cv = '{}.cv{}'.format(self._geometry, index)

            joint = self._create_joint(cv)
            self._joints.append(joint)

        if self._join_ends and not self._join_both_ends:
            self._joints.append(last_joint)

        self._skin()

        return self._joints

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_join_ends(self, flag):
        """
        Sets whether the skin ends of the surfaces take up 2 CVs or not
        :param flag: bool, Whether 2 CVs at the start have one joint, and 2 CVs on the end have one joint
        """

        self._join_ends = flag

    def set_join_both_ends(self, flag):
        """
        Sets whether the skin ends of the surface are joined together
        :param flag: bool, Whether to join or not the ends of the surface
        """

        self._join_both_ends = flag

    def set_last_joint_pivot_at_end(self, flag):
        """
        Sets whether or not the last joint pivot should be moved to the end of the curve
        :param flag: bool
        """

        self._last_joint_pivot_at_end = flag

    def set_first_joint_pivot_at_start(self, flag):
        """
        Sets whether or not the start joint pivot should be moved to the start of the curve
        :param flag: bool
        """

        self._first_joint_pivot_at_start = flag

    def set_joint_u(self, flag):
        """
        Sets whether to skin the U instead of the V spans
        :param flag: bool
        """

        self._joint_u = flag

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_start_and_end_joints(self):
        start_cvs = None
        end_cvs = None
        start_position = None
        end_position = None

        if self._maya_type == 'nurbsCurve':
            start_cvs = '{}.cv[0:1]'.format(self._geometry)
            end_cvs = '{}.cv[{}:{}]'.format(self._geometry, self._cvs_count - 2, self._cvs_count - 1)
            start_position = maya.cmds.xform('{}.cv[0]'.format(self._geometry), q=True, ws=True, t=True)
            end_position = maya.cmds.xform(
                '{}.cv[{}]'.format(self._geometry, self._cvs_count - 1), q=True, ws=True, t=True)
        elif self._maya_type == 'nurbsSurface':
            if self._joint_u:
                cv_count_u = len(maya.cmds.ls('{}.cv[*][0]'.format(self._geometry), flatten=True))
                index1 = '[0:*][0:1]'
                index2 = '[0:*][{}:{}]'.format(self._cvs_count - 2, self._cvs_count - 1)
                index3 = '[{}][0]'.format(cv_count_u - 1)
                index4 = '[0][{}]'.format(self._cvs_count - 1)
                index5 = '[{}][{}]'.format(cv_count_u, self._cvs_count - 1)
            else:
                cv_count_v = len(maya.cmds.ls('{}.cv[0][*]'.format(self._geometry), flatten=True))
                index1 = '[0:1][0:*]'
                index2 = '[{}:{}][0:*]'.format(self._cvs_count - 2, self._cvs_count - 1)
                index3 = '[0][{}]'.format(cv_count_v - 1)
                index4 = '[{}][0]'.format(self._cvs_count - 1)
                index5 = '[{}][{}]'.format(self._cvs_count - 1, cv_count_v)

            start_cvs = '{}.cv{}'.format(self._geometry, index1)
            end_cvs = '{}.cv{}'.format(self._geometry, index2)
            p1 = maya.cmds.xform('{}.cv[0][0]'.format(self._geometry), q=True, ws=True, t=True)
            p2 = maya.cmds.xform('{}.cv{}'.format(self._geometry, index3), q=True, ws=True, t=True)
            start_position = mathlib.get_mid_point(p1, p2)
            p1 = maya.cmds.xform('{}.cv{}'.format(self._geometry, index4), q=True, ws=True, t=True)
            p2 = maya.cmds.xform('{}.cv{}'.format(self._geometry, index5), q=True, ws=True, t=True)
            end_position = mathlib.get_mid_point(p1, p2)

        start_joint = self._create_joint(start_cvs)
        self._joints.append(start_joint)
        if self._first_joint_pivot_at_start:
            maya.cmds.xform(start_joint, ws=True, rp=start_position, sp=start_position)

        end_joint = self._create_joint(end_cvs)
        if self._last_joint_pivot_at_end:
            maya.cmds.xform(end_joint, ws=True, rp=end_position, sp=end_position)

        return end_joint

    def _create_start_and_end_joined_joints(self):
        start_cvs = None
        end_cvs = None

        if self._maya_type == 'nurbsCurve':
            start_cvs = '{}.cv[0:1]'.format(self._geometry)
            end_cvs = '{}.cv[{}:{}]'.format(self._geometry, self._cvs_count - 2, self._cvs_count - 1)
        elif self._maya_type == 'nurbsSurface':
            if self._joint_u:
                index1 = '[0:*][0]'
                index2 = '[0:*][{}]'.format(self._cvs_count - 1)
            else:
                index1 = '[0][0:*]'
                index2 = '[{}][0:*]'.format(self._cvs_count - 1)
            start_cvs = '{}.cv{}'.format(self._geometry, index1)
            end_cvs = '{}.cv{}'.format(self._geometry, index2)

        cvs = start_cvs + end_cvs
        joint = self._create_joint(cvs)
        self._joints.append(joint)

        return joint

    def _skin(self):
        self._skin_cluster = maya.cmds.skinCluster(self._joints, self._geometry, tsb=True)[0]
        for joint, cvs in self._cvs_dict.items():
            for cv in cvs:
                maya.cmds.skinPercent(self._skin_cluster, cv, transformValue=[(joint, 1)])
        maya.cmds.setAttr('{}.skinningMethod'.format(self._skin_cluster), 1)


class SkinJointCurve(SkinJointSurface, object):
    def __init__(self, geometry, name, joint_radius=1.0):
        super(SkinJointCurve, self).__init__(geometry, name, joint_radius)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def set_joint_u(self, flag):
        maya.logger.warning('Cannot set joint U, curves only have one direction for spans')

    def _create(self):
        self._cvs = maya.cmds.ls('{}.cv[*]'.format(self._geometry), flatten=True)
        self._cvs_count = len(self._cvs)
        start_index = 0
        cvs_count = self._cvs_count

        if self._join_ends:
            last_joint = self._create_start_and_end_joints()
            cvs_count = len(self._cvs[2:self._cvs_count])
            start_index = 2

        for i in range(start_index, cvs_count):
            joint = self._create_joint('{}.cv[{}]'.format(self._geometry, i))
            self._joints.append(joint)

        if self._join_ends:
            self._joints.append(last_joint)

        self._skin()

        return self._joints

    def _create_start_and_end_joints(self):
        joint = self._create_joint('{}.cv[0:1]'.format(self._geometry))
        self._joints.append(joint)
        position = maya.cmds.xform('{}.cv[0]'.format(self._geometry), query=True, ws=True, t=True)
        maya.cmds.xform(joint, ws=True, rp=position, sp=position)
        last_joint = self._create_joint('{}.cv[{}:{}]'.format(self._geometry, self._cvs_count - 2, self._cvs_count - 1))
        position = maya.cmds.xform('{}.cv[{}]'.format(self._geometry, self._cvs_count - 1), q=True, ws=True, t=True)
        maya.cmds.xform(last_joint, ws=True, rp=position, sp=position)

        return last_joint


def apply_smooth_bind(geo=None, show_options=True):
    """
    Applies smooth bind to given nodes
    :param geo: str or list(str) or None
    """

    if not geo:
        geo = maya.cmds.ls(slong=True)
    if not geo:
        return

    if show_options:
        maya.cmds.SmoothBindSkinOptions()
    else:
        print('Applying smooth skin')
