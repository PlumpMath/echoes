# coding=utf-8
"""A utility class that takes handles keys for a FPS-style control scheme."""
from weakref import proxy

from direct.showbase import ShowBase
from panda3d.core import WindowProperties


class FPSControls:
    """Takes in Panda3D event handling and translates those to an easily
    usable format.
    """
    __captured = False  # internal tracking of mouse capture state

    def __init__(self, base: ShowBase):
        self.base = proxy(base)
        self.mouse_captured = True

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
