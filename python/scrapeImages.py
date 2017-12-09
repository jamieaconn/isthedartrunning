import json
import os
from scipy import misc
import urllib2
import urllib
import cStringIO
import requests


"""
SCRAPING ACTUAL RADAR IMAGES 
"""

def get_radar_times():
    key = '78e077ee-7ec6-408c-9b04-b23480cbb589'
    metoff = 'http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/all/json/capabilities?key={key}'
    response = urllib2.urlopen(metoff.format(key=key))
    data = json.load(response)
    times = [lay for lay in data['Layers']['Layer'] if lay['@displayName'] == 'Rainfall'][0]['Service']['Times']['Time']
    return times
    
def scrape_radar_imgs():
    radar_url = "http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/{LayerName}/{ImageFormat}?TIME={Time}Z&key={key}"
    
    times = get_radar_times()

    for time in times:
        url = radar_url.format(LayerName = 'RADAR_UK_Composite_Highres', ImageFormat = 'png', Time = time, key = key) 
        r = requests.get(url)
        with open('../image/radar/' + time + '.png', "wb") as ff:
            ff.write(r.content)

"""
SCRAPING FORECAST RADAR IMAGES
"""

