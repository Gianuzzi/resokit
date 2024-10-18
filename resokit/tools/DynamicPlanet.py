import attrs
import numpy as np
import uttr
from typing import List


@attrs.define()
class DynamicPlanet:
    """
    Time series for the evolution of a planet
    """

    name_kw = {
        "validator": attrs.validators.instance_of(str),
        "default": '',
    }

    timeSeries_kw = {
        "validator": attrs.validators.instance_of((list, np.ndarray)),
        "converter": np.asarray,
        "default": [np.nan],
    }

    constant_kw = {
        "validator": attrs.validators.instance_of((int,float)),
        "converter": float,
        "default": np.nan,
    }
    
    bool_kw = {
        "validator": attrs.validators.instance_of(bool),
        "default": False,
    }
    
    
    # input parameters
    name: str = attrs.field(**name_kw)

    t: list = attrs.field(**timeSeries_kw)  # days
    a: list = attrs.field(**timeSeries_kw)  # AU
    e: list = attrs.field(**timeSeries_kw)  #
    inc: list = attrs.field(**timeSeries_kw)  # deg
    M: list = attrs.field(**timeSeries_kw)  # deg
    w: list = attrs.field(**timeSeries_kw)  # deg
    Omega: list = attrs.field(**timeSeries_kw)  # deg

    mass: float = attrs.field(**constant_kw)  # earth masses
    radius: float = attrs.field(**constant_kw)  # earth radii
    
    is_star : bool = attrs.field(**bool_kw)

@attrs.define()
class Star:
    """
    Star of the system
    """
    
    constant_kw = {
        "validator": attrs.validators.instance_of((int,float)),
        "converter": float,
        "default": np.nan,
    }
    
    mass: float = attrs.field(**constant_kw)  # solar masses
    radius: float = attrs.field(**constant_kw)  # solar radii
    teff: float = attrs.field(**constant_kw) # kelvin
    met: float = attrs.field(**constant_kw) 


@attrs.define()
class DynamicSystem:
    """
    Global properties of the system
    """
    
    int_kw = {
        "validator": attrs.validators.instance_of(int),
        "converter": int,
        "default": np.nan,
    }
    
    star_kw = {
        "validator": attrs.validators.instance_of(Star),
        "default": np.nan,
    }
    
    planets_kw = {
        "validator": attrs.validators.instance_of(list),
        "default": [np.nan],
    }
    
    npl: int = attrs.field(**int_kw)
    nstars: int = attrs.field(**int_kw)
    
    star: Star = attrs.field(**star_kw)
    
    planets: list = attrs.field(**planets_kw)
    
    # # validar lista de planetas        
    # def __attrs_post_init__(self):
    #     """Validate that the type of each particleset is correct."""
    #     pset_types = [
    #         ("star", self.star, Star),
    #         ("planets", self.planets, list),
    #     ]
    #     planets = self.planets
    #     for planet in planets:
    #         if not isinstance(planet,DynamicPlanet):
    #             raise TypeError(f"{planet} must be of type DynamicPlanet")  
    
    
    # sys = DynamicSystem([pl1,pl2])
    # return(sys)
