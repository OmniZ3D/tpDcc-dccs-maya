import functools
import traceback
import contextlib
from collections import OrderedDict

from Qt.QtCore import *
from Qt.QtWidgets import *
try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
import maya.OpenMayaUI as OpenMayaUI

import tpRigToolkit as tp
from tpPyUtils import qtutils

# ===================================================================================

_DPI_SCALE = 1.0 if not hasattr(cmds, "mayaDpiSetting") else cmds.mayaDpiSetting(query=True, realScaleValue=True)
current_progress_bar = None

# ===================================================================================


class ManageNodeEditors(object):
    def __init__(self):
        self.node_editors = get_node_editors()
        self._additive_state_dict = dict()
        for editor in self.node_editors:
            current_value = cmds.nodeEditor(editor, query=True, ann=True)
            self._additive_state_dict[editor] = current_value

    def turn_off_add_new_nodes(self):
        for editor in self.node_editors:
            cmds.nodeEditor(editor, e=True, ann=False)

    def restore_add_new_nodes(self):
        for editor in self.node_editors:
            cmds.nodeEditor(editor, e=True, ann=self._additive_state_dict[editor])


def maya_undo(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            cmds.undoInfo(openChunk=True)
            return fn(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)

    return lambda *args, **kwargs: utils.executeDeferred(wrapper, *args, **kwargs)

@contextlib.contextmanager
def maya_no_undo():
    """
    Disable undo functionality during the context
    """

    try:
        cmds.undoInfo(stateWithoutFlush=False)
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=True)


def get_maya_api_version():
    """
    Returns Maya API version
    :return: int
    """

    return int(cmds.about(api=True))


def get_maya_window():
    """
    Return the Maya main window widget as a Python object
    :return: Maya Window
    """

    ptr = OpenMayaUI.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(long(ptr), QWidget)

    return None


def get_main_shelf():
    """
    Returns the Maya main shelf
    """

    return mel.eval('$tempVar = $gShelfTopLevel')


def get_main_window():
    """
    Returns Maya main window through MEL
    """

    return mel.eval("$tempVar = $gMainWindow")


def viewport_message(text):
    """
    Shows a message in the Maya viewport
    :param text: str, text to show in Maya viewport
    """

    cmds.inViewMessage(amg='<hl>{}</hl>'.format(text), pos='midCenter', fade=True)


def force_stack_trace_on():
    """
    Forces enabling Maya Stack Trace
    """

    try:
        mel.eval('stackTrace -state on')
        cmds.optionVar(intValue=('stackTraceIsOn', True))
        what_is = mel.eval('whatIs "$gLastFocusedCommandReporter"')
        if what_is != 'Unknown':
            last_focused_command_reporter = mel.eval('$tmp = $gLastFocusedCommandReporter')
            if last_focused_command_reporter and last_focused_command_reporter != '':
                mel.eval('synchronizeScriptEditorOption 1 $stackTraceMenuItemSuffix')
    except RuntimeError:
        pass


def pass_message_to_main_thread(message_handler, *args):
    """
    Executes teh message_handler with the given list of arguments in Maya's main thread
    during the next idle event
    :param message_handler: variant, str || function, string containing Python code or callable function
    """

    utils.executeInMainThreadWithResult(message_handler, *args)


def dpi_scale(value):
    return _DPI_SCALE * value


def get_plugin_shapes():
    """
    Return all available plugin shapes
    :return: dict, plugin shapes by their menu label and script name
    """

    filters = cmds.pluginDisplayFilter(query=True, listFilters=True)
    labels = [cmds.pluginDisplayFilter(f, query=True, label=True) for f in filters]
    return OrderedDict(zip(labels, filters))


def get_active_editor():
    """
    Returns the active editor panel of Maya
    """

    cmds.currentTime(cmds.currentTime(query=True))
    panel = cmds.playblast(activeEditor=True)
    return panel.split('|')[-1]


