#! /usr/bin/env python
# # -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with skins
"""

from __future__ import print_function, division, absolute_import

import cStringIO

import tpMayaLib as maya
from tpMayaLib.core import decorators, exceptions, node as node_utils, mesh as mesh_utils, joint as jnt_utils, transform as xform_utils


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
            tree_connections = maya.cmds.listConnections(skin_cluster, destination=True, source=False, plugs=False, connections=False)
            for branch in tree_connections:
                node_type = maya.cmds.nodeType(branch)
                if node_type == 'objectSet':
                    skin_cluster_set = branch
                    break

            if skin_cluster_set <= 0:
                maya.logger.warning('Wrapped joint "{}" with skinCluster "{}" has no valid SkinClusterSet'.format(self.joint, skin_cluster))
                return

            obj = maya.cmds.listConnections(skin_cluster_set, destination=True, source=False, plugs=False, connections=False)
            vertex_num = maya.cmds.polyEvaluate(obj, vertex=True)
            for vtx in range(vertex_num):
                self._display_weighted_verts.step()
                vtx_name =  '{0}.vtx[{1}]'.format(obj[0], str(vtx))
                weights = maya.cmds.skinPercent(skin_cluster, vtx_name, query=True, value=True)
                influences = maya.cmds.skinPercent(skin_cluster, vtx_name, query=True, transform=None)
                for i in range(len(influences)):
                    if influences[i] == self.joint and weights[i] > 0:
                        affected_verts.append(vtx_name)
                        affected_value.append(weights[i])
                        break

        print('Showing weights ...')

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
                    point_weights = maya.cmds.skinPercent(skin_cluster_name, pnt, transform=list_joint_influences[jnt], query=True, value=True)
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
