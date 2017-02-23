# coding=utf-8
"""A prototype editor for `Echoes of the Infinite Multiverse`."""
import math
import pickle

import tqdm
from direct.showbase.ShowBase import ShowBase, Fog, Spotlight, Vec4, \
    AmbientLight, PointLight, Vec2D, Vec3
from direct.task import Task
from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletDebugNode
from panda3d.bullet import BulletRigidBodyNode
from panda3d.core import Vec3D
from panda3d.bullet import BulletWorld, BulletTriangleMesh, \
    BulletTriangleMeshShape
from characters import Character
import voxel

from fps_controls import FPSControls
from panda_utils import ReticleVoxelPicker

BOUNDARY_BLOCK = None


class RoomEditor(voxel.VoxelWorld):
    """A drawable object."""
    filepath = "untitled.pkl"

    def __init__(self, window):
        super().__init__()

        # Initialize Physics
        self.physics = BulletWorld()
        self.physics.setGravity(Vec3(0, 0, -9.81))

        # Load stuff
        self.load()

        # Match the physics to the loaded model
        self.generate_physics()

        # Add players
        controls = FPSControls(window)
        self.players = [
            Character(self, controls, Vec3D(0, 0, 0), Vec2D(0, 0))
        ]

    def _create_boundary_blocks(self) -> None:
        n = 10  # 1/2 width and height of world
        for x in tqdm.tqdm(range(-n, n + 1)):
            for z in range(-n, n + 1):
                # create a boundary floor and ceiling
                self.place_voxel(BOUNDARY_BLOCK, Vec3D(x, -n, z))
                self.place_voxel(BOUNDARY_BLOCK, Vec3D(x, n+1, z))

                import random
                self.place_voxel(BOUNDARY_BLOCK, Vec3D(x, random.randint(-n, n+1), z))

                # create outer boundary walls
                if x in (-n, n) or z in (-n, n):
                    for dy in range(-n, n + 1):
                        self.place_voxel(BOUNDARY_BLOCK, Vec3D(x, dy, z))

    def update(self, dt):
        for player in self.players:
            player.update(dt, self)
        self.physics.doPhysics(dt)

    def load(self) -> None:
        """ Initialize the world by placing all the blocks."""
        # If loading from a file, pull in those blocks.
        # if len(sys.argv) > 1:
        #     self.filepath = sys.argv[1]
        # try:
        #     with open(self.filepath, 'rb') as infile:
        #         self.world = pickle.load(infile)
        # except FileNotFoundError:
        #     self._load_default_world()
        self._create_boundary_blocks()

    def save(self):
        """Write the room to a file."""
        # TODO: I'm borked!
        with open(self.filepath, 'wb') as outfile:
            pickle.dump(self, outfile)

    def hit_test(self, position: Vec3D, vector: Vec3D,
                 max_distance: int=8) -> tuple:
        """Line of sight search from current position. If a block is
        intersected it is returned, along with the block previously in the line
        of sight. If no block is found, return None, None.
        """
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in range(max_distance * m):
            key = voxel.normalize(position)
            if key != previous and key in self:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None

    def generate_physics(self):
        mesh = BulletTriangleMesh()
        mesh.add_geom(self._geom)
        shape = BulletTriangleMeshShape(mesh, dynamic=True)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = render.attachNewNode(node)
        np.setPos(0, 0, 0)
        self.physics_np = np
        self.physics.attachRigidBody(node)

        # Show debug rendering
        # debugNode = BulletDebugNode('Debug')
        # debugNode.showWireframe(True)
        # debugNode.showConstraints(False)
        # debugNode.showBoundingBoxes(False)
        # debugNode.showNormals(False)
        # debugNP = render.attachNewNode(debugNode)
        # debugNP.show()
        # self.physics.setDebugNode(debugNP.node())


