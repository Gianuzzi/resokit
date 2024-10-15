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
from io import BytesIO

import requests
import pandas as pd
from astropy.table import Table

from .query import __query_dataset_length

# ============================================================================
# CONSTANTS
# ============================================================================

PATH = pathlib.Path(os.path.abspath(os.path.dirname(__file__)))

basename = {
    "eu": "exoplanet_eu",
    "nasa": "nasa",
}

EU_DB_URL = "https://exoplanet.eu/catalog/"
NASA_DB_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"

download_urls = {
    "eu_csv": EU_DB_URL + "csv/",
    "eu_votable": EU_DB_URL + "votable/",
    "nasa_csv": NASA_DB_URL + "query=select+*+from+ps&format=csv",
    "nasa_votable": NASA_DB_URL + "query=select+*+from+ps&format=votable",
}

ZIP_NAME = "datasets.zip"

# ============================================================================
# FUNCTIONS
# ============================================================================


def __unzip_dataset(filename: str = "", extract: bool = False) -> BytesIO:
    """
    Unzip the dataset

    Parameters
    ----------
    filename : str, optional
        The filename to extract from the ZIP archive.
    extract : bool, optional

    Returns
    -------
    If extract is False, returns the BytesIO object.
    """

    # Get the full path
    ZIP_PATH = PATH / ZIP_NAME

    # Check if the file exists
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"{ZIP_NAME} not found.")

    # Unzip the file
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        if filename:
            if filename not in zip_ref.namelist():
                raise ValueError(f"{filename} not found in {ZIP_NAME}.")
            if extract:
                print(f"Unzipping {filename} from {ZIP_NAME}...")
                zip_ref.extract(filename, PATH)
            else:
                return BytesIO(zip_ref.read(filename))
        else:
            zip_ref.extractall(PATH)
            print(f"{ZIP_NAME} fully unzipped.")

    return


def __get_filename(source: str, fmt: str) -> str:
    """
    Get the filename based on the format

    Parameters
    ----------
    source : str
        The source from which to download the dataset.
        This should be a string identifier for the source.
        Options are "eu" or "nasa".
    fmt : str
        The format of the dataset file to download.
        Options are "csv" or "votable".

    Returns
    -------
    The filename of the dataset.
    """
    if source not in ["eu", "nasa"]:
        raise ValueError("Source must be 'eu' or 'nasa'.")
    if fmt == "csv":
        return basename[source] + ".csv"
    elif fmt in ["votable", "vot"]:
        return basename[source] + ".vot"
    raise ValueError("Format must be 'csv' or 'votable'.")


def _get_dataset_age(source: str, fmt: str) -> datetime.datetime:
    """
    Check how old the local dataset is

    Parameters
    ----------
    source : str
        The source from which to download the dataset.
        This should be a string identifier for the source.
        Options are "eu" or "nasa".
    fmt : str
        The format of the dataset file to download.
        Options are "csv" or "vot".

    Returns
    -------
    The age of the dataset file.
    """

    # Check source and format, and get the filename
    FILENAME = __get_filename(source, fmt)

    # Get the full path
    FULL_PATH = PATH / FILENAME

    # Return the age
    return datetime.datetime.fromtimestamp(FULL_PATH.stat().st_mtime)


def download_dataset(
    source: str,
    fmt: str = "csv",
    overwrite: bool = False,
    return_data: bool = False,
) -> pd.DataFrame:
    """
    Downloads a dataset file from a specified source and format

    Parameters
    ----------
    source : str
     The source from which to download the dataset.
     This should be a string identifier for the source.
     Options are "eu" or "nasa".
    fmt : str, optional
     The format of the dataset file to download.
     Options are "csv" or "vot".
     Default is "csv".
    overwrite : bool, optional
     If True, will overwrite the existing file if it exists.
     Default is False.
    return_data : bool, optional
     If True, will load and return the data after downloading.
     Default is False.

    Returns
    -------
    If return_data is True, returns the loaded dataset in the
    specified format.

    Raises
    ------
    KeyError: If the source and format combination is not found
    in the download URLs.
    """

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
        return load_dataset(source=source, fmt=fmt, check_age=False)


def load_dataset(
    source: str,
    fmt: str = "csv",
    download: bool = False,
    check_age: bool = True,
    check_length: bool = False,
    extract: bool = False,
) -> pd.DataFrame:
    """
    Load nasa or exoplanet.eu dataset

    Parameters
    ----------
    source : str
        Source of the data: 'eu' or 'nasa'.
    fmt : str, optional
        Format of the data: 'csv' or 'votable'.
        Default is 'csv'.
    download : bool, optional
        Download the data if it does not exist.
        Default is False.
    check_age : bool, optional
        Check the age of the file.
        Default is True.
    check_length : bool, optional
        Check the length of the dataset.
        Default is False.
    extract : bool, optional
        Extract the file from the ZIP archive.
        Default is False.

    Returns
    -------
    The loaded dataset in pandas DataFrame format.
    """

    # Use lowercase
    source = source.lower()
    fmt = fmt.lower()

    # Check source and format, and get the filename
    FILENAME = __get_filename(source, fmt)

    # Get the full path
    FULL_PATH = PATH / FILENAME
    ZIP_PATH = PATH / ZIP_NAME

    # Check if the file exists
    if (not FULL_PATH.exists()) and (ZIP_PATH.exists()):
        # Unzip the file
        zipped = __unzip_dataset(FILENAME, extract=extract)
    elif not FULL_PATH.exists():
        print(f"{FILENAME} not found.")
        if not download:
            print("Use download=True to download it.")
            return
        else:
            # Download the data
            return download_dataset(source=source, fmt=fmt, return_data=True)
    elif download:
        # Call download_dataset to overwrite the file
        print(f"{FILENAME} already exists.")
        print("Run download_dataset to download it again.")
    else:
        zipped = None  # No ZIP file

    # Load the data
    load_path = FULL_PATH if zipped is None else zipped
    if fmt in ["votable", "vot"]:
        print(f"Loading {FILENAME} from {ZIP_NAME if zipped else PATH}...")
        # votable: astropy + pandas
        data = Table.read(load_path).to_pandas()
    else:
        print(f"Loading {FILENAME} from {ZIP_NAME if zipped else PATH}...")
        # csv: pandas
        skiprows = 291 if source == "nasa" else 0
        data = pd.read_csv(load_path, skiprows=skiprows)

    # Check the length of the dataset
    if check_length:
        length = __query_dataset_length(source)
        if length != len(data):
            print("WARNING: The file can be updated.")
            print("         Consider downloading it again.")
            print(f"Number of planets in the {source} dataset:", length)
            print(f"Number of planets in the {FILENAME} file:", len(data))
        else:
            print(f"Number of planets in the {source} dataset:", length)
    # Check the age of the file
    elif check_age:
        if zipped is not None:
            age = datetime.datetime.fromtimestamp(ZIP_PATH.stat().st_mtime)
        else:
            age = _get_dataset_age(source, fmt)
        print(f"{FILENAME} last modified: {age}")
        # Check if the file is too old
        if age < datetime.datetime.now() - datetime.timedelta(days=5):
            print("WARNING: The file has not been updated in the last 5 days.")
            print("         Consider downloading it again.\n")

    return data
