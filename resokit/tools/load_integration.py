import numpy as np


def load_integration(
    file,
    npl,
    names=["t", "ibody", "a", "e", "inc", "M", "w", "W"],
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
        Contents of the columns. Can only include the terms ["t", "ibody", 
        "a", "e", "inc", "M", "w", "W", "mass", "_"]. Use "_" for throwaways.
        The default is ["t", "ibody", "a", "e", "inc", "M", "w", "W"].
    mass : list of floats, optional
        Planet masses in Earth masses. 
        The default is None.

    Returns
    -------
    planets : list of dicts
        Data separated per planet per element.

    """
    
    if usecols is not None:
        assert len(names) == usecols, "usecols doesn't match names length"

    # allowed inputs
    elem_space = {
        "t": None,
        "ibody": None,
        "a": None,
        "e": None,
        "inc": None,
        "M": None,
        "w": None,
        "W": None,
        "_": None,
        "mass": None,
    }
    for namei in names:
        assert (
            namei in elem_space
        ), f"{namei} is not an \
    allowed input"
    if "mass" in names:
        assert mass is None, "can't input mass twice"

    # remove ibody column
    # names=names.pop(names.index("ibody"))

    # read all data
    data = np.genfromtxt(file, unpack=True, usecols=usecols)

    # separate per planet into dicts
    planets = []
    for ipl in range(npl):
        planets_i = {}
        for elem_ind, elem_label in enumerate(names):
            if elem_label == "_":
                continue
            planets_i[elem_label] = data[elem_ind, ipl::npl]
        if mass:
            planets_i["mass"] = mass[ipl]  # if mass input seperately
        planets.append(planets_i)

    # calculate mean longitude
    for i, ipl in enumerate(planets):
        ipl["lam"] = (ipl["M"] + ipl["w"] + ipl["W"]) % 360.0

    return planets


pls = load_integration(
    "../datasets/2planet_example.dat",
    npl=2,
    names=["t", "ibody", "a", "e", "inc", "M", "w", "W", "_", "_"],
)
