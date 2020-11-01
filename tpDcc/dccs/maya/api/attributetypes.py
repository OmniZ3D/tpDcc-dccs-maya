#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that centralizes May attribute types
"""

from __future__ import print_function, division, absolute_import

import maya.api.OpenMaya

kMFnNumericBoolean = 0
kMFnNumericShort = 1
kMFnNumericInt = 2
kMFnNumericLong = 3
kMFnNumericByte = 4
kMFnNumericFloat = 5
kMFnNumericDouble = 6
kMFnNumericAddr = 7
kMFnNumericChar = 8
kMFnUnitAttributeDistance = 9
kMFnUnitAttributeAngle = 10
kMFnUnitAttributeTime = 11
kMFnkEnumAttribute = 12
kMFnDataString = 13
kMFnDataMatrix = 14
kMFnDataFloatArray = 15
kMFnDataDoubleArray = 16
kMFnDataIntArray = 17
kMFnDataPointArray = 18
kMFnDataVectorArray = 19
kMFnDataStringArray = 20
kMFnDataMatrixArray = 21
kMFnCompoundAttribute = 22
kMFnNumericInt64 = 23
kMFnNumericLast = 24
kMFnNumeric2Double = 25
kMFnNumeric2Float = 26
kMFnNumeric2Int = 27
kMFnNumeric2Long = 28
kMFnNumeric2Short = 29
kMFnNumeric3Double = 30
kMFnNumeric3Float = 31
kMFnNumeric3Int = 32
kMFnNumeric3Long = 33
kMFnNumeric3Short = 34
kMFnNumeric4Double = 35
kMFnMessageAttribute = 36

_MAYA_TYPE_FROM_TYPE = dict(
    kMFnNumericBoolean=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kBoolean),
    kMFnNumericByte=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kByte),
    kMFnNumericShort=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kShort),
    kMFnNumericInt=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kInt),
    kMFnNumericLong=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kLong),
    kMFnNumericDouble=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kDouble),
    kMFnNumericFloat=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kFloat),
    kMFnNumericAddr=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kAddr),
    kMFnNumericChar=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.kChar),
    kMFnNumeric2Double=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k2Double),
    kMFnNumeric2Float=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k2Float),
    kMFnNumeric2Int=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k2Int),
    kMFnNumeric2Long=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k2Long),
    kMFnNumeric2Short=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k2Short),
    kMFnNumeric3Double=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k3Double),
    kMFnNumeric3Float=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k3Float),
    kMFnNumeric3Int=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k3Int),
    kMFnNumeric3Long=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k3Long),
    kMFnNumeric3Short=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k3Short),
    kMFnNumeric4Double=(maya.api.OpenMaya.MFnNumericAttribute, maya.api.OpenMaya.MFnNumericData.k4Double),
    kMFnUnitAttributeDistance=(maya.api.OpenMaya.MFnUnitAttribute, maya.api.OpenMaya.MFnUnitAttribute.kDistance),
    kMFnUnitAttributeAngle=(maya.api.OpenMaya.MFnUnitAttribute, maya.api.OpenMaya.MFnUnitAttribute.kAngle),
    kMFnUnitAttributeTime=(maya.api.OpenMaya.MFnUnitAttribute, maya.api.OpenMaya.MFnUnitAttribute.kTime),
    kMFnkEnumAttribute=(maya.api.OpenMaya.MFnEnumAttribute, maya.api.OpenMaya.MFn.kEnumAttribute),
    kMFnDataString=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kString),
    kMFnDataMatrix=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kMatrix),
    kMFnDataFloatArray=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kFloatArray),
    kMFnDataDoubleArray=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kDoubleArray),
    kMFnDataIntArray=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kIntArray),
    kMFnDataPointArray=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kPointArray),
    kMFnDataVectorArray=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kVectorArray),
    kMFnDataStringArray=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kStringArray),
    kMFnDataMatrixArray=(maya.api.OpenMaya.MFnTypedAttribute, maya.api.OpenMaya.MFnData.kMatrixArray),
    kMFnMessageAttribute=(maya.api.OpenMaya.MFnMessageAttribute, maya.api.OpenMaya.MFn.kMessageAttribute)
)

_TYPE_TO_STRING = {
    kMFnNumericBoolean: "kMFnNumericBoolean",
    kMFnNumericByte: "kMFnNumericByte",
    kMFnNumericShort: "kMFnNumericShort",
    kMFnNumericInt: "kMFnNumericInt",
    kMFnNumericLong: "kMFnNumericLong",
    kMFnNumericDouble: "kMFnNumericDouble",
    kMFnNumericFloat: "kMFnNumericFloat",
    kMFnNumericAddr: "kMFnNumericAddr",
    kMFnNumericChar: "kMFnNumericChar",
    kMFnNumeric2Double: "kMFnNumeric2Double",
    kMFnNumeric2Float: "kMFnNumeric2Float",
    kMFnNumeric2Int: "kMFnNumeric2Int",
    kMFnNumeric2Long: "kMFnNumeric2Long",
    kMFnNumeric2Short: "kMFnNumeric2Short",
    kMFnNumeric3Double: "kMFnNumeric3Double",
    kMFnNumeric3Float: "kMFnNumeric3Float",
    kMFnNumeric3Int: "kMFnNumeric3Int",
    kMFnNumeric3Long: "kMFnNumeric3Long",
    kMFnNumeric3Short: "kMFnNumeric3Short",
    kMFnNumeric4Double: "kMFnNumeric4Double",
    kMFnUnitAttributeDistance: "kMFnUnitAttributeDistance",
    kMFnUnitAttributeAngle: "kMFnUnitAttributeAngle",
    kMFnUnitAttributeTime: "kMFnUnitAttributeTime",
    kMFnkEnumAttribute: "kMFnkEnumAttribute",
    kMFnDataString: "kMFnDataString",
    kMFnDataMatrix: "kMFnDataMatrix",
    kMFnDataFloatArray: "kMFnDataFloatArray",
    kMFnDataDoubleArray: "kMFnDataDoubleArray",
    kMFnDataIntArray: "kMFnDataIntArray",
    kMFnDataPointArray: "kMFnDataPointArray",
    kMFnDataVectorArray: "kMFnDataVectorArray",
    kMFnDataStringArray: "kMFnDataStringArray",
    kMFnDataMatrixArray: "kMFnDataMatrixArray",
    kMFnMessageAttribute: "kMFnMessageAttribute"
}


def api_type_to_string(api_attribute_type):
    """
    Coverts Maya attribute type as a string
    :param api_attribute_type:
    :return: str
    """

    return _TYPE_TO_STRING.get(api_attribute_type)


def maya_type_from_api_type(api_type):
    """
    Returns Maya type from the given API type
    :param api_type: int
    :return: str
    """

    type_conversion = _MAYA_TYPE_FROM_TYPE.get(api_type)
    if not type_conversion:
        return None, None

    return type_conversion
