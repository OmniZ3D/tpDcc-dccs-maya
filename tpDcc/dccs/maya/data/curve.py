# #! /usr/bin/env python
# # -*- coding: utf-8 -*-
#
# """
# This module include data class for curves
# """
#
# from __future__ import print_function, division, absolute_import
#
# import logging
#
# import maya.cmds
# import maya.api.OpenMaya
#
# from tpDcc.core import data
# from tpDcc.dccs.maya.core import exceptions, curve as curve_utils
#
# LOGGER = logging.getLogger('tpDcc-dccs-maya')
#
#
# class CurveData(data.Data, object):
#     def __init__(self, curve=''):
#         super(CurveData, self).__init__()
#
#         self._curve = curve
#         self.world_space = False
#
#         if self._curve:
#             self.build_data()
#
#     def build_data(self):
#         """
#         Data is build from the given scene objects
#         """
#
#         if not self._curve:
#             LOGGER.exception('No Curves Given')
#
#         if type(self._curve) not in [list, tuple]:
#             self._curve = [self._curve]
#
#         shapes = maya.cmds.listRelatives(self._curve, shapes=True, pa=True) or []
#         curves = maya.cmds.ls(shapes, type='nurbsCurve')
#         curves += maya.cmds.ls(curves, type='nurbsCurve') or []
#         if not curves:
#             return
#
#         # Reset data
#         self.reset()
#
#         # Get Curve Data
#         for crv in curves:
#
#             # Data we want to store
#             cv_array = list()
#             world_cv_array = list()
#             knot_settings = list()
#             knot_settings_world = list()
#
#             curve_fn = curve_utils.get_curve_fn(curve=crv)
#
#             point_array = curve_fn.cvPositions(maya.api.OpenMaya.MSpace.kObject)
#             world_point_array = curve_fn.cvPositions(maya.api.OpenMaya.MSpace.kWorld)
#
#             point_array_length = point_array.length() if hasattr(point_array, 'length') else len(point_array)
#             for i in range(point_array_length):
#                 cv_array.append([point_array[i].x, point_array[i].y, point_array[i].z])
#                 world_cv_array.append([world_point_array[i].x, world_point_array[i].y, world_point_array[i].z])
#
#         # ===========================================================================================================
#
#             # # Get Bezier Curve Data
#             # temp_crv = maya.cmds.duplicate(curve)[0]
#             # maya.cmds.select(temp_crv)
#             # maya.cmds.nurbsCurveToBezier()
#             # maya.cmds.delete(temp_crv, ch=True)
#             #
#             # b_shapes = maya.cmds.listRelatives(temp_crv, shapes=True, pa=True) or []
#             # b_curves = maya.cmds.ls(b_shapes, type='bezierCurve')
#             # b_curves += maya.cmds.ls(b_curves, type='bezierCurve') or []
#             # if not curves:
#             #     maya.cmds.delete(temp_crv)
#             #     return
#             #
#             # for b_crv in b_curves:
#             #     curve_fn = curve_utils.get_curve_fn(curve=b_crv)
#             #     point_array = OpenMaya.MPointArray()
#             #     world_point_array = OpenMaya.MPointArray()
#             #     curve_fn.getCVs(point_array, OpenMaya.MSpace.kObject)
#             #     curve_fn.getCVs(world_point_array, OpenMaya.MSpace.kWorld)
#             #
#             #     first_cv = dict()
#             #     world_first_cv = dict()
#             #     temp_list = list()
#             #     world_temp_list = list()
#             #
#             #     # Loop all CVs to store the info of the first CV with its in/out handles positions
#             #     for i in range(point_array.length()-1):
#             #         if i == 0:
#             #             first_cv['cv'] = [point_array[i].x, point_array[i].y, point_array[i].z]
#             #             world_first_cv['cv'] = [
#             #             world_point_array[i].x, world_point_array[i].y, world_point_array[i].z]
#             #         elif i==1:
#             #             first_cv['in'] = [point_array[i].x, point_array[i].y, point_array[i].z]
#             #             world_first_cv['in'] = [
#             #             world_point_array[i].x, world_point_array[i].y, world_point_array[i].z]
#             #         elif i == point_array.length()-2:
#             #             first_cv['out'] = [point_array[i].x, point_array[i].y, point_array[i].z]
#             #             world_first_cv['out'] = [
#             #             world_point_array[i].x, world_point_array[i].y, world_point_array[i].z]
#             #         else:
#             #             temp_list.append([point_array[i].x, point_array[i].y, point_array[i].z])
#             #             world_temp_list.append(
#             #             [world_point_array[i].x, world_point_array[i].y, world_point_array[i].z])
#             #
#             #     knots_info = izip(temp_list, temp_list, temp_list)
#             #     knots_info_world = izip(world_temp_list, world_temp_list, world_temp_list)
#             #
#             #     for in_handle, cv, out_handle in knots_info:
#             #         knot_dict = dict()
#             #         knot_dict['in'] = in_handle
#             #         knot_dict['cv'] = cv
#             #         knot_dict['out'] = out_handle
#             #         knot_settings.append(knot_dict)
#             #
#             #     for in_handle, cv, out_handle in knots_info_world:
#             #         knot_dict = dict()
#             #         knot_dict['in'] = in_handle
#             #         knot_dict['cv'] = cv
#             #         knot_dict['out'] = out_handle
#             #         knot_settings_world.append(knot_dict)
#             #
#             #     knot_settings.insert(0, first_cv)
#             #     knot_settings_world.insert(0, world_first_cv)
#             #
#             # maya.cmds.delete(temp_crv)
#
#             # self._data[crv] = [cv_array, world_cv_array, knot_settings, knot_settings_world]
#             self._data[crv] = [cv_array, world_cv_array]
#
#         return curves
#
#     def rebuild(self, controls=[]):
#         """
#         Rebuild curve from already build data
#         :param controls: list<str>, list of controls curve shapes to rebuild
#         """
#
#         data_keys = self._data.keys()
#         if not data_keys:
#             return
#
#         if not controls:
#             controls = data_keys
#         if type(controls) not in [list, tuple]:
#             controls = [controls]
#
#         for ctrl in controls:
#             if not maya.cmds.objExists(ctrl):
#                 LOGGER.warning('CurveData: Curve Shape "{}" does not exists!'.format(ctrl))
#                 continue
#             if not data_keys.count(ctrl):
#                 LOGGER.warning('CurveData: No Data for Curve Shape "{}"'.format(ctrl))
#                 continue
#
#             point_array = maya.api.OpenMaya.MPointArray()
#             if self.world_space:
#                 crv = self._data[ctrl][1]
#             else:
#                 crv = self._data[ctrl][0]
#
#             for cv in crv:
#                 point_array.append(maya.api.OpenMaya.MPoint(cv[0], cv[1], cv[2], 1.0))
#
#             curve_fn = curve_utils.get_curve_fn(curve=ctrl)
#             if self.world_space:
#                 curve_fn.setCVs(point_array, maya.api.OpenMaya.MSpace.kWorld)
#             else:
#                 curve_fn.setCVs(point_array, maya.api.OpenMaya.MSpace.kObject)
#
#             curve_fn.updateCurve()
#
#         return controls
#
#
# class NurbsCurveData(CurveData, object):
#     def __init__(self, curve=''):
#         super(NurbsCurveData, self).__init__()
#
#         self._curve = curve
#         self.world_space = False
#
#         # Initialize NURBS curve data
#         self._data['name'] = ''
#         self._data['cv'] = list()
#         self._data['editPt'] = list()
#         self._data['knots'] = list()
#         self._data['degree'] = 0
#         self._data['form'] = 0
#         self._data['2d'] = False
#         self._data['rational'] = True
#
#         if self._curve:
#             self.build_data()
#
#     # def build_data(self):
#     #     """
#     #     Data is build from the given scene objects
#     #     """
#     #
#     #     if not self._curve:
#     #         LOGGER.exception('No Curve Given')
#     #
#     #     if not curve_utils.is_curve(curve=self._curve):
#     #         raise exceptions.NURBSCurveException(curve=self._curve)
#     #
#     #     space = maya.api.OpenMaya.MSpace.kObject
#     #     if self.world_space:
#     #         space = maya.api.OpenMaya.MSpace.kWorld
#     #
#     #     timer = maya.cmds.timerX()
#     #
#     #     curve_fn = curve_utils.get_curve_fn(curve=self._curve)
#     #
#     #     self._data['name'] = self._curve
#     #
#     #     knot_array = curve_fn.knots()
#     #     cv_array = curve_fn.cvs(space)
#     #     cv_length = len(cv_array)
#     #     self._data['degree'] = curve_fn.degree
#     #     self._data['form'] = int(curve_fn.form)
#     #
#     #     self._data['knots'] = list(knot_array)
#     #     self._data['cvs'] = [(cv_array[i].x, cv_array[i].y, cv_array[i].z) for i in range(cv_length)]
#     #
#     #     for u in self._data['knots']:
#     #         edit_pt = curve_fn.getPointAtParam(u, space)
#     #         self._data['editPt'].append((edit_pt.x, edit_pt.y, edit_pt.z))
#     #
#     #     build_time = maya.cmds.timerX(st=timer)
#     #     LOGGER.debug(
#     #         'NurbsCurveData: Data build time for curve "{}" : {}'.format(self._data['name'], str(build_time)))
#     #
#     #     return self._data['name']
#
#     def rebuild(self):
#         timer = maya.cmds.timerX()
#
#         num_cvs = len(self._data['cvs'])
#         num_knots = len(self._data['knots'])
#
#         cv_array = maya.api.OpenMaya.MPointArray(num_cvs, maya.api.OpenMaya.MPoint.kOrigin)
#         knots = maya.api.OpenMaya.MDoubleArray(num_knots, 0)
#         for i in range(num_cvs):
#             cv_array[i] = maya.api.OpenMaya.MPoint(
#                 self._data['cvs'][i][0], self._data['cvs'][i][1], self._data['cvs'][i][2], 1.0)
#         for i in range(num_knots):
#             knots[i] = self._data[knots][i]
#
#         curve_fn = maya.api.OpenMaya.MFnNurbsCurve()
#         curve_data = maya.api.OpenMaya.MFnNurbsCurveData().create()
#         curve_obj = curve_fn.create(
#             cv_array,
#             knots,
#             self._data['degree'],
#             self._data['form'],
#             self._data['2d'],
#             self._data['rational'],
#             curve_data
#         )
#
#         curve_obj_handle = maya.api.OpenMaya.MObjectHandle(curve_obj)
#
#         build_time = maya.cmds.timerX(st=timer)
#         LOGGER.debug(
#             'NurbsCurveData: Data rebuild time for curve "{}" : {}'.format(self._data['name'], str(build_time)))
#
#         return curve_obj_handle
#
#     def rebuild_curve(self):
#         timer = maya.cmds.timerX()
#
#         num_cvs = len(self._data['cvs'])
#         num_knots = len(self._data['knots'])
#
#         cv_array = maya.api.OpenMaya.MPointArray(num_cvs, maya.api.OpenMaya.MPoint.kOrigin)
#         knots = maya.api.OpenMaya.MDoubleArray(num_knots, 0)
#         for i in range(num_cvs):
#             cv_array[i] = maya.api.OpenMaya.MPoint(
#                 self._data['cvs'][i][0], self._data['cvs'][i][1], self._data['cvs'][i][2], 1.0)
#         for i in range(num_knots):
#             knots[i] = self._data[knots][i]
#
#         curve_fn = maya.api.OpenMaya.MFnNurbsCurve()
#         curve_data = maya.api.OpenMaya.MObject()
#         curve_obj = curve_fn.create(
#             cv_array,
#             knots,
#             self._data['degree'],
#             self._data['form'],
#             self._data['2d'],
#             self._data['rational'],
#             curve_data
#         )
#
#         crv = maya.api.OpenMaya.MFnDependencyNode(curve_obj).setName(self._data['name'])
#
#         build_time = maya.cmds.timerX(st=timer)
#         LOGGER.debug(
#             'NurbsCurveData: Curve rebuild time for curve "{}" : {}'.format(self._data['name'], str(build_time)))
