from requests import get, post
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import secretmanager
import os
import json

# the project id is set using an env variable when deploying
# it is needed for acessing secrets
PROJECT_ID = os.getenv("MY_PROJECT_ID")

# name of Google Sheet that has the cryptos
SHEET_NAME = "get crypto"

# name of the ifttt event that will handle the web request
IFTTT_EVENT = "crypto_script"


# this function gets a secret from the GCP secret manager
def get_secret(secret_name: str):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=name)
    secret = response.payload.data.decode("UTF-8")
    # if the secret is a file we need to convert to a dict
    # otherwise keep as is
    try:
        secret = json.loads(secret)
    except:
        pass
    return secret  # returns a json or a string depending on the secret type


# the request parameter is not used but GCP requires it
def get_crypto(request):
    ifttt_key = get_secret("ifttt_api_key")
    service_account_json = get_secret("service_account_json")
    image_url = get_secret("crypto_image_url")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        service_account_json, scope
    )

    # connect to the Google Sheet
    client = gspread.authorize(creds)
    data = client.open(SHEET_NAME).sheet1.get_all_records()

    # put into a list all the names of the coins
    # there must be a column with the name 'coins'
    coins = [x["coins"] for x in data if "coins" in x]

    # initialize some variables to be used later
    prices = []
    s = ""  # string to hold all the values we'll push to IFTTT
    error_coins = []  # will fill with coins that fail
    error = False  # will become True if a single coin fails

    # if we did not find any coins listed in Goolge Sheets
    if not coins:
        value = "The Google Sheet is missing the 'coins' column"

    # loop through all the coins we found
    for coin in coins:
        x = get(
            f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin}"
        ).json()

        # if the request came back empty make note of it and skip it
        if not x:
            error = True
            error_coins.append(coin)
            continue

        # grab some information about the coin
        try:
            x = x[0]
            request_price = x.get("current_price", None)
            symbol = x.get("symbol", None)
        except:
            error = True
            error_coins.append(coin)
            continue

        # if anything is missing then make note of it and skip this coin
        if not request_price or not symbol:
            error = True
            error_coins.append(coin)
            continue

        # if the price has too many zeros remove them to make easier to read
        price = round(float(request_price), 2)
        if price == 0:
            price = round(
                float(request_price) * 1000, 2
            )  # if the price is super low multiply it so we can see it scale
            if price == 0:
                price = round(
                    float(request_price) * 100000, 2
                )  # if the price is still super low
        prices.append(f"{symbol}: {price}")

    # create one big string for all the prices that we'll use to pipe into the variable to IFTTT
    value = " | ".join(prices)
    if error:
        value += ". FYI these coins failed: "
        value += ", ".join(error_coins)

    # at this point if value is missing something went wrong. make note of it
    if not value:
        value = "Error in getting crypto. Make sure all the names are valid."

    # ifttt will be expecting this
    data = {
        "message_title": "Crypto Update",
        "message": value,
        "image_url": image_url,
    }

    # push prices to IFTTT notification on phone
    post(
        f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/json/with/key/{ifttt_key}",
        data=data,
    )
    return "Yay Crypto!"
