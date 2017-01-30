# coding=utf-8
"""Test a procedural render of a cube in Panda3D."""
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Geom, GeomNode, GeomTriangles, SamplerState, Fog, \
    Spotlight, Vec4, PointLight, AmbientLight, Vec3D

import voxel


class Window(ShowBase):
    """Implement the code that creates the window."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.world = voxel.VoxelWorld()
        self.build_lighting()
        self.make_cube()

    def build_lighting(self):
        """Add lights, fog, and shaders to the scene."""
        # Background color
        self.setBackgroundColor(0, 0, 0)

        # Fog
        exp_fog = Fog("scene-wide-fog")
        exp_fog.setColor(0.0, 0.0, 0.0)
        exp_fog.setExpDensity(0.01)
        self.render.setFog(exp_fog)

        # Lights
        spotlight = Spotlight("spotlight")
        spotlight.setColor(Vec4(1, 1, 1, 1))
        spotlight_node = self.render.attachNewNode(spotlight)
        spotlight_node.setPos(1, 1, 1)
        spotlight_node.lookAt(0, 0, 0)
        self.render.setLight(spotlight_node)

        point = PointLight("point")
        point.setColor(Vec4(1, 1, 1, 1))
        point_node = self.render.attachNewNode(point)
        point_node.set_pos(-1, -1, -1)
        self.render.setLight(point_node)

        ambient_light = AmbientLight("ambientLight")
        ambient_light.setColor(Vec4(.25, .25, .25, 1))
        self.render.setLight(self.render.attachNewNode(ambient_light))

        # Enable the shader generator for the receiving nodes
        self.render.setShaderAuto()

    def make_cube(self):
        """Generate a cube model."""

        # Write data to the buffers
        for v in voxel.make_vertices(Vec3D(0, 0, 0)):
            self.world._vertex_w.addData3f(*v)
        for v in voxel.make_normals():
            self.world._normal_w.addData3f(*v)
        for tex in voxel.make_texcoords():
            self.world._texcoord_w.addData2f(*tex)

        # Add the indexes to a primitive
        prim = GeomTriangles(Geom.UHStatic)
        for i in voxel.make_indices():
            prim.addVertex(i)

        # Create the NodePath
        geom = Geom(self.world._vdata)
        geom.addPrimitive(prim)
        node = GeomNode('geom_node')
        node.addGeom(geom)
        node_path = self.render.attachNewNode(node)

        # Set Texture
        dungeon_tex = self.loader.loadTexture("diffuse.png")
        dungeon_tex.setMagfilter(SamplerState.FT_nearest)
        dungeon_tex.setMinfilter(SamplerState.FT_nearest)
        node_path.setTexture(dungeon_tex)

        # Set Normal Map
        # normal_tex = self.loader.loadTexture("normal_rocks.png")
        # ts = TextureStage('ts')
        # ts.setMode(TextureStage.MNormal)
        # node_path.setTexture(ts, normal_tex)


def main():
    """Run the program."""
    window = Window()
    window.run()


if __name__ == "__main__":
    main()
