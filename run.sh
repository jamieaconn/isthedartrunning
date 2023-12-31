
if [ "$1" == "all" ]; then
    gcloud functions call upload_latest_run_files --region=europe-west2
    gcloud functions call update_rainfall --region=europe-west2
    gcloud functions call update_level --region=europe-west2
    gcloud functions call run_model --region=europe-west2
elif [ "$1" == "metoffice" ]; then
    gcloud functions call upload_latest_run_files --region=europe-west2
elif [ "$1" == "dartcom" ]; then
    gcloud functions call update_rainfall --region=europe-west2
elif [ "$1" == "env_agency" ]; then
    gcloud functions call update_level --region=europe-west2
elif [ "$1" == "model" ]; then
    gcloud functions call run_model --region=europe-west2
fi


