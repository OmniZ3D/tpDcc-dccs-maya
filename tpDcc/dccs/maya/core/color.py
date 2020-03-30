#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with colors
"""

from __future__ import print_function, division, absolute_import

from Qt.QtGui import *


# ==== Control Colors
CONTROL_COLORS = []
for color in [(.467, .467, .467), [.000, .000, .000], (.247, .247, .247), (.498, .498, .498), (0.608, 0, 0.157),
              (0, 0.016, 0.373), (0, 0, 1), (0, 0.275, 0.094), (0.145, 0, 0.263), (0.78, 0, 0.78), (0.537, 0.278, 0.2),
              (0.243, 0.133, 0.122), (0.6, 0.145, 0), (1, 0, 0), (0, 1, 0), (0, 0.255, 0.6), (1, 1, 1), (1, 1, 0),
              (0.388, 0.863, 1), (0.263, 1, 0.635), (1, 0.686, 0.686), (0.89, 0.675, 0.475), (1, 1, 0.384),
              (0, 0.6, 0.325), (0.627, 0.412, 0.188), (0.62, 0.627, 0.188), (0.408, 0.627, 0.188),
              (0.188, 0.627, 0.365), (0.188, 0.627, 0.627), (0.188, 0.404, 0.627), (0.435, 0.188, 0.627),
              (0.627, 0.188, 0.404)]:
    CONTROL_COLORS.append(color)


class MayaWireColors(object):
    """
    Class that defines predefined colors of Maya wireframe
    """

    Orange = 1
    DarkYellow = 2
    LightGreen = 3
    Green = 4
    LightBlue = 5
    Blue = 6
    Purple = 7
    Pink = 8


def get_color(color):
    """
    Returns a valid QColor from the given color
    :param color: variant, list || tuple || QColor
    :return: QColor
    """

    if type(color) == QColor:
        return color
    else:
        return QColor.fromRgba(*color)


def get_rig_color(rig_type='fk', side='center'):
    """
    Return a color given a rig type
    :param rig_type: str, Rig type ('fk' or 'ik')
    :param side: str, Rig side ('left', 'right', or 'center')
    """

    if rig_type == 'fk' or rig_type == 'FK':
        if side == 'left' or side == 'Left' or side == 'L' or side == 'l' or side == 'Lt':
            cl = QColor.fromRgbF(0.7, 0.4, 0.7)
            cl.ann = 'LtFK Color'
        elif side == 'right' or side == 'Right' or side == 'R' or side == 'r' or side == 'Rt':
            cl = QColor.fromRgbF(0.7, 0.4, 0.4)
            cl.ann = 'RtFK Color'
        else:
            cl = QColor.fromRgbF(0.7, 0.7, 0.4)
            cl.ann = 'CnFK Color'
    elif rig_type == 'ik' or rig_type == 'IK':
        if side == 'left' or side == 'Left' or side == 'L' or side == 'l' or side == 'Lt':
            cl = QColor.fromRgbF(0.4, 0.5, 0.7)
            cl.ann = 'LtIK Color'
        elif side == 'right' or side == 'Right' or side == 'R' or side == 'r' or side == 'Rt':
            cl = QColor.fromRgbF(0.7, 0.4, 0.7)
            cl.ann = 'RtIK Color'
        else:
            cl = QColor.fromRgbF(0.4, 0.7, 0.4)
            cl.ann = 'CnIK Color'
    return cl


def get_mirror_rig_color_by_type(rig_type='fk', side='center'):
    """
    Returns a mirror color given a  type and a side
    :param rig_type: str, Rig type ('fk' or 'ik')
    :param side: str, Rig side ('left', 'right', or 'center')
    """

    rig_colors = dict()
    for rig_type in ['fk', 'ik']:
        rig_colors[rig_type] = dict
        for side in ['left', 'right', 'center']:
            rig_colors[dict][side] = get_rig_color(rig_type=rig_type, side=side)

    if side == 'left':
        mirror_side = 'right'
    elif side == 'right':
        mirror_side = 'left'
    else:
        mirror_side = side

    try:
        return rig_colors[rig_type][mirror_side]
    except Exception:
        return rig_colors['fk']['center']


def get_mirror_rig_color_by_color(cl):
    """
    Returns a rig mirror color from a given color. If the color is not found in the mirror colors
    the function will return the complementary color of the given color
    :param cl: QColor
    """

    from tpDcc.libs.qt.core import color as color_utils

    rig_colors = dict()
    for rig_type in ['fk', 'ik']:
        rig_colors[rig_type] = dict
        for side in ['left', 'right', 'center']:
            rig_colors[dict][side] = get_rig_color(rig_type=rig_type, side=side)

    for rig_type, side_colors in rig_colors.items():
        for side, rig_color in side_colors.items():
            if side == 'left':
                mirror_side = 'right'
            elif side == 'right':
                mirror_side = 'left'
            else:
                mirror_side = side
            if cl == rig_color:
                return rig_colors[rig_type][mirror_side]
            elif cl == rig_color.lighter():
                return rig_colors[rig_type][mirror_side].lighter()
            elif cl == rig_color.darker():
                return rig_colors[rig_type][mirror_side].darker()
            else:
                return color_utils.Color.get_complementary_color(cl)
