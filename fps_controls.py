# coding=utf-8
"""A utility class that takes handles keys for a FPS-style control scheme."""
from direct.showbase import ShowBase


class FPSControls:
    """Takes in Panda3D event handling and translates those to an easily
    usable format.
    """
    def __init__(self, base: ShowBase):
        self.base = base
