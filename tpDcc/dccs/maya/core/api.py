#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya API
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.python import mathlib, python

import tpDcc.dccs.maya as maya


class ApiObject(object):
    """
    Wrapper class for MObjects
    """

    def __init__(self):
        self.obj = self._set_api_object()

    def __call__(self):
        return self.obj

    def get(self):
        return None

    def get_api_object(self):
        return self.obj

    def _set_api_object(self):
        return None


class Point(ApiObject, object):
    def __init__(self, x=0, y=0, z=0, w=1):
        self.obj = self._set_api_object(x, y, z, w)

    def _set_api_object(self, x, y, z, w):
        return maya.OpenMaya.MPoint(x, y, z, w)

    def get(self):
        return [self.obj.x, self.obj.y, self.obj.z, self.obj.w]

    def get_as_vector(self):
        return [self.obj.x, self.obj.y, self.obj.z]


class FloatPoint(ApiObject, object):
    def __init__(self, x=0, y=0, z=0, w=1):
        self.obj = self._set_api_object(x, y, z, w)

    def _set_api_object(self, x, y, z, w):
        return maya.OpenMaya.MFloatPoint(x, y, z, w)

    def get(self):
        return [self.obj.x, self.obj.y, self.obj.z, self.obj.w]

    def get_as_vector(self):
        return [self.obj.x, self.obj.y, self.obj.z]


class Matrix(ApiObject, object):
    def __init__(self, matrix_list=None):
        if matrix_list is None:
            matrix_list = list()
        self.obj = self._set_api_object(matrix_list)

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

    def length(self):
        if maya.is_new_api():
            return len(self.obj)
        else:
            return self.obj.length()


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
        if python.is_string(mobj):
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


