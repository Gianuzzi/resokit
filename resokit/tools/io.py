import numpy as np
import pandas as pd
import attrs
from core import DynamicPlanet,Star,DynamicSystem


#####--------------------- LOAD INTEGRATION
def load_integration(
    file,
    npl,
    names=["time", "ibody", "a", "e", "inc", "m_anom", "w", "Omega"],
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
        "a", "e", "inc", "m_anom", "w", "Omega", "mass", "_"]. Use "_" for 
        throwaways. The default is ["time", "ibody", "a", "e", "inc", "m_anom", 
        "w", "Omega"].
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
        raise Exception(
            "can't use '_' in columns names and ALSO specify usecols"
        )

    # allowed inputs
    elem_space = {
        "times": None,
        "ibody": None,
        "a": None,
        "e": None,
        "inc": None,
        "m_anom": None,
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

    # create Star
    star = Star()
    return DynamicSystem(star=star, planets=planet_obj_list)


sys1 = load_integration(
    "../datasets/2planet_example.dat",
    npl=2,
    names=["times", "ibody", "a", "e", "inc", "m_anom", "w", "Omega", "_", "_"],
)

pl1 = sys1.planets[0]
pl2 = sys1.planets[1]
