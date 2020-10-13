#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya MPlugs
"""

from __future__ import print_function, division, absolute_import

import tpDcc.dccs.maya as maya
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
    n_attr = maya.OpenMaya.MFnNumericAttribute(obj)
    data_type = n_attr.numericType()
    if data_type == maya.OpenMaya.MFnNumericData.kBoolean:
        return attributetypes.kMFnNumericBoolean, plug.asBool()
    elif data_type == maya.OpenMaya.MFnNumericData.kByte:
        return attributetypes.kMFnNumericByte, plug.asBool()
    elif data_type == maya.OpenMaya.MFnNumericData.kShort:
        return attributetypes.kMFnNumericShort, plug.asShort()
    elif data_type == maya.OpenMaya.MFnNumericData.kInt:
        return attributetypes.kMFnNumericInt, plug.asInt()
    elif data_type == maya.OpenMaya.MFnNumericData.kLong:
        return attributetypes.kMFnNumericLong, plug.asInt()
    elif data_type == maya.OpenMaya.MFnNumericData.kDouble:
        return attributetypes.kMFnNumericDouble, plug.asDouble()
    elif data_type == maya.OpenMaya.MFnNumericData.kFloat:
        return attributetypes.kMFnNumericFloat, plug.asFloat()
    elif data_type == maya.OpenMaya.MFnNumericData.kAddr:
        return attributetypes.kMFnNumericAddr, plug.asAddr()
    elif data_type == maya.OpenMaya.MFnNumericData.kChar:
        return attributetypes.kMFnNumericChar, plug.asChar()
    elif data_type == maya.OpenMaya.MFnNumericData.k2Double:
        return attributetypes.kMFnNumeric2Double, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k2Float:
        return attributetypes.kMFnNumeric2Float, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k2Int:
        return attributetypes.kMFnNumeric2Int, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k2Long:
        return attributetypes.kMFnNumeric2Long, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k2Short:
        return attributetypes.kMFnNumeric2Short, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k3Double:
        return attributetypes.kMFnNumeric3Double, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k3Float:
        return attributetypes.kMFnNumeric3Float, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k3Int:
        return attributetypes.kMFnNumeric3Int, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k3Long:
        return attributetypes.kMFnNumeric3Long, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k3Short:
        return attributetypes.kMFnNumeric3Short, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()
    elif data_type == maya.OpenMaya.MFnNumericData.k4Double:
        return attributetypes.kMFnNumeric4Double, maya.OpenMaya.MFnNumericData(plug.asMObject()).getData()

    return None, None


def get_typed_value(plug):
    """
    Returns Maya type from the given MPlug
    :param plug: MPlug
    :return: Maya type
    """

    typed_attr = maya.OpenMaya.MFnTypedAttribute(plug.attribute())
    data_type = typed_attr.attrType()
    if data_type == maya.OpenMaya.MFnData.kInvalid:
        return None, None
    elif data_type == maya.OpenMaya.MFnData.kString:
        return attributetypes.kMFnDataString, plug.asString()
    elif data_type == maya.OpenMaya.MFnData.kNumeric:
        return get_numeric_value(plug)
    elif data_type == maya.OpenMaya.MFnData.kMatrix:
        return attributetypes.kMFnDataMatrix, maya.OpenMaya.MFnMatrixData(plug.asMObject()).matrix()
    elif data_type == maya.OpenMaya.MFnData.kFloatArray:
        return attributetypes.kMFnDataFloatArray, maya.OpenMaya.MFnFloatArrayData(plug.asMObject()).array()
    elif data_type == maya.OpenMaya.MFnData.kDoubleArray:
        return attributetypes.kMFnDataDoubleArray, maya.OpenMaya.MFnDoubleArrayData(plug.asMObject()).array()
    elif data_type == maya.OpenMaya.MFnData.kIntArray:
        return attributetypes.kMFnDataIntArray, maya.OpenMaya.MFnIntArrayData(plug.asMObject()).array()
    elif data_type == maya.OpenMaya.MFnData.kPointArray:
        return attributetypes.kMFnDataPointArray, maya.OpenMaya.MFnPointArrayData(plug.asMObject()).array()
    elif data_type == maya.OpenMaya.MFnData.kVectorArray:
        return attributetypes.kMFnDataVectorArray, maya.OpenMaya.MFnVectorArrayData(plug.asMObject()).array()
    elif data_type == maya.OpenMaya.MFnData.kStringArray:
        return attributetypes.kMFnDataStringArray, maya.OpenMaya.MFnStringArrayData(plug.asMObject()).array()
    elif data_type == maya.OpenMaya.MFnData.kMatrixArray:
        return attributetypes.kMFnDataMatrixArray, maya.OpenMaya.MFnMatrixArrayData(plug.asMObject()).array()
    
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

    if obj.hasFn(maya.OpenMaya.MFn.kNumericAttribute):
        return get_numeric_value(plug)
    elif obj.hasFn(maya.OpenMaya.MFn.kUnitAttribute):
        unit_attr = maya.OpenMaya.MFnUnitAttribute(obj)
        unit_type = unit_attr.unitType()
        if unit_type == maya.OpenMaya.MFnUnitAttribute.kDistance:
            return attributetypes.kMFnUnitAttributeDistance, plug.asMDistance()
        elif unit_type == maya.OpenMaya.MFnUnitAttribute.kAngle:
            return attributetypes.kMFnUnitAttributeAngle, plug.asMAngle()
        elif unit_type == maya.OpenMaya.MFnUnitAttribute.kTime:
            return attributetypes.kMFnUnitAttributeTime, plug.asMTime()
    elif obj.hasFn(maya.OpenMaya.MFn.kEnumAttribute):
        return attributetypes.kMFnkEnumAttribute, plug.asInt()
    elif obj.hasFn(maya.OpenMaya.MFn.kTypedAttribute):
        return get_typed_value(plug)
    elif obj.hasFn(maya.OpenMaya.MFn.kMessageAttribute):
        source = plug.source()
        if source is not None:
            return attributetypes.kMFnMessageAttribute, source.node()
        return attributetypes.kMFnMessageAttribute, None
    elif obj.hasFn(maya.OpenMaya.MFn.kMatrixAttribute):
        return attributetypes.kMFnDataMatrix, maya.OpenMaya.MFnMatrixData(plug.asMObject()).matrix()

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

    mod = mod or maya.OpenMaya.MDagModifier()

    is_array = plug.isArray if maya.is_new_api() else plug.isArray()
    is_compound = plug.isCompound if maya.is_new_api() else plug.isCompound()

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
    if obj.hasFn(maya.OpenMaya.MFn.kUnitAttribute):
        unit_attr = maya.OpenMaya.MFnUnitAttribute(obj)
        unit_type = unit_attr.unitType()
        if unit_type == maya.OpenMaya.MFnUnitAttribute.kDistance:
            if mod:
                mod.newPlugValueMDistance(plug, maya.OpenMaya.MDistance(value))
            else:
                plug.setMDistance(maya.OpenMaya.MDistance(value))
        elif unit_type == maya.OpenMaya.MFnUnitAttribute.kTime:
            if mod:
                mod.newPlugValueMTime(plug, maya.OpenMaya.MTime(value))
            else:
                plug.setMTime(maya.OpenMaya.MTime(value))
        elif unit_type == maya.OpenMaya.MFnUnitAttribute.kAngle:
            if mod:
                mod.newPlugValueMAngle(plug, maya.OpenMaya.MAngle(value))
            else:
                plug.setMAngle(maya.OpenMaya.MAngle(value))
        elif obj.hasFn(maya.OpenMaya.MFn.kNumericAttribute):
            numeric_attr = maya.OpenMaya.MFnNumericAttribute(obj)
            numeric_type = numeric_attr.numericType()
            if numeric_type in (
                    maya.OpenMaya.MFnNumericData.k2Double, maya.OpenMaya.MFnNumericData.k2Float,
                    maya.OpenMaya.MFnNumericData.k2Int, maya.OpenMaya.MFnNumericData.k2Long,
                    maya.OpenMaya.MFnNumericData.k2Short, maya.OpenMaya.MFnNumericData.k3Double,
                    maya.OpenMaya.MFnNumericData.k3Float, maya.OpenMaya.MFnNumericData.k3Int,
                    maya.OpenMaya.MFnNumericData.k3Long, maya.OpenMaya.MFnNumericData.k3Short,
                    maya.OpenMaya.MFnNumericData.k4Double):
                data = maya.OpenMaya.MFnNumericData().create(value)
                if mod:
                    mod.newPlugValue(plug, data.object())
                else:
                    plug.setMObject(data.object())
            elif numeric_type == maya.OpenMaya.MFnNumericData.kDouble:
                if mod:
                    mod.newPlugValueDouble(plug, value)
                else:
                    plug.setDouble(value)
            elif numeric_type == maya.OpenMaya.MFnNumericData.kFloat:
                if mod:
                    mod.newPlugValueFloat(plug, value)
                else:
                    plug.setFloat(value)
            elif numeric_type == maya.OpenMaya.MFnNumericData.kBoolean:
                if mod:
                    mod.newPlugValueBool(plug, value)
                else:
                    plug.setBool(value)
            elif numeric_type == maya.OpenMaya.MFnNumericData.kChar:
                if mod:
                    mod.newPlugValueChar(plug, value)
                else:
                    plug.setChar(value)
            elif numeric_type in (
                    maya.OpenMaya.MFnNumericData.kInt, maya.OpenMaya.MFnNumericData.kInt64, 
                    maya.OpenMaya.MFnNumericData.kLong, maya.OpenMaya.MFnNumericData.kLast):
                if mod:
                    mod.newPlugValueInt(plug, value)
                else:
                    plug.setInt(value)
            elif numeric_type == maya.OpenMaya.MFnNumericData.kShort:
                if mod:
                    mod.newPlugValueInt(plug, value)
                else:
                    plug.setInt(value)
        elif obj.hasFn(maya.OpenMaya.MFn.kEnumAttribute):
            if mod:
                mod.newPlugValueInt(plug, value)
            else:
                plug.setInt(value)
        elif obj.hasFn(maya.OpenMaya.MFn.kTypedAttribute):
            typed_attr = maya.OpenMaya.MFnTypedAttribute(obj)
            typed_type = typed_attr.attrType()
            if typed_type == maya.OpenMaya.MFnData.kMatrix:
                mat = maya.OpenMaya.MFnMatrixData().create(maya.OpenMaya.MMatrix(value))
                if mod:
                    mod.newPlugValue(plug, mat)
                else:
                    plug.setMObject(mat)
            elif typed_type == maya.OpenMaya.MFnData.kString:
                if mod:
                    mod.newPlugValueString(plug, value)
                else:
                    plug.setString(value)
        elif obj.hasFn(maya.OpenMaya.MFn.kMatrixAttribute):
            mat = maya.OpenMaya.MFnMatrixData().create(maya.OpenMaya.MMatrix(value))
            if mod:
                mod.newPlugValue(plug, mat)
            else:
                plug.setMObject(mat)
        elif obj.hasFn(maya.OpenMaya.MFn.kMessageAttribute) and not value:
            # Message attributes doesn't have any values
            pass
        elif obj.hasFn(maya.OpenMaya.MFn.kMessageAttribute) and isinstance(value, maya.OpenMaya.MPlug):
            # connect the message attribute
            connect_plugs(plug, value, mod=mod, apply=False)
        elif obj.hasFn(maya.OpenMaya.MFn.kMessageAttribute):
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

    mod = mod or maya.OpenMaya.MDGModifier()

    source_is_destination = source.isDestination if maya.is_new_api() else source.isDestination()
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
