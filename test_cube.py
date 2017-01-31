# coding=utf-8
"""Test a procedural render of a cube in Panda3D."""
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Fog, Spotlight, Vec4, PointLight, AmbientLight, Vec3D

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
        self.world.place_voxel("", Vec3D(0, 0, 0))


def main():
    """Run the program."""
    window = Window()
    window.run()


if __name__ == "__main__":
    main()
