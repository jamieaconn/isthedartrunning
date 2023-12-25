#!/bin/bash

REGION="europe-west2"
PROJECT_ID="even-autonomy-239218"

# Metoffice
SCHEDULED_JOB_NAME="metoffice"
FUNCTION_NAME="upload_latest_run_files"
SCHEDULE="0 * * * *"
SOURCE='/Users/jamieconn/isthedartrunning/gcloud/functions/metoffice'
TIMEOUT=300

# Deploy the Cloud Function
gcloud functions deploy "${FUNCTION_NAME}" \
    --runtime python39 \
    --region "${REGION}" \
    --trigger-http \
    --allow-unauthenticated \
    --timeout "${TIMEOUT}" \
    --source "${SOURCE}"

# Check if the scheduled job exists
EXISTING_JOB=$(gcloud scheduler jobs describe "${SCHEDULED_JOB_NAME}" --format="value(name)" 2>/dev/null)

# Create or update the scheduled job
if [ -z "${EXISTING_JOB}" ]; then
    # Create a new job
    gcloud scheduler jobs create http "${SCHEDULED_JOB_NAME}" \
    --schedule "${SCHEDULE}" \
	--location "${REGION}" \
    --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}" \
    --http-method POST
else
    # Update the existing job
    gcloud scheduler jobs update http "${SCHEDULED_JOB_NAME}" \
    --schedule "${SCHEDULE}" \
	--location "${REGION}" \
    --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}" \
    --http-method POST
fi

# Dartcom
SCHEDULED_JOB_NAME="dartcom"
FUNCTION_NAME="update_rainfall"
SCHEDULE="*/5 * * * *"
SOURCE='/Users/jamieconn/isthedartrunning/gcloud/functions/dartcom'
TIMEOUT=60

# Deploy the Cloud Function
gcloud functions deploy "${FUNCTION_NAME}" \
    --runtime python39 \
    --region "${REGION}" \
    --trigger-http \
    --allow-unauthenticated \
    --timeout "${TIMEOUT}" \
    --source "${SOURCE}"

# Check if the scheduled job exists
EXISTING_JOB=$(gcloud scheduler jobs describe "${SCHEDULED_JOB_NAME}" --format="value(name)" 2>/dev/null)

# Create or update the scheduled job
if [ -z "${EXISTING_JOB}" ]; then
    # Create a new job
    gcloud scheduler jobs create http "${SCHEDULED_JOB_NAME}" \
    --schedule "${SCHEDULE}" \
	--location "${REGION}" \
    --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}" \
    --http-method POST
else
    # Update the existing job
    gcloud scheduler jobs update http "${SCHEDULED_JOB_NAME}" \
    --schedule "${SCHEDULE}" \
	--location "${REGION}" \
    --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}" \
    --http-method POST
fi

# env agency
SCHEDULED_JOB_NAME="env_agency"
FUNCTION_NAME="update_level"
SCHEDULE="*/5 * * * *"
SOURCE='/Users/jamieconn/isthedartrunning/gcloud/functions/env_agency'
TIMEOUT=60

# Deploy the Cloud Function
gcloud functions deploy "${FUNCTION_NAME}" \
    --runtime python39 \
    --region "${REGION}" \
    --trigger-http \
    --allow-unauthenticated \
    --timeout "${TIMEOUT}" \
    --source "${SOURCE}"

# Check if the scheduled job exists
EXISTING_JOB=$(gcloud scheduler jobs describe "${SCHEDULED_JOB_NAME}" --format="value(name)" 2>/dev/null)

# Create or update the scheduled job
if [ -z "${EXISTING_JOB}" ]; then
    # Create a new job
    gcloud scheduler jobs create http "${SCHEDULED_JOB_NAME}" \
    --schedule "${SCHEDULE}" \
	--location "${REGION}" \
    --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}" \
    --http-method POST
else
    # Update the existing job
    gcloud scheduler jobs update http "${SCHEDULED_JOB_NAME}" \
    --schedule "${SCHEDULE}" \
	--location "${REGION}" \
    --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}" \
    --http-method POST
fi