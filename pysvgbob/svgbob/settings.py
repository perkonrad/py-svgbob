"""Rendering settings (``settings.rs``)."""

from .f32 import f32


class Settings(object):
    """Options that control the generated svg.

    ``scale`` is the number of svg units per cell width (8 by default);
    ``stroke_width`` and ``scale`` are rounded to f32 like the Rust fields.
    """

    def __init__(self, font_size=14, font_family="Iosevka Fixed, monospace",
                 fill_color="black", background="white", stroke_color="black",
                 stroke_width=2.0, scale=8.0, include_backdrop=True,
                 include_styles=True, include_defs=True):
        self.font_size = font_size
        self.font_family = font_family
        self.fill_color = fill_color
        self.background = background
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.scale = scale
        self.include_backdrop = include_backdrop
        self.include_styles = include_styles
        self.include_defs = include_defs

    @property
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value):
        self._stroke_width = f32(value)

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = f32(value)

    @staticmethod
    def for_debug():
        return Settings(include_backdrop=False, include_styles=False,
                        include_defs=False)