class MayaIterator(MayaObject, object):
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

        return maya_dag_path

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

    def get_triangle_ids(self):
        if maya.is_new_api():
            triangles, triangle_verts = self.obj.getTriangles()
        else:
            triangles = maya.OpenMaya.MIntArray()
            triangle_verts = maya.OpenMaya.MIntArray()
            self.obj.getTriangles(triangles, triangle_verts)

        id_list = list()
        for i in range(len(triangles)):
            if triangles[i] == 1:
                id_list.append(i)

        return id_list

    def get_quad_ids(self):
        if maya.is_new_api():
            triangles, triangle_verts = self.obj.getTriangles()
        else:
            triangles = maya.OpenMaya.MIntArray()
            triangle_verts = maya.OpenMaya.MIntArray()
            self.obj.getTriangles(triangles, triangle_verts)

        id_list = list()
        for i in range(len(triangles)):
            if triangles[i] == 2:
                id_list.append(i)

        return id_list

    def get_non_tri_quad_ids(self):
        if maya.is_new_api():
            triangles, triangle_verts = self.obj.getTriangles()
        else:
            triangles = maya.OpenMaya.MIntArray()
            triangle_verts = maya.OpenMaya.MIntArray()
            self.obj.getTriangles(triangles, triangle_verts)

        id_list = list()
        for i in range(len(triangles)):
            if triangles[i] > 2:
                id_list.append(i)

        return id_list

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

    def get_point_at_uv(self, u_value=0, v_value=0):

        space = maya.OpenMaya.MSpace.kWorld

        point = Point(0.0, 0.0, 0.0).get_api_object()
        util = maya.OpenMaya.MScriptUtil()
        util.createFromList([float(u_value), float(v_value)], 2)
        uv = util.asFloat2Ptr()

        # TODO: We need to get polygon ID
        polygon_id = 0
        self.obj.getPointAtUV(polygon_id, point, uv, space)

    def get_closest_face(self, vector):
        pointA = maya.OpenMaya.MPoint(vector[0], vector[1], vector[2])
        pointB = maya.OpenMaya.MPoint()
        space = maya.OpenMaya.MSpace.kWorld

        if maya.is_new_api():
            index = self.obj.getClosestPoint(pointA, pointB, space)
        else:
            util = maya.OpenMaya.MScriptUtil()
            id_pointer = util.asIntPtr()
            self.obj.getClosestPoint(pointA, pointB, space, id_pointer)
            index = maya.OpenMaya.MScriptUtil(id_pointer).asInt()

        return index

    def get_closest_position(self, source_vector):

        # TODO: Implement to support both OpenMaya and OpenMaya2

        new_point = maya.OpenMaya.MPoint()
        point_base = maya.OpenMaya.MPoint()
        point_base.x = source_vector[0]
        point_base.y = source_vector[1]
        point_base.z = source_vector[2]
        accelerator = self.obj.autoUniformGridParams()
        space = maya.OpenMaya.MSpace.kWorld
        self.obj.getClosestPoint(point_base, new_point, space, None, accelerator)

        return [new_point.x, new_point.y, new_point.z]

    def get_closest_normal(self, source_vector, at_source_position=False):
        """
        Returns the closes normal of the given source vector
        :param source_vector: list(float, float, float), position to find the normal closest
        :param at_source_position: bool, Whether to add source_vector to the normal vector so it is
            returned relative to the source vector
        """

        # TODO: Implement to support both OpenMaya and OpenMaya2

        new_point = maya.OpenMaya.MPoint()
        point_base = maya.OpenMaya.MPoint()
        point_base.x = source_vector[0]
        point_base.y = source_vector[1]
        point_base.z = source_vector[2]
        accelerator = self.obj.autoUniformGridParams()
        space = maya.OpenMaya.MSpace.kWorld
        self.obj.getClosestNormal(point_base, new_point, space, None, accelerator)

        if at_source_position:
            position = mathlib.vector_add(source_vector, new_point)
            return position
        else:
            return [new_point.x, new_point.y, new_point.z]

    def get_closest_intersection(self, source_vector, direction_vector):
        """
        Returns the closest intersection between source vector and direction vector
        :param source_vector:
        :param direction_vector:
        :return:
        """

        # TODO: Implement to support both OpenMaya and OpenMaya2

        point_base = maya.OpenMaya.MFloatPoint()
        point_base.x = source_vector[0]
        point_base.y = source_vector[1]
        point_base.z = source_vector[2]

        float_base = maya.OpenMaya.MFloatVector()
        float_base.x = source_vector[0]
        float_base.y = source_vector[1]
        float_base.z = source_vector[2]

        point_direction = maya.OpenMaya.MFloatVector()
        point_direction.x = direction_vector[0]
        point_direction.y = direction_vector[1]
        point_direction.z = direction_vector[2]

        point_direction = point_direction - float_base

        accelerator = self.api_object.autoUniformGridParams()
        space = maya.OpenMaya.MSpace.kWorld

        hit_point = maya.OpenMaya.MFloatPoint()

        hit_double = maya.OpenMaya.MScriptUtil()
        hit_param_ptr = hit_double.asFloatPtr()

        hit_face = maya.OpenMaya.MScriptUtil()
        hit_face_ptr = hit_face.asIntPtr()

        hit_triangle = maya.OpenMaya.MScriptUtil()
        hit_triangle_ptr = hit_triangle.asIntPtr()

        hit_bary1 = maya.OpenMaya.MScriptUtil()
        hit_bary1_ptr = hit_bary1.asFloatPtr()

        hit_bary2 = maya.OpenMaya.MScriptUtil()
        hit_bary2_ptr = hit_bary2.asFloatPtr()

        self.obj.closestIntersection(
            point_base, point_direction, None, None, False, space, 100000, False, accelerator,
            hit_point, hit_param_ptr, hit_face_ptr, hit_triangle_ptr, hit_bary1_ptr, hit_bary2_ptr
        )

        return [hit_point.x, hit_point.y, hit_point.z]

    def get_closest_intersection_face(self, source_vector, direction_vector, max_distance=10000):
        """
        Returns the closest face intersection between source vector and direction vector
        :param source_vector:
        :param direction_vector:
        :return: int, intersected face index
        """

        # TODO: Implement to support both OpenMaya and OpenMaya2

        point_base = maya.OpenMaya.MFloatPoint()
        point_base.x = source_vector[0]
        point_base.y = source_vector[1]
        point_base.z = source_vector[2]

        float_base = maya.OpenMaya.MFloatVector()
        float_base.x = source_vector[0]
        float_base.y = source_vector[1]
        float_base.z = source_vector[2]

        point_direction = maya.OpenMaya.MFloatVector()
        point_direction.x = direction_vector[0]
        point_direction.y = direction_vector[1]
        point_direction.z = direction_vector[2]

        point_direction = point_direction - float_base

        accelerator = self.obj.autoUniformGridParams()
        space = maya.OpenMaya.MSpace.kWorld

        hit_point = maya.OpenMaya.MFloatPoint()

        hit_double = maya.OpenMaya.MScriptUtil()
        hit_param_ptr = hit_double.asFloatPtr()

        hit_face = maya.OpenMaya.MScriptUtil()
        hit_face_ptr = hit_face.asIntPtr()

        hit_triangle = maya.OpenMaya.MScriptUtil()
        hit_triangle_ptr = hit_triangle.asIntPtr()

        hit_bary1 = maya.OpenMaya.MScriptUtil()
        hit_bary1_ptr = hit_bary1.asFloatPtr()

        hit_bary2 = maya.OpenMaya.MScriptUtil()
        hit_bary2_ptr = hit_bary2.asFloatPtr()

        self.obj.closestIntersection(
            point_base, point_direction, None, None, False, space, max_distance, False, accelerator, hit_point,
            hit_param_ptr, hit_face_ptr, hit_triangle_ptr, hit_bary1_ptr, hit_bary2_ptr)

        face_index = maya.OpenMaya.MScriptUtil.getInt(hit_face_ptr)

        return face_index


