import os
import json
from datetime import datetime
import logging

import pandas as pd
import gspread
from tqdm import tqdm
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# access google service account credentials saved in the environment (comment out to run locally!)
# GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]
SHEET_NAME = "Bluesky"  # name of the google sheet to be updated
PROFILE_URL = "https://bsky.app/profile/london.gov.uk" # bluesky profile url to be scraped

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def authenticate_google_api():
    # Authenticate with Google Sheets    
    logging.info("Authenticating with Google Sheets API...")

    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]

    # Authenticate via environment credentials (comment out to run locally)
    # creds_dict = json.loads(GOOGLE_CREDENTIALS)
    # creds = Credentials.from_service_account_info(
    #     creds_dict, scopes=scopes)

    # Uncomment this to run locally from credentials json file
    creds = Credentials.from_service_account_file(
        'credentials.json', scopes=scopes)

    client = gspread.authorize(creds)

    logging.info("Authentication successful!")
    return client

def get_driver():
    # Initialize WebDriver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=options)

    return driver

def check_sheet_access(sheet_name):
    # Check if the Google Sheet is accessible before scraping
    try:
        client = authenticate_google_api()
        
        # Test opening the Google Sheet
        logging.info(f"Checking access to Google Sheet: {sheet_name}")
        sheet = client.open(sheet_name).sheet1
        logging.info(f"Successfully verified access to Google Sheet: {sheet_name}")
        return True
        
    except gspread.SpreadsheetNotFound:
        logging.error(f"Google Sheet '{sheet_name}' was not found. Please check the sheet name.")
        return False
    except gspread.exceptions.APIError as api_error:
        logging.error(f"API Error when accessing Google Sheet: {api_error.response.text}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error when checking sheet access: {e}")
        return False    

def scroll_to_load_posts(driver):
    wait = WebDriverWait(driver, 5)
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        try:
            wait.until(
                lambda d: d.execute_script(
                    "return document.body.scrollHeight") > last_height
            )
        except TimeoutException:
            break  # No more content is loading, move to the next step

        last_height = driver.execute_script(
            "return document.body.scrollHeight")


def reformat_publish_time(publish_time):
    # Reformat the publish time to a desired format
    try:
        # Parse the original format
        parsed_time = datetime.strptime(publish_time, "%B %d, %Y at %I:%M %p")
        # Convert to the desired format (YYYY-MM-DD)
        return parsed_time.strftime("%Y-%m-%d")
    except Exception:
        # Return the original value if parsing fails
        return publish_time


def append_to_google_sheet(data, sheet_name):
    # Append data to Google Sheet in bulk with deduplication
    try:
        client = authenticate_google_api()

        # Open the Google Sheet
        logging.info(f"Attempting to access Google Sheet: {sheet_name}")
        sheet = client.open(sheet_name).sheet1
        logging.info(f"Successfully accessed Google Sheet: {sheet_name}")

        # Get existing data to avoid duplicates
        logging.info("Checking for existing data...")
        # Retrieve all rows as a list of dictionaries
        existing_records = sheet.get_all_records()
        # Extract existing Post URLs
        existing_urls = {record["Post URL"] for record in existing_records}

        # Filter out duplicate posts
        logging.info("Filtering out duplicate posts...")
        new_data = data[~data["Post URL"].isin(
            existing_urls)]  # Keep only new rows
        
        new_rows_count = len(new_data)

        if new_data.empty:
            logging.info(
                "No new posts to append. All posts are already in the sheet.")
            return

        # Append new rows in bulk
        logging.info(
            f"Appending {new_rows_count} new rows to the Google Sheet...")
        rows = new_data.values.tolist()  # Convert DataFrame to list of lists
        sheet.append_rows(rows)
        logging.info("Data appended successfully!")
        return new_rows_count

    except gspread.SpreadsheetNotFound:
        logging.exception(
            "The specified Google Sheet was not found. Check the sheet name or ID.")
    except gspread.exceptions.APIError as api_error:
        logging.exception("API Error occurred:", api_error.response.text)
    except Exception as e:
        logging.exception("An unexpected error occurred:", e)


