#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya MPlugs
"""

from __future__ import print_function, division, absolute_import

import maya.api.OpenMaya

from tpDcc.dccs.maya import api
from tpDcc.dccs.maya.api import attributetypes


def as_mplug(attr_name):
    """
    Returns the MPlug instance of the given name
    :param attr_name: str, name of the Maya node to convert to MPlug
    :return: MPlug
    """

    try:
        names = attr_name.split('.')
        sel = api.SelectionList()
        sel.add(names[0])
        node = api.DependencyNode(sel.get_depend_node(0))
        return node.find_plug('.'.join(names[1:]), False)
    except RuntimeError:
        sel = api.SelectionList()
        sel.add(str(attr_name))
        return sel.get_plug(0)


def get_numeric_value(plug):
    """
    Returns the numeric value of the given MPlug
    :param plug: MPlug
    :return: int or float
    """

    obj = plug.attribute()
    n_attr = maya.api.OpenMaya.MFnNumericAttribute(obj)
    data_type = n_attr.numericType()
    if data_type == maya.api.OpenMaya.MFnNumericData.kBoolean:
        return attributetypes.kMFnNumericBoolean, plug.asBool()
    elif data_type == maya.api.OpenMaya.MFnNumericData.kByte:
        return attributetypes.kMFnNumericByte, plug.asBool()
    elif data_type == maya.api.OpenMaya.MFnNumericData.kShort:
        return attributetypes.kMFnNumericShort, plug.asShort()
    elif data_type == maya.api.OpenMaya.MFnNumericData.kInt:
        return attributetypes.kMFnNumericInt, plug.asInt()
    elif data_type == maya.api.OpenMaya.MFnNumericData.kLong:
        return attributetypes.kMFnNumericLong, plug.asInt()
    elif data_type == maya.api.OpenMaya.MFnNumericData.kDouble:
        return attributetypes.kMFnNumericDouble, plug.asDouble()
    elif data_type == maya.api.OpenMaya.MFnNumericData.kFloat:
        return attributetypes.kMFnNumericFloat, plug.asFloat()
    elif data_type == maya.api.OpenMaya.MFnNumericData.kAddr:
        return attributetypes.kMFnNumericAddr, plug.asAddr()
    elif data_type == maya.api.OpenMaya.MFnNumericData.kChar:
        return attributetypes.kMFnNumericChar, plug.asChar()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k2Double:
        return attributetypes.kMFnNumeric2Double, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k2Float:
        return attributetypes.kMFnNumeric2Float, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k2Int:
        return attributetypes.kMFnNumeric2Int, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k2Long:
        return attributetypes.kMFnNumeric2Long, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k2Short:
        return attributetypes.kMFnNumeric2Short, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k3Double:
        return attributetypes.kMFnNumeric3Double, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k3Float:
        return attributetypes.kMFnNumeric3Float, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k3Int:
        return attributetypes.kMFnNumeric3Int, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k3Long:
        return attributetypes.kMFnNumeric3Long, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k3Short:
        return attributetypes.kMFnNumeric3Short, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.api.OpenMaya.MFnNumericData.k4Double:
        return attributetypes.kMFnNumeric4Double, maya.api.OpenMaya.MFnNumericData(plug.asMObject()).getData()

    return None, None


def get_typed_value(plug):
    """
    Returns Maya type from the given MPlug
    :param plug: MPlug
    :return: Maya type
    """

    typed_attr = maya.api.OpenMaya.MFnTypedAttribute(plug.attribute())
    data_type = typed_attr.attrType()
    if data_type == maya.api.OpenMaya.MFnData.kInvalid:
        return None, None
    elif data_type == maya.api.OpenMaya.MFnData.kString:
        return attributetypes.kMFnDataString, plug.asString()
    elif data_type == maya.api.OpenMaya.MFnData.kNumeric:
        return get_numeric_value(plug)
    elif data_type == maya.api.OpenMaya.MFnData.kMatrix:
        return attributetypes.kMFnDataMatrix, maya.api.OpenMaya.MFnMatrixData(plug.asMObject()).matrix()
    elif data_type == maya.api.OpenMaya.MFnData.kFloatArray:
        return attributetypes.kMFnDataFloatArray, maya.api.OpenMaya.MFnFloatArrayData(plug.asMObject()).array()
    elif data_type == maya.api.OpenMaya.MFnData.kDoubleArray:
        return attributetypes.kMFnDataDoubleArray, maya.api.OpenMaya.MFnDoubleArrayData(plug.asMObject()).array()
    elif data_type == maya.api.OpenMaya.MFnData.kIntArray:
        return attributetypes.kMFnDataIntArray, maya.api.OpenMaya.MFnIntArrayData(plug.asMObject()).array()
    elif data_type == maya.api.OpenMaya.MFnData.kPointArray:
        return attributetypes.kMFnDataPointArray, maya.api.OpenMaya.MFnPointArrayData(plug.asMObject()).array()
    elif data_type == maya.api.OpenMaya.MFnData.kVectorArray:
        return attributetypes.kMFnDataVectorArray, maya.api.OpenMaya.MFnVectorArrayData(plug.asMObject()).array()
    elif data_type == maya.api.OpenMaya.MFnData.kStringArray:
        return attributetypes.kMFnDataStringArray, maya.api.OpenMaya.MFnStringArrayData(plug.asMObject()).array()
    elif data_type == maya.api.OpenMaya.MFnData.kMatrixArray:
        return attributetypes.kMFnDataMatrixArray, maya.api.OpenMaya.MFnMatrixArrayData(plug.asMObject()).array()
    return None, None


def get_plug_value_and_type(plug):
    """
    Returns the value and the type of the given MPlug
    :param plug: MPlug
    :return: tuple(int, variant), MPlug value and its data type (if possible Python default types)
    """

    obj = plug.attribute()
    if plug.isArray:
        count = plug.evaluateNumElements()
        res = [None] * count, [None] * count
        data = [get_plug_value_and_type(plug.elementByPhysicalIndex(i)) for i in range(count)]
        for i in range(len(data)):
            res[0][i] = data[i][0]
            res[1][i] = data[i][1]
        return res

    if obj.hasFn(maya.api.OpenMaya.MFn.kNumericAttribute):
        return get_numeric_value(plug)
    elif obj.hasFn(maya.api.OpenMaya.MFn.kUnitAttribute):
        unit_attr = maya.api.OpenMaya.MFnUnitAttribute(obj)
        unit_type = unit_attr.unitType()
        if unit_type == maya.api.OpenMaya.MFnUnitAttribute.kDistance:
            return attributetypes.kMFnUnitAttributeDistance, plug.asMDistance()
        elif unit_type == maya.api.OpenMaya.MFnUnitAttribute.kAngle:
            return attributetypes.kMFnUnitAttributeAngle, plug.asMAngle()
        elif unit_type == maya.api.OpenMaya.MFnUnitAttribute.kTime:
            return attributetypes.kMFnUnitAttributeTime, plug.asMTime()
    elif obj.hasFn(maya.api.OpenMaya.MFn.kEnumAttribute):
        return attributetypes.kMFnkEnumAttribute, plug.asInt()
    elif obj.hasFn(maya.api.OpenMaya.MFn.kTypedAttribute):
        return get_typed_value(plug)
    elif obj.hasFn(maya.api.OpenMaya.MFn.kMessageAttribute):
        source = plug.source()
        if source is not None:
            return attributetypes.kMFnMessageAttribute, source.node()
        return attributetypes.kMFnMessageAttribute, None
    elif obj.hasFn(maya.api.OpenMaya.MFn.kMatrixAttribute):
        return attributetypes.kMFnDataMatrix, maya.api.OpenMaya.MFnMatrixData(plug.asMObject()).matrix()

    if plug.isCompound:
        count = plug.numChildren()
        res = [None] * count, [None] * count
        data = [get_plug_value_and_type(plug.child(i)) for i in range(count)]
        for i in range(len(data)):
            res[0][i] = data[i][0]
            res[1][i] = data[i][1]
        return res

    return None, None


def get_plug_value(plug):
    """
    Returns value of the given MPlug
    :param plug: MPlug
    :return: variant
    """

    return get_plug_value_and_type(plug)[1]


def set_plug_value(plug, value, mod=None, apply=True):
    """
    Sets the given lugs value to the given passed value
    :param plug: MPlug
    :param value: variant
    :param mod: MDGModifier
    :param apply: bool, Whether to apply the modifier instantly or leave it to the caller
    """

    mod = mod or maya.api.OpenMaya.MDagModifier()

    is_array = plug.isArray
    is_compound = plug.isCompound

    if is_array:
        count = plug.evaluateNumElements()
        if count != len(value):
            return
        for i in range(count):
            set_plug_value(plug.elementByPhysicalIndex(i), value[i], mod=mod)
        return
    elif is_compound:
        count = plug.numChildren()
        if count != len(value):
            return
        for i in range(count):
            set_plug_value(plug.child(i), value[i], mod=mod)
        return

    obj = plug.attribute()
    if obj.hasFn(maya.api.OpenMaya.MFn.kUnitAttribute):
        unit_attr = maya.api.OpenMaya.MFnUnitAttribute(obj)
        unit_type = unit_attr.unitType()
        if unit_type == maya.api.OpenMaya.MFnUnitAttribute.kDistance:
            if mod:
                mod.newPlugValueMDistance(plug, maya.api.OpenMaya.MDistance(value))
            else:
                plug.setMDistance(maya.api.OpenMaya.MDistance(value))
        elif unit_type == maya.api.OpenMaya.MFnUnitAttribute.kTime:
            if mod:
                mod.newPlugValueMTime(plug, maya.api.OpenMaya.MTime(value))
            else:
                plug.setMTime(maya.api.OpenMaya.MTime(value))
        elif unit_type == maya.api.OpenMaya.MFnUnitAttribute.kAngle:
            if mod:
                mod.newPlugValueMAngle(plug, maya.api.OpenMaya.MAngle(value))
            else:
                plug.setMAngle(maya.api.OpenMaya.MAngle(value))
        elif obj.hasFn(maya.api.OpenMaya.MFn.kNumericAttribute):
            numeric_attr = maya.api.OpenMaya.MFnNumericAttribute(obj)
            numeric_type = numeric_attr.numericType()
            if numeric_type in (
                    maya.api.OpenMaya.MFnNumericData.k2Double, maya.api.OpenMaya.MFnNumericData.k2Float,
                    maya.api.OpenMaya.MFnNumericData.k2Int, maya.api.OpenMaya.MFnNumericData.k2Long,
                    maya.api.OpenMaya.MFnNumericData.k2Short, maya.api.OpenMaya.MFnNumericData.k3Double,
                    maya.api.OpenMaya.MFnNumericData.k3Float, maya.api.OpenMaya.MFnNumericData.k3Int,
                    maya.api.OpenMaya.MFnNumericData.k3Long, maya.api.OpenMaya.MFnNumericData.k3Short,
                    maya.api.OpenMaya.MFnNumericData.k4Double):
                data = maya.api.OpenMaya.MFnNumericData().create(value)
                if mod:
                    mod.newPlugValue(plug, data.object())
                else:
                    plug.setMObject(data.object())
            elif numeric_type == maya.api.OpenMaya.MFnNumericData.kDouble:
                if mod:
                    mod.newPlugValueDouble(plug, value)
                else:
                    plug.setDouble(value)
            elif numeric_type == maya.api.OpenMaya.MFnNumericData.kFloat:
                if mod:
                    mod.newPlugValueFloat(plug, value)
                else:
                    plug.setFloat(value)
            elif numeric_type == maya.api.OpenMaya.MFnNumericData.kBoolean:
                if mod:
                    mod.newPlugValueBool(plug, value)
                else:
                    plug.setBool(value)
            elif numeric_type == maya.api.OpenMaya.MFnNumericData.kChar:
                if mod:
                    mod.newPlugValueChar(plug, value)
                else:
                    plug.setChar(value)
            elif numeric_type in (
                    maya.api.OpenMaya.MFnNumericData.kInt, maya.api.OpenMaya.MFnNumericData.kInt64,
                    maya.api.OpenMaya.MFnNumericData.kLong, maya.api.OpenMaya.MFnNumericData.kLast):
                if mod:
                    mod.newPlugValueInt(plug, value)
                else:
                    plug.setInt(value)
            elif numeric_type == maya.api.OpenMaya.MFnNumericData.kShort:
                if mod:
                    mod.newPlugValueInt(plug, value)
                else:
                    plug.setInt(value)
        elif obj.hasFn(maya.api.OpenMaya.MFn.kEnumAttribute):
            if mod:
                mod.newPlugValueInt(plug, value)
            else:
                plug.setInt(value)
        elif obj.hasFn(maya.api.OpenMaya.MFn.kTypedAttribute):
            typed_attr = maya.api.OpenMaya.MFnTypedAttribute(obj)
            typed_type = typed_attr.attrType()
            if typed_type == maya.api.OpenMaya.MFnData.kMatrix:
                mat = maya.api.OpenMaya.MFnMatrixData().create(maya.api.OpenMaya.MMatrix(value))
                if mod:
                    mod.newPlugValue(plug, mat)
                else:
                    plug.setMObject(mat)
            elif typed_type == maya.api.OpenMaya.MFnData.kString:
                if mod:
                    mod.newPlugValueString(plug, value)
                else:
                    plug.setString(value)
        elif obj.hasFn(maya.api.OpenMaya.MFn.kMatrixAttribute):
            mat = maya.api.OpenMaya.MFnMatrixData().create(maya.api.OpenMaya.MMatrix(value))
            if mod:
                mod.newPlugValue(plug, mat)
            else:
                plug.setMObject(mat)
        elif obj.hasFn(maya.api.OpenMaya.MFn.kMessageAttribute) and not value:
            # Message attributes doesn't have any values
            pass
        elif obj.hasFn(maya.api.OpenMaya.MFn.kMessageAttribute) and isinstance(value, maya.api.OpenMaya.MPlug):
            # connect the message attribute
            connect_plugs(plug, value, mod=mod, apply=False)
        elif obj.hasFn(maya.api.OpenMaya.MFn.kMessageAttribute):
            # Message attributes doesn't have any values
            pass
            connect_plugs(plug, value, mod=mod, apply=False)
        else:
            raise ValueError('Currently data type "{}" is not supported'.format(obj.apiTypeStr))

        if apply and mod:
            mod.doIt()

        return mod


def connect_plugs(source, target, mod=None, force=True, apply=True):
    """
    Connects given MPlugs together
    :param source: MPlug
    :param target: MPlug
    :param mod: MDGModifier
    :param force: bool
    :param apply: bool, Whether to apply the modifier instantly or leave it to the caller
    :return:
    """

    mod = mod or maya.api.OpenMaya.MDGModifier()

    source_is_destination = source.isDestination
    if source_is_destination:
        target_source = target.source()
        if force:
            mod.disconnect(target_source, target)
        else:
            raise ValueError('Plug {} has incoming connection {}'.format(target.name(), target_source.name()))
    mod.connect(source, target)
    if mod is None and apply:
        mod.doIt()

    return mod


def disconnect_plug(plug, source=True, destination=True, modifier=None):
    """
    Disconnects the plug connections, if "source" is True and the plug is a destination then disconnect the source
    from this plug. If destination is True and plug is a source the disconnect this plug from the destination.
    Plugs are also locked (to avoid Maya raises an error).
    :param plug: maya.api.OpenMaya.MPlug, plug to disconnect
    :param source: bool, If True, disconnect from the connected source plug if it has one
    :param destination: bool, If True, disconnect from the connected destination plug if it has one
    :param modifier: maya.api.OpenMaya.MDGModifier
    :return: bool, True if succeed with the disconnection
    :raises Maya API error
    """

    if plug.isLocked:
        plug.isLocked = False
    mod = modifier or maya.api.OpenMaya.MDGModifier()
    if source and plug.isDestination:
        source_plug = plug.source()
        if source_plug.isLocked:
            source_plug.isLocked = False
        mod.disconnect(source_plug, plug)
    if destination and plug.isSource:
        for connection in plug.destinations():
            if connection.isLocked:
                connection.isLocked = False
            mod.disconnect(plug, connection)
    if not modifier:
        mod.doIt()

    return True, mod
