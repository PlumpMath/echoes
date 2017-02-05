# coding=utf-8
"""A utility class that takes handles keys for a FPS-style control scheme."""
import enum
from weakref import proxy

from direct.showbase import ShowBase
from panda3d.core import ButtonMap
from panda3d.core import KeyboardButton
from panda3d.core import WindowProperties


class ActionKey(str, enum.Enum):
    """An enum that contains currently registered key codes for each action."""
    Menu = 'escape'
    Up = 'w'
    Left = 'a'
    Right = 'd'
    Down = 's'
    Jump = 'space'
    Fly = 'tab'


class FPSControls:
    """Takes in Panda3D event handling and translates those to an easily
    usable format.
    """
    __captured = False  # internal tracking of mouse capture state

    def __init__(self, base: ShowBase):
        self.base = proxy(base)
        self.__keymap: ButtonMap = base.win.get_keyboard_map()
        self.mouse_captured = True

        # Register keystrokes.
        self.base.accept(ActionKey.Menu, self.toggle_mouse_capture)

    def key_pressed(self, key: ActionKey) -> bool:
        """Returns True if the key bound to the action is currently pressed."""
        button = self.__keymap.get_mapped_button(key)
        # noinspection PyCallByClass,PyTypeChecker
        # button = KeyboardButton.asciiKey(key.value.encode())  # TODO: non-ascii?
        return self.base.mouseWatcherNode.is_button_down(button)

    # TODO: Probably remove the property here.
    @property
    def mouse_captured(self) -> bool:
        """When true, the mouse is captured by the window and is invisible."""
        return self.__captured

    @mouse_captured.setter
    def mouse_captured(self, value: bool):
        props = WindowProperties()
        props.setCursorHidden(value)
        if value:
            props.setMouseMode(WindowProperties.M_relative)
        else:
            props.setMouseMode(WindowProperties.M_absolute)
        self.base.win.requestProperties(props)
        self.__captured = value

    def toggle_mouse_capture(self):
        """Toggle the capture state of the mouse"""
        self.mouse_captured = not self.mouse_captured
