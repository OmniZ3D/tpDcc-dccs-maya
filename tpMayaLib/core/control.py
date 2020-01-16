# from tpRigToolkit.core.tools.controlrig import controlriglib
#
#
# class RigControl(object):
#     """
#     Base class to create controls
#     """
#
#     def __init__(
#             self,
#             ctrl_name,
#             name='new_ctrl',
#             scale=1,
#             translate_to=None,
#             rotate_to=None,
#             parent=None,
#             lock_channels=['s', 'v'],
#             create_root=True,
#             create_auto=True,
#             auto_rename=False,
#             rotate_order=0,
#             color=None):
#
#         self._auto_rename = auto_rename
#
#     def create(self):
#
#         # TODO: Check if color apply should be managed by ControlManager or not
#         ctrl_obj = controlriglib.create_control_by_name(
#             ctrl_name=self._ctrl_name if self._ctrl_name else 'circle',
#             name=self._name,
#             size=self._scale,
#             axis_order=str(self._rotate_order).split('.')[-1]
#         )[0][0]
#         ctrl_new_name = ctrl_obj
#         if self._auto_rename:
#             ctrl_new_name = ctrl_obj + '_ctrl'
#             cmds.rename(ctrl_obj, ctrl_new_name)
#
#         self._node = ctrl_new_name
#
#         ctrl_shapes = cmds.listRelatives(ctrl_new_name, shapes=True)
#         if self._create_auto:
#             self._auto = cmds.group(ctrl_shapes[0], name=ctrl_new_name+'_auto_grp')
#         if self._create_root:
#             if self._create_auto:
#                 self._root = cmds.group(self.auto, name=ctrl_new_name+'_root_grp')
#             else:
#                 self._root = cmds.group(ctrl_shapes[0], name=ctrl_new_name + '_root_grp')
#
#         target_obj = ctrl_new_name
#         if self.root:
#             target_obj = self.root
#
#         if self._translate_to and cmds.objExists(self._translate_to):
#             cmds.delete(cmds.pointConstraint(self._translate_to, target_obj))
#         if self._rotate_to and cmds.objExists(self._rotate_to):
#             cmds.delete(cmds.orientConstraint(self._rotate_to, target_obj))
#
#         if self._parent and cmds.objExists(self._parent):
#             cmds.parent(target_obj, self._parent)
#
#         single_attr_lock_list = list()
#         for lock in self._lock_channels:
#             if lock in ['t', 'r', 's']:
#                 for axis in 'xyz':
#                     attr = lock + axis
#                     single_attr_lock_list.append(attr)
#             else:
#                 single_attr_lock_list.append(lock)
#
#         for attr in single_attr_lock_list:
#             cmds.setAttr('{}.{}'.format(ctrl_new_name, attr), lock=True, keyable=False)
#             if self.auto:
#                 cmds.setAttr('{}.{}'.format(self.auto, attr), lock=True, keyable=False)
#             if self.root:
#                 cmds.setAttr('{}.{}'.format(self.root, attr), lock=True, keyable=False)