class NurbsSurfaceFunction(MayaFunction, object):

    def _set_api_object(self, mobj):
        return maya.OpenMaya.MFnNurbsSurface(mobj)

    def get_closest_parameter(self, vector):
        point = Point(vector[0], vector[1], vector[2])
        u = maya.OpenMaya.MScriptUtil()
        u_ptr = u.asDoublePtr()
        maya.OpenMaya.MScriptUtil.setDouble(u_ptr, 0.0)
        v = maya.OpenMaya.MScriptUtil()
        v_ptr = v.asDoublePtr()
        maya.OpenMaya.MScriptUtil.setDouble(v_ptr, 0.0)
        space = maya.OpenMaya.MSpace.kWorld
        self.obj.closestPoint(point.get_api_object(), 0, u_ptr, v_ptr, 0, 0.00001, space)
        u = maya.OpenMaya.MScriptUtil.getDouble(u_ptr)
        v = maya.OpenMaya.MScriptUtil.getDouble(v_ptr)

        return u, v

    def get_position_from_parameter(self, u, v):
        point = Point()
        space = maya.OpenMaya.MSpace.kWorld
        self.obj.getPointAtParam(u, v, point.get_api_object(), space)

        return point.get_as_vector()

    def get_closest_normal(self, source_vector, at_source_position=False):
        space = maya.OpenMaya.MSpace.kWorld
        uv = self.get_closest_parameter(source_vector)
        vector = self.obj.normal(uv[0], uv[1], space)
        if not at_source_position:
            return vector
        else:
            position = mathlib.vector_add(source_vector, vector)
            return position


class NurbsCurveFunction(MayaFunction, object):
    def _set_api_object(self, mobj):
        return maya.OpenMaya.MFnNurbsCurve(mobj)

    def get_degree(self):
        return self.obj.degree()

    def get_cv_count(self):
        return self.obj.numCVs()

    def get_cv_positions(self):
        point = PointArray()
        point = point.get_api_object()
        self.obj.getCVs(point)
        found = list()
        for i in range(point.length()):
            x = point[i][0]
            y = point[i][1]
            z = point[i][2]
            found.append([x, y, z])

        return found

    def set_cv_positions(self, positions):
        point_array = PointArray()
        point_array.set(positions)
        self.obj.setCVs(point_array)

    def get_form(self):
        return self.obj.form()

    def get_knot_count(self):
        return self.obj.numKnots()

    def get_span_count(self):
        return self.obj.numSpans()

    def get_knot_values(self):
        knots = DoubleArray()
        self.obj.getKnots(knots.get_api_object())

        return knots.get()

    def get_position_at_parameter(self, param):
        point = Point()
        self.obj.getPointAtParam(param, point.get_api_object())

        return point.get()[0:3]

    def get_closest_position(self, list_value):
        point = Point(list_value[0], list_value[1], list_value[2])
        point = self.obj.closestPoint(point.get_api_object(), None, 0.0000001, maya.OpenMaya.MSpace.kWorld)

        return [point.x, point.y, point.z]

    def get_parameter_at_position(self, list_value):
        u = maya.OpenMaya.MScriptUtil()
        u_ptr = u.asDoublePtr()
        maya.OpenMaya.MScriptUtil.setDouble(u_ptr, 0.0)
        space = maya.OpenMaya.MSpace.kWorld
        list_value = self.get_closest_position(list_value)
        point = Point(list_value[0], list_value[1], list_value[2])
        self.obj.getParamAtPoint(point.get_api_object(), u_ptr, space)

        return maya.OpenMaya.MScriptUtil.getDouble(u_ptr)

    def get_parameter_at_length(self, value):
        return self.obj.findParamFromLength(value)


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


