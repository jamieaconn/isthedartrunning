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
import csv
database = 'data.db'




con = lite.connect(database)
cur = con.cursor()



query = """

    SELECT *
    FROM nevis 
"""

cur.execute(query)


with open('nevis.csv', 'wb') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([i[0] for i in cur.description]) # write headers
    csv_writer.writerows(cur)

con.commit()
con.close()




