#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Maya Script completer
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *

from tpDcc.libs.qt.core import completer


class MayaCompleter(completer.BaseCompleter):

    @staticmethod
    def get_auto_import():
        return None

    @staticmethod
    def wrap_dropped_text(namespace, text, event):
        if event.keyboardModifiers() == Qt.AltModifier:
            # pymel with namespace
            for k, m in namespace.items():
                if hasattr(m, '__name__'):
                    if m.__name__ == 'pymel.core' and not k == 'm':
                        syntax = []
                        for node in text.split():
                            if namespace[k].objExists(node):
                                syntax.append(k + '.PyNode("%s")' % node)
                            else:
                                syntax.append(node)
                        return '\n'.join(syntax)
            # pymel no namespace
            if 'PyNode' in namespace.keys():
                syntax = []
                for node in text.split():
                    if namespace['objExists'](node):
                        syntax.append('PyNode("%s")' % node)
                    else:
                        syntax.append(node)
                return '\n'.join(syntax)
                # return 'PyNode("%s")' % text

            # cmds with namespace
            for k, m in namespace.items():
                if hasattr(m, '__name__'):
                    if m.__name__ == 'maya.cmds' and not k == 'm':
                        syntax = []
                        for node in text.split():
                            if namespace[k].objExists(node):
                                syntax.append('"%s"' % node)
                            else:
                                syntax.append(node)
                        return '\n'.join(syntax)

            # cmds without namespace
            if 'about' in namespace.keys():
                try:
                    syntax = []
                    for node in text.split():
                        if namespace['objExists'](node):
                            syntax.append('"%s"' % node)
                        else:
                            syntax.append(node)
                    return '\n'.join(syntax)
                except Exception:
                    pass
        return text
