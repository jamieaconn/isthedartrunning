from google.cloud import firestore
from flask import jsonify
import functions_framework

db = firestore.Client()

@functions_framework.http
def fetch_data(request):
    # Set CORS headers for the preflight request
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }

        return ("", 204, headers)
    try:
        snapshot = db.collection('results_graph').get()
        values = [doc.to_dict() for doc in snapshot]
        document_ref = db.collection('results').document('results')
        d = document_ref.get().to_dict()
        data = {}       
        data['current_time'] = d['current_time'] * 1000
        data['current_level'] = d['current_level']
        data['text'] = d['text']
        data['values'] = values
        # Create a response with CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept',
        }
        return jsonify({'data': data}), 200, headers
    except Exception as e:
        print(f'Error getting documents: {e}')
        return 'Internal Server Error', 500
