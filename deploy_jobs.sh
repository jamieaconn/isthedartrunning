#!/bin/bash

REGION="europe-west2"
PROJECT_ID="even-autonomy-239218"

deploy_job() {
    local SCHEDULED_JOB_NAME="$1"
    if [ "${SCHEDULED_JOB_NAME}" == "metoffice" ]; then
        local FUNCTION_NAME="upload_latest_run_files"
        local SCHEDULE="30 * * * *"
    
    elif [ "${SCHEDULED_JOB_NAME}" == "dartcom" ]; then
        local FUNCTION_NAME="update_rainfall"
        local SCHEDULE="*/5 * * * *"

    elif [ "${SCHEDULED_JOB_NAME}" == "env_agency" ]; then
        local FUNCTION_NAME="update_level"
        local SCHEDULE="*/5 * * * *"

     elif [ "${SCHEDULED_JOB_NAME}" == "model" ]; then
        local FUNCTION_NAME="run_model"
        local SCHEDULE="0,15,30,45 * * * *"
    else
        return
    fi

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
    deploy_job "metoffice"
    deploy_job "env_agency"
    deploy_job "dartcom"
else
    deploy_job "$1"
fi
