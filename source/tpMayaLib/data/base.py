import traceback

from tpQtLib.Qt.QtCore import *
from tpQtLib.QtWidgets import *

import tpRigToolkit as tp
from tpPyUtils import path, osplatform, mathlib, version, qtutils
from tpQtLib.widgets import splitters, button
from tpMayaLib.core import constants, node, geometry, scene, helpers
# from tpRigToolkit.core.data import base


class DataTypes(base.DataTypes, object):
    MayaAscii = 'MayaAscii'
    MayaBinary = 'MayaBinary'


class ScriptTypes(base.ScriptTypes, object):
    MEL = 'MELScript'


class ScriptMelData(base.ScriptData, object):

    # region Override Functions
    @staticmethod
    def get_data_type():
        return constants.ScriptLanguages.MEL

    @staticmethod
    def get_data_extension():
        return 'mel'


class MayaCustomData(base.CustomData, object):
    # region Private Functions
    def _center_view(self):
        if scene.is_batch():
            return

        try:
            cmds.select(cl=True)
            cmds.viewFit(an=True)
            self._fix_camera()
        except Exception:
            tp.logger.debug('Could not center view: {}'.format(traceback.format_exc()))

    def _fix_camera(self):
        camera_pos = cmds.xform('persp', q=True, ws=True, t=True)
        dst = mathlib.get_distance([0, 0, 0], camera_pos)
        cmds.setAttr('persp.farClipPlane', dst)
        near = 0.1
        if dst > 10000:
            near = (dst/10000) * near
        cmds.setAttr('persp.nearClipPlane', near)
    # endregion


class MayaFileData(MayaCustomData, object):
    maya_binary = 'mayaBinary'
    maya_ascii = 'mayaAscii'

    def __init__(self, name=None):
        super(MayaFileData, self).__init__(name)

        self.maya_file_type = self.get_maya_file_type()

    # region Override Functions
    def get_data_title(self):
        return 'maya_file'

    def set_directory(self, directory):
        super(MayaFileData, self).set_directory(directory)
        self.file_path = path.join_path(directory, '{}.{}'.format(self.name, self.get_data_extension()))
    # endregion

    # region Public Functions
    def get_maya_file_type(self):
        return self.maya_binary

    def open(self, file_path=None):
        if not tp.Dcc.get_name() == tp.Dccs.Maya:
            tp.logger.warning('Maya data must be accessed from within Maya!')
            return

        open_file = None
        if file_path:
            open_file = file_path
        if not open_file:
            file_path = self.get_file()
            if not path.is_file(file_path):
                tp.logger.warning('Could not open file: {}'.format(file_path))
                return
            open_file = file_path

        helpers.display_info('Opening: {}'.format(open_file))

        try:
            cmds.file(open_file, f=True, o=True, iv=True, pr=True)
        except Exception:
            tp.logger.error('Impossible to open Maya file: {} | {}'.format(open_file, traceback.format_exc()))

        self._after_open()

        top_transforms = scene.get_top_dag_nodes(exclude_cameras=True)

        return top_transforms

    def save(self, comment):
        if not tp.Dcc.get_name() == tp.Dccs.Maya:
            tp.logger.warning('Maya data must be accessed from within Maya!')
            return

        if not comment:
            comment = '-'

        file_path = self.get_file()
        osplatform.get_permission(file_path)
        self._handle_unknowns()
        self._clean_scene()

        if not file_path.endswith('.mb') and not file_path.endswith('.ma'):
            file_path = cmds.workspace(query=True, rd=True)
            if self.maya_file_type == self.maya_ascii:
                file_path = cmds.fileDialog(ds=1, fileFilter='Maya Ascii (*.ma)', dir=file_path)
            elif self.maya_file_type == self.maya_binary:
                file_path = cmds.fileDialog(ds=1, fileFilter='Maya Binary (*.mb)', dir=file_path)
            if file_path:
                file_path = file_path[0]

        saved = scene.save_as(file_path)
        if saved:
            version_file = version.VersionFile(file_path)
            # if scene.is_batch() or not version_file.has_versions():
            version_file.save(comment)

            helpers.display_info('Saved {} data'.format(self.name))
            return True

        return False

    def import_data(self, file_path=''):
        if not tp.Dcc.get_name() == tp.Dccs.Maya:
            tp.logger.warning('Data must be accessed from within Maya!')
            return

        if file_path:
            import_file = file_path
        else:
            import_file = self.get_file()
        if not path.is_file(import_file):
            tp.logger.warning('Impossible to import invalid data file: {}'.format(file_path))
            return

        track = scene.TrackNodes()
        track.load('transform')

        scene.import_scene(import_file)
        self._after_open()

        transforms = track.get_delta()
        top_transforms = scene.get_top_dag_nodes_in_list(transforms)

        return top_transforms

    def reference_data(self, file_path=''):
        if not tp.Dcc.get_name() == tp.Dccs.Maya:
            tp.logger.warning('Data must be accessed from within Maya!')
            return

        if file_path:
            reference_file = file_path
        else:
            reference_file = self.get_file()
        if not path.is_file(reference_file):
            tp.logger.warning('Impossible to reference invalid data file: {}'.format(file_path))
            return

        track = scene.TrackNodes()
        track.load('transform')

        scene.reference_scene(reference_file)

        transforms = track.get_delta()
        top_transforms = scene.get_top_dag_nodes_in_list(transforms)

        return top_transforms

    def export_data(self, comment):
        if not tp.Dcc.get_name() == tp.Dccs.Maya:
            tp.logger.warning('Data must be accessed from within Maya!')
            return

        file_path = self.get_file()
        osplatform.get_permission(file_path)
        self._handle_unknowns()
        self._clean_scene()
        cmds.file(rename=file_path)
        self._prepare_scene_for_export()

        cmds.file(exportSelected=True, prompt=False, force=True, pr=True, ch=True, chn=True, exp=True, con=True,
                  stx='always', type=self.maya_file_type)

        version_file = version.VersionFile(file_path)
        version_file.save(comment)

        helpers.display_info('Export {} data'.format(self.name))
    # endregion

    # region Private Functions
    def _check_after_save(self, client_data, comment=None):
        file_path = cmds.file(query=True, sn=True)
        version_file = version.VersionFile(file_path)
        dir_path = path.get_dirname(file_path)
        if version.VersionFile(dir_path).has_versions():
            if not comment:
                comment = 'Automatically versioned with Maya save'

            version.save(comment)
            helpers.display_info('New version saved!')

    def _after_open(self):
        geometry.smooth_preview_all(False)
        self._center_view()

    def _clean_scene(self):
        tp.logger.debug('Cleaning Maya scene ...')
        scene.delete_turtle_nodes()
        if helpers.get_maya_version() > 2014:
            scene.delete_garbage()
            scene.delete_unused_plugins()

    def _handle_unknowns(self):
        unknown_nodes = cmds.ls(type='unknown')
        if unknown_nodes:
            value = cmds.confirmDialog(
                title='Unknown Nodes!',
                message='Unknown nodes usually happen when a plugin that was being used is not loaded.\nLoad the missing plugin, and the unknown nodes could become valid.\n\nDelete unknown nodes?\n',
                button=['Yes', 'No'],
                defaultButton='Yes',
                cancelButton='No',
                dismissString='No'
            )

            if value == 'Yes':
                node.delete_unknown_nodes()
            if value == 'No':
                if self.maya_file_type == self.maya_binary:
                    cmds.warning('\tThis file contains unknown nodes. Try saving as Maya ASCII instead.')

    def _prepare_scene_for_export(self):
        outliner_sets = scene.get_sets()
        top_nodes = scene.get_top_dag_nodes()
        to_select = outliner_sets + top_nodes
        if not to_select:
            to_select = ['persp', 'side', 'top', 'front']
        cmds.select(to_select, r=True)
    # endregion


