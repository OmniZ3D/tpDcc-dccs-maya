#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya exceptions
"""

from __future__ import print_function, division, absolute_import


class MayaLibException(Exception):
    """
    Raise exceptions specific to tpDcc.dccs.maya
    """

    pass


class NodeException(MayaLibException):
    def __init__(self, node, node_type):
        super(NodeException, self).__init__('Object "{0}" is not a valid "{1}" node!'.format(node, node_type))


class NodeExistsException(MayaLibException):
    def __init__(self, node):
        super(NodeExistsException, self).__init__('Node "{}" does not exists!'.format(node))


class DagNodeException(MayaLibException):
    def __init__(self, node):
        super(DagNodeException, self).__init__('Object "{}" is not a valid DAG node!'.format(node))


class TransformException(MayaLibException):
    def __init__(self, node):
        super(TransformException, self).__init__('Object "{}" is not a valid transform node'.format(node))


class GeometryExistsException(MayaLibException):
    def __init__(self, geo):
        super(GeometryExistsException, self).__init__('Geometry "{}" does not exists!'.format(geo))


class GeometryException(MayaLibException):
    def __init__(self, node):
        super(GeometryException, self).__init__('Object "{}" is not a valid geometry!'.format(node))


class ShapeException(MayaLibException):
    def __init__(self, node):
        super(ShapeException, self).__init__('Object "{}" is not a valid shape node'.format(node))


class ShapeHistoryException(MayaLibException):
    def __init__(self, shape):
        super(ShapeHistoryException, self).__init__(
            'Unable to determine history nodes for shape "{}"'.format(shape))


class ShapeFromTransformException(MayaLibException):
    def __init__(self, transform):
        super(ShapeFromTransformException, self).__init__(
            'Unable to determine shape node from transform "{}!"'.format(transform))


class CurveException(MayaLibException):
    def __init__(self, curve):
        super(CurveException, self).__init__('Object "{}" is not a valid curve!'.format(curve))


class NURBSCurveException(MayaLibException):
    def __init__(self, curve):
        super(NURBSCurveException, self).__init__('Object "{}" is not a valid NURBS curve!'.format(curve))


class JointException(MayaLibException):
    def __init__(self, joint):
        super(JointException, self).__init__('Object "{} is not a valid joint!'.format(joint))

# ======================================================================== DEFORMERS


class DeformerException(MayaLibException):
    def __init__(self, node):
        super(DeformerException, self).__init__('Object "{}" is not a valid deformer node!'.format(node))


class DeformerHandleExistsException(MayaLibException):
    def __init__(self):
        super(DeformerHandleExistsException, self).__init__('Unable to find deformer handle!')


class DeformerSetExistsException(MayaLibException):
    def __init__(self, deformer):
        super(DeformerSetExistsException, self).__init__('Unable to determine deformer set for "{}"!'.format(deformer))


class SkinClusterException(MayaLibException):
    def __init__(self, skin_cluster):
        super(SkinClusterException, self).__init__('Object "{}" is not a valid skin cluster!'.format(skin_cluster))


class NotAffectByDeformerException(MayaLibException):
    def __init__(self, geo, deformer):
        super(NotAffectByDeformerException, self).__init__(
            'Object "{}" is not affected by deformer "{}"'.format(geo, deformer))


class GeometryIndexOutOfRange(MayaLibException):
    def __init__(self, deformer, geo, geo_index, total_indices):
        super(GeometryIndexOutOfRange, self).__init__(
            'Geometry index out of range! (Deformer: "{}", Geometry: "{}", GeoIndex: "{}", MaxIndex: "{}"'.format(
                deformer, geo, str(geo_index), str(total_indices)))


class ShapeValidDeformerAffectedException(MayaLibException):
    def __init__(self, shape):
        super(ShapeValidDeformerAffectedException, self).__init__(
            'Shape node "{}" is not affected by any valid deformers!'.format(shape))


# ======================================================================== BLENDSHAPE

class BlendShapeBaseGeometryException(MayaLibException):
    def __init__(self, base, blendshape):
        super(BlendShapeBaseGeometryException, self).__init__(
            'Object "{}" is not a base geometry for blendshape "{}"!'.format(base, blendshape))


class BlendShapeBaseIndexException(MayaLibException):
    def __init__(self, base, blendshape):
        super(BlendShapeBaseIndexException, self).__init__(
            'Unable to determine base index for "{}" on blendShape "{}"!'.format(base, blendshape))


class BlendShapeTargetException(MayaLibException):
    def __init__(self, blenshape, target):
        super(BlendShapeTargetException, self).__init__('Blendshape "{}" has no target "{}"!'.format(blenshape, target))


# ======================================================================== GEOMETRY

class NoShapeChildren(MayaLibException):
    def __init__(self, geo):
        super(NoShapeChildren, self).__init__('Geometry object "{}" has no shape children!'.format(geo))


class UnknownGeometryType(MayaLibException):
    def __init__(self, geo_type):
        super(UnknownGeometryType, self).__init__('Unknown geometry type "{}" is not supported!'.format(geo_type))


# ======================================================================== MESH

class MeshException(MayaLibException):
    def __init__(self, mesh):
        super(MeshException, self).__init__('Object "{}" is not a valid mesh node!'.format(mesh))


class MeshNoUVSetException(MayaLibException):
    def __init__(self, mesh, uv_set):
        super(MeshNoUVSetException, self).__init__('Mesh "{}" has not UV set "{}"'.format(mesh, uv_set))


# ======================================================================== ATTRIBUTES

class AttributeExistsException(MayaLibException):
    def __init__(self, attr):
        super(AttributeExistsException, self).__init__('Attribute "{}" does not exists!'.format(attr))


class InvalidMultiAttribute(MayaLibException):
    def __init__(self, attr):
        super(InvalidMultiAttribute, self).__init__('Attribute "{}" is not a multi!'.format(attr))
