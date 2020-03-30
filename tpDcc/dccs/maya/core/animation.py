# ! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module include functions related with animation
"""

from __future__ import print_function, division, absolute_import

import math
import logging
import traceback

from tpDcc.libs.python import python

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import api, attribute, scene

LOGGER = logging.getLogger()


class InsertRemoveAnimCurveKeys(object):
    def __init__(self, anim_curves=None, start_frame=0, end_frame=0, sequence_least_key=None, sequence_great_key=None):
        self._anim_curves = anim_curves or get_all_anim_curves()
        self._start_frame = start_frame
        self._end_frame = end_frame
        self._sequence_least_key = sequence_least_key or start_frame
        self._sequence_great_key = sequence_great_key or end_frame

        self._inserted_key_curves = dict()

    def key_all_animation_curves_in_given_frame(self, frame, tangent_type='step'):
        """
        Inserts keyframes on all animation curves on given frame
        :param frame: int
        :param tangent_type: str
        :return:
        """

        editable = list()
        for anim_curve in self._anim_curves:
            try:
                keyable = maya.cmds.setKeyframe(anim_curve, insert=True, t=frame)
                if keyable:
                    editable.append(anim_curve)
                    if tangent_type == 'step':
                        maya.cmds.selectKey(anim_curve, add=True, keyframe=True, time=(frame, frame))
                        maya.mel.eval('keyTangent -ott "step";')
            except Exception as exc:
                LOGGER.error(
                    'Error while keying animation curve "{}" on frame "{}" | {} | {}'.format(
                        anim_curve, frame, exc, traceback.format_exc()))

        return editable

    def insert_missing_keys(self):
        """
        Inserts keys on the animation curves if it does not exists yet
        In 'head' frames, tangent is automatically set if frame is on 'head'
        In 'tail' frames, previous key is set to tangent
        :return:
        """

        self._inserted_key_curves = dict()

        all_keyframes = maya.cmds.keyframe(self._anim_curves, query=True, timeChange=True)
        if all_keyframes is not None:
            all_anim_keys = sorted(all_keyframes)
            all_anim_first_key = all_anim_keys[0]
            all_anim_last_key = all_anim_keys[-1]
            if self._sequence_least_key < all_anim_first_key:
                all_anim_first_key = self._sequence_least_key
            if self._sequence_great_key > all_anim_last_key:
                all_anim_last_key = self._sequence_great_key

            for anim_curve in self._anim_curves:
                all_anim_keyframes = maya.cmds.keyframe(anim_curve, query=True, timeChange=True)
                if all_anim_keyframes is None:
                    continue
                all_keys = list(all_anim_keyframes)
                all_anim_keyframes = sorted(all_anim_keyframes)
                first_frame = all_anim_keyframes[0]
                last_frame = all_anim_keyframes[-1]
                for i, key in enumerate((self._start_frame, self._end_frame)):
                    where = 'head'
                    if i == 1:
                        where = 'tail'
                    if where == 'head' and key < first_frame or where == 'tail' and key > last_frame:
                        insert_key = True
                        infinity = maya.cmds.getAttr('{}.preInfinity'.format(anim_curve))
                        if where == 'tail':
                            infinity = maya.cmds.getAttr('{}.postInfinity'.format(anim_curve))
                        if infinity == 3:
                            copy_cycle_first_frame = first_frame
                            copy_cycle_last_frame = last_frame
                            copy_option = 'keys'
                            first_frame_value = round(
                                maya.cmds.keyframe(
                                    anim_curve, query=True, time=(first_frame, first_frame),
                                    valueChange=True)[0], 3)
                            last_frame_value = round(
                                maya.cmds.keyframe(
                                    anim_curve, query=True, time=(last_frame, last_frame),
                                    valueChange=True)[0], 3)
                            if first_frame_value != last_frame_value:
                                copy_option = 'curve'
                                if where == 'head':
                                    copy_cycle_last_frame = last_frame - 1
                                else:
                                    copy_cycle_first_frame = first_frame + 1
                            maya.cmds.copyKey(anim_curve, time=(copy_cycle_first_frame, copy_cycle_last_frame),
                                              float=(copy_cycle_first_frame, copy_cycle_last_frame),
                                              option=copy_option, hierarchy='none', controlPoints=False)
                            cycle_gap = all_anim_first_key - last_frame
                            if where == 'tail':
                                cycle_gap = all_anim_last_key - last_frame
                            total_cycle_frames = last_frame - copy_cycle_first_frame
                            total_cycles = cycle_gap / total_cycle_frames
                            total_cycles_to_paste = int(math.ceil(abs(total_cycles)))
                            time_offset = 0
                            paste_frame = last_frame
                            if copy_option:
                                paste_frame = last_frame
                                time_offset = 1
                            if where == 'head':
                                paste_frame = first_frame - total_cycle_frames * total_cycles_to_paste
                                if copy_option == 'curve':
                                    paste_frame = first_frame - 1 - total_cycle_frames * total_cycles_to_paste
                            maya.cmds.pasteKey(
                                anim_curve, time=(paste_frame, paste_frame), option='merge',
                                copies=total_cycles_to_paste, connect=False, timeOffset=time_offset,
                                floatOffset=0, valueOffset=0)
                            insert_key = False

                        if insert_key:
                            neight_inn_tangent = None
                            neight_out_tangent = None
                            if where == 'head':
                                if all_keys and first_frame in all_keys:
                                    key_index = all_keys.index(first_frame)
                                    neight_inn_tangent = maya.mel.eval(
                                        'keyTangent -q -inTangentType {};'.format(anim_curve))[key_index]
                                    neight_out_tangent = maya.mel.eval(
                                        'keyTangent -q -outTangentType {};'.format(anim_curve))[key_index]
                            maya.cmds.setKeyframe(anim_curve, insert=True, time=key)
                            self._inserted_key_curves = self._add_to_delete_keys_dict(
                                key, [anim_curve, [key, neight_inn_tangent, neight_out_tangent]],
                                self._inserted_key_curves)
                            if infinity == 0:
                                maya.mel.eval(
                                    'keyTangent -time {} -outTangentType "step" {} ;'.format(key, anim_curve))
                                if where == 'tail':
                                    maya.mel.eval(
                                        'keyTangent -time {} -outTangentType "step" {} ;'.format(
                                            last_frame, anim_curve))
                            if where == 'head':
                                maya.mel.eval(
                                    'keyTangent -time {} -inTangentType "{}" -outTangentType "{}" {} ;'.format(
                                        first_frame, neight_inn_tangent, neight_out_tangent, anim_curve))

    def remove_inserted_keys(self):
        """
        Remove keys that have been inserted by callling insert_missing_keys() function
        """

        if not self._inserted_key_curves:
            return

        for key in self._inserted_key_curves:
            for data in self._inserted_key_curves[key]:
                anim_curve = data[0]
                preserve_tangent_key = data[1][0]
                neight_inn_tangent = data[1][1]
                neight_out_tangent = data[1][2]
                maya.cmds.cutKey(anim_curve, time=(key, key), clear=True)
                if neight_inn_tangent is not None:
                    maya.mel.eval(
                        'keyTangent -time {} -inTangentType "{}" -outTangentType "{}" {} ;'.format(
                            preserve_tangent_key, neight_inn_tangent, neight_out_tangent, anim_curve))

    def _add_to_delete_keys_dict(self, key, anim_curve, delete_keys_dict):
        """
        Internal function that updates dict with given key and animation curve
        :param key: str
        :param anim_curve: str
        :param delete_keys_dict: dict
        :return: dict
        """

        if key not in delete_keys_dict:
            delete_keys_dict[key] = [anim_curve]
        else:
            delete_keys_dict[key] += [anim_curve]

        return delete_keys_dict


def get_animation_curve_types():
    """
    Returns a list with all animation curve types available in Maya
    :return: list(str)
    """

    anim_curve_types = ['TA', 'TL', 'TT', 'TU', 'UA', 'UL', 'UT', 'UU']
    return ['animCurve{}'.format(curve_type) for curve_type in anim_curve_types]


def get_node_animation_curves(node):
    """
    Returns all animation curves of the given node
    :param node: str
    :return: list(str)
    """

    return maya.cmds.listConnections(node, t='animCurve') or list()


def get_all_anim_curves(check_validity=True):
    """
    Returns all animation curves in current Maya scene
    :return: list(str)
    """

    anim_curves = maya.cmds.ls(type=get_animation_curve_types()) or list()

    if check_validity:
        return [anim_curve for anim_curve in anim_curves if valid_anim_curve(anim_curve)]
    else:
        return anim_curves


def get_all_keyframes_in_anim_curves(anim_curves=None):
    """
    Retursn al keyframes in given anim curves
    :param anim_curves: list(str)
    :return: list(str)
    """

    if anim_curves is None:
        anim_curves = list()

    if not anim_curves:
        anim_curves = get_all_anim_curves()

    all_keyframes = sorted(maya.cmds.keyframe(anim_curves, query=True)) or list()

    return all_keyframes


def valid_anim_curve(anim_curve):
    """
    Returns whether or not given animation curve is valid or not
    :param anim_curve: str
    :return: bool
    """

    input_connections = maya.cmds.listConnections('{}.input'.format(anim_curve))
    if not maya.cmds.referenceQuery(anim_curve, isNodeReferenced=True) and not input_connections:
        return True
    else:
        return False


def set_infinity_to_linear(keyframe, pre=False, post=False):
    """
    Sets the in and out infinity to linear in the given keyframe
    :param keyframe: str, name of a keyframe
    :param pre: bool, Whether to set pre infinity to linear or not
    :param post: bool, Whether to set post infinity to linear or not
    :return: str, name of the keyframe
    """

    fn = api.KeyframeFunction(keyframe)
    if post:
        fn.set_post_infinity(fn.LINEAR)
    if pre:
        fn.set_pre_infinity(fn.LINEAR)

    return keyframe


def get_keyframe(node_and_attr):
    """
    Given a full node and attribute name returns its inputs keyframe
    :param node_and_attr: str
    :return: str
    """

    connection = attribute.get_attribute_input(node_and_attr, node_only=True)
    if connection is None:
        return None

    node_type = maya.cmds.nodeType(connection)
    if node_type.find('animCurve') > -1:
        return connection


def get_input_keyframes(node, node_only=True):
    """
    Returns all keyframes that input into given node
    :param node: str, name of a node to check for keyframes
    :param node_only: bool, Whether to return just the keyframe name or also the keyframe.output attribute
    :return: list(str), list with all the keyframes connected to the node
    """

    found = list()

    inputs = attribute.get_inputs(node, node_only=node_only)
    if not inputs:
        return found

    for input_value in inputs:
        if maya.cmds.nodeType(input_value).startswith('animCurve'):
            found.append(input_value)

    return found


def get_output_keyframes(node):
    """
    Returns all keyframes that output from the node
    :param node: str, name of a node to check for keyframes
    :return: list(str), list of all keyframes that the node connects into
    """

    found = list()

    outputs = attribute.get_outputs(node)
    if not outputs:
        return found

    for output in outputs:
        if maya.cmds.nodeType(output).startswith('animCurve'):
            found.append(output)

    return found


def get_maya_animation_importer_export_plugin_name():
    """
    Returns the name of the plugin used by Maya to export/import animations
    :return: str
    """

    return 'animImportExport'


def load_maya_animation_import_export_plugin():
    """
    Loads (if it is not already loaded), Maya animation import/export plugin
    :return: bool
    """

    anim_plugin_name = get_maya_animation_importer_export_plugin_name()

    if not maya.cmds.pluginInfo(anim_plugin_name, query=True, loaded=True, n=True):
        try:
            maya.cmds.loadPlugin(anim_plugin_name)
            plugin_path = maya.cmds.pluginInfo(anim_plugin_name, query=True, path=True)
            maya.cmds.pluginInfo(plugin_path, edit=True, autoload=True)
            maya.cmds.pluginInfo(savePluginPrefs=True)
        except Exception as exc:
            LOGGER.error(
                'Error importing animation plugin: "{}" | {} | {}'.format(
                    anim_plugin_name, exc, traceback.format_exc()))
            return False

    return True


def convert_start_end_frame_anim_curve_tangents_to_fixed(anim_curves, frames):
    """
    Converts first and last frame keys of given curves to fixed tangents
    :param anim_curves: list(str)
    :param frames: list(int, int), start and end frames
    :return:
    """

    for anim_curve in anim_curves:
        all_keys = maya.cmds.keyframe(anim_curve, query=True, timeChange=True) or list()
        for i, frame in enumerate(frames):
            existing_frame = maya.cmds.keyframe(anim_curve, query=True, time=(frame, frame))
            if existing_frame is not None:
                if not all_keys or frame not in all_keys:
                    LOGGER.warning('Frame {} not found in {} keys for animation curve "{}"'.format(
                        frame, len(all_keys), anim_curve))
                    continue
                key_index = all_keys.index(frame)
                current_tangent_out = maya.mel.eval('keyTangent -q -ott {}'.format(anim_curve))[key_index]
                if current_tangent_out != 'step' and current_tangent_out != 'stepnext':
                    maya.mel.eval('keyTangent -time {} -outTangentType "fixed" {} ;'.format(frame, anim_curve))
                if i == 0:
                    maya.mel.eval('keyTangent -time {} -inTangentType "flat" {} ;'.format(frame, anim_curve))
                else:
                    maya.mel.eval('keyTangent -time {} -inTangentType "fixed" {} ;'.format(frame, anim_curve))


def key_all_anim_curves_in_frames(frames, anim_curves=None):
    """
    Inserts keyframes on all animation curves on given frame
    :param frame: list(int)
    :param anim_curves: list(str)
    """

    frames = python.force_list(frames)

    anim_curves = anim_curves or get_all_anim_curves()
    insert_anim_keys = InsertRemoveAnimCurveKeys(anim_curves=anim_curves)
    for frame in frames:
        return insert_anim_keys.key_all_animation_curves_in_given_frame(frame)


def delete_keys_from_animation_curves_in_range(range_to_delete, anim_curves=None):
    """
    Removes kesy in given animation and in the given range
    :param range_to_delete: list(int, int), start and end frames to delete frames from
    :param anim_curves: list(str)
    :return:
    """

    anim_curves = anim_curves or get_all_anim_curves()

    return maya.cmds.cutKey(anim_curves, time=range_to_delete, clear=True)


def check_anim_curves_has_fraction_keys(anim_curves, selected_range=None):
    """
    Returns whether or not given curves have or not fraction keys
    :param anim_curves: list(str)
    :param selected_range: list(str)
    :return: bool
    """

    fraction_keys = list()
    selected_keys = maya.cmds.keyframe(query=True, selected=True)
    if selected_range is not None and type(selected_range) in [list, tuple]:
        selected_start = selected_range[0]
        selected_end = selected_range[-1] - 1
        for anim_curve in anim_curves:
            all_keyframes = maya.cmds.keyframe(anim_curve, query=True)
            if all_keyframes is not None:
                for keyframe in all_keyframes:
                    if not keyframe.is_integer() and selected_start <= keyframe \
                            <= selected_end and keyframe not in fraction_keys:
                        fraction_keys.append(keyframe)
    elif selected_range is False and selected_keys is not None:
        fraction_keys = [k for k in list(set(selected_keys)) if not k.is_integer()]
    else:
        for anim_curve in anim_curves:
            all_keyframes = maya.cmds.keyframe(anim_curve, query=True)
            if all_keyframes is not None:
                for keyframe in all_keyframes:
                    if not keyframe.is_integer() and keyframe not in fraction_keys:
                        fraction_keys.append(keyframe)

    return len(fraction_keys) > 0


def convert_fraction_keys_to_whole_keys(animation_curves, consider_selected_range=False):
    """
    Find keys on fraction of a frame and insert a key on the nearest whole number frame
    Useful to make sure that no keys are located on fraction of frames
    :param animation_curves: list(str)
    :param consider_selected_range: bool
    :return:
    """

    from tpDcc.dccs.maya.core import gui

    if not animation_curves:
        animation_curves = get_all_anim_curves()
    if not animation_curves:
        return

    selected_keys = False
    selected_range = None
    if consider_selected_range:
        timeline = gui.get_playblack_slider()
        slider_range = maya.cmds.timeControl(timeline, query=True, rangeArray=True)
        if maya.cmds.keyframe(query=True, selected=True) is not None:
            animation_curves = maya.cmds.keyframe(query=True, selected=True, name=True)
            selected_keys = True
            selected_range = False
        elif slider_range[1] - slider_range[0] > 1:
            selected_range = slider_range

    if not check_anim_curves_has_fraction_keys(animation_curves, selected_range=selected_range):
        return

    anim_curve_count = len(animation_curves)
    LOGGER.info('Cleaning {} animation curve'.format(anim_curve_count))

    all_frames_fixed = list()
    failed_fixes = dict()

    for anim_curve in animation_curves:
        keyframes = maya.cmds.keyframe(anim_curve, query=True)
        if consider_selected_range:
            if selected_keys:
                keyframes = maya.cmds.keyframe(anim_curve, query=True, selected=True)
            elif selected_range is not None and type(selected_range) in [list, tuple] and keyframes is not None:
                selected_start = selected_range[0]
                selected_end = selected_range[-1] - 1
                keyframes = [frame for frame in keyframes if selected_start <= frame <= selected_end]
        if keyframes is None:
            continue

        keys_inserted = list()
        keys_fraction_to_delete = list()
        for frame in keyframes:
            if not frame.is_integer():
                round_frame = round(frame)
                if round_frame in keyframes or round_frame in keys_inserted:
                    try_again = True
                    if round_frame > frame:
                        round_frame = math.floor(frame)
                        if round_frame not in keyframes and round_frame not in keys_inserted:
                            try_again = False
                    if round_frame < frame and try_again:
                        round_frame = math.ceil(frame)
                        if round_frame not in keyframes and round_frame not in keys_inserted:
                            try_again = False
                        if try_again:
                            keys_fraction_to_delete.append(frame)
                            continue

                is_hold = False
                current_value = maya.cmds.keyframe(anim_curve, time=(frame, frame), query=True, valueChange=True)[0]
                frame_index = keyframes.index(frame)
                if frame_index != 0:
                    pre_frame = keyframes[frame_index - 1]
                    pre_value = maya.cmds.keyframe(
                        anim_curve, time=(pre_frame, pre_frame), query=True, valueChange=True)
                    if pre_value is not None and current_value == pre_value[0]:
                        is_hold = True
                if frame_index != keyframes.index(keyframes[-1]):
                    post_frame = keyframes[frame_index + 1]
                    post_value = maya.cmds.keyframe(
                        anim_curve, time=(post_frame, post_frame), query=True, valueChange=True)
                    if post_value is not None and current_value == post_value[0]:
                        is_hold = True
                try:
                    if is_hold:
                        maya.cmds.keyframe(
                            anim_curve, edit=True, absolute=True, timeChange=round_frame, time=(frame, frame))
                    else:
                        maya.cmds.setKeyframe(anim_curve, insert=True, t=round_frame)
                    keys_inserted.append(round_frame)
                except Exception as exc:
                    error_msg = 'AnimCurve: {}\n'.format(anim_curve)
                    if is_hold:
                        error_msg += 'Tried to move a key from frame {} to frame {} to maintain a hold with ' \
                                     'a value of {}. Usually failed due to keyframe already existing on frame trying ' \
                                     'to move to'.format(frame, round_frame, current_value)
                    else:
                        error_msg += 'Tried to insert a key on frame {} to preserve animation curve shape to replace' \
                                     ' key on frame {}'.format(round_frame, frame)
                    LOGGER.error(error_msg)
                    if anim_curve not in failed_fixes:
                        failed_fixes[anim_curve] = [frame]
                    else:
                        failed_fixes[anim_curve].append(frame)

                keys_fraction_to_delete.append(frame)

        for frame_to_delete in keys_fraction_to_delete:
            maya.cmds.cutKey(anim_curve, time=(frame_to_delete, frame_to_delete), clear=True)

        all_frames_fixed += keys_inserted

    frames_fixed = list()
    [frames_fixed.append(ff) for ff in all_frames_fixed if ff not in frames_fixed]
    if len(frames_fixed) > 0:
        LOGGER.info('Fixed keys on {} frames to be on a whole number frame.\n'.format(len(frames_fixed)))
    else:
        LOGGER.info('No keyframes found on a fraction of frame. All keyframes are on whole number frames.\n')
    if len(failed_fixes) > 0:
        LOGGER.warning('Could not put {} keyframe(s) on a whole frame'.format(len(failed_fixes)))
        for i, crv in enumerate(failed_fixes, 1):
            LOGGER.warning('\t{}. "{}" : {}'.format(i, crv, failed_fixes[crv]))


def get_active_frame_range():
    """
    Returns current animation frame range
    :return: tuple(int, int)
    """

    return maya.cmds.playbackOptions(query=True, minTime=True), maya.cmds.playbackOptions(query=True, maxTime=True)


def set_active_frame_range(start_frame, end_frame):
    """
    Sets current animation frame range
    :param start_frame: int
    :param end_frame: int
    """

    return maya.cmds.playbackOptions(
        animationStartTime=start_frame, minTime=start_frame, animationEndTime=end_frame, maxTime=end_frame)


def bake_animation(nodes, min_time=None, max_time=None):
    """
    Bakes animation on given nodes.
    This function ensures that no flipping happens during animation baking
    :param nodes: list(str)
    :param min_time: float
    :param max_time: float
    """

    if not min_time or not max_time:
        min_time, max_time = get_active_frame_range()

    maya.cmds.bakeResults(
        nodes, simulation=True, t=(min_time, max_time), sampleBy=1, oversamplingRate=1, disableImplicitControl=True,
        preserveOutsideKeys=True, sparseAnimCurveBake=True, removeBakedAttributeFromLayer=False, shape=False,
        removeBakedAnimFromLayer=True, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False)

    maya.cmds.filterCurve(nodes)


def quick_driven_key(source, target, source_values, target_values, infinite=False, tangent_type='linear'):
    """
    Simple function that simplifies the process of creating driven keys
    :param source: str, node.attribute to drive target wit
    :param target: node.attribute to be driven by source
    :param source_values: list, list of values at the source
    :param target_values: list, list of values at the target
    :param infinite: bool, Whether to infinite or not anim curves
    :param tangent_type: str, type of tangent type to create for anim curves
    """

    track_nodes = scene.TrackNodes()
    track_nodes.load('animCurve')

    if not type(tangent_type) == list:
        tangent_type = [tangent_type, tangent_type]

    for i in range(len(source_values)):
        maya.cmds.setDrivenKeyframe(
            target, cd=source, driverValue=source_values[i],
            value=target_values[i], itt=tangent_type[0], ott=tangent_type[1])

    keys = track_nodes.get_delta()
    if not keys:
        return

    keyframe = keys[0]
    fn = api.KeyframeFunction(keyframe)
    if infinite:
        fn.set_pre_infinity(fn.LINEAR)
        fn.set_pre_infinity(fn.LINEAR)
    if infinite == 'post_only':
        fn.set_post_infinity(fn.LINEAR)
        fn.set_pre_infinity(fn.CONSTANT)
    if infinite == 'pre_only':
        fn.set_pre_infinity(fn.LINEAR)
        fn.set_post_infinity(fn.CONSTANT)

    return keyframe
