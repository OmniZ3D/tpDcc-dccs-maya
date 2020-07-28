#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to Maya UI
"""

from __future__ import print_function, division, absolute_import

import functools
import traceback
import contextlib
from collections import OrderedDict

from Qt.QtWidgets import *

import tpDcc
import tpDcc.dccs.maya as maya
from tpDcc.libs.qt.core import qtutils

# ===================================================================================

_DPI_SCALE = 1.0 if not hasattr(
    maya.cmds, "mayaDpiSetting") else maya.cmds.mayaDpiSetting(query=True, realScaleValue=True)
current_progress_bar = None


# ===================================================================================


class ManageNodeEditors(object):
    def __init__(self):
        self.node_editors = get_node_editors()
        self._additive_state_dict = dict()
        for editor in self.node_editors:
            current_value = maya.cmds.nodeEditor(editor, query=True, ann=True)
            self._additive_state_dict[editor] = current_value

    def turn_off_add_new_nodes(self):
        for editor in self.node_editors:
            maya.cmds.nodeEditor(editor, e=True, ann=False)

    def restore_add_new_nodes(self):
        for editor in self.node_editors:
            maya.cmds.nodeEditor(editor, e=True, ann=self._additive_state_dict[editor])


def maya_undo(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            maya.cmds.undoInfo(openChunk=True)
            return fn(*args, **kwargs)
        finally:
            maya.cmds.undoInfo(closeChunk=True)

    return lambda *args, **kwargs: maya.utils.executeDeferred(wrapper, *args, **kwargs)


class DockWrapper(object):
    def __init__(self, settings=None):
        self._dock_area = 'right'
        self._dock_name = 'dock'
        self._allowed_areas = ['right', 'left']
        self._label = ''
        self._settings = settings
        self._name = ''

    # region Public Functions
    def create(self):
        floating = False

        if self._exists():
            maya.cmds.dockControl(self._dock_name, visible=True)
        else:
            maya.cmds.dockControl(self._dock_name, aa=self._allowed_areas, a=self._dock_area, content=self._name,
                                  label=self._label, fl=floating, visible=True, fcc=self._floating_changed)

    def set_name(self, name):
        self._name = name

    def set_dock_area(self, dock_area):
        self._dock_area = dock_area

    def set_dock_name(self, dock_name):
        self._dock_name = dock_name

    def set_label(self, label):
        self._label = label

    def set_allowed_areas(self, areas):
        self._allowed_areas = areas

    def _floating_changed(self):
        if self._settings:
            floating = is_window_floating(window_name=self._dock_name)
            self._settings.set('floating', floating)

    def _exists(self):
        return maya.cmds.dockControl(self._dock_name, exists=True)


@contextlib.contextmanager
def maya_no_undo():
    """
    Disable undo functionality during the context
    """

    try:
        maya.cmds.undoInfo(stateWithoutFlush=False)
        yield
    finally:
        maya.cmds.undoInfo(stateWithoutFlush=True)


def get_maya_api_version():
    """
    Returns Maya API version
    :return: int
    """

    return int(maya.cmds.about(api=True))


def get_maya_window(window_name=None, wrap_instance=True):
    """
    Return the Maya main window widget as a Python object
    :return: Maya Window
    """

    if wrap_instance:
        if window_name is not None:
            if '|' in str(window_name):
                # qt_obj = pm.uitypes.toQtObject(window_id)
                qt_obj = qtutils.to_qt_object(window_name)
                if qt_obj is not None:
                    return qt_obj
            ptr = maya.OpenMayaUI.MQtUtil.findControl(window_name)
            if ptr is not None:
                return qtutils.wrapinstance(ptr, QMainWindow)
        else:
            ptr = maya.OpenMayaUI.MQtUtil.mainWindow()
            if ptr is not None:
                return qtutils.wrapinstance(ptr, QMainWindow)

    if isinstance(window_name, (QWidget, QMainWindow)):
        return window_name
    search = window_name or 'MayaWindow'
    for obj in QApplication.topLevelWidgets():
        if obj.objectName() == search:
            return obj


def get_main_shelf():
    """
    Returns the Maya main shelf
    """

    return maya.mel.eval('$tempVar = $gShelfTopLevel')


def get_main_window():
    """
    Returns Maya main window through MEL
    """

    return maya.mel.eval("$tempVar = $gMainWindow")


def get_script_editor(source_type='python', command_completion=False, show_tooltip_help=False):
    """
    Returns Maya script editor window
    :param source_type: str
    :param command_completion: bool
    :param show_tooltip_help: bool
    :return:
    """

    maya.cmds.window()
    maya.cmds.columnLayout()
    executer = maya.cmds.cmdScrollFieldExecuter(
        sourceType=source_type, commandCompletion=command_completion, showTooltipHelp=show_tooltip_help)
    qtobj = to_qt_object(executer, QTextEdit)
    return executer, qtobj


def viewport_message(text):
    """
    Shows a message in the Maya viewport
    :param text: str, text to show in Maya viewport
    """

    maya.cmds.inViewMessage(amg='<hl>{}</hl>'.format(text), pos='midCenter', fade=True)


def force_stack_trace_on():
    """
    Forces enabling Maya Stack Trace
    """

    try:
        maya.mel.eval('stackTrace -state on')
        maya.cmds.optionVar(intValue=('stackTraceIsOn', True))
        what_is = maya.mel.eval('whatIs "$gLastFocusedCommandReporter"')
        if what_is != 'Unknown':
            last_focused_command_reporter = maya.mel.eval('$tmp = $gLastFocusedCommandReporter')
            if last_focused_command_reporter and last_focused_command_reporter != '':
                maya.mel.eval('synchronizeScriptEditorOption 1 $stackTraceMenuItemSuffix')
    except RuntimeError:
        pass


def pass_message_to_main_thread(message_handler, *args):
    """
    Executes teh message_handler with the given list of arguments in Maya's main thread
    during the next idle event
    :param message_handler: variant, str || function, string containing Python code or callable function
    """

    maya.utils.executeInMainThreadWithResult(message_handler, *args)


def dpi_scale(value):
    return _DPI_SCALE * value


def get_plugin_shapes():
    """
    Return all available plugin shapes
    :return: dict, plugin shapes by their menu label and script name
    """

    filters = maya.cmds.pluginDisplayFilter(query=True, listFilters=True)
    labels = [maya.cmds.pluginDisplayFilter(f, query=True, label=True) for f in filters]
    return OrderedDict(zip(labels, filters))


def get_active_editor():
    """
    Returns the active editor panel of Maya
    """

    maya.cmds.currentTime(maya.cmds.currentTime(query=True))
    panel = maya.cmds.playblast(activeEditor=True)
    return panel.split('|')[-1]


def get_active_panel():
    """
    Returns the current active modelPanel
    :return: str, name of the active panel or raises an error if no active modelPanel iis found
    """

    panel = maya.cmds.getPanel(withFocus=True)

    return panel


def get_current_frame():
    """
    Return current Maya frame set in time slier
    :return: int
    """

    return maya.cmds.currentTime(query=True)


def set_current_frame(frame):
    """
    Sets current Maya fram in time slider
    :param frame: int
    """

    return maya.cmds.currentTime(frame, update=True)


def get_playblack_slider():
    """
    Returns playback slider Maya control
    :return: str
    """

    return maya.mel.eval("global string $gPlayBackSlider; " "$gPlayBackSlider = $gPlayBackSlider;")


def get_time_slider_range(highlighted=True, within_highlighted=True, highlighted_only=False):
    """
    Return the time range from Maya time slider
    :param highlighted: bool, If True it will return a selected frame range (if there is any selection of
        more than one frame) else it will return min and max playblack time
    :param within_highlighted: bool, Maya returns the highlighted range end as a plus one value by default.
        If True, this is fixed by removing one from the last frame number
    :param highlighted_only: bool, If True, it wil return only highlighted frame range
    :return: list<float, float>, [start_frame, end_frame]
    """

    if highlighted is True:
        playback_slider = get_playblack_slider()
        if maya.cmds.timeControl(playback_slider, query=True, rangeVisible=True):
            highlighted_range = maya.cmds.timeControl(playback_slider, query=True, rangeArray=True)
            if within_highlighted:
                highlighted_range[-1] -= 1
            return highlighted_range

    if not highlighted_only:
        return [maya.cmds.playbackOptions(
            query=True, minTime=True), maya.cmds.playbackOptions(query=True, maxTime=True)]


def get_is_standalone():
    return not hasattr(maya.cmds, 'about') or maya.cmds.about(batch=True)


def get_active_panel():
    """
    Returns the current active modelPanel
    :return: str, name of the model panel or raises an error if no active modelPanel iis found
    """

    panel = maya.cmds.getPanel(withFocus=True)
    if not panel or 'modelPanel' not in panel:
        raise RuntimeError('No active model panel found!')

    return panel


def get_available_screen_size():
    """
    Returns available screen size without space occupied by task bar
    """

    if get_is_standalone():
        return [0, 0]

    rect = QDesktopWidget().screenGeometry(-1)
    return [rect.width(), rect.height()]


def get_top_maya_shelf():
    return maya.mel.eval("global string $gShelfTopLevel; $temp = $gShelfTopLevel;")


def get_all_shelves():
    return maya.cmds.tabLayout(get_top_maya_shelf(), query=True, ca=True)


def get_current_shelf():
    return maya.cmds.tabLayout(get_top_maya_shelf(), query=True, st=True)


def shelf_exists(shelf_name):
    """
    Returns True if the given shelf name already exists or False otherwise
    :param shelf_name: str, shelf name
    :return: bool
    """

    return maya.cmds.shelfLayout(shelf_name, exists=True)


def delete_shelf(shelf_name):
    """
    Deletes given shelf by name, if exists
    :param shelf_name: str, shelf name
    """

    if shelf_exists(shelf_name=shelf_name):
        maya.cmds.deleteUI(shelf_name)


def create_shelf(name, parent_layout='ShelfLayout'):
    """
    Creates a new shelf parented on the given layout
    :param name: str, name of the shelf to create
    :param parent_layout: name of the parent shelf layout
    :return: str
    """

    return maya.cmds.shelfLayout(name, parent=parent_layout)


@contextlib.contextmanager
def create_independent_panel(width, height, off_screen=False):
    """
    Creates a Maya panel window without decorations
    :param width: int, width of panel
    :param height: int, height of panel
    :param off_screen: bool
    with create_independent_panel(800, 600):
        cmds.capture()
    """

    screen_width, screen_height = get_available_screen_size()
    top_left = [int((screen_height - height) * 0.5), int((screen_width - width) * 0.5)]
    window = maya.cmds.window(
        width=width, height=height, topLeftCorner=top_left,
        menuBarVisible=False, titleBar=False, visible=not off_screen)
    maya.cmds.paneLayout()
    panel = maya.cmds.modelPanel(menuBarVisible=False, label='CapturePanel')
    # Hide icons under panel menus
    bar_layout = maya.cmds.modelPanel(panel, query=True, barLayout=True)
    maya.cmds.frameLayout(bar_layout, edit=True, collapse=True)
    if not off_screen:
        maya.cmds.showWindow(window)

    # Set the modelEditor of the modelPanel as the active view, so it takes the playback focus
    editor = maya.cmds.modelPanel(panel, query=True, modelEditor=True)
    maya.cmds.modelEditor(editor, edit=True, activeView=True)
    maya.cmds.refresh(force=True)

    try:
        yield panel
    finally:
        maya.cmds.deleteUI(panel, panel=True)
        maya.cmds.deleteUI(window)


@contextlib.contextmanager
def disable_inview_messages():
    """
    Disable in-view help messages during the context
    """

    original = maya.cmds.optionVar(query='inViewMessageEnable')
    maya.cmds.optionVar(iv=('inViewMessageEnable', 0))
    try:
        yield
    finally:
        maya.cmds.optionVar(iv=('inViewMessageEnable', original))


@contextlib.contextmanager
def maintain_camera_on_panel(panel, camera):
    """
    Tries to maintain given camera on given panel during the context
    :param panel: str, name of the panel to focus camera on
    :param camera: str, name of the camera we want to focus
    """

    state = dict()
    if not get_is_standalone():
        maya.cmds.lookThru(panel, camera)
    else:
        state = dict((camera, maya.cmds.getAttr(camera + '.rnd')) for camera in maya.cmds.ls(type='camera'))
        maya.cmds.setAttr(camera + '.rnd', True)
    try:
        yield
    finally:
        for camera, renderable in state.items():
            maya.cmds.setAttr(camera + '.rnd', renderable)


@contextlib.contextmanager
def reset_time():
    """
    The time is reset once the context is finished
    """

    current_time = maya.cmds.currentTime(query=True)
    try:
        yield
    finally:
        maya.cmds.currentTime(current_time)


@contextlib.contextmanager
def isolated_nodes(nodes, panel):
    """
    Context manager used for isolating given nodes in  given panel
    """

    if nodes is not None:
        maya.cmds.isolateSelect(panel, state=True)
        for obj in nodes:
            maya.cmds.isolateSelect(panel, addDagObject=obj)
    yield


def to_qt_object(maya_name, qobj=None):
    """
    Returns an instance of the Maya UI element as a QWidget
    """

    if not qobj:
        qobj = QWidget
    ptr = maya.OpenMayaUI.MQtUtil.findControl(maya_name)
    if ptr is None:
        ptr = maya.OpenMayaUI.MQtUtil.findLayout(maya_name)
    if ptr is None:
        ptr = maya.OpenMayaUI.MQtUtil.findMenuItem(maya_name)
    if ptr is not None:
        return qtutils.wrapinstance(long(ptr), qobj)
    return None


def to_maya_object(qt_object):
    """
    Returns a QtObject as Maya object
    """

    return maya.OpenMayaUI.MQtUtil.fullName(qtutils.unwrapinstance(qt_object))


def get_parent_widget(widget):
    """
    Returns given QWidget Maya UI parent
    :param widget: QWidget, Qt widget to get parent for
    :return: QWidget
    """

    ptr = maya.OpenMayaUI.MQtUtil.getParent(qtutils.unwrapinstance(widget))
    return qtutils.wrapinstance(long(ptr))


def get_ui_gvars():
    """
    Returns a list with all UI related vars used by Maya
    :return: list<str>
    """

    gvars = list()
    for g in [x for x in sorted(maya.mel.eval('env')) if x.find('$g') > -1]:
        try:
            var_type = maya.mel.eval('whatIs "{0}"'.format(g))
            if not var_type == 'string variable':
                raise TypeError
            tmp = maya.mel.eval('string $temp = {0};'.format(g))
            if tmp is None:
                raise TypeError
            target_widget = to_qt_object(maya_name=tmp)
            widget_type = type(target_widget)
            if widget_type is None:
                raise ValueError
        except Exception:
            continue
        gvars.append([g, widget_type.__name__])
    return gvars


def create_dock_window(window, dock_area='right', allowed_areas=['left', 'right']):
    """
    Docks given window in Maya (used in conjunction with DockedWindow class from window.py module)
    :param window: DockedWindow, UI we want to attach into Maya UI
    :param dock_area: str, area where we want to dock the UI
    :param allowed_areas: list<str>, list of allowed areas for the dock UI
    :return:
    """

    ui_name = str(window.objectName())
    ui_title = str(window.windowTitle())
    dock_name = '{}Dock'.format(ui_name)
    dock_name = dock_name.replace(' ', '_').replace('-', '_')
    path = 'MayaWindow|{}'.format(dock_name)
    if maya.cmds.dockControl(path, exists=True):
        maya.cmds.deleteUI(dock_name, control=True)
    maya.mel.eval('updateRendererUI;')

    try:
        dock = DockWrapper()
        dock.set_dock_name(dock_name)
        dock.set_name(ui_name)
        dock.set_label(ui_title)
        dock.set_dock_area(dock_area)
        dock.set_allowed_areas(allowed_areas)
        dock.create()
        window.show()
    except Exception:
        tpDcc.logger.warning('{} window failed to load. Maya may need to finish loading'.format(ui_name))
        tpDcc.logger.error(traceback.format_exc())


def is_window_floating(window_name):
    """
    Returns whether or not given window is floating
    :param window_name: str
    :return: bool
    """

    if tpDcc.Dcc.get_version() < 2017:
        floating = maya.cmds.dockControl(window_name, floating=True, query=True)
    else:
        floating = maya.cmds.workspaceControl(window_name, floating=True, query=True)

    return floating


def get_progress_bar():
    """
    Returns Maya progress bar
    :return: str
    """

    main_progress_bar = maya.mel.eval('$tmp = $gMainProgressBar')
    return main_progress_bar


def get_node_editors():
    """
    Returns all node editors panels opened in Maya
    """

    found = list()
    for panel in maya.cmds.getPanel(type='scriptedPanel'):
        if maya.cmds.scriptedPanel(panel, query=True, type=True) == 'nodeEditorPanel':
            node_editor = panel + 'NodeEditorEd'
            found.append(node_editor)

    return found


def add_maya_widget(layout, layout_parent, maya_fn, *args, **kwargs):
    if not maya.cmds.window('tempAttrWidgetWin', exists=True):
        maya.cmds.window('tempAttrWidgetWin')

    maya.cmds.columnLayout(adjustableColumn=True)
    try:
        maya_ui = maya_fn(*args, **kwargs)
        qtobj = to_qt_object(maya_ui)
        qtobj.setParent(layout_parent)
        layout.addWidget(qtobj)
    finally:
        if maya.cmds.window('tempAttrWidgetWin', exists=True):
            maya.cmds.deleteUI('tempAttrWidgetWin')

    return qtobj, maya_ui


def add_attribute_widget(layout, layout_parent, lbl, attr=None, attr_type='cbx', size=[10, 60, 40, 80],
                         attr_changed_fn=None):
    if attr and not maya.cmds.objExists(attr):
        return False

    if not maya.cmds.window('tempAttrWidgetWin', exists=True):
        maya.cmds.window('tempAttrWidgetWin')

    maya.cmds.columnLayout(adjustableColumn=True)

    try:
        if attr_type == 'cbx':
            ui_item = maya.cmds.checkBox(label=lbl, v=False, rs=False, w=60)
            maya.cmds.checkBox(ui_item, changeCommand=lambda attr: attr_changed_fn(attr), edit=True)
            maya.cmds.connectControl(ui_item, attr)

        if attr_type == 'color':
            ui_item = maya.cmds.attrColorSliderGrp(
                label=lbl, attribute=attr, cl4=['left', 'left', 'left', 'left'], cw4=[10, 15, 50, 80])

        if attr_type == 'floatSlider':
            ui_item = maya.cmds.attrFieldSliderGrp(
                label=lbl, attribute=attr, cl4=['left', 'left', 'left', 'left'], cw4=size, pre=2)
            maya.cmds.attrFieldSliderGrp(ui_item, changeCommand=lambda *args: attr_changed_fn(attr), edit=True)

        if attr_type == 'floatSliderMesh':
            ui_item = maya.cmds.attrFieldSliderGrp(
                label=lbl, attribute=attr, cl3=["left", "left", "left"], cw3=size, pre=2)
            maya.cmds.attrFieldSliderGrp(ui_item, changeCommand=lambda *args: attr_changed_fn(attr), edit=True)

        if attr_type == 'float2Col':
            ui_item = maya.cmds.attrFieldSliderGrp(label=lbl, attribute=attr, cl2=["left", "left"], cw2=size, pre=2)
            maya.cmds.attrFieldSliderGrp(ui_item, changeCommand=lambda *args: attr_changed_fn(attr), edit=True)

        qtobj = to_qt_object(ui_item)
        qtobj.setParent(layout_parent)
        layout.addWidget(qtobj)
    finally:
        if maya.cmds.window('tempAttrWidgetWin', exists=True):
            maya.cmds.deleteUI('tempAttrWidgetWin')

    return qtobj


def current_model_panel():
    """
    Returns current model panel name
    :return: str
    """

    current_panel = maya.cmds.getPanel(withFocus=True)
    current_panel_type = maya.cmds.getPanel(typeOf=current_panel)
    if current_panel_type not in ['modelPanel']:
        return None

    return current_panel


def open_render_settings_window():
    """
    Opens Maya Render Settings window
    """

    maya.mel.eval('unifiedRenderGlobalsWindow')


def delete_dock_control(control_name):
    """
    Handles the deletion of a dock control with a specific name
    :param control_name: str
    :return: bool
    """

    if maya.cmds.dockControl(control_name, query=True, exists=True):
        floating = maya.cmds.dockControl(control_name, query=True, floating=True)
        maya.cmds.dockControl(control_name, edit=True, r=True)
        maya.cmds.dockControl(control_name, edit=True, floating=False)
    else:
        floating = False

    window_wrap = get_maya_window(window_name=control_name)
    if window_wrap:
        if window_wrap.parent().parent() is not None:
            get_maya_window(window_name=control_name).parent().close()

    if floating is not None:
        try:
            maya.cmds.dockControl(control_name, edit=True, floating=floating)
        except RuntimeError:
            pass

    return floating


def delete_workspace_control(control_name, reset_floating=True):
    """
    Handles the deletion of a workspace control with a specific name
    :param control_name: str
    :param reset_floating: bool
    :return: bool
    """

    if not tpDcc.Dcc.get_version() > 2017:
        return None

    if maya.cmds.workspaceControl(control_name, query=True, exists=True):
        floating = maya.cmds.workspaceControl(control_name, query=True, floating=True)
        maya.cmds.deleteUI(control_name)
    else:
        floating = None

    # If the window is not currently floating, we remove stored preferences
    if maya.cmds.workspaceControlState(
            control_name, query=True, exists=True) and not (floating or floating and reset_floating):
        maya.cmds.workspaceControlState(control_name, remove=True)

    return floating


def open_namespace_editor():
    """
    Opens Maya Namespace Editor GUI
    """

    maya.mel.eval('namespaceEditor')


def open_reference_editor():
    """
    Opens Maya Reference Editor GUI
    """

    maya.mel.eval('tearOffRestorePanel "Reference Editor" referenceEditor true')
