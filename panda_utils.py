# coding=utf-8
"""Some useful utility classes and functions for Panda3D."""
from typing import Callable, Any

from panda3d.core import CollisionRay, CollisionTraverser, GeomNode, \
    CollisionNode, CollisionHandlerQueue
from panda3d.core import Vec3


Filter = Callable[[Any], bool]


class RayPicker:
    _parent = None

    def __init__(self, debug: bool=False):
        if self._parent is None:
            self._parent = render

        # Init components
        self._traverser = CollisionTraverser()
        self._handler = CollisionHandlerQueue()
        self._node = CollisionNode('picker_ray')
        self._nodepath = self._parent.attachNewNode(self._node)
        self._ray = CollisionRay()

        # Set up relationships
        self._node.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self._node.addSolid(self._ray)
        self._traverser.addCollider(self._nodepath, self._handler)

        # Show collisions?
        if debug:
            self._traverser.showCollisions(render)

    def _iterate(self, condition: Filter):
        # TODO: Move condition to the constructor
        # Iterate over the collisions and pick one
        self._traverser.traverse(render)

        # Go closest to farthest
        self._handler.sortEntries()

        for i in range(self._handler.getNumEntries()):
            picked_obj = self._handler.getEntry(i).getIntoNodePath()
            # picker = self.handler.getEntry(i).getFromNodePath()

            if not condition or (condition and condition(picked_obj)):
                point = self._handler.getEntry(i).getSurfacePoint(render)
                normal = self._handler.getEntry(i).getSurfaceNormal(render)
                return point, normal

        # Too bad, didn't find any matches
        return None

    def from_ray(self, origin, direction, condition=None):
        # Set the ray from a specified point and direction
        self._ray.setOrigin(origin)
        self._ray.setDirection(direction)
        return self._iterate(condition)


# TODO: Maybe we don't need this one. But it is useful.
class MouseRayPicker(RayPicker):
    """A ray picker that uses the mouse position to pick an object."""
    def __init__(self, debug: bool=False):
        self._parent = camera
        super().__init__(debug=debug)

    def from_mouse(self, condition: Filter=None):
        """Return the point in space that the mouse visually hovers over."""
        mouse = base.mouseWatcherNode.getMouse()
        self._ray.setFromLens(base.camNode, mouse.getX(), mouse.getY())
        return self._iterate(condition)[0]


class ReticleVoxelPicker(RayPicker):
    """A ray picker that uses the center of the screen to pick a voxel location.
    """
    def __init__(self, debug: bool=False):
        self._parent = camera
        super().__init__(debug=debug)

    def from_reticle(self, condition: Filter=None) -> (Vec3, Vec3):
        """Return both the previous and next voxel locations that the
        center of the screen is looking at.
        """
        self._ray.setFromLens(base.camNode, 0, 0)
        hit_pos, hit_normal = self._iterate(condition)
        hit_pos -= hit_normal * 0.5
        rounded = Vec3(round(hit_pos.x), round(hit_pos.y), round(hit_pos.z))
        return rounded + hit_normal, rounded
