# This file is part of the
#   ResoKit Project (https://github.com/Gianuzzi/resokit).
# Copyright (c) 2024, Emmanuel Gianuzzi
# License: MIT
#   Full Text: https://github.com/Gianuzzi/resokit/blob/master/LICENSE

# ============================================================================
# DOCS
# ============================================================================

"""Module to load exoplanet.eu and nasa datasets."""

# =============================================================================
# IMPORTS
# =============================================================================

import os
import datetime
import pathlib
import zipfile

import pandas as pd

# ============================================================================
# CONSTANTS
# ============================================================================

PATH = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))

basename = {
    "eu": "exoplanet_eu",
    "nasa": "nasa",
}

EU_URL = "https://exoplanet.eu/catalog/"
NASA_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"

download_urls = {
    "eu_csv": EU_URL + "csv/",
    "eu_votable": EU_URL + "votable/",
    "nasa_csv": NASA_URL + "query=select+*+from+ps&format=csv",
    "nasa_votable": NASA_URL + "query=select+*+from+ps&format=votable",
}

ZIPNAME = "datasets.zip"

# ============================================================================
# FUNCTIONS
# ============================================================================


def __unzip_database(filename: str = "", extract: bool = False):
    """Unzip the database."""

    # Get the full path
    ZIP_PATH = PATH / ZIPNAME

    # Check if the file exists
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"{ZIPNAME} not found.")

    # Unzip the file
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        if filename:
            if filename not in zip_ref.namelist():
                raise ValueError(f"{filename} not found in {ZIPNAME}.")
            if extract:
                print(f"Unzipping {filename} from {ZIPNAME}...")
                zip_ref.extract(filename, PATH)
            else:
                from io import BytesIO
                return BytesIO(zip_ref.read(filename))
        else:
            zip_ref.extractall(PATH)
            print(f"{ZIPNAME} fully unzipped.")

    return


def __get_filename(source: str, fmt: str):
    """Get the filename based on the format."""
    if source not in ["eu", "nasa"]:
        raise ValueError("Source must be 'eu' or 'nasa'.")
    if fmt == "csv":
        return basename[source] + ".csv"
    elif fmt in ["votable", "vot"]:
        return basename[source] + ".vot"
    raise ValueError("Format must be 'csv' or 'votable'.")


def download_database(
    source: str,
    fmt: str = "csv",
    overwrite: bool = False,
    return_data: bool = False,
):
    """
    Download nasa or exoplanet.eu dataset.
    """
    import requests

    # Use lowercase
    source = source.lower()
    fmt = fmt.lower()

    # Check source and format, and get the filename
    FILENAME = __get_filename(source, fmt)

    # Get the full path
    FULL_PATH = PATH / FILENAME

    # Check if the file exists
    if FULL_PATH.exists():
        print(f"{FULL_PATH} already exists.")
        if not overwrite:
            print("Use overwrite=True to download again.")
            return
    else:
        # Download the data
        url = download_urls[source + "_" + fmt[:3]]  # votable -> vot
        print(f"Downloading data from {url}...")
        with requests.get(url) as response:
            with open(FULL_PATH, "wb") as f:
                f.write(response.content)
        print(f"File {FILENAME} saved.")

    # Load the data if requested
    if return_data:
        return load_database(fmt=fmt)


def load_database(
    source: str,
    fmt: str = "csv",
    download: bool = False,
    check_age: bool = True,
    check_length: bool = False,
    extract: bool = False,
):
    """
    Load nasa or exoplanet.eu dataset.

    Parameters
    ----------
    source : str
        Source of the data: 'eu' or 'nasa'.
    fmt : str, optional (default='csv')
        Format of the data: 'csv' or 'votable'.
    download : bool, optional (default=False)
        Download the data if it does not exist.
    check_age : bool, optional (default=True)
        Check the age of the file.
    check_length : bool, optional (default=False)
        Check the length of the database.
    extract : bool, optional (default=False)
        Extract the file from the ZIP archive.
    """

    # Use lowercase
    source = source.lower()
    fmt = fmt.lower()

    if fmt in ["votable", "vot"]:
        from astropy.table import Table

    # Check source and format, and get the filename
    FILENAME = __get_filename(source, fmt)

    # Get the full path
    FULL_PATH = PATH / FILENAME
    ZIP_PATH = PATH / ZIPNAME

    # Check if the file exists
    if (not FULL_PATH.exists()) and (ZIP_PATH.exists()):
        # Unzip the file
        zipped = __unzip_database(FILENAME, extract=extract)
    elif not FULL_PATH.exists():
        print(f"{FILENAME} not found.")
        if not download:
            print("Use download=True to download it.")
            return
        else:
            # Download the data
            return download_database(source=source, fmt=fmt, return_data=True)
    elif download:
        # Call download_database to overwrite the file
        print(f"{FILENAME} already exists.")
        print("Run download_database to download it again.")

    # Load the data
    load_path = FULL_PATH if zipped is None else zipped
    if fmt in ["votable", "vot"]:
        # votable: astropy + pandas
        data = Table.read(load_path).to_pandas()
    else:
        # csv: pandas
        skiprows = 291 if source == "nasa" else 0
        data = pd.read_csv(load_path, skiprows=skiprows)

    # Check the length of the database
    if check_length:
        length = _query_database_length(source)
        if length != len(data):
            print("WARNING: The file can be updated.")
            print("         Consider downloading it again.")
            print(f"Number of planets in the {source} database:", length)
            print(f"Number of planets in the {FILENAME} file:", len(data))
        else:
            print(f"Number of planets in the {source} database:", length)
    # Check the age of the file
    elif check_age:
        if zipped is not None:
            age = datetime.datetime.fromtimestamp(ZIP_PATH.stat().st_mtime)
        else:
            age = _get_database_age(source, fmt)
        print(f"{FILENAME} last modified: {age}")
        # Check if the file is too old
        if age < datetime.datetime.now() - datetime.timedelta(days=5):
            print("WARNING: The file has not been updated in the last 5 days.")
            print("         Consider downloading it again.\n")

    return data


def _query_database_length(source: str):
    """Query the database length."""

    import requests
    from astropy.io.votable import parse_single_table
    from io import BytesIO

    if source == "nasa":
        url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
        query = "query=select+count(*)+from+ps&format=csv"
    elif source == "eu":
        url = "http://voparis-tap-planeto.obspm.fr/tap/sync?lang=ADQL&"
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


def _get_database_age(source: str, fmt: str):
    """Check how old the local database is."""

    # Check source and format, and get the filename
    FILENAME = __get_filename(source, fmt)

    # Get the full path
    FULL_PATH = PATH / FILENAME

    # Return the age
    return datetime.datetime.fromtimestamp(FULL_PATH.stat().st_mtime)
