import attrs
import numpy as np

_SEQUENCE_TYPES = (list, tuple, np.ndarray)

_TIME_SERIES_KWARGS = {
    "validator": attrs.validators.instance_of(_SEQUENCE_TYPES),
    "converter": np.asarray,
    "default": [np.nan],
}

_PLNAME_KWARGS = {
    "validator": attrs.validators.instance_of(str),
    "default": "",
}

_CONSTANT_KWARGS = {
    "validator": attrs.validators.instance_of((int, float)),
    "converter": float,
    "default": np.nan,
}

_BOOL_KWARGS = {
    "validator": attrs.validators.instance_of(bool),
    "default": False,
}

_INTEGER_KWARGS = {
    "validator": attrs.validators.instance_of(int),
    "default": 0,
}


@attrs.define()
class DynamicPlanet:
    """Time series for the evolution of a planet"""

    # input parameters
    name: str = attrs.field(**_PLNAME_KWARGS)

    times: list = attrs.field(**_TIME_SERIES_KWARGS)  # days
    a: list = attrs.field(**_TIME_SERIES_KWARGS)  # AU
    e: list = attrs.field(**_TIME_SERIES_KWARGS)  #
    inc: list = attrs.field(**_TIME_SERIES_KWARGS)  # deg
    M: list = attrs.field(**_TIME_SERIES_KWARGS)  # deg
    w: list = attrs.field(**_TIME_SERIES_KWARGS)  # deg
    Omega: list = attrs.field(**_TIME_SERIES_KWARGS)  # deg

    mass: float = attrs.field(**_CONSTANT_KWARGS)  # earth masses
    radius: float = attrs.field(**_CONSTANT_KWARGS)  # earth radii

    is_star: bool = attrs.field(**_BOOL_KWARGS)


@attrs.define()
class Star:
    """
    Star of the system

    """

    mass: float = attrs.field(**_CONSTANT_KWARGS)  # solar masses
    radius: float = attrs.field(**_CONSTANT_KWARGS)  # solar radii
    teff: float = attrs.field(**_CONSTANT_KWARGS)  # kelvin
    met: float = attrs.field(**_CONSTANT_KWARGS)


_STAR_OBJECT_KWARGS = {
    "validator": attrs.validators.instance_of(Star),
    "default": Star(),  # empty star
}

_PLANET_OBJECT_KWARGS = {
    "validator": attrs.validators.instance_of((list, tuple, np.ndarray)),
    "default": [np.nan],
}


@attrs.define()
class DynamicSystem:
    """Global properties of the system"""

    nstars: int = attrs.field(**_INTEGER_KWARGS)
    star: Star = attrs.field(**_STAR_OBJECT_KWARGS)
    planets: list = attrs.field(**_PLANET_OBJECT_KWARGS)
    npl: int = attrs.field(init=False, **_INTEGER_KWARGS)

    def __attrs_post_init__(self):
        """Validate types of star and planets,
        AND add calculated attributes.

        """
        # Validation
        if not isinstance(self.star, Star):
            raise TypeError("star must be of type Star")

        for ith, planet in enumerate(self.planets):
            if not isinstance(planet, DynamicPlanet):
                raise TypeError(f"planet {ith+1} must be of type DynamicPlanet")

        # Additional calculated attributes
        self.npl = len(self.planets)


pl1 = DynamicPlanet()
pl2 = DynamicPlanet()
st1 = Star()
sys1 = DynamicSystem(planets=[pl1, pl2])
sys2 = DynamicSystem(planets=[pl1, pl2, pl1])
