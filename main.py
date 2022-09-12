# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller

# MongoDB import
import mongoengine as db

# Google Sheets imports
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Other imports
from datetime import datetime, timedelta
import json
import os
import io


# database credentials
db_user = 'test_user'
db_pass = 's0p9UmPrwFcVeZ1y'
db_name = 'kijiji'

# connect to MongoDB
db.connect(host=f'mongodb+srv://test_user:{db_pass}@cluster0.kofnl7r.mongodb.net/{db_name}?retryWrites=true&w=majority')


class Ads(db.Document):
    ads_title = db.StringField()
    image_url = db.URLField()
    date_posted = db.StringField()
    location = db.StringField()
    description = db.StringField()
    beds = db.StringField()
    currency = db.StringField()
    price = db.StringField()


def site_parse():
    # Prase site with selenium
    chromedriver_autoinstaller.install()
    driver = webdriver.Chrome()
    driver.get('https://www.kijiji.ca/b-apartments-condos/city-of-toronto/c37l1700273')
    next_button = True

    # Fetching all ads and checking for next page
    while next_button:
        ads_info = driver.find_elements(By.CLASS_NAME, 'search-item')
        for ad in ads_info:
            image_url = ad.find_element(By.TAG_NAME, 'img').get_attribute('src')
            ads_title = ad.find_element(By.TAG_NAME, 'a').text
            date_posted = ad.find_element(By.CSS_SELECTOR, 'span[class="date-posted"]').text
            if date_posted.endswith('ago'):
                date_posted = datetime.today().strftime("%d/%m/%Y")
            elif date_posted.endswith('Yesterday'):
                date_posted = datetime.today() - timedelta(days=1)
                date_posted = date_posted.strftime("%d/%m/%Y")

            location = ad.find_element(By.CSS_SELECTOR, 'div[class="location"] > span').text
            description = ad.find_element(By.CSS_SELECTOR, 'div[class="description"]').text
            beds = ad.find_element(By.CSS_SELECTOR, 'span[class="bedrooms"]').text
            currency = ad.find_element(By.CSS_SELECTOR, 'div[class="price"]').text[0]
            price = ad.find_element(By.CSS_SELECTOR, 'div[class="price"]').text[1:]

            #Save add in db
            add = Ads(
                ads_title=ads_title,
                image_url=image_url,
                date_posted=date_posted,
                location=location,
                description=description,
                beds=beds,
                currency=currency,
                price=price
            ).save()

        # Checking for next page
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'a[title="Next"]')
            next_button.click()
        except:
            break


def download_from_db():
    # Export file from MongoDB
    # Docs https://www.mongodb.com/docs/database-tools/mongoexport/
    command = 'mongoexport --uri mongodb+srv://test_user:s0p9UmPrwFcVeZ1y@cluster0.kofnl7r.mongodb.net/kijiji --collection ads --out ads.json'
    os.system(command)


def google_data_prepare():
    # prepare data for upload to GooglesSheet
    google_upload_data = []
    columns = ['Id', 'Ads_title', 'Image_url', 'Date_posted', 'Location', 'Description', 'Beds', 'Currency', 'Price']
    google_upload_data.append(columns)

    # Open and prepare a file for upload to GoogleSheet
    with io.open('ads.json', encoding='utf-8') as file:
        for line in file:
            dict_line = json.loads(line)
            data = []
            for key in dict_line.keys():
                if key == '_id':
                    data.append(dict_line['_id']['$oid'])
                else:
                    data.append(dict_line[key])
            google_upload_data.append(data)

    return google_upload_data


def google_sheet_upload(google_upload_data):
    # Set credentials
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = 'keys.json'

    creds = None
    creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # The ID spreadsheet.
    SAMPLE_SPREADSHEET_ID = '1IreO6pw2KK4ox1azIEno6g4BDFIUG9sybli4U4GctWU'

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    request = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range='ads!A1',
                                    valueInputOption='USER_ENTERED', body={'values': google_upload_data}).execute()
    sheet_link = 'https://docs.google.com/spreadsheets/d/' + SAMPLE_SPREADSHEET_ID
    res_message = f'All info uploaded.\nCheck:{sheet_link}'
    return res_message


if __name__ == '__main__':
    site_parse()
    download_from_db()
    upload_data = google_data_prepare()
    res = google_sheet_upload(upload_data)
    print(res)
