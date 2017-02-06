# coding=utf-8
"""Classes containing the state of a player."""
from panda3d.core import Vec2D, Vec3D


class Character:
    """A decision-making object with some sort of controls, whether AI or
    human.
    """

    def __init__(self, position: Vec3D, rotation: Vec2D):
        self.position = position
        self.rotation = rotation  # horizontal and vertical angle (no roll)
        self.dz = 0
