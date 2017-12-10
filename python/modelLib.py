import pandas as pd
import sqlite3
import os, sys

from logfuncts import logger

FDIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(FDIR, '../data.db')


def load_dataframe_from_sql(river, limit=-1):
    """Load data from the database and return a pandas dataframe. 
    Limit param specifies number of rows returned. Default is to return all"""
    logger.debug("loading df for river {river} from sql with row limit of {limit}".format(river=river, limit=limit))
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    query = """
            SELECT timestamp, rain, level, forecast 
                from {river}
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
    cur.execute(query.format(river=river, limit=limit))
    result = cur.fetchall()
    return pd.DataFrame(result, columns=['timestamp', 'cum_rain', 'level', 'forecast'])
