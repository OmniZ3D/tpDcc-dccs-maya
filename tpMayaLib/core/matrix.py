#! /usr/bin/env python

"""
Utility methods related to Maya matrix operations
"""


from __future__ import print_function, division, absolute_import, unicode_literals


import tpMayaLib as maya


def set_matrix_cell(matrix, value, row, column):
    """
    Sets a MMatrix cell
    :param matrix:  MMatrix, matrix to set cell
    :param value: variant, value to set cell
    :param row: int, matrix row number
    :param column: int, matrix, column number
    """

    if maya.is_new_api():
        matrix[row][column] = value
    else:
        maya.OpenMaya.MScriptUtil.setDoubleArray(matrix[row], column, value)


def set_matrix_row(matrix, vector, row):
    """
    Sets a matrix row with an MVector or MPoint
    :param matrix: MMatrix, matrix to set row
    :param vector: MVector || MPoint, vector to set matrix row to
    :param row: int, matrix row number
    """

    set_matrix_cell(matrix, vector.x, row, 0)
    set_matrix_cell(matrix, vector.y, row, 1)
    set_matrix_cell(matrix, vector.z, row, 2)


def build_matrix(translate=(0,0,0), x_axis=(1,0,0), y_axis=(0,1,0), z_axis=(0,0,1)):
    """
    Builds a transformation matrix based on the input vectors
    :param translate: tuple/list, translate values for the matrix
    :param x_axis: tuple/list, X axis of the matrix
    :param y_axis: tuple/list, Y axis of the matrix
    :param z_axis: tuple/list, Z axis of the matrix
    :return: MMatrix
    """

    matrix = maya.OpenMaya.MMatrix()
    values = list()

    if not isinstance(translate, maya.OpenMaya.MVector):
        translate = maya.OpenMaya.MVector(translate[0], translate[1], translate[2])
    if not isinstance(x_axis, maya.OpenMaya.MVector):
        x_axis = maya.OpenMaya.MVector(x_axis[0], x_axis[1], x_axis[2])
    if not isinstance(y_axis, maya.OpenMaya.MVector):
        y_axis = maya.OpenMaya.MVector(y_axis[0], y_axis[1], y_axis[2])
    if not isinstance(z_axis, maya.OpenMaya.MVector):
        z_axis = maya.OpenMaya.MVector(z_axis[0], y_axis[1], y_axis[2])

    set_matrix_row(matrix, x_axis, 0)
    set_matrix_row(matrix, y_axis, 1)
    set_matrix_row(matrix, z_axis, 2)
    set_matrix_row(matrix, translate, 3)

    return matrix
