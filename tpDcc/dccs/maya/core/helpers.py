#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya utility functions and classes
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import stat
import shutil

from tpDcc.libs.python import python
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import time, gui


class SelectionMasks(object):
    """
    https://help.autodesk.com/cloudhelp/2017/ENU/Maya-Tech-Docs/CommandsPython/filterExpand.html
    """

    Handle = 0
    NurbsCurves = 9
    NurbsSurfaces = 10
    NurbsCurvesOnSurface = 11
    Polygon = 12
    LocatorXYZ = 22
    OrientationLocator = 23
    LocatorUV = 24
    ControlVertices = 28
    CVs = 28
    EditPoints = 30
    PolygonVertices = 31
    PolygonEdges = 32
    PolygonFace = 34
    PolygonUVs = 35
    SubdivisionMeshPoints = 36
    SubdivisionMeshEdges = 37
    SubdivisionMeshFaces = 38
    CurveParameterPoints = 39
    CurveKnot = 40
    SurfaceParameterPoints = 41
    SurfaceKnot = 42
    SurfaceRange = 43
    TrimSurfaceEdge = 44
    SurfaceIsoparms = 45
    LatticePoints = 46
    Particles = 47
    ScalePivots = 49
    RotatePivots = 50
    SelectHandles = 51
    SubdivisionSurface = 68
    PolygonVertexFace = 70
    NurbsSurfaceFace = 72
    SubdivisionMeshUVs = 73


def get_up_axis():
    """
    Returns up axis of the Maya scene
    :return: str, ('y' or 'z')
    """

    return maya.cmds.upAxis(axis=True, query=True)


def create_group(name, nodes=None, world=False, parent=None):
    """
    Creates new group with the given names
    :param name: str, name of the group
    :param nodes: bool
    :param world: bool
    :param parent: str, parent node of the group
    :return:
    """

    if not name:
        return

    nodes = python.force_list(nodes)

    name = python.force_list(name)
    parent = python.force_list(parent)
    if parent:
        parent = parent[0]

    found = list()

    for n in name:
        if not maya.cmds.objExists(n):
            if world:
                if nodes:
                    n = maya.cmds.group(*nodes, name=n, world=True)
                else:
                    n = maya.cmds.group(name=n, empty=True, world=True)
            else:
                if nodes:
                    n = maya.cmds.group(*nodes, name=n)
                else:
                    n = maya.cmds.group(name=n, empty=True)

        if parent and maya.cmds.objExists(parent):
            actual_parent = maya.cmds.listRelatives(n, p=True)
            if actual_parent:
                actual_parent = actual_parent[0]
            if parent != actual_parent:
                maya.cmds.parent(n, parent)

        found.append(n)

    return found


def get_selection_iterator():
    """
    Returns an iterator of Maya objects currently selected
    :return: iterator
    """

    selection = maya.OpenMaya.MSelectionList()
    maya.OpenMaya.MGlobal.getActiveSelectionList(selection)
    selection_iter = maya.OpenMaya.MItSelectionList(selection)
    while not selection_iter.isDone():
        obj = maya.OpenMaya.MObject()
        selection_iter.getDependNode(obj)
        yield obj
        selection_iter.next()


def selection_to_list():
    """
    Returns the currenet maya selection in a list form
    :return: list(variant)
    """

    selected_objs = (maya.cmds.ls(sl=True, flatten=True))
    return selected_objs


def get_objects_of_mtype_iterator(object_type):
    """
    Returns a iterator of Maya objects filtered by object type
    :param object_type: enum value used to identify Maya objects
    :return: SceneObject:_abstract_to_native_object_type
    """

    if not isinstance(object_type, (tuple, list)):
        object_type = [object_type]
    for obj_type in object_type:
        obj_iter = maya.OpenMaya.MItDependencyNodes(obj_type)
        while not obj_iter.isDone():
            yield obj_iter.thisNode()
            obj_iter.next()


def get_current_time_unit():

    """
    Returns the current time unit name
    :return:  str, name of the current fps
    """

    return maya.cmds.currentUnit(query=True, time=True)