def get_current_frame():
    """
    Return current Maya frame set in time slier
    :return: int
    """

    return cmds.currentTime(query=True)


def get_time_slider_range(highlighted=True, within_highlighted=True, highlighted_only=False):
    """
    Return the time range from Maya time slider
    :param highlighted: bool, If True it will return a selected frame range (if there is any selection of more than one frame) else
    it will return min and max playblack time
    :param within_highlighted: bool, Maya returns the highlighted range end as a plus one value by default. If True, this is fixed by
    removing one from the last frame number
    :param highlighted_only: bool, If True, it wil return only highlighted frame range
    :return: list<float, float>, [start_frame, end_frame]
    """

    if highlighted is True:
        playback_slider = mel.eval("global string $gPlayBackSlider; " "$gPlayBackSlider = $gPlayBackSlider;")
        if cmds.timeControl(playback_slider, query=True, rangeVisible=True):
            highlighted_range = cmds.timeControl(playback_slider, query=True, rangeArray=True)
            if within_highlighted:
                highlighted_range[-1] -= 1
            return highlighted_range

    if not highlighted_only:
        return [cmds.playbackOptions(query=True, minTime=True), cmds.playbackOptions(query=True, maxTime=True)]


def get_is_standalone():
    return not hasattr(cmds, 'about') or cmds.about(batch=True)


def get_active_panel():
    """
    Returns the current active modelPanel
    :return: str, name of the model panel or raises an error if no active modelPanel iis found
    """

    panel = cmds.getPanel(withFocus=True)
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
    return mel.eval("global string $gShelfTopLevel; $temp = $gShelfTopLevel;")


def get_all_shelves():
    return cmds.tabLayout(get_top_maya_shelf(), query=True, ca=True)


def get_current_shelf():
    return cmds.tabLayout(get_top_maya_shelf(), query=True, st=True)


def shelf_exists(shelf_name):
    """
    Returns True if the given shelf name already exists or False otherwise
    :param shelf_name: str, shelf name
    :return: bool
    """

    return cmds.shelfLayout(shelf_name, exists=True)


def delete_shelf(shelf_name):
    """
    Deletes given shelf by name, if exists
    :param shelf_name: str, shelf name
    """

    if shelf_exists(shelf_name=shelf_name):
        cmds.deleteUI(shelf_name)


def create_shelf(name, parent_layout='ShelfLayout'):
    """
    Creates a new shelf parented on the given layout
    :param name: str, name of the shelf to create
    :param parent_layout: name of the parent shelf layout
    :return: str
    """

    return cmds.shelfLayout(name, parent=parent_layout)


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
    top_left = [int((screen_height-height)*0.5), int((screen_width-width)*0.5)]
    window = cmds.window(width=width, height=height, topLeftCorner=top_left, menuBarVisible=False, titleBar=False, visible=not off_screen)
    cmds.paneLayout()
    panel = cmds.modelPanel(menuBarVisible=False, label='CapturePanel')
    # Hide icons under panel menus
    bar_layout = cmds.modelPanel(panel, query=True, barLayout=True)
    cmds.frameLayout(bar_layout, edit=True, collapse=True)
    if not off_screen:
        cmds.showWindow(window)

    # Set the modelEditor of the modelPanel as the active view, so it takes the playback focus
    editor = cmds.modelPanel(panel, query=True, modelEditor=True)
    cmds.modelEditor(editor, edit=True, activeView=True)
    cmds.refresh(force=True)

    try:
        yield panel
    finally:
        cmds.deleteUI(panel, panel=True)
        cmds.deleteUI(window)


@contextlib.contextmanager
def disable_inview_messages():
    """
    Disable in-view help messages during the context
    """

    original = cmds.optionVar(query='inViewMessageEnable')
    cmds.optionVar(iv=('inViewMessageEnable', 0))
    try:
        yield
    finally:
        cmds.optionVar(iv=('inViewMessageEnable', original))


