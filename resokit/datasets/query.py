# This file is part of the
#   ResoKit Project (https://github.com/Gianuzzi/resokit).
# Copyright (c) 2024, Emmanuel Gianuzzi
# License: MIT
#   Full Text: https://github.com/Gianuzzi/resokit/blob/master/LICENSE

# ============================================================================
# DOCS
# ============================================================================

"""Module to query exoplanet.eu and nasa datasets."""

# =============================================================================
# IMPORTS
# =============================================================================

from io import BytesIO

import requests
import pandas as pd
from astropy.io.votable import parse_single_table
from astropy.table import Table

# from .databases import PATH

# ============================================================================
# CONSTANTS
# ============================================================================

EU_QUERY_URL = "http://voparis-tap-planeto.obspm.fr/tap/sync?lang=ADQL&"
NASA_QUERY_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"


# ============================================================================
# FUNCTIONS
# ============================================================================


def _create_query(
    source: str,
    select: str = "*",
    alias: str = None,
    where: list = None,
    order_by: str = None,
) -> str:
    """
    Create the query for the exoplanet.eu or nasa datasets

    Parameters
    ----------
    source : str
        The source from which to download the dataset.
        The options are "eu" or "nasa".
    select : str
        The columns to select.
        Default is "*".
    alias : str
        The alias (as) for the the column/table.
        Default is None.
    where : list
        The conditions to filter the data.
        Default is None.
    order_by : str
        The column to order the data by.
        Default is None.

    Returns
    -------
    The query as a string.
    """

    # Check the input
    if not isinstance(select, str):
        raise ValueError("Select must be a string.")

    # Create the query
    query = f"select {select} "

    # Add the alias
    if alias is not None:
        if not isinstance(alias, str):
            raise ValueError("Alias must be a string.")
        query += f"as {alias} "

    # Add the table
    if source == "nasa":
        query += " from ps"
    elif source == "eu":
        query += " from exoplanet.epn_core"
    else:
        raise ValueError("Source must be 'eu' or 'nasa'.")

    # Add the where clause
    if where is not None:
        if isinstance(where, str):
            query += f" where {where}"
        elif isinstance(where, list):
            query += " where ("
            for condition in where:
                query += f"({condition}) and "
            query = query[:-5]
            query += ")"
        else:
            raise ValueError("Where must be a string or a list.")

    # Add the order by clause
    if order_by is not None:
        if not isinstance(order_by, str):
            raise ValueError("Order by must be a string.")
        query += f" order by {order_by}"

    return query


def query_from_db(
    source: str,
    target_name: str = None,
    star_name: str = None,
    default_flag: int = 1,
) -> pd.DataFrame:
    """
    Query the exoplanet.eu dataset

    Parameters
    ----------
    source : str
        The source from which to download the dataset.
        The options are "eu" or "nasa".
    system_name : str
        The name of the system.
        Default is None.
    star_name : str
        The name of the star.
        Default is None.
    default_flag : int
        Return only default system values.
        Default is 1.

    Returns
    -------
    The dataset as a pandas DataFrame.
    """

    # Check the input
    if target_name is None and star_name is None:
        raise ValueError(
            "At least one of system_name or star_name must be provided."
        )

    # Create the query
    if target_name is not None:
        target = "target_name" if source == "eu" else "pl_name"
        query = _create_query(
            source=source,
            where=[f"{target}='{target_name}'"],
        )
    else:
        star = "star_name" if source == "eu" else "hostname"
        query = _create_query(
            source=source,
            where=[f"{star}='{star_name}'"],
        )

    # Add the default flag
    if default_flag and source == "nasa":
        query += " and default_flag=1"

    # Format the query
    query = "query=" + query.replace(" ", "+")

    # Query the dataset
    if source == "nasa":
        # Extra format to the query
        query += "&format=csv"
        print(f"Running table query: {query}...")
        print(f" from NASA dataset: {NASA_QUERY_URL}...")
        # Fetch the data
        with requests.get(NASA_QUERY_URL + query) as response:
            data = pd.read_csv(BytesIO(response.content))

    elif source == "eu":
        print(f"Running table query: {query}...")
        print(f" from EU dataset: {EU_QUERY_URL}...")
        # Fetch the data
        with requests.get(EU_QUERY_URL + query) as response:
            # votable: astropy + pandas
            data = Table.read(BytesIO(response.content)).to_pandas()

    else:
        raise ValueError("Source must be 'eu' or 'nasa'.")

    return data


def __query_dataset_length(source: str) -> int:
    """
    Query the dataset length

    Parameters
    ----------
    source : str
        The source from which to download the dataset.
        This should be a string identifier for the source.
        Options are "eu" or "nasa".

    Returns
    -------
    The length of the dataset.
    """

    if source == "nasa":
        url = NASA_QUERY_URL
        query = "query=select+count(*)+from+ps&format=csv"
    elif source == "eu":
        url = EU_QUERY_URL
        query = "query=select+count(*)+from+exoplanet.epn_core"
    else:
        raise ValueError("Source must be 'eu' or 'nasa'.")

    print(f"Fetching table length from {url}...")
    with requests.get(url + query) as response:
        if source == "nasa":
            # Split the response by lines and get the second line
            data = response.text.splitlines()
            lines = int(data[1])
        else:
            # Parse the votable and get the first value
            data = parse_single_table(BytesIO(response.content))  # BytesIO
            lines = data.array[0][0]

    return lines