def create_mtime(value, unit=None):

    """
    Constructs an OpenMaya.MTime with the provided value. If unit is None, unit is set to the
    current unit setting in Maya
    :param value: time value
    :param unit: int, Time unit value
    :return: OpenMaya.MTime
    """

    if unit is None:
        unit = get_current_time_unit()
    return maya.OpenMaya.MTime(value, time.fps_to_mtime[unit])


def get_mfn_apy_type_map():

    """
    Returns a dictionary mapping all apiType values to their apiTypeStr
    A few values have duplicate keys so the names are inside a list.
    :return: dict, A dict mapping int values to list of OpenMaya.MFn constant names
    """

    out = dict()
    for name in dir(maya.OpenMaya.MFn):
        value = getattr(maya.OpenMaya.MFn, name)
        if name.startswith('k'):
            out.setdefault(value, []).append(name)

    return out


def get_maya_version():
    """
    Returns version of the executed Maya, or 0 if not Maya version is found
    @returns: int, Version of Maya
    """

    return int(maya.cmds.about(version=True))


def get_maya_api_version():
    """
    Returns the Maya version
    @returns: int, Version of Maya
    """

    return int(maya.cmds.about(api=True))


def get_global_variable(var_name):
    """
    Returns the value of a MEL global variable
    @param var_name: str, name of the MEL global variable
    """

    return maya.mel.eval("$tempVar = {0}".format(var_name))


def get_maya_python_interpreter_path():
    """
    Returns the path to Maya Python interpretet path
    :return: str
    """

    return str(sys.executable).replace('maya.exe', 'mayapy.exe')


def error(message, prefix=''):
    """
    Shows an error message on output
    :param message: str, Error message to show
    :param prefix: str, Prefix to the erros message
    """

    if len(message) > 160:
        print(message)
        maya.cmds.error(prefix + ' | ' + 'Check Maya Console for more information!')
        return False
    maya.cmds.error(prefix + ' | {0}'.format(message))
    return False


def warning(message, prefix=''):
    """
    Shows a warning message on output
    :param message: str, Warning message to show
    :param prefix: str, Prefix to the warning message
    """

    if len(message) > 160:
        print(message)
        maya.cmds.warning(prefix + ' | ' + 'Check Maya Console for more information!')
        return True
    maya.cmds.warning(prefix + ' | {0}'.format(message))
    return True


def add_button_to_current_shelf(enable=True,
                                name="tpShelfButton",
                                width=234,
                                height=34,
                                manage=True,
                                visible=True,
                                annotation="",
                                label="",
                                image1="commandButton.png",
                                style="iconAndTextCentered",
                                command="",
                                check_if_already_exists=True):
    """
    Adds a new button to the current selected Maya shelf
    :param enable: bool, True if the new button should be enabled or not
    :param name:  str, Name of the button
    :param width: int, Width for the new button
    :param height: int, Height for the new window
    :param manage: bool
    :param visible: bool, True if the button should be vsiible
    :param annotation: str, Annotation for the new shelf button
    :param label: str, Label of the button
    :param image1: str, Image name of the button icon
    :param style: str, style for the shelf button
    :param command: str, command that the button should execute
    :param check_if_already_exists: bool, True if you want to check if that button already exists in the shelf
    """

    if check_if_already_exists:
        curr_shelf = gui.get_current_shelf()
        shelf_buttons = maya.cmds.shelfLayout(curr_shelf, ca=True, query=True)
        for shelf_btn in shelf_buttons:
            if maya.cmds.control(shelf_btn, query=True, docTag=True):
                doc_tag = maya.cmds.control(shelf_btn, query=True, docTag=True)
                if doc_tag == name:
                    return
    maya.cmds.shelfButton(
        parent=gui.get_current_shelf(), enable=True, width=34, height=34, manage=True,
        visible=True, annotation=annotation, label=label, image1=image1, style=style, command=command)


def set_tool(name):
    """
    Sets the current tool (translate, rotate, scale) that is being used inside Maya viewport
    @param name: str, name of the tool to select: 'move', 'rotate', or 'scale'
    """

    context_lookup = {
        'move': "$gMove",
        'rotate': "$gRotate",
        'scale': "$gSacle"
    }
    tool_context = get_global_variable(context_lookup[name])
    maya.cmds.setToolTo(tool_context)


