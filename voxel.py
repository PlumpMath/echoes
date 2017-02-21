# coding=utf-8
"""Expose utility classes and functions for handling voxel-based worlds."""
from typing import Tuple, Dict

from panda3d.core import Geom
from panda3d.core import GeomNode
from panda3d.core import GeomTriangles
from panda3d.core import GeomVertexData
from panda3d.core import GeomVertexFormat
from panda3d.core import GeomVertexWriter
from panda3d.core import SamplerState
from panda3d.core import Vec3D

from characters import Character

CUBE_SIZE = 1.0
UNIT_VECTORS = [
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]


def normalize(position: Vec3D) -> Vec3D:
    """ Accepts `position` of arbitrary precision and returns the block
    containing that position.
    """
    x, y, z = position
    return Vec3D(int(round(x)), int(round(y)), int(round(z)))


class Voxel:
    """A container to remember all the memory locations of the graphics data.
    """
    def __init__(self, position, initial_index):
        # TODO: Is position necessary? Rotation will be someday.
        self.position = position
        self.index = initial_index


class VoxelWorld:
    """A container for many voxels."""
    def __init__(self):
        # State setup
        self._voxels: Dict[Vec3D, Voxel] = {}

        # Panda3D setup
        self._prepare_format()
        self._prepare_node_path()
        self._prepare_texture()

    def __iter__(self):
        return iter(self._voxels)

    def __setitem__(self, key, value):
        self._voxels[key] = value

    def __getitem__(self, item):
        return self._voxels[item]

    def _prepare_format(self):
        # TODO: Get normal mapping working
        # array = GeomVertexArrayFormat()
        # array.addColumn("vertex", 3, Geom.NTFloat32, Geom.CPoint)
        # array.addColumn("normal", 3, Geom.NTFloat32, Geom.CPoint)
        # array.addColumn("tangent", 3, Geom.NTFloat32, Geom.CPoint)
        # array.addColumn("binormal", 3, Geom.NTFloat32, Geom.CPoint)
        # array.addColumn("texcoord", 2, Geom.NTFloat32, Geom.CTexcoord)
        # vertex_format = GeomVertexFormat()
        # vertex_format.add_array(array)
        # vertex_format.registerFormat(vertex_format)

        self._format = GeomVertexFormat.get_v3n3t2()
        self._vdata = GeomVertexData('cube', self._format, Geom.UH_dynamic)
        # self.vertex_data.setNumRows(4)  # TODO: For performance
        self._vertex_w = GeomVertexWriter(self._vdata, 'vertex')
        self._normal_w = GeomVertexWriter(self._vdata, 'normal')
        self._texcoord_w = GeomVertexWriter(self._vdata, 'texcoord')

    def _prepare_node_path(self):
        """Create the publicly accessible node path needed for rendering."""
        # Add the indexes to a primitive -> geom -> node -> node path
        self._prim = GeomTriangles(Geom.UHStatic)
        self._geom = Geom(self._vdata)
        self._geom.addPrimitive(self._prim)
        self._node = GeomNode('geom_node')
        self._node.addGeom(self._geom)
        self.node_path = render.attachNewNode(self._node)  # TODO: ew, linting

    def _prepare_texture(self):
        """Load and set texture stages for the node path."""
        # Set Texture
        dungeon_tex = loader.loadTexture("diffuse.png")  # TODO: ew, linting
        dungeon_tex.setMagfilter(SamplerState.FT_nearest)
        dungeon_tex.setMinfilter(SamplerState.FT_nearest)
        self.node_path.setTexture(dungeon_tex)

        # TODO: Set Normal Map
        # normal_tex = self.loader.loadTexture("normal_rocks.png")
        # ts = TextureStage('ts')
        # ts.setMode(TextureStage.MNormal)
        # node_path.setTexture(ts, normal_tex)

    def place_voxel(self, voxel_type, position: Vec3D) -> None:
        """Create or replace a voxel with a new one."""
        # TODO: Needs if self.exposed(position) in there somewhere.
        if position in self:
            return  # TODO: Replace instead!
        start_index = len(self._voxels) * 24
        # TODO: We need to recycle vertex indices that have been disabled.
        self._voxels[position] = Voxel(position, start_index)
        self.add_data(self._voxels[position])

    def remove_voxel(self, position: Vec3D) -> None:
        """Remove the voxel at the given position."""
        # TODO:
        # del self.world[position]
        # if position in self._shown:
        #     self.hide_block(position)
        # self.check_neighbors(position)
        raise NotImplementedError()

    # TODO: Calculate which faces to show and hide every time there's a voxel
    # change. Luckily any single voxel change only affects adjacent voxels
    # (plus voxels around adjacent, transparent voxels)

    def exposed(self, position: Vec3D) -> bool:
        """Returns a boolean specifying if the given voxel is visible from any
        angle (because it is NOT completely surrounded by opaque voxels.
        """
        x, y, z = position
        for dx, dy, dz in UNIT_VECTORS:
            if Vec3D(x + dx, y + dy, z + dz) not in self._voxels:
                return True
        return False

    def add_data(self, voxel: Voxel):
        """Write vertex and other data to the buffers."""
        # Write data to the buffers
        for v in make_vertices(voxel.position):
            self._vertex_w.addData3f(*v)
        for v in make_normals():
            self._normal_w.addData3f(*v)
        for tex in make_texcoords():
            self._texcoord_w.addData2f(*tex)
        # TODO: Optimize make_indices by combining similar points across voxels
        for i in make_indices(start=voxel.index):
            self._prim.addVertex(i)
            self._prim.modifyVertices()


