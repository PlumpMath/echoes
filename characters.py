# coding=utf-8
"""Classes containing the state of a player."""
import math

from panda3d.bullet import BulletCapsuleShape, ZUp
from panda3d.bullet import BulletCharacterControllerNode
from panda3d.core import Vec2D, Vec3D
from panda3d.core import Vec3

from fps_controls import FPSControls, ActionKey


WALKING_SPEED = 5
FLYING_SPEED = 15
GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.0
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50
PLAYER_HEIGHT = 2
PLAYER_RADIUS = 0.45


class Character:
    """A decision-making object with some sort of controls, whether AI or
    human.
    """

    def __init__(self, world, controls: FPSControls, position: Vec3D, rotation: Vec2D):
        self.rotation = rotation  # horizontal and vertical angle (no roll)
        self.controls = controls
        self.make_physics(world, position)

    def make_physics(self, world, position):
        shape = BulletCapsuleShape(PLAYER_RADIUS, PLAYER_HEIGHT - 2 * PLAYER_RADIUS, ZUp)

        self.physics = BulletCharacterControllerNode(shape, 0.4, 'Player')
        playerNP = world.physics_np.attachNewNode(self.physics)
        playerNP.setPos(*position)
        playerNP.setH(45)

        world.physics.attachCharacter(playerNP.node())

        # TODO: Shouldn't be on all characters
        camera.reparentTo(playerNP)

    def update(self, dt, world):
        # Check input
        movement_direction = self.controls.get_movement_direction()

        if self.controls.key_pressed(ActionKey.Jump):
            self.physics.setMaxJumpHeight(5.0)
            self.physics.setJumpSpeed(8.0)
            self.physics.doJump()

        # walking
        velocity = self.get_motion_vector(movement_direction) * WALKING_SPEED
        self.physics.setLinearMovement(velocity, True)

        # Handle mouse movements
        # TODO: Pull from the fps controls
        dx, dy = self.controls.get_mouse_change()

        # update the camera
        # base.camera.setPos(*self.position)
        self.rotation[0] -= dx * 60
        self.rotation[1] += dy * 60
        # Clamp to (-pi, pi)
        self.rotation[1] = min(max(-90, self.rotation[1]), 90)
        base.camera.setHpr(self.rotation[0], self.rotation[1], 0)

    def get_motion_vector(self, motion: Vec2D) -> Vec3D:
        """ Returns the current motion vector indicating the velocity of the
        player.
        """
        if any(motion):
            x, z = self.rotation
            motion: Vec2D = math.degrees(math.atan2(motion[0], motion[1]))
            x_angle = math.radians(x + motion)
            dx = math.cos(x_angle)
            dy = math.sin(x_angle)
            dz = 0.0
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return Vec3(dx, dy, dz)
