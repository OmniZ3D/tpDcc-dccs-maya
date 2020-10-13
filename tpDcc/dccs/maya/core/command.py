#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya command implementation
"""

from __future__ import print_function, division, absolute_import

import sys
import traceback

from tpDcc.core import command, exceptions
import tpDcc.dccs.maya as maya


class MayaCommandRunner(command.BaseCommandRunner, object):
    def __init__(self):
        super(MayaCommandRunner, self).__init__()

        maya._COMMAND_RUNNER = None

    def run(self, command_id, **kwargs):

        command_to_run = self.find_command(command_id)
        if not command_to_run:
            raise ValueError(
                'No command found with given id "{}" for "{}"'.format(command_id, self._manager.interfaces))

        if maya._COMMAND_RUNNER is None:
            maya._COMMAND_RUNNER = self

        command_to_run = command_to_run()
        if not command_to_run.is_enabled:
            return
        try:
            command_to_run.parse_arguments(kwargs)
        except exceptions.CommandCancel:
            return
        except Exception:
            raise

        trace = None
        command_to_run.stats = command.CommandStats(command_to_run)
        try:
            if command_to_run.is_undoable:
                maya.cmds.undoInfo(openChunk=True)
            maya._TPDCC_COMMAND = command_to_run
            maya.cmds.tpDccUndo(id=command_to_run.id)
        except exceptions.CommandCancel:
            command.stats.finish(None)
        except Exception:
            exc_type, exc_value, exc_trace = sys.exc_info()
            trace = traceback.format_exception(exc_type, exc_value, exc_trace)
            maya.logger.exception(trace)
            raise
        finally:
            if not trace and command_to_run.is_undoable:
                self._undo_stack.append(command_to_run)
                maya.cmds.undoInfo(closeChunk=True)
            command_to_run.stats.finish(trace)
            return command_to_run._return_result

    def flush(self):
        super(MayaCommandRunner, self).flush()
        maya.cmds.flushUndo()

    def _run(self, command_to_run):
        if maya.OpenMaya.MGlobal.isRedoing():
            self._redo_stack.pop()
            result = super(MayaCommandRunner, self)._run(command_to_run)
            self._undo_stack.append(command_to_run)
            return result
        return super(MayaCommandRunner, self)._run(command_to_run)
