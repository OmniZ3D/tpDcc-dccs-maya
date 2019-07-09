#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya API
"""

from __future__ import print_function, division, absolute_import

import tpMayaLib as maya


class ApiObject(object):
    """
    Wrapper class for MObjects
    """

    def __init__(self):
        self.obj = self._set_api_object()

    def __call__(self):
        return self.obj

    # region Public Functions
    def get(self):
        return None

    def get_api_object(self):
        return self.obj
    # endregion

    # region Private Functions
    def _set_api_object(self):
        return None
    # endregion


class Point(ApiObject, object):
    def __init__(self, x=0, y=0, z=0, w=1):
        self.obj = self._set_api_object(x, y, z, w)

    # region Override Functions
    def _set_api_object(self, x, y, z, w):
        return maya.OpenMaya.MPoint(x, y, z, w)

    def get(self):
        return [self.obj.x, self.obj.y, self.obj.z, self.obj.w]

    def get_as_vector(self):
        return [self.obj.x, self.obj.y, self.obj.z]
    # endregion


class FloatPoint(ApiObject, object):
    def __init__(self, x=0, y=0, z=0, w=1):
        self.obj = self._set_api_object(x, y, z, w)

    # region Override Functions
    def _set_api_object(self, x, y, z, w):
        return maya.OpenMaya.MFloatPoint(x, y, z, w)

    def get(self):
        return [self.obj.x, self.obj.y, self.obj.z, self.obj.w]

    def get_as_vector(self):
        return [self.obj.x, self.obj.y, self.obj.z]
    # endregion


class Matrix(ApiObject, object):
    def __init__(self, matrix_list=None):
        if matrix_list is None:
            matrix_list = list()
        self.obj = self._set_api_object(matrix_list)

    # region Override Functions
    def _set_api_object(self, matrix_list):
        matrix = maya.OpenMaya.MMatrix()
        if matrix_list:
            if maya.is_new_api():
                matrix = maya.OpenMaya.MScriptUtil.createMatrixFromList(matrix_list)
            else:
                maya.OpenMaya.MScriptUtil.createMatrixFromList(matrix_list, matrix)

        return matrix

    def set_matrix_from_list(self, matrix_list):
        if maya.is_new_api():
            self.obj = maya.OpenMaya.MScriptUtil.createMatrixFromList(matrix_list)
        else:
            maya.OpenMaya.MScriptUtil.createMatrixFromList(matrix_list, self.obj)


class IntArray(ApiObject, object):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        super(IntArray, self).__init__()

    def __getitem__(self, key):
        return self.obj[key]

    def __setitem__(self, key, value):
        self.obj[key] = value

    def __len__(self):
        return self.length()

    def _set_api_object(self):
        if self._args or self._kwargs:
            return maya.OpenMaya.MIntArray(*self._args, **self._kwargs)
        else:
            return maya.OpenMaya.MIntArray()

    def get(self):
        numbers = list()
        length = self.obj.length()
        for i in range(length):
            numbers.append(self.obj[i])

        return numbers

    def set(self, numbers):
        for i in range(len(numbers)):
            self.obj.append(i)

    def length(self):
        """
        Returns total numbers of elements in the array
        :return: int
        """

        if maya.is_new_api():
            return len(self.obj)
        else:
            return self.obj.length()


class DoubleArray(ApiObject, object):

    def __init__(self, double_array=None, *args, **kwargs):
        self._double_array = double_array
        self._args = args
        self._kwargs = kwargs
        super(DoubleArray, self).__init__()

    def __getitem__(self, key):
        return self.obj[key]

    def __setitem__(self, key, value):
        self.obj[key] = value

    def __len__(self):
        return self.length()

    def _set_api_object(self):

        if self._double_array:
            return self._double_array
        else:
            if self._args or self._kwargs:
                return maya.OpenMaya.MDoubleArray(*self._args, **self._kwargs)
            else:
                return maya.OpenMaya.MDoubleArray()

    def get(self):
        numbers = list()
        length = self.obj.length()
        for i in range(length):
            numbers.append(self.obj[i])

        return numbers

    def set(self, numbers):
        for i in range(len(numbers)):
            self.obj.append(i)

    def length(self):
        """
        Returns total numbers of elements in the array
        :return: int
        """

        if maya.is_new_api():
            return len(self.obj)
        else:
            return self.obj.length()


class PointArray(ApiObject, object):

    def _set_api_object(self):
        return maya.OpenMaya.MPointArray()

    def get(self):
        values = list()
        length = self.obj.length()
        for i in range(length):
            point = self.obj[i]
            part = [point.x, point.y, point.z]
            values.append(part)

        return values

    def set(self, positions):
        for i in range(len(positions)):
            self.obj.set(i, positions[i][0], positions[i][1], positions[i][2])


class DagPathArray(ApiObject, object):

    def __init__(self, dag_path_array=None):
        self._dag_path_array = dag_path_array
        super(DagPathArray, self).__init__()

    def __getitem__(self, key):
        return self.obj[key]

    def __setitem__(self, key, value):
        self.obj[key] = value

    def __len__(self):
        return self.length()

    def _set_api_object(self):
        if self._dag_path_array:
            return self._dag_path_array
        else:
            return maya.OpenMaya.MDagPathArray()

    def length(self):
        """
        Returns total numbers of elements in the array
        :return: int
        """

        if maya.is_new_api():
            return len(self.obj)
        else:
            return self.obj.length()


class MayaObject(ApiObject, object):
    """
    Wrapper class for API objects
    """

    def __init__(self, mobj=None):
        if type(mobj) in [str, unicode]:
            mobj = node_name_to_mobject(mobj)

        if mobj:
            self.obj = self._set_api_object(mobj)
        else:
            self.obj = maya.OpenMaya.MObject()

        self.mobj = mobj

    def _set_api_object(self, mobj):
        return mobj

    def has_fn(self, fn):
        """
        Returns True if the internal Maya object supports the specified function set specified by fn.
        :param fn: MFn
        :return: bool
        """

        return self.obj.hasFn(fn)

    def set_node_as_mjobject(self, node_name):
        """
        Sets the MObject from a node name
        :param node_name: str, name of a node
        """

        mobj = node_name_to_mobject(node_name)
        self.obj = self._set_api_object(mobj)


class MayaFunction(MayaObject, object):
    pass


class DagPath(ApiObject, object):
    def __init__(self, dag_path=None):
        self._dag_path = dag_path
        super(DagPath, self).__init__()

    def _set_api_object(self):
        if self._dag_path:
            return self._dag_path
        else:
            return maya.OpenMaya.MDagPath()

    def full_path_name(self):
        """
        Returns a string representation of the path from the DAG root to the path's last node
        :return: str
        """

        return self.obj.fullPathName()

    def has_fn(self, fn):
        """
        Returns True if the object at the end of the path supports the function set represented by type.
        :param fn: MFn
        :return: bool
        """

        return self.obj.hasFn(fn)


class SelectionList(ApiObject, object):
    def __init__(self, sel_list=None):
        self._sel_list = sel_list
        super(SelectionList, self).__init__()

    def _set_api_object(self):
        if self._sel_list:
            return self._sel_list
        else:
            return maya.OpenMaya.MSelectionList()

    def add(self, item):
        """
        Adds given item to the list
        :param item: variant, str or MPlug, MObject, MDagPath, component (tuple(MDagPath, MObject))
        """

        self.obj.add(item)

    def add_item(self, item, merge_with_existing=True):
        """
        Adds the given item to the list, where the item
        :param item: variant, MPlug, MObject, MDagPath, component (tuple(MDagPath, MObject))
        :param merge_with_existing: bool
        """

        self.obj.add(item, merge_with_existing)

    def add_by_pattern(self, pattern, search_child_namespaces=False):
        """
        Adds to the list nay nodes, DAG paths, components or plugs which match the given pattern string
        :param pattern: str
        :param search_child_namespaces: bool
        """

        self.obj.add(pattern, search_child_namespaces)

    def create_by_name(self, name):
        """
        Creates a selection list with the given object name added
        :param name: str
        """

        try:
            self.obj.add(name)
        except Exception:
            maya.logger.warning('Could not add {} into selection list'.format(name))
            return

    def get_depend_node(self, index=0):
        """
        Returns depend node at given index
        :param index:
        :return:
        """
        mobj = MayaObject()
        try:
            if maya.is_new_api():
                mobj = MayaObject(self.obj.getDependNode(0))
            else:
                self.obj.getDependNode(0, mobj())
            return mobj()
        except Exception:
            maya.logger.warning('Could not get MObject at index {}'.format(index))
            return

    def get_dag_path(self, index=0):
        """
        Returns the DAG path associated with the index'th item of the list.
        Raises TypeError if the item is neither a DAG path nor a component.
        Raises IndexError if index is out of range.
        :param index: int
        :return: DagPath
        """

        if maya.is_new_api():
            maya_dag_path = self.obj.getDagPath(index)
        else:
            maya_dag_path = maya.OpenMaya.MDagPath()
            self.obj.getDagPath(index, maya_dag_path)

        return DagPath(maya_dag_path)

    def get_component(self, index=0):
        """
        Returns the index'th item of the list as a component, represented by
        a tuple containing an MDagPath and an MObject. If the item is just a
        DAG path without a component then MObject.kNullObj will be returned
        in the second element of the tuple. Raises TypeError if the item is
        neither a DAG path nor a component. Raises IndexError if index is
        out of range.
        :return: tuple(MDagPath, MObject)
        """

        if maya.is_new_api():
            maya_dag, maya_component = self.obj.getComponent(index)
        else:
            maya_dag = maya.OpenMaya.MDagPath()
            maya_component = maya.OpenMaya.MObject()
            self.obj.getDagPath(index, maya_dag, maya_component)

        mesh_dag = DagPath(maya_dag)
        component = MayaObject(maya_component)

        return mesh_dag, component


class SelectionListIterator(ApiObject, object):

    def __init__(self, sel_list):
        self._sel_list = sel_list
        super(SelectionListIterator, self).__init__()

    def _set_api_object(self):
        if hasattr(self._sel_list, 'obj'):
            return maya.OpenMaya.MItSelectionList(self._sel_list.obj)
        else:
            return maya.OpenMaya.MItSelectionList(self._sel_list)

    def is_done(self):
        """
        Returns whether or not there is anything more to iterator over
        :return: bool
        """

        return self.obj.isDone()

    def next(self):
        """
        Advances to the next item. If components are selected then advance to the next component
        If a filter is specified then the next item will be one that matches the filter
        """

        self.obj.next()

    def get_dag_path(self):
        """
        Returns the DAG path of the current selection item
        :return: MDagPath
        """

        if maya.is_new_api():
            maya_dag_path = self.obj.getDagPath()
        else:
            maya_dag_path = maya.OpenMaya.MDagPath()
            self.obj.getDagPath(maya_dag_path)

        return DagPath(maya_dag_path)

    def get_component(self):
        """
        Returns the DAG path and the component of the current selection item
        :return: tuple(MDagPath, MObject)
        """

        if maya.is_new_api():
            maya_dag, maya_component = self.obj.getComponent()
        else:
            maya_dag = maya.OpenMaya.MDagPath()
            maya_component = maya.OpenMaya.MObject()
            self.obj.getDagPath(maya_dag, maya_component)

        mesh_dag = DagPath(maya_dag)
        component = MayaObject(maya_component)

        return mesh_dag, component


class SingleIndexedComponent(ApiObject, object):
    def __init__(self, maya_object=None):
        self._mobj = maya_object
        super(SingleIndexedComponent, self).__init__()

    def _set_api_object(self):
        if self._mobj:
            if hasattr(self._mobj, 'obj'):
                return maya.OpenMaya.MFnSingleIndexedComponent(self._mobj.obj)
            else:
                return maya.OpenMaya.MFnSingleIndexedComponent(self._mobj)
        else:
            return maya.OpenMaya.MFnSingleIndexedComponent()

    def create(self, mfn):
        """
        Creates a new, empty component, attaches it to the function set and returns a MayaObject which references it
        :param mfn: MFn
        :return: MayaObject
        """

        new_cmp = self.obj.create(mfn)
        return MayaObject(new_cmp)

    def add_elements(self, elements):
        """
        Adds the specified elements to the component
        :param elements: variant, int or MIntArray or IntArray
        """

        if hasattr(elements, 'obj'):
            self.obj.addElements(elements.obj)
        else:
            self.obj.addElements(elements)


class SkinCluster(ApiObject, object):

    def __init__(self, skin_node):
        self._skin_node = skin_node
        super(SkinCluster, self).__init__()

    def _set_api_object(self):

        if isinstance(self._skin_node, maya.OpenMayaAnim.MFnSkinCluster):
            return self._skin_node
        else:
            if hasattr(self._skin_node, 'obj'):
                return maya.OpenMayaAnim.MFnSkinCluster(self._skin_node.obj)
            else:
                return maya.OpenMayaAnim.MFnSkinCluster(self._skin_node)

    def influence_objects(self):
        """
        Returns an array of paths to the influence objects for the skinCluster
        :return: DagPathArray
        """

        if maya.is_new_api():
            maya_dag_path_array = self.obj.influenceObjects()
        else:
            maya_dag_path_array = maya.OpenMaya.MDagPathArray()
            self.obj.influenceObjects(maya_dag_path_array)

        dag_path_array = DagPathArray(maya_dag_path_array)
        return dag_path_array

    def index_for_influence_object(self, influence_obj):
        """
        Returns the logical index of the matrix array attribute where the
        specified influence object is attached.
        :param influence_obj: MayaObject or MObject
        """

        if isinstance(influence_obj, MayaObject):
            return self.obj.indexForInfluenceObject(influence_obj.obj)
        else:
            return self.obj.indexForInfluenceObject(influence_obj)

    def get_weights(self, shape=None, components=None, influence=None):
        """
        Returns the skinCluster weights of the given influence objects on
        the specified components of the deformed shape.

        If no influence index is provided then a tuple containing the weights
        and the number of influence objects will be returned.

        If a single influence index is provided the an array of weights will
        be returned, one per component in the same order as in 'components'.

        If an array of influence indices is provided an array of weights will
        be returned containing as many weights for each component as there
        are influences in the 'influenceIndices' array. The weights will be
        in component order: i.e. all of the weight values for the first
        component, followed by all the weight values for the second component,
        and so on.

        :param shape: MDagPath or DagPath
        :param components: MObject or MayaObject
        :param influence: MIntArray or IntArray or int
        :return: (DoubleArray, int) or DoubleArray
        """

        if shape:
            if isinstance(shape, DagPath):
                shape = shape.obj
        if components:
            if isinstance(components, MayaObject):
                components = components.obj

        if maya.is_new_api():
            if not shape and not components and not influence:
                raise RuntimeError('You need to pass at least two arguments to get_weights function')

            if shape and components:
                if not influence:
                    weights, index = self.obj.getWeights(shape, components)
                    api_double_array = DoubleArray(weights)
                    return api_double_array, index
                else:
                    if isinstance(influence, IntArray):
                        influence_to_use = influence.obj
                    else:
                        influence_to_use = influence
                    weights = self.obj.getWeights(shape, components, influence_to_use)
                    api_double_array = DoubleArray(weights)
                    return api_double_array

            else:
                if not influence:
                    return None
                else:
                    return None, None
        else:
            weights = maya.OpenMaya.MDoubleArray()
            influences_counter_utils = ScriptUtils()
            influences_ptr = influences_counter_utils.as_integer_pointer()
            self.obj.getWeights(shape, components, weights, influences_ptr)
            api_double_array = DoubleArray(weights)
            return api_double_array



class TransformFunction(MayaFunction, object):

    def _set_api_object(self, mobj):
        return maya.OpenMaya.MFnTransform(mobj)

    def get_transformation_matrix(self):
        return self.obj.transformation()

    def get_matrix(self):
        transform_matrix = self.get_transformation_matrix()
        return transform_matrix.asMatrix()

    def get_vector_matrix_product(self, vector):
        # TODO: Not working properly
        maya.logger.warning('get_vector_matrix_product() does not work properly yet ...!')
        vct = maya.OpenMaya.MVector()
        vct.x = vector[0]
        vct.y = vector[1]
        vct.z = vector[2]
        space = maya.OpenMaya.MSpace.kWorld
        orig_vct = self.obj.getTranslation(space)
        vct *= self.get_matrix()
        vct += orig_vct

        return vct.x, vct.y, vct.z


class MeshFunction(MayaFunction, object):

    def _set_api_object(self, mobj):
        if hasattr(mobj, 'obj'):
            return maya.OpenMaya.MFnMesh(mobj.obj)
        else:
            return maya.OpenMaya.MFnMesh(mobj)
    # endregion

    # region Public Functions
    def refresh_mesh(self):
        self.obj.updateSurface()

    def copy(self, source_mesh, transform):
        mesh_obj = node_name_to_mobject(source_mesh)
        self.obj.copy(mesh_obj, transform)

    def get_number_of_vertices(self):
        if maya.is_new_api():
            return self.obj.numVertices
        else:
            return self.obj.numVertices()

    def get_number_of_edges(self):
        if maya.is_new_api():
            return self.obj.numEdges
        else:
            return self.obj.numEdges()

    def get_number_of_faces(self):
        if maya.is_new_api():
            return self.obj.numPolygons
        else:
            return self.obj.numPolygons()

    def get_number_of_uvs(self):
        if maya.is_new_api():
            return self.obj.numUVs
        else:
            return self.obj.numUVs()

    def get_number_of_triangles(self):

        if maya.is_new_api():
            triangles, triangle_verts = self.obj.getTriangles()
        else:
            triangles, triangle_verts = maya.OpenMaya.MIntArray(), maya.OpenMaya.MIntArray()
            self.obj.getTriangles(triangles, triangle_verts)

        count = 0
        for triangle in triangles:
            if triangle == 1:
                count += 1

        return count

    def get_vertex_positions(self):
        if maya.is_new_api():
            point_array = PointArray()
            point_array.obj = self.obj.getPoints(maya.OpenMaya.MSpace.kWorld)
        else:
            point_array = PointArray()
            self.obj.getPoints(point_array.obj, maya.OpenMaya.MSpace.kWorld)

        return point_array.get()

    def set_vertex_positions(self, positions):
        point_array = PointArray()
        for pos in positions:
            point_array.obj.append(*pos)

        self.obj.setPoints(point_array.obj, maya.OpenMaya.MSpace.kWorld)

    def get_uv_at_point(self, vector):
        api_space = maya.OpenMaya.MSpace.kWorld
        point = Point(vector[0], vector[1], vector[2])
        uv = maya.OpenMaya.MScriptUtil().asFloat2Ptr()
        self.obj.getUVAtPoint(point.get_api_object(), uv, api_space)
        u = maya.OpenMaya.MScriptUtil.getFloat2ArrayItem(uv, 0, 0)
        v = maya.OpenMaya.MScriptUtil.getFloat2ArrayItem(uv, 0, 1)

        return u, v


class ScriptUtils(ApiObject, object):

    def _set_api_object(self):
        return maya.OpenMaya.MScriptUtil()

    def as_integer_pointer(self):
        """
        Return an unsigned integer pointer to the data of this class.
        :return: int
        """

        return self.obj.asUintPtr()


def node_name_to_mobject(object_name):
    """
    Initializes MObject of the given node
    :param object_name: str, name of a node
    :return: MObject
    """

    if not maya.cmds.objExists(object_name):
        return None

    selection_list = SelectionList()
    selection_list.create_by_name(object_name)
    if maya.cmds.objectType(object_name, isAType='transform') or maya.cmds.objectType(object_name, isAType='shape'):
        return selection_list.get_dag_path(0)

    return selection_list.get_depend_node(0)


def get_active_selection_list():
    """
    Returns selection list with current selected objects
    :return: maya.OpenMaya.MSelectionList
    """

    if maya.is_new_api():
        selection_list = maya.OpenMaya.MGlobal.getActiveSelectionList()
    else:
        selection_list = maya.OpenMaya.MSelectionList()
        maya.OpenMaya.MGlobal.getActiveSelectionList(selection_list)

    return SelectionList(sel_list=selection_list)