def make_vertices(position: Vec3D) -> Tuple:
    """ Return the vertices of a 2-unit cube centered at the origin."""
    x, y, z = position
    s = CUBE_SIZE / 2.0
    return (
        # top
        (x-s, y+s, z-s),
        (x-s, y+s, z+s),
        (x+s, y+s, z-s),
        (x+s, y+s, z+s),
        # bottom
        (x-s, y-s, z-s),
        (x+s, y-s, z-s),
        (x-s, y-s, z+s),
        (x+s, y-s, z+s),
        # left
        (x-s, y-s, z-s),
        (x-s, y-s, z+s),
        (x-s, y+s, z-s),
        (x-s, y+s, z+s),
        # right
        (x+s, y-s, z+s),
        (x+s, y-s, z-s),
        (x+s, y+s, z+s),
        (x+s, y+s, z-s),
        # front
        (x-s, y-s, z+s),
        (x+s, y-s, z+s),
        (x-s, y+s, z+s),
        (x+s, y+s, z+s),
        # back
        (x+s, y-s, z-s),
        (x-s, y-s, z-s),
        (x+s, y+s, z-s),
        (x-s, y+s, z-s),
    )


def make_normals() -> Tuple:
    """Return the normals for the vertices of a cube."""
    return (
        # top
        (0, +1, 0),
        (0, +1, 0),
        (0, +1, 0),
        (0, +1, 0),
        # bottom
        (0, -1, 0),
        (0, -1, 0),
        (0, -1, 0),
        (0, -1, 0),
        # left
        (-1, 0, 0),
        (-1, 0, 0),
        (-1, 0, 0),
        (-1, 0, 0),
        # right
        (+1, 0, 0),
        (+1, 0, 0),
        (+1, 0, 0),
        (+1, 0, 0),
        # front
        (0, 0, +1),
        (0, 0, +1),
        (0, 0, +1),
        (0, 0, +1),
        # back
        (0, 0, -1),
        (0, 0, -1),
        (0, 0, -1),
        (0, 0, -1),
    )


def make_texcoords() -> Tuple:
    """ Return the vertices of a 2-unit cube centered at the origin."""
    return (
        # top
        (0.0, 0.0),
        (0.0, 1.0),
        (1.0, 0.0),
        (1.0, 1.0),
    ) * 6  # We're just cheating here.


def make_indices(start=0) -> Tuple:
    """The indices of a cube."""
    offsets = (
        # top
        0, 1, 2, 3, 2, 1,
        # bottom
        4, 5, 6, 7, 6, 5,
        # left
        8, 9, 10, 11, 10, 9,
        # right
        12, 13, 14, 15, 14, 13,
        # front
        16, 17, 18, 19, 18, 17,
        # back
        20, 21, 22, 23, 22, 21,
    )
    return tuple(start + v for v in offsets)


# def check_neighbors(self, position):
#     """ Check all blocks surrounding `position` and ensure their visual
#     state is current. This means hiding blocks that are not exposed and
#     ensuring that all exposed blocks are shown. Usually used after a block
#     is added or removed.
#     """
#     x, y, z = position
#     for dx, dy, dz in FACES:
#         key = (x + dx, y + dy, z + dz)
#         if key not in self.world:
#             continue
#         if self.exposed(key):
#             if key not in self._shown:
#                 self.show_block(key)
#         else:
#             if key in self._shown:
#                 self.hide_block(key)