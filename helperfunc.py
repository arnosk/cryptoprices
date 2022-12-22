"""
Created on December 22, 2022

@author: arno

Several helper functions

"""
import os
from datetime import datetime, timezone

import cfscrape
import pandas as pd


def save_file(url: str, folder: str, filename: str):
    """Download and safe a file from internet

    If folder doesn't exists, create the folder

    url = url to download file
    folder = folder for saving downloaded file
    filename = filename for saving downloaded file
    """
    os.makedirs(folder, exist_ok=True)

    url = url.split('?')[0]
    ext = url.split('.')[-1]
    file = '%s\\%s.%s' % (folder, filename, ext)

    # Download file
    scraper = cfscrape.create_scraper()
    cfurl = scraper.get(url).content

    # Safe file
    with open(file, 'wb') as f:
        f.write(cfurl)


def convert_timestamp(ts: int, ms: bool = False) -> datetime:
    """Convert timestamp to date string

    ts = timestamp in sec if ms = False
    ts = timestamp in msec if ms = True
    """
    if ms:
        ts = int(ts/1000)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt


def remove_tz(serie: pd.Series) -> pd.Series:
    """Remove timezone in panda column

    because excel cannot handle this timezone
    """
    return serie.apply(lambda d: d if d.tzinfo is None or d.tzinfo.utcoffset(d) is None else pd.to_datetime(d).tz_localize(None))
