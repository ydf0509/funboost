from typing import TypeVar

TShape = TypeVar("TShape", bound="Shape")

class Shape:
    def set_scale(self: TShape, scale: float) :
        self.scale = scale
        return self


class Circle(Shape):
    def set_radius(self, radius: float) -> Circle:
        self.radius = radius
        return self

Shape().set_scale().
Circle().set_scale(0.5).set_radius(2.7)  # => Circle