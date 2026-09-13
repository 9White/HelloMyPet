# -*- coding: utf-8 -*-
"""带日志的伸懒腰验证：追踪动作切换来源"""
import sys
import time

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

import pet_qt

t0 = time.time()


def log(msg):
    print("%6.2f %s" % (time.time() - t0, msg), flush=True)


# 打桩
_orig_start = pet_qt.PetWindow._start_action
_orig_run = pet_qt.PetWindow._run_random_action
_orig_exit = pet_qt.PetWindow._exit_sequence
_orig_end = pet_qt.PetWindow._end_action
_orig_back = pet_qt.PetWindow._back_idle
_orig_trans = pet_qt.PetWindow._transition_to


def p_start(self, name, dur):
    log("start_action %s dur=%s state=%s" % (name, dur, self.state))
    return _orig_start(self, name, dur)


def p_run(self):
    log("run_random state=%s" % self.state)
    return _orig_run(self)


def p_exit(self, s):
    log("exit_sequence state=%s name=%s" % (self.state, s["name"]))
    return _orig_exit(self, s)


def p_end(self):
    log("end_action state=%s last=%s" % (self.state, self._last_action_name))
    return _orig_end(self)


def p_back(self):
    log("back_idle")
    return _orig_back(self)


def p_trans(self, name, after_done=None):
    log("transition_to %s state=%s" % (name, self.state))
    return _orig_trans(self, name, after_done)


pet_qt.PetWindow._start_action = p_start
pet_qt.PetWindow._run_random_action = p_run
pet_qt.PetWindow._exit_sequence = p_exit
pet_qt.PetWindow._end_action = p_end
pet_qt.PetWindow._back_idle = p_back
pet_qt.PetWindow._transition_to = p_trans

app = pet_qt.QApplication(sys.argv)
w = pet_qt.PetWindow()
w.show()

QTimer.singleShot(300, lambda: w._start_action("stretch", 0))
QTimer.singleShot(15000, app.quit)
sys.exit(app.exec())
