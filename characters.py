# coding=utf-8
"""Classes containing the state of a player."""
import math
from panda3d.core import Vec2D, Vec3D

from fps_controls import FPSControls, ActionKey


WALKING_SPEED = 5
FLYING_SPEED = 15
GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.0
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50
PLAYER_HEIGHT = 2


class Character:
    """A decision-making object with some sort of controls, whether AI or
    human.
    """

    def __init__(self, controls: FPSControls, position: Vec3D, rotation: Vec2D):
        self.position = position
        self.rotation = rotation  # horizontal and vertical angle (no roll)
        self.dz = 0
        self.controls = controls

    def update(self, dt, world):
        # Check input
        self.strafe = [0, 0]
        if self.controls.key_pressed(ActionKey.Left):
            self.strafe[1] = -1
        elif self.controls.key_pressed(ActionKey.Right):
            self.strafe[1] = 1
        if self.controls.key_pressed(ActionKey.Up):
            self.strafe[0] = 1
        elif self.controls.key_pressed(ActionKey.Down):
            self.strafe[0] = -1

        if self.controls.key_pressed(ActionKey.Jump):
            if self.dz == 0:
                self.dz = JUMP_SPEED

        # walking
        speed = FLYING_SPEED if self.controls.flying else WALKING_SPEED
        d = dt * speed  # distance covered this tick.
        dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * d, dy * d, dz * d
        # gravity
        if not self.controls.flying:
            # Update your vertical speed: if you are falling, speed up until you
            # hit terminal velocity; if you are jumping, slow down until you
            # start falling.
            self.dz -= dt * GRAVITY
            self.dz = max(self.dz, -TERMINAL_VELOCITY)
            dz += self.dz * dt

        # collisions
        x, y, z = self.position
        self.position = world.collide(
            self, Vec3D(x + dx, y + dy, z + dz), PLAYER_HEIGHT)

        # Handle mouse movements
        # TODO: Pull from the fps controls
        dx, dy = self.controls.get_mouse_change()

        # update the camera
        base.camera.setPos(*self.position)
        self.rotation[0] -= dx * 60
        self.rotation[1] += dy * 60
        # Clamp to (-pi, pi)
        self.rotation[1] = min(max(-90, self.rotation[1]), 90)
        base.camera.setHpr(self.rotation[0], self.rotation[1], 0)

    def get_motion_vector(self) -> Vec3D:
        """ Returns the current motion vector indicating the velocity of the
        player.
        """
        if any(self.strafe):
            x, z = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            z_angle = math.radians(z)
            x_angle = math.radians(x + strafe)
            if self.controls.flying:
                m = math.cos(z_angle)
                dz = math.sin(z_angle)
                if self.strafe[1]:
                    # Moving left or right.
                    dz = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    # Moving backwards.
                    dz *= -1
                # When you are flying up or down, you have less left and right
                # motion.
                dx = math.cos(x_angle) * m
                dy = math.sin(x_angle) * m
            else:
                dx = math.cos(x_angle)
                dy = math.sin(x_angle)
                dz = 0.0
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return Vec3D(dx, dy, dz)