def in_view_log(color='', *args):
    """
    Logs some info into the Maya viewport
    :param color: color to use in the text
    :param args: text concatenation to show
    """

    text = ''
    for item in args:
        text += ' '
        text += str(item)

    if color != '':
        text = "<span style=\"color:{0};\">{1}</span>".format(color, text)

    maya.cmds.inViewMessage(amg=text, pos='topCenter', fade=True, fst=1000, dk=True)


def display_info(info_msg):
    """
    Displays info message in Maya
    :param info_msg: str, info text to display
    """

    info_msg = info_msg.replace('\n', '\ntp:\t\t')
    maya.OpenMaya.MGlobal.displayInfo('tp:\t\t' + info_msg)
    maya.logger.debug('\n{}'.format(info_msg))


def display_warning(warning_msg):
    """
    Displays warning message in Maya
    :param warning_msg: str, warning text to display
    """

    warning_msg = warning_msg.replace('\n', '\ntp:\t\t')
    maya.OpenMaya.MGlobal.displayWarning('tp:\t\t' + warning_msg)
    maya.logger.warning('\n{}'.format(warning_msg))


def display_error(error_msg):
    """
    Displays error message in Maya
    :param error_msg: str, error text to display
    """

    error_msg = error_msg.replace('\n', '\ntp:\t\t')
    maya.OpenMaya.MGlobal.displayError('tp:\t\t' + error_msg)
    maya.logger.error('\n{}'.format(error_msg))


def file_has_student_line(filename):
    """
    Returns True if the given Maya file has a student license on it
    :param filename: str
    :return: bool
    """

    if not os.path.exists(filename):
        maya.logger.error('File "{}" does not exists!'.format(filename))
        return False

    if filename.endswith('.mb'):
        maya.logger.warning('Student License Check is not supported in binary files!')
        return True

    with open(filename, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if 'createNode' in line:
            return False
        if 'fileInfo' in line and 'student' in line:
            return True

    return False


def clean_student_line(filename=None):
    """
    Clean the student line from the given Maya file name
    :param filename: str
    """

    changed = False

    if not filename:
        filename = maya.cmds.file(query=True, sn=True)

    if not os.path.exists(filename):
        maya.logger.error('File "{}" does not exists!'.format(filename))
        return False

    if not file_has_student_line(filename=filename):
        maya.logger.info('File is already cleaned: no student line found!')
        return False

    if not filename.endswith('.ma'):
        maya.logger.info('Maya Binary files cannot be cleaned!')
        return False

    with open(filename, 'r') as f:
        lines = f.readlines()
    step = len(lines) / 4

    no_student_filename = filename[:-3] + '.no_student.ma'
    with open(no_student_filename, 'w') as f:
        step_count = 0
        for line in lines:
            step_count += 1
            if 'fileInfo' in line:
                if 'student' in line:
                    changed = True
                    continue
            f.write(line)
            if step_count > step:
                maya.logger.debug('Updating File: {}% ...'.format(100 / (len(lines) / step_count)))
                step += step

    if changed:
        os.chmod(filename, stat.S_IWUSR | stat.S_IREAD)
        shutil.copy2(no_student_filename, filename)

        try:
            os.remove(no_student_filename)
        except Exception as exc:
            maya.logger.warning('Error while cleanup no student file process files ... >> {}'.format(exc))
            return False

        maya.logger.info('Student file cleaned successfully!')

    return True


def load_plugin(plugin_name, quiet=True):
    """
    Loads plugin with the given name (full path)
    :param plugin_name: str, name or path of the plugin to load
    :param quiet: bool, Whether to show info to user that plugin has been loaded or not
    """

    if not maya.cmds.pluginInfo(plugin_name, query=True, loaded=True):
        try:
            maya.cmds.loadPlugin(plugin_name, quiet=quiet)
        except Exception as exc:
            maya.logger.error('Impossible to load plugin: {} | {}'.format(plugin_name, exc))
            return False

    return True


def get_project_rule(rule):
    """
    Get the full path of the rule of the project
    :param rule: str
    :return: str
    """

    workspace = maya.cmds.workspace(query=True, rootDirectory=True)
    workspace_folder = maya.cmds.workspace(fileRuleEntry=rule)
    if not workspace_folder:
        maya.logger.warning(
            'File Rule Entry "{}" has no value, please check if the rule name is typed correctly!'.format(rule))

    return os.path.join(workspace, workspace_folder)
