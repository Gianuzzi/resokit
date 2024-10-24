import numpy as np
import pandas as pd
import attrs
from core import DynamicPlanet,Star,DynamicSystem

# allowed inputs
ELEM_SPACE = {
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


#####--------------------- LOAD INTEGRATION
def load_integration(
    file,
    npl,
    names=["time", "ibody", "a", "e", "inc", "m_anom", "w", "Omega"],
    mass=None,
    radius=None,
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

    # =============== VALIDATE PARAMETERS =============== #
    for namei in names:
        assert (namei in ELEM_SPACE), f"{namei} is not an \
    allowed input"

    if (usecols is not None) and (len(names) != len(usecols)):
        raise Exception("usecols doesn't match names length")

    # correct use of mass
    if ("mass" in names) and (mass is not None):
        raise Exception("can't input mass twice")
    
    # =============== READ DATA =============== #
    # select parameters with usecols
    N_names = len(names)
    usecols = [i for i in range(N_names) if names[i] != "_"]
    names = [names[i] for i in usecols]
    
    # read data
    data = pd.read_table(
        file,
        delimiter=r"\s+",
        names=names,
        header=None,
        usecols=usecols,
    )
    nrows = len(data.index)

    # =============== PREPARE DATAFRAME =============== #
    # validate consistent number of planets
    if "ibody" in names:
        _npl_from_table = np.max(data["ibody"].values)
        if npl != _npl_from_table:
            raise Exception("number of planets mismatch")

    # add ibody column if not there
    if "ibody" not in names:
        pl_ibodies = np.arange(npl) + 1
        pl_ibodies = np.tile(pl_ibodies, nrows // npl)
        if len(pl_ibodies) != nrows:
            raise Exception(
                f"{file} missing lines. If collisions, consider \
                            using an 'ibody' column or one file per planet"
            )
        data["ibody"] = pl_ibodies
    
    # set default values of mass and radius to list of nones
    if mass is None: mass = [None]*npl
    if radius is None: radius = [None]*npl
    
    # always use a list of masses
    if ('mass' in names):
        mass=data['mass'].values[:npl]

    # fill empty columns
    for namei in ELEM_SPACE:
        if (namei not in names) and (namei!='_'):
            dummy_col=np.ones(nrows)*np.nan
            data[namei] = dummy_col
    
    # =============== CREATE DYNAMICPLANETS =============== #
    planets = []
    for ipl in range(npl):
        ith_pl = data[data["ibody"] == ipl + 1]
        ith_pl_obj = DynamicPlanet(
            times=ith_pl['times'],
            a = ith_pl['a'],
            e = ith_pl['e'],
            inc=ith_pl['inc'],
            m_anom=ith_pl['m_anom'],
            w = ith_pl['w'],
            Omega=ith_pl['Omega'],
            mass=mass[ipl],
            radius=radius[ipl]
            )
        planets.append(ith_pl_obj)

    # =============== CREATE STAR =============== #
    star = Star()
    return DynamicSystem(star=star, planets=planets)


sys1 = load_integration(
    "../datasets/2planet_example.dat",
    npl=2,
    names=["times", "ibody", "a", "e", "_", "m_anom", "w", "Omega", "_", "_"],
)

pl1 = sys1.planets[0]
pl2 = sys1.planets[1]
