from google.cloud import firestore

db = firestore.Client()

def fetch_data(request):
    try:
        snapshot = db.collection('results_graph').get()
        values = [doc.to_dict() for doc in snapshot]
        document_ref = db.collection('results').document('results')
        d = document_ref.get().to_dict()
        data = {}       
        data['current_time'] = d['current_time'] / 1000
        data['current_level'] = d['current_level']
        data['text'] = d['text']
        data['values'] = values
        return {'data': data}, 200
    except Exception as e:
        print(f'Error getting documents: {e}')
        return 'Internal Server Error', 500
