#!/bin/bash

REGION="europe-west2"

deploy_function() {
    local SCHEDULED_JOB_NAME="$1"
    if [ "${SCHEDULED_JOB_NAME}" == "metoffice" ]; then
        local FUNCTION_NAME="upload_latest_run_files"
        local SOURCE="/Users/jamieconn/isthedartrunning/gcloud/functions/metoffice"
        local TIMEOUT=300
        local MEMORY=256M
    
    elif [ "${SCHEDULED_JOB_NAME}" == "dartcom" ]; then
        local FUNCTION_NAME="update_rainfall"
        local SOURCE="/Users/jamieconn/isthedartrunning/gcloud/functions/dartcom"
        local TIMEOUT=60
        local MEMORY=256M

    elif [ "${SCHEDULED_JOB_NAME}" == "env_agency" ]; then
        local FUNCTION_NAME="update_level"
        local SOURCE="/Users/jamieconn/isthedartrunning/gcloud/functions/env_agency"
        local TIMEOUT=60
        local MEMORY=256M

     elif [ "${SCHEDULED_JOB_NAME}" == "model" ]; then
        local FUNCTION_NAME="run_model"
        local SOURCE="/Users/jamieconn/isthedartrunning/gcloud/functions/model"
        local TIMEOUT=240
        local MEMORY=2048
    
    elif [ "${SCHEDULED_JOB_NAME}" == "api" ]; then
        local FUNCTION_NAME="fetch_data"
        local SOURCE="/Users/jamieconn/isthedartrunning/gcloud/functions/api"
        local TIMEOUT=240
        local MEMORY=2048
    else
        return
    fi
    
    # Deploy the Cloud Function
    gcloud functions deploy "${FUNCTION_NAME}" \
        --runtime python39 \
        --region "${REGION}" \
        --trigger-http \
        --timeout "${TIMEOUT}" \
        --source "${SOURCE}" \
        --memory "${MEMORY}"
}

if [ "$1" == "all" ]; then
    deploy_function "metoffice"
    deploy_function "env_agency"
    deploy_function "dartcom"
    deploy_function "api"
else
    deploy_function "$1"
fi
