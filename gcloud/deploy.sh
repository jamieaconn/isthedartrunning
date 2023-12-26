#!/bin/bash

REGION="europe-west2"
PROJECT_ID="even-autonomy-239218"

deploy_function() {
    local SCHEDULED_JOB_NAME="$1"
    if [ "${SCHEDULED_JOB_NAME}" == "metoffice" ]; then
        local FUNCTION_NAME="upload_latest_run_files"
        local SCHEDULE="30 * * * *"
        local SOURCE="/Users/jamieconn/isthedartrunning/gcloud/functions/metoffice"
        local TIMEOUT=300
    
    elif [ "${SCHEDULED_JOB_NAME}" == "dartcom" ]; then
        local FUNCTION_NAME="update_rainfall"
        local SCHEDULE="*/5 * * * *"
        local SOURCE="/Users/jamieconn/isthedartrunning/gcloud/functions/dartcom"
        local TIMEOUT=60

    elif [ "${SCHEDULED_JOB_NAME}" == "env_agency" ]; then
        local FUNCTION_NAME="update_level"
        local SCHEDULE="*/5 * * * *"
        local SOURCE="/Users/jamieconn/isthedartrunning/gcloud/functions/env_agency"
        local TIMEOUT="60"
    else
        return
    fi
    
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
}

if [ "$1" == "all" ]; then
    deploy_function "metoffice"
    deploy_function "env_agency"
    deploy_function "dartcom"
else
    deploy_function "$1"
fi
