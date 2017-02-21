# coding=utf-8
"""Some useful utility classes and functions for Panda3D."""

from panda3d.core import CollisionRay, CollisionTraverser, GeomNode, \
    CollisionNode, CollisionHandlerQueue


class RayPicker:
    _parent = None

    def __init__(self, debug=False):
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

    def _iterate(self, condition):
        # TODO: Move condition to the constructor
        # Iterate over the collisions and pick one
        self._traverser.traverse(render)

        # Go closest to farthest
        self._handler.sortEntries()

        for i in range(self._handler.getNumEntries()):
            pickedObj = self._handler.getEntry(i).getIntoNodePath()
            # picker = self.handler.getEntry(i).getFromNodePath()

            if not condition or (condition and condition(pickedObj)):
                point = self._handler.getEntry(i).getSurfacePoint(render)
                return point

        # Too bad, didn't find any matches
        return None

    def from_ray(self, origin, direction, condition=None):
        # Set the ray from a specified point and direction
        self._ray.setOrigin(origin)
        self._ray.setDirection(direction)
        return self._iterate(condition)


class MouseRayPicker(RayPicker):
    def __init__(self, debug=False):
        self._parent = camera
        super().__init__(debug=debug)

    def from_mouse(self, condition=None):
        # Get the mouse and generate a ray from the camera to its 2D position
        mouse = base.mouseWatcherNode.getMouse()
        self._ray.setFromLens(base.camNode, 0, 0)
        # self._ray.setFromLens(base.camNode, mouse.getX(), mouse.getY())
        return self._iterate(condition)