@contextlib.contextmanager
def maintain_camera_on_panel(panel, camera):
    """
    Tries to maintain given camera on given panel during the context
    :param panel: str, name of the panel to focus camera on
    :param camera: str, name of the camera we want to focus
    """

    state = dict()
    if not get_is_standalone():
        cmds.lookThru(panel, camera)
    else:
        state = dict((camera, cmds.getAttr(camera + '.rnd')) for camera in cmds.ls(type='camera'))
        cmds.setAttr(camera + '.rnd', True)
    try:
        yield
    finally:
        for camera, renderable in state.items():
            cmds.setAttr(camera + '.rnd', renderable)


@contextlib.contextmanager
def reset_time():
    """
    The time is reset once the context is finished
    """

    current_time = cmds.currentTime(query=True)
    try:
        yield
    finally:
        cmds.currentTime(current_time)


@contextlib.contextmanager
def isolated_nodes(nodes, panel):
    """
    Context manager used for isolating given nodes in  given panel
    """

    if nodes is not None:
        cmds.isolateSelect(panel, state=True)
        for obj in nodes:
            cmds.isolateSelect(panel, addDagObject=obj)
    yield


def to_qt_object(maya_name, qobj=None):
    """
    Returns an instance of the Maya UI element as a QWidget
    """

    if not qobj:
        qobj = QWidget
    ptr = OpenMayaUI.MQtUtil.findControl(maya_name)
    if ptr is None:
        ptr = OpenMayaUI.MQtUtil.findLayout(maya_name)
    if ptr is None:
        ptr = OpenMayaUI.MQtUtil.findMenuItem(maya_name)
    if ptr is not None:
        return qtutils.wrapinstance(long(ptr), qobj)
    return None


def to_maya_object(qt_object):
    """
    Returns a QtObject as Maya object
    """

    return OpenMayaUI.MQtUtil.fullName(qtutils.unwrapinstance(qt_object))


def get_parent_widget(widget):
    """
    Returns given QWidget Maya UI parent
    :param widget: QWidget, Qt widget to get parent for
    :return: QWidget
    """

    ptr = OpenMayaUI.MQtUtil.getParent(qtutils.unwrapinstance(widget))
    return qtutils.wrapinstance(long(ptr))


def get_ui_gvars():
    """
    Returns a list with all UI related vars used by Maya
    :return: list<str>
    """

    gvars = list()
    for g in [x for x in sorted(mel.eval('env')) if x.find('$g') > -1]:
        try:
            var_type = mel.eval('whatIs "{0}"'.format(g))
            if not var_type == 'string variable':
                raise TypeError
            tmp = mel.eval('string $temp = {0};'.format(g))
            if tmp is None:
                raise TypeError
            target_widget = to_qt_object(maya_name=tmp)
            widget_type = type(target_widget)
            if widget_type == type(None):
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
    if cmds.dockControl(path, exists=True):
        cmds.deleteUI(dock_name, control=True)
        if hasattr(window, '_has_exit_prompt'):
            window._has_exit_prompt = False
        window.close()
    mel.eval('updateRendererUI;')

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
        tp.logger.warning('{} window failed to load. Maya may need to finish loading'.format(ui_name))
        tp.logger.error(traceback.format_exc())


def get_progress_bar():
    """
    Returns Maya progress bar
    :return: str
    """

    main_progress_bar = mel.eval('$tmp = $gMainProgressBar')
    return main_progress_bar


def get_node_editors():
    """
    Returns all node editors panels opened in Maya
    """

    found = list()
    for panel in cmds.getPanel(type='scriptedPanel'):
        if cmds.scriptedPanel(panel, query=True, type=True) == 'nodeEditorPanel':
            node_editor = panel + 'NodeEditorEd'
            found.append(node_editor)

    return found


