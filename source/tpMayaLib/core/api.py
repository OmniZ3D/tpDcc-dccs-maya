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
    # endregion


class DoubleArray(ApiObject, object):
    # region Override Functions
    def _set_api_object(self):
        return maya.OpenMaya.MDoubleArray()

    def get(self):
        numbers = list()
        length = self.obj.length()
        for i in range(length):
            numbers.append(self.obj[i])

        return numbers
    # endregion


class PointArray(ApiObject, object):
    # region Override Functions
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
    # endregion

    # region Public Functions
    def length(self):
        return self.obju.length()
    # endregion


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

    # region Override Functions
    def _set_api_object(self, mobj):
        return mobj
    # endregion

    # region Public Functions
    def set_node_as_mjobject(self, node_name):
        """
        Sets the MObject from a node name
        :param node_name: str, name of a node
        """

        mobj = node_name_to_mobject(node_name)
        self.obj = self._set_api_object(mobj)
    # endregion


class MayaFunction(MayaObject, object):
    pass


class SelectionList(ApiObject, object):
    # region Override Functions
    def _set_api_object(self):
        return maya.OpenMaya.MSelectionList()
    # endregion

    # region Public Functions
    def create_by_name(self, name):
        try:
            self.obj.add(name)
        except Exception:
            maya.logger.warning('Could not add {} into selection list'.format(name))
            return

    def get_at_index(self, index=0):
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
        if maya.is_new_api():
            return self.obj.getDagPath(index)
        else:
            node_dag_path = maya.OpenMaya.MDagPath()
            self.obj.getDagPath(index, node_dag_path)
            return node_dag_path
    # endregion


class TransformFunction(MayaFunction, object):
    # region Override Functions
    def _set_api_object(self, mobj):
        return maya.OpenMaya.MFnTransform(mobj)
    # endregion

    # region Public Functions
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
    # endregion


class MeshFunction(MayaFunction, object):
    # region Override Functions
    def _set_api_object(self, mobj):
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

    # endregion


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

    return selection_list.get_at_index(0)
