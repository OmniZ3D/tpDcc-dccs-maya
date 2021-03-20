#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to nodes
"""

from __future__ import print_function, division, absolute_import

import re
import uuid
import logging

import maya.cmds
import maya.api.OpenMaya

from tpDcc.libs.python import python, name, color
from tpDcc.dccs.maya.api import node as api_node
from tpDcc.dccs.maya.core import exceptions, helpers, color as maya_color

LOGGER = logging.getLogger('tpDcc-dccs-maya')


def is_a_shape(node_name):
    """
    Returns whether a given node name is a shape node
    :param node_name: str, name of a Maya node
    :return: bool
    """

    if maya.cmds.objectType(node_name, isAType='shape'):
        return True

    return False


def is_a_transform(node_name):
    """
    Check if the specified object is a valid transform node
    :param node_name: str, object to check as a transform node
    :return: bool
    """

    if not maya.cmds.objExists(node_name):
        return False

    if not maya.cmds.objectType(node_name, isAType='transform'):
        return False

    return True


def is_referenced(node_name):
    """
    Returns whether a given node name is referenced or not
    :param node_name: str, name of a Maya node
    :return: bool
    """

    if not node_name:
        return False
    if not maya.cmds.objExists(node_name):
        return False
    is_node_referenced = maya.cmds.referenceQuery(node_name, isNodeReferenced=True)

    return is_node_referenced


def is_empty(node_name, no_user_attributes=True, no_connections=True):
    """
    Returns whether a given node is an empty one (is not referenced, has no child transforms,
    has no custom attributes and has no connections)
    :param node_name: str, name of a Maya node
    :param no_user_attributes: bool
    :param no_connections: bool
    :return: bool
    """

    if is_referenced(node_name=node_name):
        return False

    if is_a_transform(node_name=node_name):
        relatives = maya.cmds.listRelatives(node_name)
        if relatives:
            return False

    if no_user_attributes:
        attrs = maya.cmds.listAttr(node_name, userDefined=True, keyable=True)
        if attrs:
            return False

    default_nodes = ['defaultLightSet', 'defaultObjectSet', 'initialShadingGroup', 'uiConfigurationScriptNode',
                     'sceneConfigurationScriptNode']
    if node_name in default_nodes:
        return False

    if no_connections:
        connections = maya.cmds.listConnections(node_name)
        if connections != ['defaultRenderGlobals']:
            if connections:
                return False

    return True


def is_undeletable(node_name):
    """
    Returns whether a given node is deletable or not
    :param node_name: str, name of a Maya node
    :return: bool
    """

    try:
        nodes = maya.cmds.ls(undeletable=True)
        if node_name in nodes:
            return True
    except Exception:
        return False

    return False


def is_unique(node_name):
    """
    Returns whether a given node is unique or not
    :param node_name: str, name of Maya node
    :return: bool
    """

    scope = maya.cmds.ls(node_name)
    count = len(scope)
    if count > 1:
        return False
    elif count == 1:
        return True

    return True


def get_node_types(nodes, return_shape_type=True):
    """
    Returns the Maya node type for the given nodes
    :param nodes: list<str>, list of nodes we want to check types of
    :param return_shape_type: bool, Whether to check shape type or not
    :return: dict<str>, [node_type_name], node dictionary of matching nodes
    """

    from tpDcc.dccs.maya.core import shape

    nodes = python.force_list(nodes)

    found_type = dict()

    for n in nodes:
        node_type = maya.cmds.nodeType(n)
        if node_type == 'transform':
            if return_shape_type:
                shapes = shape.get_shapes(n)
                if shapes:
                    node_type = maya.cmds.nodeType(shapes[0])
        if node_type not in found_type:
            found_type[node_type] = list()

        found_type[node_type].append(n)

    return found_type


def update_uuid(node_name):
    """
    Updates the unique identifier of the given Maya node
    :param node_name: str
    :return:
    """

    ids = list()
    for attr in maya.cmds.ls('*.uuid'):
        node_id = maya.cmds.getAttr(attr)
        ids.append(node_id)

    uuid_attr = node_name + '.uuid'
    if not maya.cmds.objExists(uuid_attr):
        maya.cmds.addAttr(node_name, longName='uuid', dataType='string')
        new_id = str(uuid.uuid4())
        ids.append(new_id)
    else:
        existing_id = maya.cmds.getAttr(uuid_attr)
        if existing_id not in ids:
            ids.append(existing_id)
            return
        new_id = str(uuid.uuid4())
    maya.cmds.setAttr(uuid_attr, new_id, type='string')


def check_node(node):
    """
    Checks if a node is a valid node and raise and exception if the node is not valid
    :param node: str | MObject, name of the node to be checked or MObject to be checked
     :return: bool, True if the given node is valid
    """

    if python.is_string(node):
        if not maya.cmds.objExists(node):
            return False
    elif isinstance(node, maya.api.OpenMaya.MObject):
        return not node.isNull()

    return True


def is_type(node_name, node_type):
    """
    Checks if the input object has the specified node type
    :param node_name: str, Name of the node
    :param node_type: str, Node type
    :return: bool, True if the node is the same type of the passed type or False otherwise
    """

    if not maya.cmds.objExists(node_name):
        return False
    if maya.cmds.objectType(node_name) != node_type:
        return False
    return True


def verify_node(node, node_type):
    """
    Run standard checks on the specified node. Raise an exception if any checks fail
    :param node: str, Node name of the node to verify
    :param node_type: Node type
    :return: bool, True if the ndoe is valid or False otherwise
    """

    check_node(node)

    # Check node type
    obj_type = maya.cmds.objectType(node)
    if obj_type != node_type:
        raise exceptions.NodeException(node, node_type)


def is_dag_node(mobj):
    """
    Checks if an MObject is a DAG node
    :param mobj: MObject
    :return: True if the MObject is a DAG node or False otherwise
    """

    return mobj.hasFn(maya.api.OpenMaya.MFn.kDagNode)


def is_visible(node, check_lod_vis=True, check_draw_override=True):
    """
    Checks if a specified DAG node is visibility by checking visibility of all ancestor nodes
    :param node: str, Node name of the node to verify
    :param check_lod_vis: bool, Check LOD visibility
    :param check_draw_override: bool, Check drawing override visibility
    :return: bool, True if the node is visible or False otherwise
    """

    check_node(node)

    if not maya.cmds.ls(node, dag=True):
        raise exceptions.DagNodeException(node)

    full_path = maya.cmds.ls(node, long=True)[0]
    path_part = full_path.split('|')
    path_part.reverse()

    # Check visibility
    is_visible_ = True
    for part in path_part:

        # Skip unknown nodes
        if not part:
            continue
        if not maya.cmds.objExists(part):
            LOGGER.debug('Unable to find ancestor node {}!'.format(part))
            continue

        if not maya.cmds.getAttr(part + '.visibility'):
            is_visible_ = False
        if check_lod_vis:
            if not maya.cmds.getAttr(part + '.lodVisibility'):
                is_visible_ = False
        if check_draw_override:
            if maya.cmds.getAttr(part + '.overrideEnabled'):
                if not maya.cmds.getAttr(part + '.overrideVisibility'):
                    return False

        return is_visible_


def get_mobject(node_name):
    """
    Returns an MObject for the input scene object
    :param node_name: str, Name of the Maya node to get MObject for
    :return:
    """

    check_node(node_name)

    if isinstance(node_name, str) or isinstance(node_name, unicode):
        selection_list = maya.api.OpenMaya.MSelectionList()
        selection_list.add(node_name)
        try:
            mobj = selection_list.getDependNode(0)
        except Exception as exc:
            maya.cmds.warning('Impossible to get MObject from name {} : {}'.format(node_name, exc))
            return

        return mobj

    elif node_name.__module__.startswith('pymel'):
        return node_name.__apimfn__().object()

    return node_name


def get_name(mobj, fullname=True):
    """
    Returns the name of an object
    :param mobj: OpenMaya.MObject, MObject to get name of
    :param fullname: bool, If True return the full path of the node, else return the displayName
    :return: str, object name
    """

    try:
        if not mobj or mobj.isNull():
            return None
        if is_dag_node(mobj):
            dag_path = maya.api.OpenMaya.MDagPath.getAPathTo(mobj)
            if fullname:
                return dag_path.fullPathName()
            return dag_path.partialPathName().split('|')[-1]
        return maya.api.OpenMaya.MFnDependencyNode(mobj).name()
    except Exception as e:
        maya.cmds.warning('Impossible to get name from MObject: {} - {}'.format(mobj, str(e)))
        return None


def set_names(nodes, names):
    """
    Renames given list of nodes with the given list of names
    :param nodes: list(MObject)
    :param names: list(str)
    """

    nodes = python.force_list(nodes)
    names = python.force_list(names)

    # TODO: Check why after calling this function, the undo does not allow to undo the renaming operation
    for node, node_name in zip(nodes, names):
        maya.api.OpenMaya.MFnDagNode(node).setName(node_name)


def get_mdag_path(obj):
    """
    Takes an object name as a string and returns its MDAGPath
    :param obj: str, Name of the object
    :return: str, DAG Path
    """

    # sel = OpenMaya.MSelectionList()
    # sel.add(objName)
    # return sel.getDagPath(0)

    check_node(obj)

    selection_list = maya.api.OpenMaya.MGlobal.getSelectionListByName(obj)
    dag_path = selection_list.getDagPath(0)

    return dag_path


def get_depend_node(node):
    """
    :param node: str | MObject, Name of the object or MObject
    :return: MObject
    """

    check_node(node)

    if type(node) in [str, unicode]:
        selection_list = maya.api.OpenMaya.MSelectionList()
        selection_list.add(node)
        dep_node = selection_list.getDependNode(0)
    else:
        dep_node = maya.api.OpenMaya.MFnDependencyNode(node)

    return dep_node


def get_plug(node, plug_name):
    """
    Get the plug of a Maya node
    :param node: str | MObject, Name of the object or MObject
    :param plug_name: str, Name of the plug
    """

    check_node(node)

    if type(node) in [str, unicode]:
        mobj = get_depend_node(node)
        dep_fn = maya.api.OpenMaya.MFnDependencyNode()
        dep_fn.setObject(mobj)
        plug = dep_fn.findPlug(plug_name, False)
    else:
        dep_node = get_depend_node(node)
        attr = dep_node.attribute(plug_name)
        plug = maya.api.OpenMaya.MPlug(node, attr)

    return plug


def get_shape(node, intermediate=False):
    """
     Get the shape node of a transform
     This is useful if you don't want to have to check if a node is a shape node or transform.
     You can pass in a shape node or transform and the function will return the shape node
     If no shape exists, the original name or MObject is returned
     @param node: str | MObject, Name of the node or MObject
     @param intermediate: bool, True to get the intermediate shape
     @return: The name of the shape node
    """

    if type(node) in [list, tuple]:
        node = node[0]

    check_node(node)

    if isinstance(node, str) or isinstance(node, unicode):
        if maya.cmds.nodeType(node) == 'transform':
            shapes = maya.cmds.listRelatives(node, shapes=True, path=True)
            if not shapes:
                shapes = []
            for shape in shapes:
                is_intermediate = maya.cmds.getAttr('%s.intermediateObject' % shape)
                if intermediate and is_intermediate and maya.cmds.listConnections(shape, source=False):
                    return shape
                elif not intermediate and not is_intermediate:
                    return shape
            if shapes:
                return shapes[0]
        elif maya.cmds.nodeType(node) in ['mesh', 'nurbsCurve', 'nurbsSurface']:
            is_intermediate = maya.cmds.getAttr('%s.intermediateObject' % node)
            if is_intermediate and not intermediate:
                node = maya.cmds.listRelatives(node, parent=True, path=True)[0]
                return get_shape(node)
            else:
                return node
    elif isinstance(node, maya.api.OpenMaya.MObject):
        if not node.apiType() == maya.api.OpenMaya.MFn.kTransform:
            return node

        path = maya.api.OpenMaya.MDagPath.getAPathTo(node)
        num_shapes = path.numberOfShapesDirectlyBelow()
        if num_shapes:
            # TODO: Should this return the last shape, instead of the first?
            path.extendToShapeDirectlyBelow(0)
            return path.node()

    return node


def attribute_check(obj, attribute):
    """
    Check an object for a given attribute
    :param obj: str, Name of an object
    :param attribute: str, Name of an attribute
    :return: bool, True if the attribute exists. Otherwise False.
    """

    check_node(obj)

    dep_node = get_depend_node(obj)
    dep_fn = maya.api.OpenMaya.MFnDependencyNode()
    dep_fn.setObject(dep_node)
    return dep_fn.hasAttribute(attribute)


def connect_nodes(parent_obj, parent_plug, child_obj, child_plug):
    """
    Connects two nodes using Maya API
    @param parent_obj: str, Name of the parent node
    @param parent_plug: str, Name of plug on parent node
    @param child_obj: str, Name of the child node
    @param child_plug: str, Name of plug on child node
    """

    parent_plug = get_plug(parent_obj, parent_plug)
    child_plug = get_plug(child_obj, child_plug)
    mdg_mod = maya.api.OpenMaya.MDGModifier()
    mdg_mod.connect(parent_plug, child_plug)
    mdg_mod.doIt()


def disconnect_nodes(parent_obj, parent_plug, child_obj, child_plug):
    """
    Disconnects two nodes using Maya API
    @param parent_obj: str, Name of the parent node
    @param parent_plug: str, Name of plug on the parent node
    @param child_obj: str, Name of child node
    @param child_plug: str, Name of plug on the child node
    """

    parent_plug = get_plug(parent_obj, parent_plug)
    child_plug = get_plug(child_obj, child_plug)
    mdg_mod = maya.api.OpenMaya.MDGModifier()
    mdg_mod.disconnect(parent_plug, child_plug)
    mdg_mod.doIt()


def get_attr_message_value(node, attr):
    """
    Retrieves the connections to/from a message attribute
    @param node: str, Node with the desired attribute
    @param attr: str, Name of source attribute
    @return String for unicode or String[] for list
    """

    check_node(node)

    dst_check = maya.cmds.connectionInfo('{0}.{1}'.format(node, attr), isDestination=True)
    source_check = maya.cmds.connectionInfo('{0}.{1}'.format(node, attr), isSource=True)
    if dst_check:
        attr_connection = maya.cmds.connectionInfo('{0}.{1}'.format(node, attr), sourceFromDestination=True)
    elif source_check:
        attr_connection = maya.cmds.connectionInfo('{0}.{1}'.format(node, attr), destinationFromSource=True)
    else:
        return None
    return attr_connection


def get_node_attr_destination(node, attr):
    """
    Gets the destination of an attribute on the given node.
    @param node: str, Node with the desired attribute
    @param attr: str, Name of the source attribute
    @return List containing the destination attribute and it's node
    """

    check_node(node)

    attr_connection = maya.cmds.connectionInfo('{0}.{1}'.format(node, attr), destinationFromSource=True)
    if len(attr_connection) == 1:
        return attr_connection[0].split('.')
    elif len(attr_connection) > 1:
        return attr_connection
    else:
        return None


def get_node_attr_source(node, attr):
    """
    Gets the source of an attribute on the given node
    @param node: str, Node with the desired attribute
    @param attr: str, Name of source attribute
    @return List containing the source attribute and it's node
    """

    check_node(node)

    attr_connection = maya.cmds.connectionInfo('{0}.{1}'.format(node, attr), sourceFromDestination=True)
    if not attr_connection:
        return None
    elif isinstance(attr_connection, list):
        return attr_connection
    elif isinstance(attr_connection, unicode):
        dest_info = attr_connection.split('.')
        return dest_info


def get_plug_value(plug):
    """
    @param plug: MPlug, The node plug
    @return The value of the passed in node plug
    """

    plug_attr = plug.attribute()
    api_type = plug_attr.apiType()

    # Float Groups - rotate, translate, scale; Compounds
    if api_type in [maya.api.OpenMaya.MFn.kAttribute3Double, maya.api.OpenMaya.MFn.kAttribute3Float,
                    maya.api.OpenMaya.MFn.kCompoundAttribute]:
        result = []
        if plug.isCompound:
            for c in range(plug.numChildren()):
                result.append(get_plug_value(plug.child(c)))
            return result

    # Distance
    elif api_type in [maya.api.OpenMaya.MFn.kDoubleLinearAttribute, maya.api.OpenMaya.MFn.kFloatLinearAttribute]:
        return plug.asMDistance().asCentimeters()

    # Angle
    elif api_type in [maya.api.OpenMaya.MFn.kDoubleAngleAttribute, maya.api.OpenMaya.MFn.kFloatAngleAttribute]:
        return plug.asMAngle().asDegrees()

    # TYPED
    elif api_type == maya.api.OpenMaya.MFn.kTypedAttribute:
        plug_type = maya.api.OpenMaya.MFnTypedAttribute(plug_attr).attrType()

        # Matrix
        if plug_type == maya.api.OpenMaya.MFnData.kMatrix:
            return maya.api.OpenMaya.MFnMatrixData(plug.asMObject()).matrix()

        # String
        elif plug_type == maya.api.OpenMaya.MFnData.kString:
            return plug.asString()

    # Matrix
    elif api_type == maya.api.OpenMaya.MFn.kMatrixAttribute:
        return maya.api.OpenMaya.MFnMatrixData(plug.asMObject()).matrix()

    # NUMBERS
    elif api_type == maya.api.OpenMaya.MFn.kNumericAttribute:

        plug_type = maya.api.OpenMaya.MFnNumericAttribute(plug_attr).numericType()

        # Boolean
        if plug_type == maya.api.OpenMaya.MFnNumericData.kBoolean:
            return plug.asBool()

        # Integer - Short, Int, Long, Byte
        elif plug_type in [maya.api.OpenMaya.MFnNumericData.kShort, maya.api.OpenMaya.MFnNumericData.kInt,
                           maya.api.OpenMaya.MFnNumericData.kLong, maya.api.OpenMaya.MFnNumericData.kByte]:
            return plug.asInt()

        # Float - Float, Double, Address
        elif plug_type in [maya.api.OpenMaya.MFnNumericData.kFloat, maya.api.OpenMaya.MFnNumericData.kDouble,
                           maya.api.OpenMaya.MFnNumericData.kAddr]:
            return plug.asDouble()

    # Enum
    elif api_type == maya.api.OpenMaya.MFn.kEnumAttribute:
        return plug.asInt()


def normalize_attribute_name(attr):
    """
    Removes invalid characters for attribute names from the provided string
    :param attr: str, string used as the name of an attribute
    :return: str
    """

    return re.sub(r'\W', '', attr)


def normalize_attribute_short_name(short_name, unique_on_obj=None):
    """
    Creates a shortName for the provided attribute name following:
    1.- Normalize attribute
    2.- Adds the first character to any capital letters in the rest of the name
    3.- Name is lowercase
    If unique_on_obj is provided with an object, it will ensure the returned attribute name is
    unique by attaching a 3 digit padded number to it. It will be the lowest available number.
    :param short_name: str, string used to generate the short name
    :param unique_on_obj: bool, True to ensure that the name is unique
    :return: str
    """

    short_name = normalize_attribute_name(short_name)
    if len(short_name):
        short_name = short_name[0] + re.sub(r'[a-z]', '', short_name[1:])
    short_name = short_name.lower()
    if unique_on_obj:
        names = set(maya.cmds.listAttr(get_name(unique_on_obj), shortNames=True))
        short_name = name.find_unique_name(short_name, names, inc_format='{name}{count}')

    return short_name


def get_attribute_data_type(data):
    """
    Returns the OpenMaya.MFnData id for the given object.
    If the object type could not identified the function returns OpenMaya.MFnData.kInvalid
    :param data: object to get the data type of
    :return: int, value for the data type
    """

    data_type = maya.api.OpenMaya.MFnData.kInvalid
    if isinstance(data, str):
        data_type = maya.api.OpenMaya.MFnData.kString
    if isinstance(data, float):
        data_type = maya.api.OpenMaya.MFnData.kFloatArray
    if isinstance(data, int):
        data_type = maya.api.OpenMaya.MFnData.kIntArray

    # TODO: Add support for other types

    return data_type


def has_attribute(node, attr_name):
    """
    Returns True if the OpenMaya.MObject has a specific attribute or False otherwise
    :param node: OpenMaya.MObject
    :param attr_name: str, attribute name to search for
    :return: bool
    """

    check_node(node)

    dep_node = get_depend_node(node)

    # TODO: hasAttribute fails when trying to check user defined non existent attributes
    # TODO: More info --> http://discourse.techart.online/t/getting-attribute-using-maya-api-in-python/1224/7
    try:
        return dep_node.hasAttribute(attr_name)
    except Exception:
        return False


def create_attribute(mobj, attribute_name, data_type=None, short_name=None, default=None):
    """
    Creates an attribute on the provided object.
    Returns the attribute name and shortName
    :param mobj: OpenMaya.MObject, MObject to create the attribute for
    :param attribute_name: str, name of the attribute
    :param data_type: Type of data to store in the attribute
    :param short_name: str, short name for the attribute
    :param default: default value assigned to teh attribute
    :return: (name, short name) As name and short name are normalized, this returns the actual names used for attribute
        names
    """

    # TODO: Reimplement this function so it can work on all cases (take the one that appears on the MetaData class)

    attribute_name = normalize_attribute_name(attribute_name)
    if data_type is None and default is not None:
        data_type = get_attribute_data_type(default)
        if data_type == maya.api.OpenMaya.MFnData.kInvalid:
            data_type = None
            LOGGER.debug('Unable to determine the attribute type => {}'.format(str(default)))
        if data_type is None:
            data_type = maya.api.OpenMaya.MFnData.kAny

        try:
            if short_name is None:
                short_name = normalize_attribute_short_name(attribute_name, unique_on_obj=mobj)
            dep_node = maya.api.OpenMaya.MFnDependencyNode(mobj)
        except Exception as e:
            raise Exception('Error while getting dependency node from MObject "{}" - {}'.format(mobj, str(e)))

        s_attr = maya.api.OpenMaya.MFnTypedAttribute()
        if default:
            attr = s_attr.create(attribute_name, short_name, data_type, default)
        else:
            attr = s_attr.create(attribute_name, short_name, data_type)
        dep_node.addAttribute(attr)

        return attribute_name, short_name


def set_attribute(mobj, attr_name, value):
    """
    Sets the value of a current existing attribute of the passed node
    :param mobj: OpenMaya.MObject, MObject to set the attribute value to
    :param attr_name: str, name of the attribute to store the value in
    :param value: value to store in the attribute
    """

    plug = get_plug(mobj, attr_name)
    if isinstance(value, str):
        plug.setString(value)
    elif isinstance(value, bool):
        plug.setBool(value)
    elif isinstance(value, float):
        plug.setFloat(value)
    elif isinstance(value, int):
        plug.setInt(value)
    # elif isinstance(value, double):
    #     plug.setDouble(value)
    # elif isinstance(value, MAngle):
    #     plug.setMAngle(value)
    # elif isinstance(value, MDataHandle):
    #     plug.setMDataHandle(value)
    # elif isinstance(value, MDistance):
    #     plug.setMDistance(value)
    # elif isinstance(value, MObject):
    #     plug.setMObject(value)
    # elif isinstance(value, MPxData):
    #     plug.setMPxData(value)
    # elif isinstance(value, MTime):
    #     plug.setMTime(value)
    # elif isinstance(value, int):
    #     plug.setNumElements(value)
    # elif isinstance(value, ShortInt):
    #     plug.setShort(value)


def display_override(obj, override_enabled=False, override_display=0, override_lod=0, override_visibility=True,
                     override_shading=True):
    """
    Set display override attributes for the given object
    :param obj: str, object to set display overrides for
    :param override_enabled: bool, set the display override enable state for the given DAG object
    :param override_display: int, set the display override type for the given DAG object
        (0=normal, 1=template, 2=reference)
    :param override_lod: int, set the display override level of detail value for the given DAG object
        (0=full, 1=boundingBox)
    :param override_visibility: bool, set the display override visibility value for the given DAG object
    :param override_shading: bool, set the display override shading value for the given DAG object
    """

    if not maya.cmds.objExists(obj):
        raise Exception('Object "{}" does not exists!'.format(obj))
    if not maya.cmds.ls(obj, dag=True):
        raise Exception('Object "{}" is not a valid DAG node!'.format(obj))

    # Set the display override values
    maya.cmds.setAttr('{}.overrideEnabled'.format(override_enabled))
    maya.cmds.setAttr('{}.overrideDisplayType'.format(override_display))
    maya.cmds.setAttr('{}.overrideLevelOfDetail'.format(override_lod))
    maya.cmds.setAttr('{}.overrideVisibility'.format(override_visibility))
    maya.cmds.setAttr('{}.overrideShading'.format(override_shading))


def get_input_attributes(node):
    """
    Returns a list with all input attributes of the given node
    :param node: str, node name we want to retrieve input attributes of
    :return: list<str>
    """

    if not maya.cmds.objExists(node):
        raise Exception('Object "{}" does not exists!'.format(node))

    inputs = maya.cmds.listConnections(
        node, connections=True, destination=False, source=True, plugs=True, skipConversionNodes=True)
    if inputs:
        inputs.reverse()
    else:
        inputs = list()

    return inputs


def get_output_attributes(node):
    """
    Returns a list with all outputs attributes of the given node
    :param node: str, node name we want to retrieve output attributes of
    :return: list<str>
    """

    if not maya.cmds.objExists(node):
        raise Exception('Object "{}" does not exists!'.format(node))

    outputs = maya.cmds.listConnections(
        node, connections=True, destination=True, source=False, plugs=True, skipConversionNodes=True)
    if not outputs:
        outputs = list()

    return outputs


def get_all_hierarchy_nodes(node, direction=None, object_type=None):
    """
    Returns a list with all nodes in the given node hierarchy
    :param node: str, node to retrieve hierarchy from
    :param direction: str
    :param object_type: str
    :return:
    """

    if direction is None:
        # if helpers.get_maya_version() > 2016:
        #     direction = maya.api.OpenMaya.MItDependencyGraph.kDownstream
        # else:
        #     direction = OpenMaya.MItDependencyGraph.kDownstream
        direction = maya.api.OpenMaya.MItDependencyGraph.kDownstream

    check_node(node)

    object_type = python.force_list(object_type)
    nodes = list()

    if type(node) == maya.api.OpenMaya.MObject:
        mobj = node
    else:
        sel_list = maya.api.OpenMaya.MSelectionList()
        sel_list.add(node)
        mobj = sel_list.getDependNode(0)

    mit_dependency_graph = maya.api.OpenMaya.MItDependencyGraph(
        mobj, direction, maya.api.OpenMaya.MItDependencyGraph.kPlugLevel)

    while not mit_dependency_graph.isDone():
        current_item = mit_dependency_graph.currentNode()
        depend_node_fn = maya.api.OpenMaya.MFnDependencyNode(current_item)
        node_name = depend_node_fn.name()
        if object_type:
            for o_type in object_type:
                if current_item.hasFn(o_type):
                    nodes.append(node_name)
                    break
        else:
            nodes.append(node_name)

        mit_dependency_graph.next()

    return nodes


def get_objects_of_mtype_iterator(object_type):
    """
    Returns a iterator of Maya objects filtered by object type
    :param object_type: enum value used to identify Maya objects
    :return: SceneObject:_abstract_to_native_object_type
    """

    object_type = python.force_list(object_type)
    for obj_type in object_type:
        obj_iter = maya.api.OpenMaya.MItDependencyNodes(obj_type)
        while not obj_iter.isDone():
            yield obj_iter.thisNode()
            obj_iter.next()


def delete_nodes_of_type(node_type):
    """
    Delete all nodes of the given type
    :param node_type: varaiant, list<str> || str, name of node type (eg: hyperView, etc) or list of names
    """

    node_type = python.force_list(node_type)
    deleted_nodes = list()

    for node_type_name in node_type:
        nodes_to_delete = maya.cmds.ls(type=node_type_name)
        for n in nodes_to_delete:
            if n == 'hyperGraphLayout':
                continue
            if not maya.cmds.objExists(n):
                continue

            maya.cmds.lockNode(n, lock=False)
            maya.cmds.delete(n)
            deleted_nodes.append(n)

    return deleted_nodes


def get_index_color(node):
    """
    Returns the node color as Maya color index
    :param node: str
    :return: int or None, -1 if index not found because shape RGB mode color is enabled
    """

    if not node:
        return None

    if not maya.cmds.getAttr('{}.overrideEnabled'.format(node)):
        return 0
    elif not maya.cmds.getAttr('{}.overrideRGBColors'.format(node)):
        return maya.cmds.getAttr('{}.overrideColor'.format(node))

    return -1


def get_rgb_color(node, linear=True, limit_decimal_places=False):
    """
    Returns the color of the given node in RGB
    :param node: str, name of the shape node to retrieve color of
    :param linear: bool, Whether or not the RGB should be in linear space (matches viewport color)
    :param limit_decimal_places: bool, Whether or not decimal places should be limited to a maximum of 3
    :return: tuple(float, float, float), tuple of floats in 0-1 range
    """

    if not maya.cmds.objExists('{}.overrideColor'.format(node)):
        return maya_color.MAYA_COLORS_LINEAR_RGB[0] if linear else maya_color.MAYA_COLORS_SRGB[0]

    rgb = None
    if not maya.cmds.getAttr('{}.overrideEnabled'.format(node)):
        if linear:
            rgb = maya_color.MAYA_COLORS_LINEAR_RGB[0] if linear else maya_color.MAYA_COLORS_SRGB[0]
    elif not maya.cmds.getAttr('{}.overrideRGBColors'.format(node)):
        color_index = maya.cmds.getAttr('{}.overrideColor'.format(node))
        rgb = maya_color.MAYA_COLORS_LINEAR_RGB[color_index] if linear else maya_color.MAYA_COLORS_SRGB[color_index]
    else:
        rgb = tuple([
            maya.cmds.getAttr('{}.overrideColorR'.format(node)),
            maya.cmds.getAttr('{}.overrideColorG'.format(node)),
            maya.cmds.getAttr('{}.overrideColorB'.format(node))])
        if not linear:
            rgb = color.convert_color_linear_to_srgb(rgb)

    if rgb and limit_decimal_places:
        rgb = list(rgb)
        for i, value in enumerate(rgb):
            rgb[i] = float("{0:.3f}".format(value))
        return tuple(rgb)

    return rgb


def get_hsv_color(shape, linear=True):
    """
    Returns the color of the given node in HSV
    :param shape: str, name of the shape node to retrieve color of
    :param linear: bool, Whether or not the RGB should be in linear space (matches viewport color)
    :return: tuple(float, float, float), tuple of floats in 0-1 range
    """

    rgb_color = get_rgb_color(shape, linear=linear)
    if not rgb_color:
        return None

    hsv_color = color.convert_rgb_to_hsv(rgb_color)

    return hsv_color


def set_color(nodes, value):
    """
    Sets the override color for the given nodes
    :param nodes: str or list(str), list of nodes to change override color of
    :param value: int, color index to set override color to
    """

    if isinstance(value, int):
        set_index_color(nodes, value)
    else:
        set_rgb_color(nodes, value)


def set_index_color(nodes, index):
    """
    Sets the override Maya index color of the given nodes
    :param nodes: str or list(str), list of nodes to change override color of
    :param index: int, Maya color index to apply (from 0 to 30)
    """

    nodes = python.force_list(nodes)
    for node in nodes:
        if python.is_string(index):
            index = maya_color.convert_maya_color_string_to_index(index)
        if index is not None:
            if maya.cmds.objExists('{}.overrideRGBColors'.format(node)):
                maya.cmds.setAttr('{}.overrideRGBColors'.format(node), False)
            maya.cmds.setAttr('{}.overrideEnabled'.format(node), True)
            maya.cmds.setAttr('{}.overrideColor'.format(node), index)

    return index


def set_index_color_as_rgb(node, index, linear=True):
    """
    Sets the override RGB color by the given Maya color index
    :param node: str or list(str)
    :param index: int or str, Maya index color or Maya nice name color
    :param linear: bool, Whether or not the RGB should be set in linear space (matches viewport color)
    """

    if python.is_string(index):
        index = maya_color.convert_maya_color_string_to_index(index)
    rgb_list = maya_color.convert_maya_color_index_to_rgb(index, linear=linear)
    set_rgb_color(node, rgb_list=rgb_list)


def set_rgb_color(node, rgb_list, linear=True, color_shapes=True):
    """
    Sets the override RGB color of the given nodes
    NOTE: This function only works for versions of Maya greater than 2015
    :param node: str or list(str)
    :param linear: bool, Whether or not the RGB should be set in linear space (matches viewport color)
    :param color_shapes: bool, Whether to apply color to the given node or its shapes
    :param rgb_list: list(float, float, float)
    """

    from tpDcc.dccs.maya.core import shape

    if not linear:
        rgb_list = color.convert_color_linear_to_srgb(rgb_list)

    nodes = python.force_list(node)
    if color_shapes:
        nodes = shape.filter_shapes_in_list(nodes)
    if not nodes:
        return

    for node in nodes:
        if not maya.cmds.objExists(
                '{}.overrideRGBColors'.format(node)) or not maya.cmds.objExists('{}.overrideEnabled'.format(node)):
            continue

        maya.cmds.setAttr('{}.overrideRGBColors'.format(node), True)
        maya.cmds.setAttr('{}.overrideEnabled'.format(node), True)
        maya.cmds.setAttr('{}.overrideColorR'.format(node), rgb_list[0])
        maya.cmds.setAttr('{}.overrideColorG'.format(node), rgb_list[1])
        maya.cmds.setAttr('{}.overrideColorB'.format(node), rgb_list[2])
        maya.cmds.setAttr('{}.overrideColorRGB'.format(node), rgb_list[0], rgb_list[1], rgb_list[2])


def set_hsv_color(node, hsv, linear=True, color_shapes=True):
    """
    Sets the override color of the given node as HSV
    :param node: str or list(str)
    :param hsv: tuple(float, float, float), HSV color
    :param linear: bool, Whether or not the RGB should be set in linear space (matches viewport color)
    :param color_shapes: bool, Whether to apply color to the given node or its shapes
    """

    rgb = color.convert_hsv_to_rgb(hsv)
    set_rgb_color(node, rgb, linear=linear, color_shapes=color_shapes)


def filter_nodes_by_rgb_color(nodes_list, rgb_color, tolerance=0.05, query_shapes=True):
    """
    Returns nodes with the given color from the given list of nodes
    :param nodes_list: list(str), list of Maya nodes we want to to select
    :param rgb_color: tuple(float, float, float), color to find
    :param tolerance: float, margin for errors when comparing RGB float color values
    :param query_shapes: bool, Whether or not nodes shapes should be check to find color of
    :return: list(str), list of filtered nodes
    """

    # Import here to avoid cyclic imports
    from tpDcc.dccs.maya.core import shape as shape_utils

    colored_nodes = list()
    for i, node in enumerate(nodes_list):
        nodes_to_check = [nodes_list[i]]
        if query_shapes:
            nodes_to_check = shape_utils.filter_shapes_in_list([node])
        if nodes_to_check:
            if color.compare_rgb_colors_tolerance(get_rgb_color(nodes_to_check[0]), rgb_color, tolerance=tolerance):
                colored_nodes.append(node)

    return colored_nodes


def select_nodes_by_rgb_color(nodes_list, rgb_color, tolerance=0.05, query_shapes=False):
    """
    Selects nodes with the given color from the given list of nodes
    :param nodes_list: list(str), list of Maya nodes we want to to select
    :param rgb_color: tuple(float, float, float), color to find
    :param tolerance: float, margin for errors when comparing RGB float color values
    :param query_shapes: bool, Whether or not nodes shapes should be check to find color of
    :return: list(str), list of filtered nodes
    """

    colored_nodes = filter_nodes_by_rgb_color(nodes_list, rgb_color, tolerance=tolerance, query_shapes=query_shapes)
    if not colored_nodes:
        return None
    maya.cmds.select(colored_nodes, replace=True)

    return colored_nodes


def get_node_by_id(node_id, full_path=True):
    """
    Returns a node by its UUID (support starting from Maya 2016)
    :param node_id: str
    :param full_path: bool
    :return: str
    """

    if helpers.get_maya_version() >= 2016:
        maya_nodes = maya.cmds.ls(node_id, long=full_path)
        if maya_nodes and len(maya_nodes) > 1:
            LOGGER.warning('Multiple Maya nodes found with same IDs (this can happen when using heavy references')
        return maya_nodes[0]

    return None


def get_node_color_data(node):
    """
    Returns the color data in the given Maya node
    :param node: str or OpenMaya.MObject
    :return: dict
    """

    if python.is_string(node):
        node = get_mobject(node)

    return api_node.get_node_color_data(node)


def get_all_parents(node, full_path=True):
    """
    Returns all parents of the given node
    :param node: str, Maya DAG object name
    :param full_path: bool, Whether or not to return parent full names
    :return: list(str)
    """

    parents = maya.cmds.ls(node, long=True)[0].split('|')[1:-1]
    if full_path:
        parents = ['|'.join(parents[:i]) for i in range(1, 1 + len(parents))]
        for i, obj in enumerate(parents):
            parents[i] = '|{}'.format(obj)

    return parents
