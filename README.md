# Crypto Script
This script sends crypto price updates to your ifttt app that show up as notifications on your phone. It reads a list of crypto names from a Google Sheet.

# How to deploy

## Create an IFTTT worflow
 
 - **if this** should be a webhook with a json payload
    - name the event `crypto_script`
 - **then that** should be a notification
    - choose the rich one
    - the title and message are irrelavant as they will overwrriten
- add a filter code step in between the two
> let payload = JSON.parse(MakerWebhooks.jsonEvent.JsonPayload)
IfNotifications.sendRichNotification.setTitle(payload.message_title)
IfNotifications.sendRichNotification.setMessage(payload.message)
IfNotifications.sendRichNotification.setImageUrl(payload.image_url)
- locate the api key for IFTTT under your account
    - go to My services
    - then choose Webhooks and go to settings

## Configure GCP
- Create a Google Cloud Project that can do billing
- Enable the following APIs in the project
    - Google Sheets
    - Google Drive
    - Secrets Manager
    - Cloud Functions
- Add the following secrets in the secrets manager
    - 'ifttt_api_key' as a string
    - url for image to be used in notification
        - call it `crypto_image_url`
    - default app engine service account json key as a file
        - call it `service_account_json`
        - this can be downloaded from IAM
        - other service account can be created an used
        - if so make sure to grant this account permission to the funcion
- In the IAM console add a new role to give the service account access to secret manager secret accessor
- Create a google sheet with one column titled `coins`
    - name the sheet `get crypto`
    - share this sheet with the service account you are using
    - use their service account email address
    - add in row by row the names of the coins of interest
- Enable the Cloud Scheduler in GCP
    - Add a new job with a frequency like: `0 7-22 * * *`
    - Make sure to set the right timezone
    - for the execution use the URL from the cloud function

## Deploy

*Make sure to update the project ids below. It should be the same for both variables*

*Ensure that you have setup gcloud from the command line and it points to your correct GCP project*

`gcloud functions deploy get_crypto --set-env-vars MY_PROJECT_ID=xxx --project=xxxx --runtime python39 --trigger-http --allow-unauthenticated`
