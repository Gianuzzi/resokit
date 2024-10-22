import numpy as np
import pandas as pd
import attrs

#####--------------------- FORMATOS DE VARIABLES
_SEQUENCE_TYPES = (list, tuple, np.ndarray)
_TIME_SERIES_KWARGS = {
    "validator": attrs.validators.instance_of(_SEQUENCE_TYPES),
    "converter": np.asarray,
    "default": [np.nan],
}

_TABLE_KWARGS = {
    "validator": attrs.validators.instance_of(pd.DataFrame),
    "default": pd.DataFrame(),
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


#####--------------------- DynamicPlanet
@attrs.define(frozen=True, slots=True, repr=False)
class DynamicPlanet:
    """Time series for the evolution of a planet"""

    # input parameters
    time_series_table: pd.DataFrame = attrs.field(**_TABLE_KWARGS)
    name: str = attrs.field(**_PLNAME_KWARGS)

    times: list = attrs.field(init=False, **_TIME_SERIES_KWARGS)  # days
    a: list = attrs.field(init=False, **_TIME_SERIES_KWARGS)  # AU
    e: list = attrs.field(init=False, **_TIME_SERIES_KWARGS)  #
    inc: list = attrs.field(init=False, **_TIME_SERIES_KWARGS)  # deg
    M: list = attrs.field(init=False, **_TIME_SERIES_KWARGS)  # deg
    w: list = attrs.field(init=False, **_TIME_SERIES_KWARGS)  # deg
    Omega: list = attrs.field(init=False, **_TIME_SERIES_KWARGS)  # deg

    mass: float = attrs.field(**_CONSTANT_KWARGS)  # earth masses
    radius: float = attrs.field(**_CONSTANT_KWARGS)  # earth radii

    is_star: bool = attrs.field(**_BOOL_KWARGS)

    def __attrs_post_init__(self):
        table_elems = self.time_series_table.columns
        for elem in table_elems:
            setattr(self, elem, self.time_series_table[elem])

    def planet_method(self): ...


#####--------------------- STAR
@attrs.define()
class Star:
    """
    Star of the system

    """

    mass: float = attrs.field(**_CONSTANT_KWARGS)  # solar masses
    radius: float = attrs.field(**_CONSTANT_KWARGS)  # solar radii
    teff: float = attrs.field(**_CONSTANT_KWARGS)  # kelvin
    met: float = attrs.field(**_CONSTANT_KWARGS)

    def star_method(self): ...


#####--------------------- DynamicSystem
#####--------------------- FORMATO DE VARIABLES
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

    def system_method(self): ...


#####--------------------- LOAD INTEGRATION
def load_integration(
    file,
    npl,
    names=["time", "ibody", "a", "e", "inc", "M", "w", "Omega"],
    mass=None,
    usecols=None,
):
    """
    Load integration from file.

    Parameters
    ----------
    file : str
        Path to file. Has to be separated by spaces.
    npl : int
        Number of planets.
    names : list of str, optional
        Contents of the columns. Can only include the terms ["time", "ibody",
        "a", "e", "inc", "M", "w", "W", "mass", "_"]. Use "_" for throwaways.
        The default is ["time", "ibody", "a", "e", "inc", "M", "w", "W"].
    mass : list of floats, optional
        Planet masses in Earth masses.
        The default is None.

    Returns
    -------
    planets : list of dicts
        Data separated per planet per element.

    """

    if (usecols is not None) and (len(names) != len(usecols)):
        raise Exception("usecols doesn't match names length")

    if ("_" in names) and (usecols is not None):
        raise Exception("can't use '_' in columns names and ALSO specify usecols")

    # allowed inputs
    elem_space = {
        "times": None,
        "ibody": None,
        "a": None,
        "e": None,
        "inc": None,
        "M": None,
        "w": None,
        "Omega": None,
        "_": None,
        "mass": None,
    }
    for namei in names:
        assert (
            namei in elem_space
        ), f"{namei} is not an \
    allowed input"
    if ("mass" in names) and (mass is not None):
        raise Exception("can't input mass twice")

    # select parameters with usecols
    Nnames = len(names)
    usecols = [i for i in range(Nnames) if names[i] != "_"]
    names = [names[i] for i in usecols]

    # read data
    data = pd.read_table(
        file,
        delimiter=r"\s+",
        names=names,
        header=None,
        usecols=usecols,
    )

    # validate consistent number of planets
    if "ibody" in names:
        _npl_from_table = np.max(data["ibody"].values)
        if npl != _npl_from_table:
            raise Exception("number of planets mismatch")

    # add ibody column if not there
    if "ibody" not in names:
        nrows = len(data.index)
        pl_ibodies = np.arange(npl) + 1
        pl_ibodies = np.tile(pl_ibodies, nrows // npl)
        if len(pl_ibodies) != nrows:
            raise Exception(
                f"{file} missing lines. If collisions consider \
                            using an 'ibody' column or one file per planet"
            )
        data["ibody"] = pl_ibodies

    # create DynamicPlanet's
    planet_obj_list = []
    for ipl in range(npl):
        ith_planet_table = data[data["ibody"] == ipl + 1]
        ith_planet_table.pop("ibody")
        ith_planet_obj = DynamicPlanet(time_series_table=ith_planet_table)
        planet_obj_list.append(ith_planet_obj)
        break

    # create Star
    star = Star()
    return DynamicSystem(star=star, planets=planet_obj_list)


sys1 = load_integration(
    "../datasets/2planet_example.dat",
    npl=2,
    names=["times", "ibody", "a", "e", "inc", "M", "w", "Omega", "_", "_"],
)

pl1 = sys1.planets[0]
pl2 = sys1.planets[1]