class Window(ShowBase):
    """Implement the code that creates the window."""
    previous_mouse = (0, 0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The crosshairs at the center of the screen.
        self.reticle = None

        # Instance of the model that handles the world.
        self.world = RoomEditor(self)

        # Lighting
        self.build_lighting()

        # Get the picker
        self.picker = ReticleVoxelPicker(debug=True)

        # This call schedules the `update()` method to be called
        # TICKS_PER_SEC. This is the main game event loop.
        # pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
        self.update_task = self.task_mgr.add(self.update, 'update_task')
        self.accept('mouse1', self.add_voxel)
        self.accept('mouse2', self.remove_voxel)

    def add_voxel(self):
        prev_pos, next_pos = self.picker.from_reticle()
        if not prev_pos:
            return

        self.world.place_voxel(None, prev_pos)

        # shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        # node = BulletRigidBodyNode('Box')
        # node.setMass(1.0)
        # node.addShape(shape)
        # np = render.attachNewNode(node)
        # np.setPos(prev_pos)
        # self.world.physics.attachRigidBody(node)
        # model = loader.loadModel('models/box.egg')
        # model.flattenLight()
        # model.reparentTo(np)

    def remove_voxel(self):
        prev_pos, next_pos = self.picker.from_reticle()
        if not next_pos:
            return

        self.world.remove_voxel(next_pos)

    def build_lighting(self):
        """Set up the lighting for the game."""
        self.camLens.setNear(0.01)

        # Fog
        exp_fog = Fog("scene-wide-fog")
        exp_fog.setColor(0.0, 0.0, 0.0)
        exp_fog.setExpDensity(0.01)
        self.render.setFog(exp_fog)
        self.setBackgroundColor(0, 0, 0)

        # Lights
        spotlight = Spotlight("spotlight")
        spotlight.setColor(Vec4(1, 1, 1, 1))
        spotlight.setShadowCaster(True, 2048, 2048)
        spotlight_node = self.render.attachNewNode(spotlight)
        spotlight_node.setPos(9, 9, 9)
        spotlight_node.lookAt(0, 0, 0)
        self.render.setLight(spotlight_node)

        point = PointLight("point")
        point.setColor(Vec4(1, 1, 1, 1))
        point.setShadowCaster(True, 2048, 2048)
        point_node = self.render.attachNewNode(point)
        point_node.set_pos(-9, -9, -9)
        self.render.setLight(point_node)

        ambient_light = AmbientLight("ambientLight")
        ambient_light.setColor(Vec4(.25, .25, .25, 1))
        self.render.setLight(self.render.attachNewNode(ambient_light))

        # Enable the shader generator for the receiving nodes
        self.render.setShaderAuto()

    def get_sight_vector(self) -> Vec3D:
        """ Returns the current line of sight vector indicating the direction
        the player is looking.
        """
        x, y = self.player.rotation
        # y ranges from -90 to 90, or -pi/2 to pi/2, so m ranges from 0 to 1 and
        # is 1 when looking ahead parallel to the ground and 0 when looking
        # straight up or down.
        m = math.cos(math.radians(y))
        # dy ranges from -1 to 1 and is -1 when looking straight down and 1 when
        # looking straight up.
        dx = math.cos(math.radians(x - 90)) * m
        dy = math.sin(math.radians(x - 90)) * m
        dz = math.sin(math.radians(y))
        return Vec3D(dx, dy, dz)

    def update(self, task: Task):
        """Once per frame, we update the player physics."""
        # noinspection PyUnresolvedReferences
        dt = globalClock.getDt()
        self.world.update(dt)
        return task.cont

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """ Called when a mouse button is pressed. See pyglet docs for button
        and modifier mappings.
        """
        if self.controls.mouse_captured:
            vector = self.get_sight_vector()
            position, previous = self.world.hit_test(self.player.position, vector)
            # previous is the block adjacent to the touched block
            if button == mouse.RIGHT:
                if previous:
                    self.world.place_voxel("", previous)
            elif button == pyglet.window.mouse.LEFT and position:
                texture = self.world[position]
                if texture != BOUNDARY_BLOCK:
                    self.world.remove_voxel(position)
        else:
            self.controls.toggle_mouse_capture()


def main():
    """Run the program."""
    window = Window()
    window.run()


if __name__ == '__main__':
    main()