class IterateCurveCV(MayaIterator, object):
    def _set_api_object(self, mobj):
        return maya.OpenMaya.MItCurveCV(mobj)


class IterateGeometry(MayaIterator, object):
    def _set_api_object(self, mobj):
        return maya.OpenMaya.MItGeometry(mobj)

    def get_points(self):
        space = maya.OpenMaya.MSpace.kObject

        if maya.is_new_api():
            points = self.obj.allPositions(space)
        else:
            points = maya.OpenMaya.MPointArray()
            self.obj.allPositions(points, space)

        return points

    def set_points(self, points):
        space = maya.OpenMaya.MSpace.kObject
        self.obj.setAllPositions(points, space)

    def get_points_as_list(self):
        points = self.get_points()
        found = list()
        for i in range(points.length()):
            x = points[i][0]
            y = points[i][1]
            z = points[i][2]
            found.append([x, y, z])

        return found


class IterateEdges(MayaIterator, object):
    def _set_api_object(self, mobj):
        return maya.OpenMaya.MItMeshEdge(mobj)

    def set_edge(self, edge_id):
        if maya.is_new_api():
            prev = self.obj.setIndex(edge_id)
        else:
            script_util = maya.OpenMaya.MScriptUtil()
            prev = script_util.asIntPtr()

        return prev

    def get_connected_vertices(self, edge_id):
        self.set_edge(edge_id)
        vert1_id = self.obj.index(0)
        vert2_id = self.obj.index(1)
        self.obj.reset()

        return [vert1_id, vert2_id]

    def get_connected_faces(self, edge_id):
        self.set_edge(edge_id)
        if maya.is_new_api():
            connected_faces = self.obj.getConnectedFaces()
        else:
            connected_faces = maya.OpenMaya.MIntArray()
            self.obj.getConnectedFaces(connected_faces)

        return connected_faces

    def get_connected_edges(self, edge_id):
        self.set_edge(edge_id)

        if maya.is_new_api():
            connected_edges = self.obj.getConnectedEdges()
        else:
            connected_edges = maya.OpenMaya.MIntArray()
            self.obj.getConnectedFaces(connected_edges)

        return connected_edges


class IterateVertices(MayaIterator, object):
    def _set_api_object(self, mobj):
        return maya.OpenMaya.MItMeshVertex(mobj)

    def is_done(self):
        return self.obj.isDone()

    def index(self):
        return self.obj.index()

    def next(self):
        self.obj.next()

    def count(self):
        return self.obj.count()

    def has_vertex_colors(self):
        """
        Returns whether or not any of the vertices has vertex colors
        :return: bool
        """
        has_vertex_color = False
        while not self.obj.isDone():
            has_vertex_color = self.obj.hasColor()
            if has_vertex_color:
                break
            self.obj.next()
        self.obj.reset()

        return has_vertex_color

    def get_vertex_colors(self, skip_vertices_without_vertex_colors=True):
        """
        Returns dictionary which contains vertices indices as keys and its associated vertex color as value (if exists)
        :param skip_vertices_without_vertex_colors: bool, If True, vertices with no vertex colors are skipped
        :return: dict(int, maya.OpenMaya.MColor)
        """

        vertices_color = dict()
        while not self.obj.isDone():
            has_vertex_color = self.obj.hasColor()
            if has_vertex_color:
                if maya.is_new_api():
                    vertices_color[self.obj.index()] = self.obj.getColor()
                else:
                    vertex_color = maya.OpenMaya.MColor()
                    self.obj.getColor(vertex_color)
                    vertices_color[self.obj.index()] = vertex_color
            else:
                if not skip_vertices_without_vertex_colors:
                    vertices_color[self.obj.index()] = None
            self.obj.next()

        self.obj.reset()

        return vertices_color


