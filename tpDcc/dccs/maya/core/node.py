#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to nodes
"""

from __future__ import print_function, division, absolute_import

import re
import uuid
import logging

from tpDcc.libs.python import python, name
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import exceptions

LOGGER = logging.getLogger()


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

        found_type[n] = list()

        node_type = maya.cmds.nodeType(n)
        if node_type == 'transform':

            children = maya.cmds.listRelatives(n, shapes=True)
            if not children:
                node_type = 'group'
            else:
                if return_shape_type:
                    shapes = shape.get_shapes(n)
                    if shapes:
                        node_type = maya.cmds.nodeType(shapes[0])

        # TODO: Check if we need this
        # if not node_type in found_type:
        #     found_type[node_type] = list()
        #
        # found_type[node_type].append(n)

        found_type[n].append(node_type)

    return found_type


def update_uuid(node_name):
    """
    Updates the unique identifier of the given Maya node
    :param node: str
    :return:
    """

    ids = list()
    for attr in maya.cmds.ls('*.uuid'):
        id = maya.cmds.getAttr(attr)
        ids.append(id)

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

    if isinstance(node, str):
        if not maya.cmds.objExists(node):
            raise exceptions.NodeExistsException(node)
    elif isinstance(node, maya.OpenMaya.MObject):
        return node.isNull()

    return False


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

    return mobj.hasFn(maya.OpenMaya.MFn.kDagNode)


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
        selection_list = maya.OpenMaya.MSelectionList()
        selection_list.add(node_name)

        if maya.is_new_api():
            try:
                mobj = selection_list.getDependNode(0)
            except Exception as e:
                maya.cmds.warning('Impossible to get MObject from name {}'.format(node_name))
                return
        else:
            mobj = maya.OpenMaya.MObject()
            try:
                selection_list.getDependNode(0, mobj)
            except Exception as e:
                maya.cmds.warning('Impossible to get MObject from name {}'.format(node_name))
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
        if is_dag_node(mobj):
            dag_path = maya.OpenMaya.MDagPath.getAPathTo(mobj)
            if fullname:
                return dag_path.fullPathName()
            return dag_path.partialPathName().split('|')[-1]
        return maya.OpenMaya.MFnDependencyNode(mobj).name()
    except Exception as e:
        maya.cmds.warning('Ipmossible to get name from MObject: {} - {}'.format(mobj, str(e)))
        return None


def set_names(nodes, names):
    nodes = python.force_list(nodes)
    names = python.force_list(names)

    for node, name in zip(nodes, names):
        maya.OpenMaya.MFnDagNode(node).setName(name)


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

    if maya.is_new_api():
        selection_list = maya.OpenMaya.MGlobal.getSelectionListByName(obj)
        dag_path = selection_list.getDagPath(0)
    else:
        selection_list = maya.OpenMaya.MSelectionList()
        dag_path = maya.OpenMaya.MDagPath()
        maya.OpenMaya.MGlobal.getSelectionListByName(obj, selection_list)
        selection_list.getDagPath(0, dag_path)

    return dag_path


def get_depend_node(node):
    """
    :param node: str | MObject, Name of the object or MObject
    :return: MObject
    """

    check_node(node)

    if type(node) in [str, unicode]:
        selection_list = maya.OpenMaya.MSelectionList()
        selection_list.add(node)

        if maya.is_new_api():
            dep_node = selection_list.getDependNode(0)
        else:
            try:
                dep_node = maya.OpenMaya.MFnDependencyNode()
                selection_list.getDependNode(0, dep_node)
            except Exception:
                dep_node = maya.OpenMaya.MObject()
                selection_list.getDependNode(0, dep_node)
    else:
        dep_node = maya.OpenMaya.MFnDependencyNode(node)

    return dep_node


def get_plug(node, plug_name):
    """
    Get the plug of a Maya node
    :param obj_name: str | MObject, Name of the object or MObject
    :param plug_name: str, Name of the plug
    """

    check_node(node)

    if type(node) in [str, unicode]:
        mobj = get_depend_node(node)
        dep_fn = maya.OpenMaya.MFnDependencyNode()
        dep_fn.setObject(mobj)
        plug = dep_fn.findPlug(plug_name, False)
    else:
        dep_node = get_depend_node(node)
        attr = dep_node.attribute(plug_name)
        plug = maya.OpenMaya.MPlug(node, attr)

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
    elif isinstance(node, maya.OpenMaya.MObject):
        if not node.apiType() == maya.OpenMaya.MFn.kTransform:
            return node

        path = maya.OpenMaya.MDagPath.getAPathTo(node)
        num_shapes = maya.OpenMaya.MScriptUtil()
        num_shapes.createFromInt(0)
        num_shapes_ptr = num_shapes.asUintPtr()
        path.numberOfShapesDirectlyBelow(num_shapes_ptr)
        if maya.OpenMaya.MScriptUtil(num_shapes_ptr).asUint():
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
    dep_fn = maya.OpenMaya.MFnDependencyNode()
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
    mdg_mod = maya.OpenMaya.MDGModifier()
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
    mdg_mod = maya.OpenMaya.MDGModifier()
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
    if api_type in [maya.OpenMaya.MFn.kAttribute3Double, maya.OpenMaya.MFn.kAttribute3Float,
                    maya.OpenMaya.MFn.kCompoundAttribute]:
        result = []
        if plug.isCompound:
            for c in range(plug.numChildren()):
                result.append(get_plug_value(plug.child(c)))
            return result

    # Distance
    elif api_type in [maya.OpenMaya.MFn.kDoubleLinearAttribute, maya.OpenMaya.MFn.kFloatLinearAttribute]:
        return plug.asMDistance().asCentimeters()

    # Angle
    elif api_type in [maya.OpenMaya.MFn.kDoubleAngleAttribute, maya.OpenMaya.MFn.kFloatAngleAttribute]:
        return plug.asMAngle().asDegrees()

    # TYPED
    elif api_type == maya.OpenMaya.MFn.kTypedAttribute:
        plug_type = maya.OpenMaya.MFnTypedAttribute(plug_attr).attrType()

        # Matrix
        if plug_type == maya.OpenMaya.MFnData.kMatrix:
            return maya.OpenMaya.MFnMatrixData(plug.asMObject()).matrix()

        # String
        elif plug_type == maya.OpenMaya.MFnData.kString:
            return plug.asString()

    # Matrix
    elif api_type == maya.OpenMaya.MFn.kMatrixAttribute:
        return maya.OpenMaya.MFnMatrixData(plug.asMObject()).matrix()

    # NUMBERS
    elif api_type == maya.OpenMaya.MFn.kNumericAttribute:

        plug_type = maya.OpenMaya.MFnNumericAttribute(plug_attr).numericType()

        # Boolean
        if plug_type == maya.OpenMaya.MFnNumericData.kBoolean:
            return plug.asBool()

        # Integer - Short, Int, Long, Byte
        elif plug_type in [maya.OpenMaya.MFnNumericData.kShort, maya.OpenMaya.MFnNumericData.kInt,
                           maya.OpenMaya.MFnNumericData.kLong, maya.OpenMaya.MFnNumericData.kByte]:
            return plug.asInt()

        # Float - Float, Double, Address
        elif plug_type in [maya.OpenMaya.MFnNumericData.kFloat, maya.OpenMaya.MFnNumericData.kDouble,
                           maya.OpenMaya.MFnNumericData.kAddr]:
            return plug.asDouble()

    # Enum
    elif api_type == maya.OpenMaya.MFn.kEnumAttribute:
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

    data_type = maya.OpenMaya.MFnData.kInvalid
    if isinstance(data, str):
        data_type = maya.OpenMaya.MFnData.kString
    if isinstance(data, float):
        data_type = maya.OpenMaya.MFnData.kFloatArray
    if isinstance(data, int):
        data_type = maya.OpenMaya.MFnData.kIntArray

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


def create_attribute(mobj, name, data_type=None, short_name=None, default=None):
    """
    Creates an attribute on the provided object.
    Returns the attribute anme and shortName
    :param mobj: OpenMaya.MObject, MObject to create the attribute for
    :param name: str, name of the attribute
    :param data_type: Type of data to store in the attribute
    :param short_name: str, short name for the attribute
    :param default: default value assinged to teh attribute
    :return: (name, short name) As name and short name are normalized, this returns the actual names used for attribute
        names
    """

    # TODO: Reimplement this function so it can work on all cases (take the one that appears on the MetaData class)

    name = normalize_attribute_name(name)
    if data_type is None and default is not None:
        data_type = get_attribute_data_type(default)
        if data_type == maya.OpenMaya.MFnData.kInvalid:
            data_type = None
            LOGGER.debug('Unable to determien the attribute type => {}'.format(str(default)))
        if data_type is None:
            data_type = maya.OpenMaya.MFnData.kAny

        try:
            if short_name is None:
                short_name = normalize_attribute_short_name(name, unique_on_obj=mobj)
            dep_node = maya.OpenMaya.MFnDependencyNode(mobj)
        except Exception as e:
            raise Exception('Error while getting dependency node from MObject "{}" - {}'.format(mobj, str(e)))

        s_attr = maya.OpenMaya.MFnTypedAttribute()
        if default:
            attr = s_attr.create(name, short_name, data_type, default)
        else:
            attr = s_attr.create(name, short_name, data_type)
        dep_node.addAttribute(attr)

        return name, short_name


def set_attribute(mobj, name, value):
    """
    Sets the value of a current existing attribute of the passed node
    :param mobj: OpenMaya.MObject, MObject to set the attribute value to
    :param name: str, name of the attribute to store the value in
    :param value: value to store in the attribute
    """

    plug = get_plug(mobj, name)
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


def get_all_hiearchy_nodes(node, direction=None, object_type=None):
    """
    Returns a list with all nodes in the given node hierarchy
    :param node: str, node to retrieve hierarchy from
    :return:
    """

    if direction is None:
        # if helpers.get_maya_version() > 2016:
        #     direction = maya.OpenMaya.MItDependencyGraph.kDownstream
        # else:
        #     direction = OpenMaya.MItDependencyGraph.kDownstream
        direction = maya.OpenMaya.MItDependencyGraph.kDownstream

    check_node(node)

    object_type = python.force_list(object_type)
    nodes = list()

    if type(node) == maya.OpenMaya.MObject:
        mobj = node
    else:
        if maya.is_new_api():
            sel_list = maya.OpenMaya.MSelectionList()
            sel_list.add(node)
            mobj = sel_list.getDependNode(0)
        else:
            mobj = maya.OpenMaya.MObject()
            sel_list = maya.OpenMaya.MSelectionList()
            sel_list.add(node)
            sel_list.getDependNode(0, mobj)

    mit_dependency_graph = maya.OpenMaya.MItDependencyGraph(
        mobj, direction, maya.OpenMaya.MItDependencyGraph.kPlugLevel)

    while not mit_dependency_graph.isDone():
        if maya.is_new_api():
            current_item = mit_dependency_graph.currentNode()
        else:
            current_item = mit_dependency_graph.currentItem()

        depend_node_fn = maya.OpenMaya.MFnDependencyNode(current_item)
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
        obj_iter = maya.OpenMaya.MItDependencyNodes(obj_type)
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
