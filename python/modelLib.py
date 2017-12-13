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

    df = pd.DataFrame(result, columns=['timestamp', 'cum_rain', 'level', 'forecast'])
    # # Set index to timestamp column as object
    df.timestamp = pd.to_datetime(df.timestamp)
    df = df.set_index('timestamp')
    df = df.sort_index()

    return df

def pre_model_checks(df, current_time):
    # Check that there is a level update in df
    if len(df[df.level.notnull()]) == 0:
        logger.warning("No level update - exiting")
        sys.exit()   
    # Check that there is a row for now or past now
    if len(df[df.index >= current_time]) == 0:
        logger.warning("Not enough data - exiting")
        sys.exit()


def preprocessing(df):
    """Reindex to include missing timestamps and create new column for actual rain from cumulative rain"""
    logger.debug("Fill in missing timestamps by reindexing")
    
    min_time = min(df.index)
    max_time = max(df.index)

    rng = pd.date_range(min_time, max_time, freq='15Min')
    df = df.reindex(rng)

    logger.debug("Convert cumulative rain to actual rain")

    df['rain'] = df['cum_rain'].diff(periods=2)

    # negative values from diff are when the rain value resets so we set equal to the cumulative value
    df.loc[df['rain'] < 0, 'rain'] = df.loc[df['rain'] < 0, 'cum_rain']

    logger.debug("Concat rain and forecast to create model_rain")

    latest_rain_time = max(df.index[df.cum_rain.notnull()])

    df['model_rain'] = pd.concat([
        df[df.index <= latest_rain_time]['rain'],
        df[df.index > latest_rain_time]['forecast']
    ])

    logger.debug("interpolate model_rain")

    df['model_rain'] = df['model_rain'].interpolate()

    return df



def f(x):
    return math.exp(k*x)
def g(x):
    return (scale_m * x) + scale_a
def f_inv(x):
    return math.log(x) / k
def g_inv(x):
    return (x - scale_a) / scale_m