class IteratePolygonFaces(MayaIterator, object):
    def _set_api_object(self, mobj):
        return maya.OpenMaya.MItMeshPolygon(mobj)

    def is_done(self):
        return self.obj.isDone()

    def index(self):
        return self.obj.index()

    def next(self):
        self.obj.next()

    def reset(self):
        self.obj.reset()

    def count(self):
        return self.obj.count()

    def get_area(self, face_id=None):
        if face_id:
            if maya.is_new_api():
                prev = self.obj.setIndex(face_id)
            else:
                script_util = maya.OpenMaya.MScriptUtil()
                prev = script_util.asIntPtr()
                self.obj.setIndex(face_id, prev)

        if maya.is_new_api():
            area_value = self.obj.getArea()
        else:
            script_util = maya.OpenMaya.MScriptUtil()
            area_ptr = script_util.asDoublePtr()
            maya.OpenMaya.MScriptUtil.setDouble(area_ptr, 0.0)
            self.obj.getArea(area_ptr)
            area_value = maya.OpenMaya.MScriptUtil.getDouble(area_ptr)

        return area_value

    def get_face_center_vectors(self):
        center_vectors = list()
        for i in range(self.obj.count()):
            point = self.obj.center()
            center_vectors.append([point.x, point.y, point.z])
            self.obj.next()
        self.obj.reset()

        return center_vectors

    def get_closest_face(self, vector):
        closest_distance = None
        closest_face = None

        while not self.obj.isDone():
            center = self.obj.center()
            distance = mathlib.get_distance_between_vectors(vector, [center.x, center.y, center.z])
            if distance < 0.001:
                closest_face = self.obj.index()
                self.obj.reset()
                return closest_face
            if distance < closest_distance or not closest_distance:
                closest_distance = distance
                closest_face = self.obj.index()
            self.obj.next()

        self.obj.reset()

        return closest_face

    def get_edges(self, face_id):
        if maya.is_new_api():
            prev = self.obj.setIndex(face_id)
            edges = self.obj.getEdges()
        else:
            script_util = maya.OpenMaya.MScriptUtil()
            prev = script_util.asIntPtr()
            self.obj.setIndex(face_id, prev)
            edges = maya.OpenMaya.MIntArray()
            self.obj.getEdges(edges)

        self.obj.reset()

        return edges

    def get_center(self, face_id=None):
        space = maya.OpenMaya.MSpace.kWorld
        if face_id:
            if maya.is_new_api():
                prev = self.obj.setIndex(face_id)
            else:
                script_util = maya.OpenMaya.MScriptUtil()
                prev = script_util.asIntPtr()
                self.obj.setIndex(face_id, prev)

        point = self.obj.center(space)

        return point.x, point.y, point.z

    def get_normal(self, face_id=None):
        space = maya.OpenMaya.MSpace.kWorld
        if face_id:
            if maya.is_new_api():
                prev = self.obj.setIndex(face_id)
            else:
                script_util = maya.OpenMaya.MScriptUtil()
                prev = script_util.asIntPtr()
                self.obj.setIndex(face_id, prev)

        if maya.is_new_api():
            vector = self.obj.getNormal(space)
        else:
            vector = maya.OpenMaya.MVector()
            self.obj.getNormal(vector, space)

        return vector.x, vector.y, vector.z

    def get_normal_tangent(self, face_id=None):

        # TODO: Finish this implementation

        space = maya.OpenMaya.MSpace.kWorld
        if face_id:
            if maya.is_new_api():
                prev = self.obj.setIndex(face_id)
            else:
                script_util = maya.OpenMaya.MScriptUtil()
                prev = script_util.asIntPtr()
                self.obj.setIndex(face_id, prev)

        position = self.obj.center(space)
        if maya.is_new_api():
            normal_vector = self.obj.getNormal(space)
        else:
            normal_vector = maya.OpenMaya.MVector()
            self.obj.getNormal(normal_vector, space)

        position_vector = maya.OpenMaya.MVector()
        position_vector.x = 0
        position_vector.y = 0
        position_vector.z = 0

        tangent = position_vector * normal_vector

        return tangent


class KeyframeFunction(MayaFunction, object):

    CONSTANT = None
    LINEAR = None
    CYCLE = None
    CYCLE_RELATIVE = None
    OSCILLATE = None

    def _set_api_object(self, mobj):
        api_obj = maya.OpenMayaAnim.MFnAnimCurve(mobj)
        self.CONSTANT = api_obj.kConstant
        self.LINEAR = api_obj.kLinear
        self.CYCLE = api_obj.kCycle
        self.CYCLE_RELATIVE = api_obj.kCycleRelative
        self.OSCILLATE = api_obj.kOscillate

        return api_obj

    def set_post_infinity(self, infinity_type):
        self.obj.setPostInfinityType(infinity_type)

    def set_pre_infinity(self, infinity_type):
        self.obj.setPreInfinityType(infinity_type)
