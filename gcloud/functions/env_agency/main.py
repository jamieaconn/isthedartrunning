import requests
from google.cloud import firestore
import datetime


def update_level(request):
    # Calculate yesterday's date
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    formatted_yesterday = yesterday.strftime('%Y-%m-%d')
    url = 'http://environment.data.gov.uk/flood-monitoring/id/stations/46126/readings?startdate=' + formatted_yesterday + '&_sorted'

    r = requests.get(url)
    db = firestore.Client()
    for i in r.json()['items']:
        doc_ref = db.collection('level_data').document(i['dateTime'])
        doc_ref.set({
        'level': i['value']
        })
    return('Complete')