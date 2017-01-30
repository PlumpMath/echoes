# coding=utf-8
"""Expose utility classes and functions for handling voxel-based worlds."""
from typing import Tuple

from panda3d.core import Geom
from panda3d.core import GeomVertexData
from panda3d.core import GeomVertexFormat
from panda3d.core import GeomVertexWriter
from panda3d.core import Vec3D


CUBE_SIZE = 1.0


GLOBAL_CACHE = {}


class VoxelWorld:
    """A container for many voxels."""
    def __init__(self):
        self._prepare_format()

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


class Voxel:
    """A container to remember all the memory locations of the graphics data.
    """
    def __init__(self, position):
        self.position = position


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


