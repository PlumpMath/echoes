# coding=utf-8
"""A prototype editor for `Echoes of the Infinite Multiverse`."""
import math
import pickle

import tqdm
from direct.showbase.ShowBase import ShowBase, Fog, \
    Spotlight, Vec4, AmbientLight, PointLight, Vec2D, WindowProperties
from direct.task import Task
from panda3d.core import Vec3D
import voxel

# Typing convenience
Vector = (float, float, float)
IntVector = (int, int, int)

TICKS_PER_SEC = 60
WALKING_SPEED = 5
FLYING_SPEED = 15
GRAVITY = 20.0
MAX_JUMP_HEIGHT = 5.0
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50
PLAYER_HEIGHT = 2
TEXTURE_PATH = 'texture.png'
BOUNDARY_BLOCK = None


def normalize(position: Vector) -> IntVector:
    """ Accepts `position` of arbitrary precision and returns the block
    containing that position.
    """
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return x, y, z


class Model(object):
    """A drawable object."""
    filepath = "untitled.pkl"

    def __init__(self):
        self.world = voxel.VoxelWorld()
        # Mapping from position to a pyglet `VertexList` for all shown blocks.
        self._shown = {}
        self.load()

    def _create_boundary_blocks(self):
        n = 10  # 1/2 width and height of world
        for x in tqdm.tqdm(range(-n, n + 1)):
            for z in range(-n, n + 1):
                # create a boundary floor and ceiling
                self.world.place_voxel(BOUNDARY_BLOCK, Vec3D(x, -n, z))
                self.world.place_voxel(BOUNDARY_BLOCK, Vec3D(x, n+1, z))

                # create outer boundary walls
                if x in (-n, n) or z in (-n, n):
                    for dy in range(-n, n + 1):
                        self.world.place_voxel(BOUNDARY_BLOCK, Vec3D(x, dy, z))

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
        with open(self.filepath, 'wb') as outfile:
            pickle.dump(self.world, outfile)

    def hit_test(self, position: Vector, vector: Vector,
                 max_distance: int=8) -> tuple:
        """ Line of sight search from current position. If a block is
        intersected it is returned, along with the block previously in the line
        of sight. If no block is found, return None, None.
        """
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in range(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None

    def check_neighbors(self, position):
        """ Check all blocks surrounding `position` and ensure their visual
        state is current. This means hiding blocks that are not exposed and
        ensuring that all exposed blocks are shown. Usually used after a block
        is added or removed.
        """
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self._shown:
                    self.show_block(key)
            else:
                if key in self._shown:
                    self.hide_block(key)

    def show_block(self, position: IntVector, immediate: bool=True):
        """ Show the block at the given `position`. This method assumes the
        block has already been added with add_block()
        """
        # texture = self.world[position]
        # if immediate:
        self.world.place_voxel("", position)
        # else:
        #     self._enqueue(self._show_block, position, texture)

    def hide_block(self, position: IntVector):
        """ Hide the block at the given `position`. Hiding does not remove the
        block from the world.
        """
        self._shown.pop(position).delete()

    def _enqueue(self, func, *args):
        """ Add `func` to the internal queue."""
        self.queue.append((func, args))

    def process_entire_queue(self):
        """ Process the entire queue with no breaks."""
        while self.queue:
            func, args = self.queue.popleft()
            func(*args)


class Window(ShowBase):
    """Implement the code that creates the window."""
    previous_mouse = (0, 0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Whether or not the window exclusively captures the mouse.
        self.exclusive = False

        # When flying gravity has no effect and speed is increased.
        self.flying = False

        # Strafing is moving lateral to the direction you are facing,
        # e.g. moving to the left or right while continuing to face forward.
        #
        # First element is -1 when moving forward, 1 when moving back, and 0
        # otherwise. The second element is -1 when moving left, 1 when moving
        # right, and 0 otherwise.
        self.strafe = [0, 0]

        # Current (x, y, z) position in the world, specified with floats. Note
        # that, perhaps unlike in math class, the y-axis is the vertical axis.
        self.position = Vec3D(0, 0, 0)

        # First element is rotation of the player in the x-z plane (ground
        # plane) measured from the z-axis down. The second is the rotation
        # angle from the ground plane up. Rotation is in degrees.
        #
        # The vertical plane rotation ranges from -90 (looking straight down) to
        # 90 (looking straight up). The horizontal rotation range is unbounded.
        self.rotation = Vec2D(0, 0)

        # The crosshairs at the center of the screen.
        self.reticle = None

        # Velocity in the z (upward) direction.
        self.dz = 0

        # A list of blocks the player can place. Hit num keys to cycle.
        # self.inventory = [SOLID_BLOCK, MISSILE_BLOCK, HAZARD_BLOCK]

        # The current block the user can place. Hit num keys to cycle.
        # self.block = self.inventory[0]

        # Instance of the model that handles the world.
        self.model = Model()

        # The label that is displayed in the top left of the canvas.
        # self.label = pyglet.text.Label(
        #     '', font_name='Ubuntu', font_size=18,
        #     x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
        #     color=(0, 0, 0, 255))

        self.build_lighting()

        # This call schedules the `update()` method to be called
        # TICKS_PER_SEC. This is the main game event loop.
        # pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
        self.disableMouse()
        self.toggle_exclusive_mouse()
        self.update_task = self.task_mgr.add(self.update, 'update_task')
        self.accept('escape', self.toggle_exclusive_mouse)

    def build_lighting(self):
        """Set up the lighting for the game."""
        # Fog
        exp_fog = Fog("scene-wide-fog")
        exp_fog.setColor(0.0, 0.0, 0.0)
        exp_fog.setExpDensity(0.01)
        self.render.setFog(exp_fog)
        self.setBackgroundColor(0, 0, 0)

        # Lights
        spotlight = Spotlight("spotlight")
        spotlight.setColor(Vec4(1, 1, 1, 1))
        # spotlight.setShadowCaster(True, 2048, 2048)
        spotlight_node = self.render.attachNewNode(spotlight)
        spotlight_node.setPos(11, 11, 11)
        spotlight_node.lookAt(0, 0, 0)
        self.render.setLight(spotlight_node)

        point = PointLight("point")
        point.setColor(Vec4(1, 1, 1, 1))
        # point.setShadowCaster(True, 2048, 2048)
        point_node = self.render.attachNewNode(point)
        point_node.set_pos(-11, -11, -11)
        self.render.setLight(point_node)

        ambient_light = AmbientLight("ambientLight")
        ambient_light.setColor(Vec4(.25, .25, .25, 1))
        self.render.setLight(self.render.attachNewNode(ambient_light))

        # Enable the shader generator for the receiving nodes
        self.render.setShaderAuto()

    def toggle_exclusive_mouse(self):
        """ If `exclusive` is True, the game will capture the mouse, if False
        the game will ignore the mouse.
        """
        props = WindowProperties()
        if self.exclusive:
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.M_absolute)
            self.win.requestProperties(props)
        else:
            props.setCursorHidden(True)
            props.setMouseMode(WindowProperties.M_relative)
            self.win.requestProperties(props)
        # TODO: Reset previous_mouse here
        self.exclusive = not self.exclusive

    def get_sight_vector(self) -> Vector:
        """ Returns the current line of sight vector indicating the direction
        the player is looking.
        """
        x, y = self.rotation
        # y ranges from -90 to 90, or -pi/2 to pi/2, so m ranges from 0 to 1 and
        # is 1 when looking ahead parallel to the ground and 0 when looking
        # straight up or down.
        m = math.cos(math.radians(y))
        # dy ranges from -1 to 1 and is -1 when looking straight down and 1 when
        # looking straight up.
        dx = math.cos(math.radians(x - 90)) * m
        dy = math.sin(math.radians(x - 90)) * m
        dz = math.sin(math.radians(y))
        return dx, dy, dz

    def get_motion_vector(self) -> Vector:
        """ Returns the current motion vector indicating the velocity of the
        player.
        """
        if any(self.strafe):
            x, z = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            z_angle = math.radians(z)
            x_angle = math.radians(x + strafe)
            if self.flying:
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
        return dx, dy, dz

    def update(self, task: Task):
        """Once per frame, we update the player physics."""
        # noinspection PyUnresolvedReferences
        dt = globalClock.getDt()
        # Use 8 steps to be somewhat continuous or something lame like that.
        m = 8
        dt = min(dt, 0.2)
        for _ in range(m):
            self._update(dt / m)
        return task.cont

    def _update(self, dt: float) -> None:
        """Private implementation of the `update()` method. This is where most
        of the motion logic lives, along with gravity and collision detection.
        """
        # walking
        speed = FLYING_SPEED if self.flying else WALKING_SPEED
        d = dt * speed  # distance covered this tick.
        dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * d, dy * d, dz * d
        # gravity
        if not self.flying:
            # Update your vertical speed: if you are falling, speed up until you
            # hit terminal velocity; if you are jumping, slow down until you
            # start falling.
            self.dz -= dt * GRAVITY
            self.dz = max(self.dz, -TERMINAL_VELOCITY)
            dz += self.dz * dt
        # collisions
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)  # TODO: re-add
        self.position = (x, y, z)

        # Handle mouse movements
        dx, dy = 0, 0
        if self.mouseWatcherNode.hasMouse() and self.exclusive:
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            dx = x - self.previous_mouse[0]
            dy = y - self.previous_mouse[1]
            self.previous_mouse = x, y

        # update the camera
        self.camera.setPos(*self.position)
        self.rotation[0] -= dx * 60
        self.rotation[1] += dy * 60
        # Clamp to (-pi, pi)
        self.rotation[1] = min(max(-90, self.rotation[1]), 90)
        self.camera.setHpr(self.rotation[0], self.rotation[1], 0)

    def collide(self, position: Vector, height: float) -> Vector:
        """ Checks to see if the player at the given `position` and `height`
        is colliding with any blocks in the world and returns the new position.
        """
        # How much overlap with a dimension of a surrounding block you need to
        # have to count as a collision. If 0, touching terrain at all counts as
        # a collision. If .49, you sink into the ground, as if walking through
        # tall grass. If >= .5, you'll fall through the ground.
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in voxel.UNIT_VECTORS:  # check all surrounding blocks
            for i in range(3):  # check each dimension independently
                if not face[i]:
                    continue
                # How much overlap you have with this dimension.
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dz in range(height):  # check each height
                    op = list(np)
                    op[1] -= dz
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, 0, -1) or face == (0, 0, 1):
                        # You are colliding with the ground or ceiling, so stop
                        # falling / rising.
                        self.dz = 0
                    break
        return tuple(p)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """ Called when a mouse button is pressed. See pyglet docs for button
        and modifier mappings.
        """
        if self.exclusive:
            vector = self.get_sight_vector()
            position, previous = self.model.hit_test(self.position, vector)
            # previous is the block adjacent to the touched block
            if button == mouse.RIGHT:
                if previous:
                    self.model.world.place_voxel("", previous)
                    # self.model.add_block(previous, self.block)
            elif button == pyglet.window.mouse.LEFT and position:
                texture = self.model.world[position]
                if texture != BOUNDARY_BLOCK:
                    self.model.world.remove_voxel(position)
        else:
            self.toggle_exclusive_mouse()

    def on_key_press(self, symbol: int, modifiers: int):
        """ Called when the player presses a key. See pyglet docs for key
        mappings.
        """
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.dz == 0:
                self.dz = JUMP_SPEED
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol == key.ENTER:
            self.model.save()
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
            self.block = self.inventory[index]

    def on_key_release(self, symbol: int, modifiers: int):
        """ Called when the player releases a key. See pyglet docs for key
        mappings.
        """
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1

    def on_resize(self, width, height):
        """ Called when the window is resized to a new `width` and `height`."""
        # label
        self.label.y = height - 10
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(
            4, ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n)))

    def on_draw(self):
        """ Called by pyglet to draw the canvas."""
        self.clear()
        self.set_3d()
        gl.glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        self.draw_reticle()

    def draw_focused_block(self):
        """ Draw black edges around the block that is currently under the
        crosshairs.
        """
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            vertex_data = cube_vertices(block, 0.51)
            gl.glColor3d(0, 0, 0)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            pyglet.graphics.draw(24, gl.GL_QUADS, ('v3f/static', vertex_data))
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

    def draw_label(self):
        """ Draw the label in the top left of the screen."""
        x, y, z = self.position
        self.label.text = f'{round(pyglet.clock.get_fps())} ' \
                          f'({int(x)}, {int(y)}, {int(z)}) ' \
                          f'{len(self.model._shown)} / {len(self.model.world)}'
        self.label.draw()

    def draw_reticle(self):
        """ Draw the crosshairs in the center of the screen."""
        gl.glColor3d(0, 0, 0)
        self.reticle.draw(gl.GL_LINES)


def main():
    """Run the program."""
    window = Window()
    window.run()


if __name__ == '__main__':
    main()
