#!/usr/bin/env python


import requests
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
from numpy import recfromcsv
from subprocess import call
import ftplib
import sqlite3 as lite
import sys
import pandas as pd
from scipy import ndimage
from scipy import sum, average
import os.path

river = 'dart'
testing = False

err_print = 0 # st to 1 for lots of printing messages : )

fdir = os.path.abspath(os.path.dirname(__file__))
database = os.path.join(fdir, 'data.db')

zero = misc.imread(os.path.join(fdir, 'ref_images/zero.png'))
one = misc.imread(os.path.join(fdir, 'ref_images/one.png'))
two = misc.imread(os.path.join(fdir, 'ref_images/two.png'))
three = misc.imread(os.path.join(fdir, 'ref_images/three.png'))
four = misc.imread(os.path.join(fdir, 'ref_images/four.png'))
five = misc.imread(os.path.join(fdir, 'ref_images/five.png'))
six = misc.imread(os.path.join(fdir, 'ref_images/six.png'))
seven = misc.imread(os.path.join(fdir, 'ref_images/seven.png'))
eight = misc.imread(os.path.join(fdir, 'ref_images/eight.png'))
nine = misc.imread(os.path.join(fdir, 'ref_images/nine.png'))
dot = misc.imread(os.path.join(fdir, 'ref_images/dot.png'))
black = misc.imread(os.path.join(fdir, 'ref_images/black.png'))

numbers = [zero, one, two, three, four, five, six, seven, eight, nine, dot, black]


def return_digit(image, dig):
    n = 4 + dig * 12
    return image[25:45, n:n+12]

def to_grayscale(arr):
    if len(arr.shape) == 3:
        return average(arr, -1)
    else:   
        return arr

def match_digit(arr1, arr2):
    diff = arr2 - arr1
    return sum(abs(diff))

# Returns the position of the best match out of the possible images definited in numbers
def digit_to_value(arr):
    mini = 80000
    for i in range(0, len(numbers)):
        dum = match_digit(arr, to_grayscale(numbers[i]))
        if dum < mini:
            mini = dum
            result = i
    return result

def image_to_value(im, limit):
    string = ''
    for i in range(0, limit):
        dig = digit_to_value(return_digit(im, i))
        if dig < 10:
            string += str(dig)
        elif dig == 10:
            string += "."
        elif dig == 11: # case where digit is black image
            return string
    return string

def get_rainfall():
    url = "http://www.dartcom.co.uk/images/weather/vws1003.jpg"

    file = cStringIO.StringIO(urllib2.urlopen(url).read())
    im = misc.imread(file)
    im = to_grayscale(im)
    return float(image_to_value(im, 6))



def update_sql(time_val, rain_val):
    con = lite.connect(database)
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO {river} (timestamp) VALUES('{time_val}')".format(river=river, time_val = time_val))
    cur.execute("UPDATE {river} SET rain=({rain_val}) WHERE timestamp = ('{time_val}')".format(river=river, rain_val = rain_val, time_val = time_val))
    con.commit()
    con.close()

def gettime():
    time = gmtime()  #Current time - 16 minutes
    if(time[4] > 15 & time[4] < 45): 
        timestamp = strftime("%Y-%m-%dT%H:30", time)
    else:
        timestamp = strftime("%Y-%m-%dT%H:00", time)
    if (err_print == 1):
        print "Current time rounded down to nearest 15 min: " + timestamp
    return(timestamp)


def rain(testing=False):

    timestamp = gettime()
    rain = get_rainfall()


    #Update database with newest rain value
    update_sql(timestamp, rain)

def main():
    rain()

if __name__ == "__main__":
    main()



