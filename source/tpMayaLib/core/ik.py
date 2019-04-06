# #! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# """
# Module that contains functions and classes related with IKs
# """
#
# from __future__ import print_function, division, absolute_import
#
# from tpPyUtils import mathlib
#
# from tpRigToolkit.core.tools.nameit import nameit
# from tpRigToolkit.maya.lib import name as name_utils, attribute as attr_utils
#
#
# class IkHandle(object):
#     """
#     Base class to crete and work with IK handles
#     """
#
#     SOLVER_RP = 'ikRPsolver'
#     SOLVER_SC = 'ikSCsolver'
#     SOLVER_SPLINE = 'ikSplineSolver'
#     SOLVER_SPRING = 'ikSpringSolver'
#
#     def __init__(self, name):
#
#         self._name = name
#         self._start_joint = None
#         self._end_joint = None
#         self._solver_type = self.SOLVER_SC
#         self._curve = None
#
#         self._ik_handle = None
#         self._ik_effector = None
#         self._joints = list()
#
#     # region Public Functions
#     def set_start_joint(self, joint):
#         """
#         Set start joint for IK handle to use
#         :param joint: str, name of the start joint
#         """
#
#         self._start_joint = joint
#
#     def set_end_joint(self, joint):
#         """
#         Set end joint for IK handle to use
#         :param joint: str, name of the end joint
#         """
#
#         self._end_joint = joint
#
#     def set_joints(self, joints_list):
#         """
#         Sets  the ojints for the IK handle to use
#         First entry of the list is the start joint and the last entry is the end joint
#         :param joints_list: list<str>, a list of joints
#         """
#
#         self._start_joint = joints_list[0]
#         self._end_joint = joints_list[-1]
#         self._joints = joints_list
#
#     def set_curve(self, curve):
#         """
#         Sets teh curve for Spline IK handle to use
#         :param curve: str, name of the curve
#         """
#
#         if type(curve) in [list, tuple]:
#             self._curve = curve[0]
#         else:
#             self._curve = curve
#
#     def set_solver(self, solver_name):
#         """
#         Sets the solver type for the IK handle to use
#         :param solver_name: str, name of the solver type to use:
#             'ikRPsolver'
#             'ikSCsolver'
#             'ikSplineSolver'
#             'ikSpringSolver'
#         """
#
#         self._solver_type = solver_name
#
#     def set_full_name(self, full_name):
#         """
#         Sets the full name for the IK handle to use
#         :param full_name: str
#         """
#
#         self._name = full_name
#
#     def create(self):
#         """
#         Creates IK handle with the store atrributes
#         :return: str, name of thre IK handle
#         """
#
#         if not self._start_joint or not self._end_joint:
#             return
#
#         if not self._curve and not self._solver_type == self.SOLVER_SPLINE:
#             self._create_regular_ik()
#
#         if self._curve or self._solver_type == self.SOLVER_SPLINE:
#             self._solver_type = self.SOLVER_SPLINE
#             self._create_spline_ik()
#
#         return self._ik_handle
#     # endregion
#
#     # region Private Functions
#     def _create_regular_ik(self):
#         ik_handle, ik_effector = cmds.ikHandle(
#             name=name_utils.find_unique_name(self._name),
#             startJoint=self._start_joint,
#             endEffector=self._end_joint,
#             sol=self._solver_type
#         )
#         cmds.rename(ik_effector, name_utils.find_unique_name('effector_{}'.format(ik_handle)))
#         self._ik_handle = ik_handle
#         self._ik_effector = ik_effector
#
#     def _create_spline_ik(self):
#         if self._curve:
#             ik_handle = cmds.ikHandle(
#                 name=name_utils.find_unique_name(self._name),
#                 startJoint=self._start_joint,
#                 endEffector=self._end_joint,
#                 sol=self._solver_type,
#                 curve=self._curve,
#                 ccv=False,
#                 pcv=False
#             )
#             cmds.rename(ik_handle[1], 'effector_{}'.format(ik_handle[0]))
#             self._ik_handle = ik_handle[0]
#             self._ik_effector = ik_handle[1]
#         else:
#             ik_handle = cmds.ikHandle(
#                 name=name_utils.find_unique_name(self._name),
#                 startJoint=self._start_joint,
#                 endEffector=self._end_joint,
#                 sol=self._solver_type,
#                 scv=False,
#                 pcv=False
#             )
#             cmds.rename(ik_handle[1], 'effector_{}'.format(ik_handle[0]))
#             self._ik_handle = ik_handle[0]
#             self._ik_effector = ik_handle[1]
#             self._curve = ik_handle[2]
#             self._curve = cmds.rename(self._curve, name_utils.find_unique_name('curve_{}'.format(self._name)))
#     # endregion
#
#
# def create_spline_ik_stretch(curve, joints, prefix_name=None, node_for_attribute=None, create_stretch_on_off=False, create_bulge=True, scale_axis='X'):
#     """
#     Makes the joints stretch on the curve
#     :param curve: str, name of the curve that joints are attached via Spline IK
#     :param joints: list<str>, list of joints attached to Spline IK
#     :param node_for_attribute: str, name of the node to create the attributes on
#     :param create_stretch_on_off: bool, Whether to create or not extra attributes to slide the stretch value on/off
#     :param create_bulge: bool, Whether to add bulging to the other axis that are not the scale axis
#     :param scale_axis: str('X', 'Y', 'Z'), axis that the joints stretch on
#     """
#
#     if prefix_name is None:
#         prefix_name = curve
#
#     if scale_axis == 0:
#         scale_axis = 'X'
#     elif scale_axis == 1:
#         scale_axis = 'Y'
#     elif scale_axis == 2:
#         scale_axis = 'Z'
#     else:
#         scale_axis = scale_axis.capitalize()
#
#     current_rule = nameit.NameIt.get_active_rule()
#     if current_rule:
#         name = nameit.NameIt.solve('{}_stretch'.format(prefix_name), type='arcLength')
#     else:
#         name = 'curveInfo_{}'.format(prefix_name)
#
#     arclen_node = cmds.arclen(curve, ch=True, n=name_utils.find_unique_name(name))
#     arclen_node = cmds.rename(arclen_node, name_utils.find_unique_name(name))
#
#     if current_rule:
#         name1 = nameit.NameIt.solve('{}_stretch_offset'.format(prefix_name), type='multiplyDivide')
#         name2 = nameit.NameIt.solve('{}_stretch'.format(prefix_name), type='multiplyDivide')
#     else:
#         name1 = 'multiplyDivide_offset_{}'.format(arclen_node)
#         name2 = 'multiplyDivide_{}'.format(arclen_node)
#
#     multiply_scale_offset = cmds.createNode('multiplyDivide', n=name_utils.find_unique_name(name1))
#     multiply = cmds.createNode('multiplyDivide', n=name_utils.find_unique_name(name2))
#
#     cmds.setAttr('{}.operation'.format(multiply_scale_offset), 2)
#     cmds.connectAttr('{}.arcLength'.format(arclen_node), '{}.input1X'.format(multiply_scale_offset))
#     cmds.connectAttr('{}.outputX'.format(multiply_scale_offset), '{}.input1X'.format(multiply))
#     cmds.setAttr('{}.input2X'.format(multiply), cmds.getAttr('{}.arcLength'.format(arclen_node)))
#     cmds.setAttr('{}.operation'.format(multiply), 2)
#
#     joint_count = len(joints)
#     segment = 1.00/joint_count
#     percent = 0
#
#     for jnt in joints:
#         mult_attr = '{}.outputX'.format(multiply)
#         if create_stretch_on_off and node_for_attribute:
#             attr = attr_utils.NumericAttribute('stretchOnOff')
#             attr.set_min_value(0)
#             attr.set_max_value(1)
#             attr.set_keyable(True)
#             attr.create(node_for_attribute)
#
#             if current_rule:
#                 blend_name = nameit.NameIt.solve('{}_stretch_switch'.format(prefix_name), type='blendColors')
#             else:
#                 blend_name = 'blendColors_stretchOnOff_{}'.format(curve)
#
#             blend = cmds.createNode('blendColors', n=blend_name)
#             cmds.connectAttr(mult_attr, '{}.color1R'.format(blend))
#             cmds.setAttr('{}.color2R'.format(blend), 1)
#             cmds.connectAttr('{}.outputR'.format(blend), '{}.scale{}'.format(jnt, scale_axis))
#             cmds.connectAttr('{}.stretchOnOff'.format(node_for_attribute), '{}.blender'.format(blend))
#
#         if not create_stretch_on_off:
#             cmds.connectAttr(mult_attr, '{}.scale{}'.format(jnt, scale_axis))
#
#         if create_bulge:
#             if current_rule:
#                 plus_name = nameit.NameIt.solve('{}_bulge_scale'.format(jnt), type='plusMinusAverage')
#             else:
#                 plus_name = 'plusMinusAverage_bulge_scale_{}'.format(jnt)
#             plus = cmds.createNode('plusMinusAverage', n=plus_name)
#             cmds.addAttr(plus, ln='scaleOffset', dv=1, k=True)
#             cmds.addAttr(plus, ln='bulge', dv=1, k=True)
#             arc_value = mathlib.fade_sine(percent)
#             attr_utils.connect_multiply('{}.outputX'.format(multiply_scale_offset), '{}.bulge'.format(plus), arc_value)
#             attr_utils.connect_plus('{}.scaleOffset'.format(plus), '{}.input1D[0]'.format(plus))
#             attr_utils.connect_plus('{}.bulge'.format(plus), '{}.input1D[1]'.format(plus))
#             scale_value = cmds.getAttr('{}.output1D'.format(plus))
#
#             if current_rule:
#                 mult_offset_name = nameit.NameIt.solve('{}_bulge_multiply'.format(jnt), type='plusMinusAverage')
#             else:
#                 mult_offset_name = 'multiply_{}'.format(jnt)
#             multiply_offset = cmds.createNode('multiplyDivide', n=mult_offset_name)
#             cmds.setAttr('{}.operation'.format(multiply_offset), 2)
#             cmds.setAttr('{}.input1X'.format(multiply_offset), scale_value)
#             cmds.connectAttr('{}.output1D'.format(plus), '{}.input2X'.format(multiply_offset))
#
#             if current_rule:
#                 blend_name = nameit.NameIt.solve('{}_bulge_blend'.format(jnt), type='blendColors')
#             else:
#                 blend_name = 'blendColors_{}'.format(jnt)
#             blend = cmds.createNode('blendColors', n=blend_name)
#             blend_attr = '{}.outputR'.format(blend)
#
#             if node_for_attribute:
#                 cmds.connectAttr('{}.outputX'.format(multiply_offset), '{}.color1R'.format(blend))
#                 cmds.setAttr('{}.color2R'.format(blend), 1)
#                 attr = attr_utils.NumericAttribute('stretchyBulge')
#                 attr.set_min_value(0)
#                 attr.set_max_value(10)
#                 attr.set_keyable(True)
#                 attr.create(node_for_attribute)
#                 attr_utils.connect_multiply('{}.stretchyBulge'.format(node_for_attribute), '{}.blender'.format(blend), 0.1)
#             else:
#                 blend_attr = '{}.outputX'.format(multiply_offset)
#
#             if scale_axis == 'X':
#                 cmds.connectAttr(blend_attr, '%s.scaleY' % jnt)
#                 cmds.connectAttr(blend_attr, '%s.scaleZ' % jnt)
#             if scale_axis == 'Y':
#                 cmds.connectAttr(blend_attr, '%s.scaleX' % jnt)
#                 cmds.connectAttr(blend_attr, '%s.scaleZ' % jnt)
#             if scale_axis == 'Z':
#                 cmds.connectAttr(blend_attr, '%s.scaleX' % jnt)
#                 cmds.connectAttr(blend_attr, '%s.scaleY' % jnt)
#
#         percent += segment
#