def parse_post(post):
    # Extract post data

    # Extract publish time
    try:
        publish_time_element = post.find_element(
            By.CSS_SELECTOR, "a[aria-label][role='link'][href*='/post/']")
    except Exception:
        publish_time = "N/A"
        post_url = "N/A"

    publish_time = publish_time_element.get_attribute("aria-label")
    # Reformat the publish time
    publish_time = reformat_publish_time(
        publish_time)
    # Get the post URL
    post_url = publish_time_element.get_attribute(
        "href")

    try:
        post_text = post.find_element(
            By.CSS_SELECTOR, "div[data-testid='postText']").text
    except Exception:
        post_text = "N/A"

    try:
        comment_button = post.find_element(
            By.CSS_SELECTOR, "button[data-testid='replyBtn']")
        comment_count = comment_button.get_attribute("aria-label")
        comment_count = int(''.join(filter(str.isdigit, comment_count)))

    except Exception:
        comment_count = 0

    try:
        repost_button = post.find_element(
            By.CSS_SELECTOR, "button[aria-label='Repost or quote post']")
        repost_count_element = repost_button.find_element(
            By.CSS_SELECTOR, "div[data-testid='repostCount']")
        repost_count = int(repost_count_element.text)
    except Exception:
        repost_count = 0

    try:
        like_button = post.find_element(
            By.CSS_SELECTOR, "button[data-testid='likeBtn']")
        like_count_element = like_button.find_element(
            By.CSS_SELECTOR, "div[data-testid='likeCount']")
        like_count = int(like_count_element.text)
    except Exception:
        like_count = 0

    return {
        "Publish Time": publish_time,
        "Post URL": post_url,
        "Post Text": post_text,
        "Comments": comment_count,
        "Reposts": repost_count,
        "Likes": like_count
    }


def main():
    '''Automation Script Logic'''

    # Check Google Sheet access before starting scraping
    if not check_sheet_access(SHEET_NAME):
        logging.error("Cannot access Google Sheet. Exiting script.")
        return

    driver = get_driver()

    logging.info("Starting Bluesky scraper...")
    logging.info(f"Target profile: {PROFILE_URL}")
    logging.info(f"Target sheet: {SHEET_NAME}")

    try:
        # Step 1: Open the public Bluesky page
        logging.info("Opening Bluesky page...")
        driver.get(PROFILE_URL)

        try:
            # Wait until the feed is present
            wait = WebDriverWait(driver, 10)
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-testid='postsFeed-flatlist']"))
            )
            logging.info("Feed loaded successfully!")
        except TimeoutException:
            logging.exception("Timed out waiting for the post feed to load.")

        # Step 2: Scroll to load all posts
        logging.info("Scrolling to load posts...")
        scroll_to_load_posts(driver)

        # Step 3: Locate the parent container
        logging.info("Locating the parent container...")
        parent_container = driver.find_element(
            By.CSS_SELECTOR, "div[data-testid='postsFeed-flatlist']")

        # Step 4: Identify post containers within the parent
        logging.info("Identifying post containers...")
        post_containers = parent_container.find_elements(
            By.XPATH, ".//div[@data-testid='feedItem-by-london.gov.uk']")

        # Step 5: Scrape data for each post
        logging.info("Scraping data from posts...")
        data = []
        for post in tqdm(post_containers):

            data.append(parse_post(post))

        # Step 6: Save data to a DataFrame
        logging.info("Converting scraped data to DataFrame...")
        df = pd.DataFrame(data)
        print(df)

        # Step 7: Save to Google Sheets
        new_rows_added = append_to_google_sheet(df, SHEET_NAME)

        # Display summary
        logging.info("Scraped data summary:")
        logging.info(f"Total posts scraped: {len(df)}")
        logging.info(f"Date range: {df['Publish Time'].min()} to {df['Publish Time'].max()}")
        logging.info(f"New posts added to sheet: {new_rows_added}")

    except Exception as e:
        logging.exception(f"An error occurred during scraping: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()