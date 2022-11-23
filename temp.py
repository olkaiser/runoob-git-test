# -*- coding: iso-8859-1 -*-

#   Copyright 2010 Pepijn de Vos
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""The goal of PyMouse is to have a cross-platform way to control the mouse.
PyMouse should work on Windows, Mac and any Unix that has xlib.

See http://github.com/pepijndevos/PyMouse for more information.
"""

import sys
from threading import Thread

class PyMouseMeta(object):

    def press(self, x, y, button = 1):
        """Press the mouse on a givven x, y and button.
        Button is defined as 1 = left, 2 = right, 3 = middle."""

        raise NotImplementedError

    def release(self, x, y, button = 1):
        """Release the mouse on a givven x, y and button.
        Button is defined as 1 = left, 2 = right, 3 = middle."""

        raise NotImplementedError

    def click(self, x, y, button = 1):
        """Click the mouse on a givven x, y and button.
        Button is defined as 1 = left, 2 = right, 3 = middle."""

        self.press(x, y, button)
        self.release(x, y, button)
 
    def move(self, x, y):
        """Move the mouse to a givven x and y"""

        raise NotImplementedError

    def position(self):
        """Get the current mouse position in pixels.
        Returns a tuple of 2 integers"""

        raise NotImplementedError

    def screen_size(self):
        """Get the current screen size in pixels.
        Returns a tuple of 2 integers"""

        raise NotImplementedError

class PyMouseEventMeta(Thread):
    
    deamon = True
    capture = False
    state = True

    def stop(self):
        self.state = False

    def click(self, x, y, button, press):
        """Subclass this method with your click event handler"""

        pass

    def move(self, x, y):
        """Subclass this method with your move event handler"""

        pass



if sys.platform.startswith('java'):
    from java_ import PyMouse

elif sys.platform == 'darwin':
    from mac import PyMouse, PyMouseEvent

elif sys.platform == 'win32':
    from windows import PyMouse, PyMouseEvent

else:
    from unix import PyMouse, PyMouseEvent




################

# -*- coding: iso-8859-1 -*-

#   Copyright 2010 Pepijn de Vos
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

clicks = [None, 2, 8, 32]
releases = [None, 4, 16, 64]

from ctypes import *
from win32api import GetSystemMetrics
from pymouse import PyMouseMeta, PyMouseEventMeta
import pythoncom, pyHook
from time import sleep

PUL = POINTER(c_ulong)
class MouseInput(Structure):
    _fields_ = [("dx", c_long),
             ("dy", c_long),
             ("mouseData", c_ulong),
             ("dwFlags", c_ulong),
             ("time",c_ulong),
             ("dwExtraInfo", PUL)]

class Input_I(Union):
    _fields_ = [("mi", MouseInput)]

class Input(Structure):
    _fields_ = [("type", c_ulong), ("ii", Input_I)]

FInputs = Input * 2
extra = c_ulong(0)

click = Input_I()
click.mi = MouseInput(0, 0, 0, 2, 0, pointer(extra))
release = Input_I()
release.mi = MouseInput(0, 0, 0, 4, 0, pointer(extra))

blob = FInputs( (0, click), (0, release) )

class POINT(Structure):
    _fields_ = [("x", c_ulong),
                ("y", c_ulong)]

class PyMouse(PyMouseMeta):
    def press(self, x, y, button = 1):
        self.move(x, y)
        blob[0].ii.mi.dwFlags = clicks[button]
        windll.user32.SendInput(2,pointer(blob),sizeof(blob[0]))

    def release(self, x, y, button = 1):
        self.move(x, y)
        blob[1].ii.mi.dwFlags = releases[button]
        windll.user32.SendInput(2,pointer(blob),sizeof(blob[0]))

    def move(self, x, y):
        windll.user32.SetCursorPos(x, y)

    def position(self):
        pt = POINT()
        windll.user32.GetCursorPos(byref(pt))
        return pt.x, pt.y

    def screen_size(self):
        width = GetSystemMetrics(0)
        height = GetSystemMetrics(1)
        return width, height

class PyMouseEvent(PyMouseEventMeta):
    def run(self):
        hm = pyHook.HookManager()
        hm.MouseAllButtons = self._click
        hm.MouseMove = self._move
        hm.HookMouse()

        while self.state:
            sleep(0.01)
            pythoncom.PumpWaitingMessages()

    def _click(self, event):
        x,y = event.Position

        if event.Message == pyHook.HookConstants.WM_LBUTTONDOWN:
            self.click(x, y, 1, True)
        elif event.Message == pyHook.HookConstants.WM_LBUTTONUP:
            self.click(x, y, 1, False)
        elif event.Message == pyHook.HookConstants.WM_RBUTTONDOWN:
            self.click(x, y, 2, True)
        elif event.Message == pyHook.HookConstants.WM_RBUTTONUP:
            self.click(x, y, 2, False)
        elif event.Message == pyHook.HookConstants.WM_MBUTTONDOWN:
            self.click(x, y, 3, True)
        elif event.Message == pyHook.HookConstants.WM_MBUTTONUP:
            self.click(x, y, 3, False)
        return not self.capture

    def _move(self, event):
        x,y = event.Position
        self.move(x, y)
        return not self.capture
