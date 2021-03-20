#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains collections of decorators related with Maya
"""

from __future__ import print_function, division, absolute_import

import sys
import traceback
from functools import wraps

import maya.mel
import maya.cmds


class ShowMayaProgress(object):

    """
    Function decorator to show user (progress) feedback
    http://josbalcaen.com/maya-python-progress-decorator/
    @usage
    from tpRigLib.utils.tpDecorators import showMayaProgress
    @showMayaProgress(status='Creating cubes...', end=10)
    def createCubes():
    for i in range(10):
        time.sleep(1)
        if createCubes.isInterrupted(): break
        iCube = cmds.polyCube(w=1,h=1,d=1)
        cmds.move(i,i*.2,0,iCube)
        createCubes.step()
    createCubes()
    """

    def __init__(self, status='Working...', start=0, end=100, interruptable=True):

        self._start_value = start
        self._end_value = end
        self._status = status
        self._interruptable = interruptable

        self._main_progressbar = maya.mel.eval('$tmp = $gMainProgressBar')

    def start(self):
        """
        Start progress bar
        """

        if self._main_progressbar is None:
            return

        maya.cmds.waitCursor(state=True)
        maya.cmds.progressBar(self._main_progressbar, edit=True, beginProgress=True,
                              isInterruptable=self._interruptable, status=self._status,
                              minValue=self._start_value, maxValue=self._end_value)
        maya.cmds.refresh()

    def end(self):
        """
        Mark the progress bar as ended
        """

        if self._main_progressbar is None:
            return

        maya.cmds.progressBar(self._main_progressbar, edit=True, endProgress=True)
        maya.cmds.waitCursor(state=False)

    def step(self, value=1):
        """
        Increases progress bar step by value
        :param value: int, step
        """

        if self._main_progressbar is None:
            return

        maya.cmds.progressBar(self._main_progressbar, edit=True, step=value)

    def is_interrupted(self):
        """
        Checks if the user has interrupted the progress
        """

        if self._main_progressbar is None:
            return False

        return maya.cmds.progressBar(self._main_progressbar, query=True, isCancelled=True)

    def __call__(self, fn):
        """
        Override call method
        If there are decorator aguments, __cal__() is only called once, as part of the decoration process!
        You can only give it a single argument, which is the function object
        :param fn: Original function
        :return Wrapped function
        """

        def wrapped_fn(*args, **kwargs):
            self.start()                # Start progress
            fn(*args, **kwargs)         # Call original function
            self.end()                  # End progress

        # Add special method to the wrapped function
        wrapped_fn.step = self.step
        wrapped_fn.is_interrupted = self.is_interrupted

        # Copy over attributes
        wrapped_fn.__doc__ = fn.__doc__
        wrapped_fn.__name__ = fn.__name__
        wrapped_fn.__module__ = fn.__module__

        return wrapped_fn


class SuspendRefresh(object):
    def __enter__(self):
        maya.cmds.refresh(suspend=True)

    def __exit__(self, *exc_info):
        maya.cmds.refresh(suspend=False)


class RestoreContext(object):
    def __init__(self):
        self.auto_key_state = None
        self.time = None
        self.selection = None

    def __enter__(self):
        self.auto_key_state = maya.cmds.autoKeyframe(query=True, state=True)
        self.time = int(maya.cmds.currentTime(q=True))
        self.selection = maya.cmds.ls(sl=True)

    def __exit__(self, *exc_info):
        maya.cmds.autoKeyframe(state=self.auto_key_state)
        maya.cmds.currentTime(self.time)
        if self.selection:
            maya.cmds.select(self.selection)


class UndoChunk(object):
    def __enter__(self):
        maya.cmds.undoInfo(openChunk=True)

    def __exit__(self, *exc_info):
        maya.cmds.undoInfo(closeChunk=True)


class SkipUndo(object):
    def __enter__(self):
        maya.cmds.undoInfo(swf=False)

    def __exit__(self, *exc_info):
        maya.cmds.undoInfo(swf=True)


class ToggleScrub(object):
    def __init__(self):
        self._playblack_slider = maya.mel.eval('$tmp=$gPlayBackSlider')

    def __enter__(self):
        maya.cmds.timeControl(self._playblack_slider, beginScrub=True, e=True)

    def __exit__(self, *exc_info):
        maya.cmds.timeControl(self._playblack_slider, endScrub=True, e=True)


def try_except(fn):
    """
    Exception wrapper with undo functionality. Use @try_except above the function to wrap it.
    @param fn: function to wrap
    @return: wrapped function
    """

    error_text = '\n ====== tpRigLib: Something bad happened :( ======'

    def wrapper(*args, **kwargs):
        try:
            maya.cmds.undoInfo(openChunk=True)
            result = fn(*args, **kwargs)
            maya.cmds.undoInfo(closeChunk=True)
            return result
        except Exception as e:
            maya.cmds.undoInfo(closeChunk=True)
            gMainProgressBar = maya.mel.eval('$tmp = $gMainProgressBar')
            maya.cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)

            et, ei, tb = sys.exc_info()
            print(error_text, '\n')
            print("ERROR IN: ", fn.__name__, "Function.")
            print(e, '\n')
            print(traceback.print_exc(), '\n')
            print("=================== HELP ===================")
            print(fn.__doc__, 'n')
            print("=================== ERROR ===================")
            maya.cmds.inViewMessage(
                amg='<span style=\"color:#F05A5A;'
                    '\">Error: </span>' + str(e) + ' <span style=\"color:#FAA300;\">Look at the script '
                                                   'editor for more info about the error.</span>',
                pos='topCenter', fade=True, fst=4000, dk=True)
            raise Exception(e, tb)

    return wrapper


def viewport_off(f):
    """
    Function decorator that turns off Maya display while the function is running
    if the function fails, the error will be raised after
    :param f: fn, function
    """

    @wraps(f)
    def wrap(*args, **kwargs):
        # Turn $gMainPanel off
        gMainPane = maya.mel.eval('global string $gMainPane; $temp = $gMainPane;')
        maya.cmds.paneLayout(gMainPane, edit=True, manage=False)
        try:
            return f(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            maya.cmds.paneLayout(gMainPane, edit=True, manage=True)
    return wrap


def undo(f):
    """
    Function decorator that enables undo functionality using Maya Python commands
    :param f: fn, function
    """

    def wrapper(*args, **kwargs):
        maya.cmds.undoInfo(openChunk=True)
        try:
            ret = f(*args, **kwargs)
        except Exception as exc:
            raise Exception(traceback.format_exc())
        finally:
            maya.cmds.undoInfo(closeChunk=True)
        return ret
    return wrapper


def undo_pm(f):
    """
    Function decorator that enables undo functionality using PyMEL
    :param f: fn, function
    """

    from pymel import all as pm

    def wrapper(*args, **kwargs):
        pm.undoInfo(openChunk=True)
        try:
            ret = f(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            pm.undoInfo(closeChunk=True)
        return ret
    return wrapper


def disable_undo(fn):

    @wraps(fn)
    def wrapped(*args, **kwargs):
        initial_undo_state = maya.cmds.undoInfo(query=True, state=True)
        maya.cmds.undoInfo(stateWithoutFlush=False)
        try:
            return fn(*args, **kwargs)
        finally:
            maya.cmds.undoInfo(stateWithoutFlush=initial_undo_state)
    return wrapped


def operate_on_selected(f):
    """
    Function decorator that enables a function to operate only on selected objects
    :param f: fn, function
    """

    def wrapper(*args, **kwargs):
        selection = maya.cmds.ls(sl=True)
        return f(selection, *args, **kwargs)

    return wrapper


def suspend_refresh(f):
    """
    Function decorator that suspend the refersh of Maya viewport
    :param f: fn, function
    """

    def wrapper(*args, **kwargs):
        with SuspendRefresh():
            return f(*args, **kwargs)

    return wrapper


def restore_context(f):
    """
    Function decorator that restores Maya context
    :param f: fn, function
    """

    def wrapper(*args, **kwargs):
        with RestoreContext():
            return f(*args, **kwargs)

    return wrapper


def undo_chunk(f):
    """
    Function decorator that enables Maya undo functionality for a function
    :param f: fn, function
    """

    def wrapper(*args, **kwargs):
        with UndoChunk():
            return f(*args, **kwargs)

    return wrapper


def skip_undo(f):
    """
    Function decorator that skip Maya undo functionality for a function
    :param f; fn, function
    """

    def wrapper(*args, **kwargs):
        with SkipUndo():
            return f(*args, **kwargs)

    return wrapper


def toggle_scrub(f):
    """
    Function decorator that enables Maya scrub toggling functionality for a function
    :param f: fn, function
    """

    def wrapper(*args, **kwargs):
        with ToggleScrub():
            return f(*args, **kwargs)

    return wrapper


def repeat_static_command(class_name, skip_arguments=False):
    """
    Decorator that will make static functions repeatable for Maya
    :param class_name, str, path to the Python module where function we want to repeat is located
    :param skip_arguments, bool, Whether or not force the execution of the repeat function without passing any argument
    """

    def repeat_command(fn):
        def wrapper(*args, **kwargs):
            arg_str = ''
            if args:
                for each in args:
                    arg_str += str(each) + ', '
                    arg_str += '"{}", '.format(each)

            if kwargs:
                for k, v in kwargs.items():
                    arg_str += str(k) + '=' + str(v) + ', '

            if not skip_arguments:
                cmd = 'python("' + class_name + '.' + fn.__name__ + '(' + arg_str + ')")'
            else:
                cmd = 'python("' + class_name + '.' + fn.__name__ + '()")'
            fn_return = fn(*args, **kwargs)
            try:
                maya.cmds.repeatLast(ac=cmd, acl=fn.__name__)
            except Exception:
                pass
            return fn_return
        return wrapper
    return repeat_command


def disable_auto_key(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        initial_state = maya.cmds.autoKeyframe(query=True, state=True)
        maya.cmds.autoKeyframe(edit=True, state=False)
        try:
            return fn(*args, **kwargs)
        finally:
            maya.cmds.autoKeyframe(edit=True, state=initial_state)
    return wrapped


def restore_selection(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        selection = maya.cmds.ls(selection=True) or list()
        try:
            return fn(*args, **kwargs)
        finally:
            if selection:
                maya.cmds.select(selection)
    return wrapped


def restore_current_time(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        initial_time = maya.cmds.currentTime(query=True)
        try:
            return fn(*args, **kwargs)
        finally:
            maya.cmds.currentTime(initial_time, edit=True)
    return wrapped


def show_wait_cursor(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        maya.cmds.waitCursor(state=True)
        try:
            return fn(*args, **kwargs)
        finally:
            maya.cmds.currentTime(state=False)
    return wrapped


def disable_views(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        model_panels = maya.cmds.getPanel(vis=True)
        empty_selection_connection = maya.cmds.selectionConnection()
        for panel in model_panels:
            maya.cmds.isolateSelect(panel, state=True)
            maya.cmds.modelEditor(panel, edit=True, mainListConnection=empty_selection_connection)
        try:
            return fn(*args, **kwargs)
        finally:
            for panel in model_panels:
                if maya.cmds.getPanel(typeOf=panel) == 'modelPanel':
                    maya.cmds.isolateSelect(panel, state=False)
            maya.cmds.deleteUI(empty_selection_connection)
    return wrapped
