"""
Created on December 22, 2022

@author: arno

Several helper functions

"""
import os
from datetime import datetime, timezone

import cfscrape
import pandas as pd
from dateutil import parser


def save_file(url: str, folder: str, filename: str):
    """Download and safe a file from internet

    If folder doesn't exists, create the folder

    url = url to download file
    folder = folder for saving downloaded file
    filename = filename for saving downloaded file
    """
    if url != '':
        os.makedirs(folder, exist_ok=True)

        url = url.split('?')[0]
        ext = url.split('.')[-1]
        file = f'{folder}\\{filename}.{ext}'

        # Download file
        scraper = cfscrape.create_scraper()
        cfurl = scraper.get(url).content

        # Safe file
        with open(file, 'wb') as f:
            f.write(cfurl)
        print(f'Image file saved: {file}')
    else:
        print(f'URL is empty! No image filed saved {filename}')


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


def get_date_identifier() -> int:
    day_of_year = datetime.now().timetuple().tm_yday
    return day_of_year


def convert_str_to_date(date: str) -> datetime:
    """Convert a date string to a datetime
    When no timezone in string presume it is UTC instead of local
    """
    default_dt = datetime.now(timezone.utc)
    try:
        dt = parser.parse(date, default=default_dt)
    except parser.ParserError as e:
        print(f'Date format error: {e}')
        return default_dt
    else:
        return dt


def convert_date_to_utc_str(dt: datetime) -> str:
    """Convert datetime with timezone to a string in UTC
    """
    return dt.astimezone(tz=timezone.utc).strftime('%d-%m-%Y_%H:%M')
