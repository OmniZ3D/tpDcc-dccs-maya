#! /usr/bin/env python

"""
Helper utility methods related with time in Maya
"""

from __future__ import print_function, division, absolute_import, unicode_literals

# region Imports
from collections import OrderedDict

import maya.cmds as cmds
from maya import OpenMaya
# endregion

time_unit_to_fps = OrderedDict()
for k, v in (
('game', 15), ('film', 24), ('pal', 25), ('ntsc', 30), ('show', 48), ('palf', 50), ('ntscf', 60), ('millisec', 1000),
('sec', 1), ('min', 1 / 60.0), ('hour', 1 / 3600.0)):
    time_unit_to_fps.update({k: v})
for val in (2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 40, 75, 80, 100, 120, 125, 150,
            200, 240, 250, 300, 375, 400, 500, 600, 750, 1200, 1500, 2000, 3000, 6000):
    time_unit_to_fps.update({'{}fps'.format(val): val})

time_unit_to_const = dict([(v, i) for i, v in time_unit_to_fps.items()])

# This is used because OpenMaya.MTime doesnt't default to the current fps setting
fps_to_mtime = OrderedDict()
fps_to_mtime.update({'hour': OpenMaya.MTime.kHours})
fps_to_mtime.update({'min': OpenMaya.MTime.kMinutes})
fps_to_mtime.update({'sec': OpenMaya.MTime.kSeconds})  # 1 fps
fps_to_mtime.update({'2fps': OpenMaya.MTime.k2FPS})
fps_to_mtime.update({'3fps': OpenMaya.MTime.k3FPS})
fps_to_mtime.update({'4fps': OpenMaya.MTime.k4FPS})
fps_to_mtime.update({'5fps': OpenMaya.MTime.k5FPS})
fps_to_mtime.update({'6fps': OpenMaya.MTime.k6FPS})
fps_to_mtime.update({'8fps': OpenMaya.MTime.k8FPS})
fps_to_mtime.update({'10fps': OpenMaya.MTime.k10FPS})
fps_to_mtime.update({'12fps': OpenMaya.MTime.k12FPS})
fps_to_mtime.update({'game': OpenMaya.MTime.kGames})  # 15 FPS
fps_to_mtime.update({'16fps': OpenMaya.MTime.k16FPS})
fps_to_mtime.update({'20fps': OpenMaya.MTime.k20FPS})
fps_to_mtime.update({'film': OpenMaya.MTime.kFilm})  # 24 fps
fps_to_mtime.update({'pal': OpenMaya.MTime.kPALFrame})  # 25 fps
fps_to_mtime.update({'ntsc': OpenMaya.MTime.kNTSCFrame})  # 30 fps
fps_to_mtime.update({'40fps': OpenMaya.MTime.k40FPS})
fps_to_mtime.update({'show': OpenMaya.MTime.kShowScan})  # 48 fps
fps_to_mtime.update({'palf': OpenMaya.MTime.kPALField})  # # 50 fps
fps_to_mtime.update({'ntscf': OpenMaya.MTime.kNTSCField})  # 60 fps
fps_to_mtime.update({'75fps': OpenMaya.MTime.k75FPS})
fps_to_mtime.update({'80fps': OpenMaya.MTime.k80FPS})
fps_to_mtime.update({'100fps': OpenMaya.MTime.k100FPS})
fps_to_mtime.update({'120fps': OpenMaya.MTime.k120FPS})
fps_to_mtime.update({'125fps': OpenMaya.MTime.k125FPS})
fps_to_mtime.update({'150fps': OpenMaya.MTime.k150FPS})
fps_to_mtime.update({'200fps': OpenMaya.MTime.k200FPS})
fps_to_mtime.update({'240fps': OpenMaya.MTime.k240FPS})
fps_to_mtime.update({'250fps': OpenMaya.MTime.k250FPS})
fps_to_mtime.update({'300fps': OpenMaya.MTime.k300FPS})
fps_to_mtime.update({'375fps': OpenMaya.MTime.k375FPS})
fps_to_mtime.update({'400fps': OpenMaya.MTime.k400FPS})
fps_to_mtime.update({'500fps': OpenMaya.MTime.k500FPS})
fps_to_mtime.update({'600fps': OpenMaya.MTime.k600FPS})
fps_to_mtime.update({'750fps': OpenMaya.MTime.k750FPS})
fps_to_mtime.update({'millisec': OpenMaya.MTime.kMilliseconds})  # 1000 fps
fps_to_mtime.update({'1200fps': OpenMaya.MTime.k1200FPS})
fps_to_mtime.update({'1500fps': OpenMaya.MTime.k1500FPS})
fps_to_mtime.update({'2000fps': OpenMaya.MTime.k2000FPS})
fps_to_mtime.update({'3000fps': OpenMaya.MTime.k3000FPS})
fps_to_mtime.update({'6000fps': OpenMaya.MTime.k6000FPS})


# region Functions
def current_time_unit():
    """
    Returns the current time unit name.
    :return: str, name of the current fps
    """

    return cmds.currentUnit(query=True, time=True)
# endregion