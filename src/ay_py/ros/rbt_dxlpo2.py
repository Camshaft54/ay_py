#! /usr/bin/env python
#Robot controller for DxlpO2 gripper.
from const import *

from robot import TGripper2F1,TMultiArmRobot
from ..misc.dxl_dxlpo2 import TDxlpO2


'''DxlpO2 gripper utility class'''
class TDxlpO2Gripper(TGripper2F1):
  def __init__(self, dev='/dev/ttyUSB0'):
    super(TDxlpO2Gripper,self).__init__()

    self.dxlpo2= TDxlpO2(dev=dev)

  '''Initialize (e.g. establish ROS connection).'''
  def Init(self):
    self._is_initialized= self.dxlpo2.Init()

    if self._is_initialized:
      self.dxlpo2.StartStateObs()
      self.dxlpo2.StartMoveTh()

    return self._is_initialized

  def Cleanup(self):
    if self._is_initialized:
      self.dxlpo2.StopMoveTh()
      self.dxlpo2.StopStateObs()
      self.dxlpo2.Cleanup()
      self._is_initialized= False
    super(TDxlpO2Gripper,self).Cleanup()

  '''Answer to a query q by {True,False}. e.g. Is('Robotiq').'''
  def Is(self, q):
    if q=='DxlpO2Gripper':  return True
    return super(TDxlpO2Gripper,self).Is(q)

  '''Get current position.'''
  def Position(self):
    return self.dxlpo2.State()['position']

  '''Get a fingertip height offset in meter.
    The fingertip trajectory of some grippers has a rounded shape.
    This function gives the offset from the highest (longest) point (= closed fingertip position),
    and the offset is always negative.
      pos: Gripper position to get the offset. '''
  def FingertipOffset(self, pos):
    #WARNING: NotImplemented
    return 0.0

  def PosRange(self):
    return self.dxlpo2.PosRange()
  def Activate(self):
    return self.dxlpo2.Activate()
  def Deactivate(self):
    return self.dxlpo2.Deactivate()
  def Open(self, blocking=False):
    self.Move(pos=self.dxlpo2.gripper_range[1], blocking=blocking)
  def Close(self, blocking=False):
    self.Move(pos=self.dxlpo2.gripper_range[0], blocking=blocking)
  def Move(self, pos, max_effort=50.0, speed=50.0, blocking=False):
    self.dxlpo2.MoveTh(pos, max_effort, speed, blocking)
  def Stop(self):
    self.dxlpo2.StopMoveTh()


'''Robot control class for DxlpO2Gripper.
  This is defined as a subclass of TMultiArmRobot,
  but actually it does not have a body (only DxlpO2Gripper gripper).
  This virtual body is designed for a compatibility of programs.'''
class TRobotDxlpO2Gripper(TMultiArmRobot):
  def __init__(self, name='DxlpO2Gripper', dev='/dev/ttyUSB0'):
    super(TRobotDxlpO2Gripper,self).__init__(name=name)
    self.currarm= 0
    self.dev= dev

  '''Initialize (e.g. establish ROS connection).'''
  def Init(self):
    self._is_initialized= False
    res= []
    ra= lambda r: res.append(r)

    self.dxlpo2_gripper= TDxlpO2Gripper(dev=self.dev)
    self.grippers= [self.dxlpo2_gripper]

    print 'Initializing and activating DxlpO2Gripper gripper...'
    ra(self.dxlpo2_gripper.Init())

    if False not in res:  self._is_initialized= True
    return self._is_initialized

  def Cleanup(self):
    #NOTE: cleaning-up order is important. consider dependency
    self.dxlpo2_gripper.Cleanup()
    super(TRobotDxlpO2Gripper,self).Cleanup()

  '''Answer to a query q by {True,False}. e.g. Is('PR2').'''
  def Is(self, q):
    if q in ('DxlpO2','DxlpO2Gripper'):  return True
    return super(TRobotDxlpO2Gripper,self).Is(q)

  @property
  def NumArms(self):
    return 1

  @property
  def BaseFrame(self):
    return 'world'

  '''Return range of gripper.
    arm: arm id, or None (==currarm). '''
  def GripperRange(self, arm=None):
    arm= 0
    return self.grippers[arm].PosRange()

  '''End effector of an arm.'''
  def EndEff(self, arm):
    arm= 0
    return self.grippers[arm]

  #Dummy FK.
  def FK(self, q=None, x_ext=None, arm=None, with_st=False):
    x_res= [0,0,0, 0,0,0,1]
    return (x_res, True) if with_st else x_res

  '''Open a gripper.
    arm: arm id, or None (==currarm).
    blocking: False: move background, True: wait until motion ends.  '''
  def OpenGripper(self, arm=None, blocking=False):
    arm= 0
    gripper= self.grippers[arm]
    with self.gripper_locker:
      gripper.Open(blocking=blocking)

  '''Close a gripper.
    arm: arm id, or None (==currarm).
    blocking: False: move background, True: wait until motion ends.  '''
  def CloseGripper(self, arm=None, blocking=False):
    arm= 0
    gripper= self.grippers[arm]
    with self.gripper_locker:
      gripper.Close(blocking=blocking)

  '''High level interface to control a gripper.
    arm: arm id, or None (==currarm).
    pos: target position in meter.
    max_effort: maximum effort to control; 0 (weakest), 100 (strongest).
    speed: speed of the movement; 0 (minimum), 100 (maximum).
    blocking: False: move background, True: wait until motion ends.  '''
  def MoveGripper(self, pos, max_effort=50.0, speed=50.0, arm=None, blocking=False):
    arm= 0
    gripper= self.grippers[arm]
    with self.gripper_locker:
      gripper.Move(pos, max_effort, speed, blocking=blocking)

  '''Get a gripper position in meter.
    arm: arm id, or None (==currarm). '''
  def GripperPos(self, arm=None):
    arm= 0
    gripper= self.grippers[arm]
    with self.sensor_locker:
      pos= gripper.Position()
    return pos

  '''Get a fingertip height offset in meter.
    The fingertip trajectory of some grippers has a rounded shape.
    This function gives the offset from the highest (longest) point (= closed fingertip position),
    and the offset is always negative.
    NOTE: In the previous versions (before 2019-12-10), this offset was from the opened fingertip position.
      pos: Gripper position to get the offset. None: Current position.
      arm: arm id, or None (==currarm).'''
  def FingertipOffset(self, pos=None, arm=None):
    arm= 0
    if pos is None:  pos= self.GripperPos(arm)
    return self.grippers[arm].FingertipOffset(pos)


