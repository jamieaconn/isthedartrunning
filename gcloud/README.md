gcloud config configurations list
gcloud config configurations activate isthedartrunning

# running firebase locally

import os
credential_path = '/Users/jamieconn/isthedartrunning/gcloud/service_account_token.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path