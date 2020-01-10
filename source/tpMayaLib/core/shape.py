#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to shapes
"""

from __future__ import print_function, division, absolute_import


import tpMayaLib as maya
from tpMayaLib.core import node, exceptions


TYPE_DICT = {
    'mesh': 'vtx',
    'nurbsCurve': 'cv',
    'nurbsSurface': 'cv',
    'lattice': 'pt',
    'subdiv': 'smp'
}

GEO_OUTPUT = {
    'mesh': ['.outMesh', '.worldMesh'],
    'nurbsCurve': ['.local', '.worldSpace'],
    'nurbsSurface': ['.local', '.worldSpace'],
    'lattice': ['.latticeOutput', '.worldLattice'],
    'subdiv': ['.outSubdiv', '.worldSubdiv']
}

ALL_GEO = [
    'mesh',
    'nurbsSurface',
    'subdiv'
]

GEO_INPUT = {
    'mesh': '.inMesh',
    'nurbsCurve': '.create',
    'nurbsSurface': '.create',
    'lattice': '.latticeInput',
    'subdiv': '.create'
}


def check_shape(shape):
    """
    Checks if a node is a valid shape and raise a exception if the shape is not valid
    :param shape: str, name of the node to be checked
    :return: bool, True if the given node is a shape node
    """

    if not is_shape(shape):
        raise exceptions.ShapeException(shape)


def is_a_shape(node):
    """
    Checks node type to determine if the given node is a shape or not
    :param node: str
    :return: bool
    """

    if not maya.cmds.objectType(node, isAType='shape'):
        return False

    return True


def is_shape(obj):
    """
    Check if the specified object is a valid shape node
    :param obj: str, object to check as a shape node
    :return: bool
    """

    if not maya.cmds.objExists(obj):
        return False

    if not maya.cmds.objectType(obj, isAType='shape'):
        return False

    mobj = node.get_mobject(obj)
    if not mobj.hasFn(maya.OpenMaya.MFn.kShape):
        return False

    return True


def has_intermediate(geo):

    """
    Checks if the specified geometry has any intermediate shapes
    :param geo: str, transform to check intermediate shapes for
    """

    return bool(len(list_intermediates(geo)))


def list_intermediates(geo):
    """
    Return a list of intermediate shapes under a transform parent
    :param geo: str, transform to list intermediate shapes for
    """

    if not maya.cmds.objExists(geo):
        raise exceptions.NodeExistsException(geo)
    if is_shape(geo):
        geo = maya.cmds.listRelatives(geo, parent=True, path=True)[0]

    # Get intermediate shapes
    shapes = maya.cmds.listRelatives(geo, shapes=True, noIntermediate=True, path=True)
    all_shapes = maya.cmds.listRelatives(geo, shapes=True, path=True)
    if not all_shapes:
        return []
    if not shapes:
        return all_shapes
    intermediate_shapes = list(set(all_shapes) - set(shapes))

    return intermediate_shapes


def get_first_shape(node):
    """
    Returns the first active shape on a given transform
    :param node: str, transform node to get shape from
    :return: str
    """

    shapes = get_shapes(node=node, non_intermediates=True, intermediates=False)
    if shapes:
        return shapes[0]

    return None


def get_shapes(node_name, non_intermediates=True, intermediates=True, full_path=True):
    """
    Returns a list of shapes under a transform parent
    :param node_name: str, transform to list parent for
    :param non_intermediates: bool, list non intermediate shapes
    :param intermediates: bool, list intermediate shapes
    :param full_path: bool, Whether to return long names or not
    :return: list
    """

    if node_name is None or not maya.cmds.objExists(node_name):
        raise exceptions.NodeExistsException(node_name)

    if is_shape(node_name):
        parent = maya.cmds.listRelatives(node_name, parent=True, fullPath=full_path)
        return maya.cmds.listRelatives(parent, shapes=True, fullPath=True, ni=non_intermediates)
        # node_name = cmds.listRelatives(node_name, parent=True, path=True)[0]

    # Get shapes
    shapes = list()
    if non_intermediates:
        non_intermediate_shapes = maya.cmds.listRelatives(node_name, shapes=True, noIntermediate=True, path=True)
        if non_intermediate_shapes:
            shapes.extend(non_intermediate_shapes)
    if intermediates:
        shapes.extend(list_intermediates(node_name))

    return shapes


def get_shape_node_type(node_name):
    """
    Returns the node type of the given node
    :param shape_node: str, name of a maya node
    :return: str
    """

    shapes = get_shapes(node)
    if shapes:
        return maya.cmds.nodeType(shapes[0])


def get_shapes_of_type(node_name, shape_type=None, no_intermediate=False):
    """
    Returns a list of shapes under a transform parent
    :param node_name: str, transform to list parent for
    :param shape_type: str, shape type to get
    :param no_intermediate: bool, list non intermediate shapes
    :return: list
    """

    if node.is_a_shape(node_name):
        parent = maya.cmds.listRelatives(node_name, p=True, f=True)
        return maya.cmds.listRelatives(parent, s=True, f=True, ni=no_intermediate)

    if shape_type:
        maya.cmds.listRelatives(node_name, s=True, f=True, type=shape_type, ni=no_intermediate)
    else:
        return maya.cmds.listRelatives(node_name, s=True, f=True, ni=no_intermediate)


def get_shapes_generator(mobj):
    """
    Returns a generator of all shape nodes for the provided transform node
    :param mobj: MObject, MObject to get teh shape nodes of
    :return: generator
    """

    # TODO: Make this function to work in both OpenMayaV1 and V2

    import maya.OpenMaya as OpenMaya

    if not mobj.apiType() == OpenMaya.MFn.kTransform:
        return

    path = OpenMaya.MDagPath.getAPathTo(mobj)
    num_shapes = OpenMaya.MScriptUtil()
    num_shapes.createFromInt(0)
    num_shapes_ptr = num_shapes.asUintPtr()
    path.numberOfShapesDirectlyBelow(num_shapes_ptr)
    for index in range(OpenMaya.MScriptUtil(num_shapes_ptr).asUint()):
        p = OpenMaya.MDagPath.getAPathTo(mobj)
        p.extendToShapeDirectlyBelow(index)
        yield p.node()


def get_transform(mobj):
    """
    Returns the first transform node of the provided shape node
    If the mobj is already a transform node, its returned
    :param mobj: OpenMaya.MObject, MObject to get transform node of
    :return: OpenMaya.MObject
    """

    # TODO: Make this function to work in both OpenMayaV1 and V2

    import maya.OpenMaya as OpenMaya

    if not node.is_dag_node(mobj):
        return mobj

    path = OpenMaya.MDagPath.getAPathTo(mobj)
    new_ptr = path.transform()
    if new_ptr != mobj:
        return new_ptr

    return mobj


def rename(geo):
    """
    Rename shape nodes based on the parent transform node
    :param geo: str, transform to rename shapes for
    :return: list, renamed shapes
    """

    shapes = get_shapes(geo)
    if not shapes:
        return []

    # Rename shapes
    for i in range(len(shapes)):
        shape_type = maya.cmds.objectType(shapes[i])

        # Rename temporary shapes so hash index (#) is accurate
        shapes[i] = maya.cmds.rename(shapes[i], geo+'ShapeTMP')

        if shape_type == 'nurbsCurve':
            shapes[i] = maya.cmds.rename(shapes[i], geo+'CrvShape#')
        elif shape_type == 'nurbsSurface':
            shapes[i] = maya.cmds.rename(shapes[i], geo+'SrfShape#')
        elif shape_type == 'mesh':
            shapes[i] = maya.cmds.rename(shapes[i], geo+'MeshShape#')
        else:
            shapes[i] = maya.cmds.rename(shapes[i], geo+'Shape#')

    return shapes


def shape_input_attr(shape):
    """
    Returns the shape input attribute
    :param shape:  str, shape node to find the shape input attribute for
    :return: str, attr
    """

    check_shape(shape)

    # Determine shape input plug
    shp_input_attr = ''
    shp_input_type = maya.cmds.objectType(shape)
    shp_input_dict = {
        'mesh': 'inMesh',
        'nurbsCurve': 'create',
        'nurbsSurface': 'create',
        'lattice': 'latticeInput',
        'subdiv': 'create'
    }
    if shp_input_type in shp_input_dict:
        shp_input_attr = shp_input_dict[shp_input_type]
    else:
        raise exceptions.ShapeUnsupportedType(shp_input_attr)

    return shp_input_attr


def shape_output_attr(shape, world_space=True):
    """
    Returns the shape output attribute
    :param shape: str, shape node to find the shape output attribute for
    :param world_space: bool, return world space output attribute if exists
    :return: attr, str
    """

    check_shape(shape)

    # Determine shae output plug
    shp_output_attr = ''
    shp_output_type = maya.cmds.objectType(shape)
    shp_output_dict = {
        'mesh': ['outMesh', 'worldMesh'],
        'nurbsCurve': ['local', 'worldSpace'],
        'nurbsSurface': ['local', 'worldSpace'],
        'lattice': ['latticeOutput', 'worldLattice'],
        'subdiv': ['outSubdiv', 'worldSubdiv']
    }
    if shp_output_type in shp_output_dict:
        shp_output_attr = shp_output_dict[shp_output_type][int(world_space)]
    else:
        raise exceptions.ShapeUnsupportedType(shp_output_attr)

    return shp_output_attr


def shape_input_source(shape):
    """
    Returns the shape input source plug. If not input exists, returns an empty string
    :param shape: str, shape node to find shape input source for
    :return: str
    """

    check_shape(shape)

    # Determine shape input plug and shape input source plug
    shape_in_attr = shape_input_attr(shape)
    shape_in_plug = ''
    shape_in_source = maya.cmds.listConnections(shape+'.'+shape_in_attr, source=True, destination=False, plugs=True)
    if shape_in_source:
        shape_in_plug = shape_in_source[0]

    return shape_in_plug


def find_input_shape(obj, recursive=False, print_exceptions=False):
    """
    Returns the input shape for the specified shape node or transform
    :param obj: str, shape/transform node to find the corresponding input shape for
    :param recursive: bool, True if you want to change shape in a recursive way
    :param print_exceptions: bool, True if you want print exceptions while recursive searchhing
    :return: str
    """

    input_shape = None

    if not input_shape:
        try:
            input_shape = find_input_shape_1(obj)
        except Exception as e:
            if print_exceptions:
                maya.logger.debug('Caught exception: {}'.format(str(e)))
    if not input_shape:
        try:
            input_shape = find_input_shape_2(obj)
        except Exception as e:
            if print_exceptions:
                maya.logger.debug('Caught exception: {}'.format(str(e)))

    # Check if input shape is valid
    if not input_shape:
        raise exceptions.ShapeException(obj)

    # Do recursion if necessary
    # TODO: Limit the recursion to a maximum number of times to avoid infinit loops
    if recursive:
        while input_shape != find_input_shape(input_shape):
            input_shape = find_input_shape(input_shape)

    return input_shape


def find_input_shape_1(shape):
    """
    Returns the orig input shape (...ShapeOrig') for the specified shape node based on deformer data
    This function assumes that the specified shape is affected by at least one valid deformer
    :param shape: str, shape node to find the corresponding input shape for
    :return:  str
    """

    # TODO: Make this function to work in both OpenMayaV1 and V2

    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaAnim as OpenMayaAnim

    # Get MObject for shape
    shape_obj = node.get_mobject(shape)

    # Get inMesh connection attribute
    in_conn = maya.cmds.listConnections(shape, source=True, destination=False)
    if not in_conn:
        return shape

    # Find connected deformer
    deformer_history = maya.cmds.ls(maya.cmds.listHistory(shape), type='geometryFilter')
    if not deformer_history:
        raise exceptions.ShapeValidDeformerAffectedException(shape)
    deformer_obj = node.get_mobject(deformer_history[0])

    # Get deformer function set
    deformer_fn = OpenMayaAnim.MFnGeometryFilter(deformer_obj)

    # Get input shape deformer
    geom_index = deformer_fn.indexForOutputShape(shape_obj)
    input_shape_obj = deformer_fn.inputShapeAtIndex(geom_index)

    return OpenMaya.MFnDagNode(input_shape_obj).partialPathName()


def find_input_shape_2(shape):
    """
    Determine the input shape for the specified geometry based on construction history
    :param shape: str, shape node to find the corresponding input shape for
    :return: str
    """

    transform = maya.cmds.listRelatives(shape, parent=True, path=True) or []

    if node.is_type(shape, 'transform'):
        transform = [shape]
        shapes = maya.cmds.listRelatives(shape, shapes=True, noIntermediate=True, path=True)
        if not shapes:
            raise exceptions.ShapeFromTransformException(shape)
        shape = shapes[0]

    # Get all shapes and type
    all_shapes = maya.cmds.listRelatives(transform[0], shapes=True, path=True)
    shape_type = maya.cmds.objectType(shape)

    # Get shape history and check it
    shape_history = maya.cmds.listRelatives(maya.cmds.listHistory(shape), type=shape_type)
    if shape_history.count(shape):
        shape_history.remove(shape)
    if not shape_history:
        raise exceptions.ShapeHistoryException(shape)
    if len(shape_history) == 1:
        input_shape = shape_history[0]
    else:
        shape_input = list(set(shape_history).intersection(set(all_shapes)))
        if shape_input:
            input_shape = shape_input[0]
        else:
            input_shape = shape_history[0]

    return input_shape


def find_orig_shape(shape):
    """
    Returns the orig input shape (...ShapeOrig') for the specified shape node based on deformer data
    This function assumes that the specified shape is affected by at least one valid deformer
    :param shape: str, shape node to find the corresponding input shape for
    :return:  str
    """

    return find_input_shape_1(shape)


def get_components_from_shapes(shapes=None):
    """
    Get the components from a list of shapes
    NOTE: Only supports CV and Vertex Components
    :param shapes: list<str>, list of shapes to retrieve components from
    :return: list<str>, components of the given shapes
    """

    comps = list()
    if shapes:
        for shape in shapes:
            found_comps = None
            if maya.cmds.nodeType(shape) == 'nurbsSurface':
                found_comps = '%s.cv[*]' % shape

            if maya.cmds.nodeType(shape) == 'nurbsCurve':
                found_comps = '%s.cv[*]' % shape

            if maya.cmds.nodeType(shape) == 'mesh':
                found_comps = '%s.vtx[*]' % shape

            if found_comps:
                comps.append(found_comps)

    return comps


def rename_shapes(transform_node):
    """
    Rename all shapes under the given transform to match the name of the transform
    :param transform_node: str, name of a transform
    """

    shapes = get_shapes(transform_node)
    if shapes:
        maya.cmds.rename(shapes[0], '{}Shape'.format(transform_node))

    if not shapes or len(shapes) == 1:
        return

    i = 1
    for s in shapes[1:]:
        maya.cmds.rename(s, '{}Shape{}'.format(transform_node, i))
        i += 1


def get_shapes_in_hierarchy(transform_node, shape_type='', return_parent=False, skip_first_relative=False):
    """
    Get all the shapes in the child hierarchy excluding intermediates shapes
    :param transform_node: str, name of a transform
    :param shape_type: str, shape types we want to retrieve
    :param return_parent: bool, Whether to return parent node also or not
    :param skip_first_relative: bool
    :return: list<str, list of shape nodes
    """

    hierarchy = [transform_node]
    relatives = maya.cmds.listRelatives(transform_node, ad=True, type='transform', f=True)
    if relatives:
        hierarchy.extend(relatives)
    if skip_first_relative:
        hierarchy = hierarchy[1:]

    shapes = list()

    for child in hierarchy:
        found_shapes = get_shapes(node=child, shape_type=shape_type)
        sifted_shapes = list()
        if not found_shapes:
            continue
        for found_shape in found_shapes:
            if maya.cmds.getAttr('{}.intermediateObject'.format(found_shape)):
                continue
            if return_parent:
                found_shape = child
            sifted_shapes.append(found_shape)

        if sifted_shapes:
            shapes.extend(sifted_shapes)

    return shapes


def has_shape_of_type(node, shape_type):
    """
    Checks whether the given node has a shape of the given type
    :param node: str, name of a node
    :param shape_type: str, shape type (mesh, nurbsCurve or any Maya shape type)
    :return: bool
    """

    has_shape = None

    if maya.cmds.objExists(node):
        has_shape = node

    if not maya.cmds.objectType(node, isAType='shape'):
        shapes = get_shapes(node)
        if shapes:
            has_shape = shapes[0]

    if has_shape:
        if shape_type == maya.cmds.nodeType(has_shape):
            return True

    return False


def scale_shapes(node, scale, use_pivot=True, relative=True):
    """
    Scales shapes of given transform node
    :param node:
    :param scale: variant, float || list<float, float, float>
    :param use_pivot:
    :param relative:
    :return:
    """

    shapes = get_shapes(node, intermediates=False, full_path=True)
    comps = get_components_from_shapes(shapes)
    if use_pivot:
        pivot = maya.cmds.xform(node, query=True, rp=True, ws=True)
    else:
        from tpMayaLib.core import transform
        bounding_box = transform.BoundingBox(comps)
        pivot = bounding_box.get_center()

    if comps:
        if type(scale) in [list, tuple]:
            if relative:
                maya.cmds.scale(scale[0], scale[1], scale[2], comps, pivot=pivot, r=True)
            else:
                maya.cmds.scale(scale[0], scale[1], scale[2], comps, pivot=pivot, a=True)
        else:
            if relative:
                maya.cmds.scale(scale, scale, scale, comps, pivot=pivot, r=True)
            else:
                maya.cmds.scale(scale, scale, scale, comps, pivot=pivot, a=True)
