#!/usr/bin/env python

import datetime
import numpy as np
from scipy import misc
import glob, os
import math
import urllib2
import urllib
import cStringIO
import calendar
import csv
from time import gmtime, strftime, strptime
from tempfile import NamedTemporaryFile
import shutil
import requests
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from numpy import recfromcsv
from subprocess import call
import ftplib
import sqlite3 as lite
import sys

def create_db(river, database):
    con = lite.connect(database)
    cur = con.cursor()
    cur.execute("CREATE TABLE {river}(Id INTEGER PRIMARY KEY, timestamp TIMESTAMP UNIQUE, rain FLOAT, level FLOAT, predict FLOAT)".format(river = river))
    con.commit()
    con.close()