class MayaBinaryFileData(MayaFileData):
    def __init__(self, name=None):
        super(MayaBinaryFileData, self).__init__(name)

    # region Override Functions
    @staticmethod
    def get_data_type():
        return 'maya.binary'

    @staticmethod
    def get_data_extension():
        return 'mb'
    # endregion


class MayaAsciiFileData(MayaFileData):
    def __init__(self, name=None):
        super(MayaAsciiFileData, self).__init__(name)

    # region Override Functions
    @staticmethod
    def get_data_type():
        return 'maya.ascii'

    @staticmethod
    def get_data_extension():
        return 'ma'

    @staticmethod
    def get_data_title():
        return 'Maya ASCII'
    # endregion


class MayaInfoWidget(base.DataInfoWidget, object):
    def __init__(self, data_widget, parent=None):
        super(MayaInfoWidget, self).__init__(data_widget, parent)

    # region Override Functions
    def is_linked_widget(self):
        return False

    def set_sub_folder(self, folder_name):
        self._data_widget.set_sub_folder(folder_name)

    def get_main_tab_name(self):
        return 'Maya File'

    def get_save_widget(self):
        return MayaSaveFileWidget()

    def get_history_widget(self):
        return MayaHistoryWidget()
    # endregion


class MayaSaveFileWidget(base.SaveFileWidget, object):
    def __init__(self, data_widget=None, parent=None):
        super(MayaSaveFileWidget, self).__init__(data_widget, parent)

    # region Override Functions
    def ui(self):
        self.main_layout= self.get_main_layout()
        self.setLayout(self.main_layout)
        self.main_layout.setAlignment(Qt.AlignTop)

        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)
        self.main_layout.addLayout(v_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(2, 2, 2, 2)
        buttons_layout.setSpacing(2)
        v_layout.addLayout(buttons_layout)
        v_layout.addLayout(splitters.SplitterLayout())

        # v_layout_1 = QVBoxLayout()
        # v_layout_2 = QVBoxLayout()

        self.save_btn = button.BaseButton('Save', icon_name='save', icon_extension='png', icon_padding=3, button_style=button.ButtonStyles.FlatStyle)

        # Export functionality at this moment brokes Maya 2018 sessions (not testing in other versions)
        self.export_btn = button.BaseButton('Export', icon_name='external', icon_extension='png', icon_padding=3, button_style=button.ButtonStyles.FlatStyle)
        self.export_btn.setVisible(False)

        self.open_btn = button.BaseButton('Open', icon_name='open_folder', icon_extension='png', icon_padding=3, button_style=button.ButtonStyles.FlatStyle)
        self.import_btn = button.BaseButton('Import', icon_name='import', icon_extension='png', icon_padding=3, button_style=button.ButtonStyles.FlatStyle)
        self.reference_btn = button.BaseButton('Reference', icon_name='reference', icon_extension='png', icon_padding=3, button_style=button.ButtonStyles.FlatStyle)

        buttons_layout.addWidget(self.open_btn)
        buttons_layout.addWidget(self.save_btn)
        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.VLine)
        self.sep.setFrameShadow(QFrame.Sunken)
        buttons_layout.addWidget(self.sep)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.import_btn)
        buttons_layout.addWidget(self.reference_btn)

    def setup_signals(self):
        self.save_btn.clicked.connect(self._on_save)
        self.export_btn.clicked.connect(self._on_export)
        self.open_btn.clicked.connect(self._on_open)
        self.import_btn.clicked.connect(self._on_import)
        self.reference_btn.clicked.connect(self._on_reference)
    # endregion

    # region Private Functions
    def _skip_mismatch_file(self):

        if tp.Dcc.get_name() == tp.Dccs.Maya:
            import maya.cmds as cmds
            current_directory = cmds.file(query=True, expandName=True)
        else:
            raise RuntimeError('Impossible to continue because necessary functionality is not implemented in current DCC')

        test_directory = path.get_dirname(current_directory)
        if current_directory.endswith('unknown') or current_directory.endswith('untitled'):
            return False

        if not current_directory.startswith(test_directory):
            result = qtutils.get_permission('Root directory is different from current directory.\nAre you sure you are saving into the right folder?', parent=self)
            if result:
                return False
            else:
                return True

        return False

    def _auto_save(self):
        if not tp.Dcc.get_name() == tp.Dccs.Maya:
            return

        import maya.cmds as cmds
        from tpRigToolkit.maya.lib import scene
        file_path = cmds.file(q=True, sn=True)
        saved = scene.save_as(file_path)

        return saved

    def _on_open(self, file_path=None):
        if not self._data_widget:
            tp.logger.warning('Impossible to open invalid data!')
            return
        #
        # current_task = rigtask.get_current_task()
        # if not current_task:
        #     tp.logger.warning('Impossible to open file because task is not defined!')
        #     return

        # data_file = self._data_widget.get_file()
        # if not path.is_file(data_file):
        #     tp.logger.warning('No data to open. Please save once!')
        #     return
        #
        # if tp.Dcc.get_name() == tp.Dccs.Maya:
        #     import maya.cmds as cmds
        #     if cmds.file(query=True, mf=True):
        #         file_path = cmds.file(q=True, sn=True)
        #         task_path = current_task.get_path()
        #         relative_path = path.remove_common_path(task_path, file_path)
        #         if not relative_path:
        #             if file_path:
        #                 relative_path = file_path
        #             else:
        #                 relative_path = 'New Scene'
        #
        #         result = qtutils.get_save_permission(
        #             'Do you want to save changes in current scene?',
        #             file_path=relative_path,
        #             title='Save Current Scene',
        #             parent=self
        #         )
        #         if result:
        #             saved = self._auto_save()
        #             if not saved:
        #                 return
        #         if result is None:
        #             return

        self._data_widget.open()

    def _on_save(self):

        if not self._data_widget:
            tp.logger.warning('Impossible to save invalid data!')
            return

        if self._skip_mismatch_file():
            return

        comment = qtutils.get_comment(parent=self)
        if not comment:
            return

        self._data_widget.save(comment=comment)

        self.fileChanged.emit()

    def _on_import(self):
        if not self._data_widget:
            tp.logger.warning('Impossible to import invalid data!')
            return

        file_to_import = self._data_widget.get_file()

        if not path.is_file(file_to_import) and not path.is_dir(file_to_import):
            qtutils.warning_message('No data to import. Please save once', self)
            return

        self._data_widget.import_data()

    def _on_reference(self):
        if not self._data_widget:
            tp.logger.warning('Impossible to reference invalid data!')
            return

        self._data_widget.reference_data()

    def _on_export(self):
        if not self._data_widget:
            tp.logger.warning('Impossible to export invalid data!')
            return

        comment = qtutils.get_comment(parent=self)
        if comment is None:
            return

        self._data_widget.export_data(comment)

        self.fileChanged.emit()
    # endregion


class MayaHistoryWidget(base.HistoryFileWidget, object):
    def __init__(self, data_widget=None, parent=None):
        super(MayaHistoryWidget, self).__init__(data_widget, parent)

    def ui(self):
        super(MayaHistoryWidget, self).ui()

