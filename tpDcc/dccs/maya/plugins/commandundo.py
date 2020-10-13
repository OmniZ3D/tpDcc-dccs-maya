import sys

import tpDcc.dccs.maya as maya
from maya.api import OpenMaya as OpenMaya

if not hasattr(maya, '_TPDCC_COMMAND'):
    maya._TPDCC_COMMAND = None
    maya._COMMAND_RUNNER = None


def maya_useNewAPI():
    pass


class UndoCommand(OpenMaya.MPxCommand):
    """
    Custom undo command plugin that allow us to support the undo of custom tpDcc
    commands that uses both API and MEL code
    """

    commandName = 'tpDccUndo'

    def __init__(self):
        super(UndoCommand, self).__init__()

        self._command = None
        self._command_runner = None

    @classmethod
    def command_creator(cls):
        return UndoCommand()

    @staticmethod
    def syntax_creator():
        return OpenMaya.MSyntax()

    def doIt(self, args_list):
        import tpDcc.dccs.maya as maya
        if maya._TPDCC_COMMAND is not None:
            self._command = maya._TPDCC_COMMAND
            maya._TPDCC_COMMAND = None
            self._command_runner = maya._COMMAND_RUNNER
            self.redoIt()

    def redoIt(self):
        if self._command is None:
            return

        self._command_runner._run(self._command)

    def undoIt(self):
        import tpDcc.dccs.maya as maya
        if self._command is None:
            return

        if self._command != maya._COMMAND_RUNNER.undo_stack[-1]:
            raise ValueError('Undo stack has become out of sync with tpDcc commands {}'.format(self._command.id))
        elif self._command.is_undoable:
            try:
                self._command.undo()
            finally:
                maya._COMMAND_RUNNER.redo_stack.append(self._command)
                maya._COMMAND_RUNNER.undo_stack.pop()

    def isUndoable(self):
        return self._command.is_undoable


def initializePlugin(mobj):
    mplugin = OpenMaya.MFnPlugin(mobj, 'Tomas Poveda', '1.0', 'Any')
    try:
        mplugin.registerCommand(UndoCommand.commandName, UndoCommand.command_creator, UndoCommand.syntax_creator)
    except:
        sys.stderr.write('Failed to register command: {}'.format(UndoCommand.commandName))


def uninitializePlugin(mobj):
    mplugin = OpenMaya.MFnPlugin(mobj)
    try:
        mplugin.deregisterCommand(UndoCommand.commandName)
    except:
        sys.stderr.write('Failed to unregister command: {}'.format(UndoCommand.commandName))