class DockWrapper(object):
    def __init__(self, settings=None):
        self._dock_area = 'right'
        self._dock_name = 'dock'
        self._allowed_areas = ['right', 'left']
        self._label = ''
        self._settings = None
        self._name = ''

    # region Public Functions
    def create(self):
        floating = False

        if tp.Dcc.get_name() == tp.Dccs.Maya:
            import maya.cmds as cmds
            if self._exists():
                cmds.dockControl(self._dock_name, visible=True)
            else:
                cmds.dockControl(self._dock_name, aa=self._allowed_areas, a=self._dock_area, content=self._name, label=self._label, fl=floating, visible=True, fcc=self._floating_changed)

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
    # endregion

    # region Private Functions
    def _floating_changed(self):
        if self._settings:
            if tp.Dcc.get_name() == tp.Dccs.Maya:
                import maya.cmds as cmds
                floating = cmds.dockControl(self._dock_name, floating=True, query=True)
                self._settings.set('floating', floating)

    def _exists(self):
        if tp.Dcc.get_name() == tp.Dccs.Maya:
            import maya.cmds as cmds
            return cmds.dockControl(self._dock_name, exists=True)
    # endregion

def add_maya_widget(layout, layout_parent, maya_fn, *args, **kwargs):
    if not cmds.window('tempAttrWidgetWin', exists=True):
        cmds.window('tempAttrWidgetWin')

    cmds.columnLayout(adjustableColumn=True)
    try:
        maya_ui = maya_fn(*args, **kwargs)
        qtobj = to_qt_object(maya_ui)
        qtobj.setParent(layout_parent)
        layout.addWidget(qtobj)
    finally:
        if cmds.window('tempAttrWidgetWin', exists=True):
            cmds.deleteUI('tempAttrWidgetWin')

    return qtobj, maya_ui


def add_attribute_widget(layout, layout_parent, lbl, attr=None, attr_type='cbx', size=[10, 60, 40, 80], attr_changed_fn=None):

    if attr and not cmds.objExists(attr):
        return False

    if not cmds.window('tempAttrWidgetWin', exists=True):
        cmds.window('tempAttrWidgetWin')

    cmds.columnLayout(adjustableColumn=True)

    try:
        if attr_type == 'cbx':
            ui_item = cmds.checkBox(label=lbl, v=False, rs=False, w=60)
            cmds.checkBox(ui_item, changeCommand=lambda attr: attr_changed_fn(attr), edit=True)
            cmds.connectControl(ui_item, attr)

        if attr_type == 'color':
            ui_item = cmds.attrColorSliderGrp(label=lbl, attribute=attr, cl4=['left', 'left', 'left', 'left'], cw4=[10, 15, 50, 80])

        if attr_type == 'floatSlider':
            ui_item = cmds.attrFieldSliderGrp(label=lbl, attribute=attr,
                                              cl4=['left', 'left', 'left', 'left'], cw4=size, pre=2)
            cmds.attrFieldSliderGrp(ui_item, changeCommand=lambda *args: attr_changed_fn(attr), edit=True)

        if attr_type == 'floatSliderMesh':
            ui_item = cmds.attrFieldSliderGrp(label=lbl, attribute=attr,
                                              cl3=["left", "left", "left"], cw3=size, pre=2)
            cmds.attrFieldSliderGrp(ui_item, changeCommand=lambda *args: attr_changed_fn(attr), edit=True)

        if attr_type == 'float2Col':
            ui_item = cmds.attrFieldSliderGrp(label=lbl, attribute=attr, cl2=["left", "left"], cw2=size, pre=2)
            cmds.attrFieldSliderGrp(ui_item, changeCommand=lambda *args: attr_changed_fn(attr), edit=True)

        qtobj = to_qt_object(ui_item)
        qtobj.setParent(layout_parent)
        layout.addWidget(qtobj)
    finally:
        if cmds.window('tempAttrWidgetWin', exists=True):
            cmds.deleteUI('tempAttrWidgetWin')

    return qtobj
