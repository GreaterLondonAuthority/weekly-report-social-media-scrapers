import os
import json
import time
from datetime import datetime

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


# Scroll to load more posts


def scroll_to_load_posts(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait longer for posts to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Stop if no new posts are loaded
        last_height = new_height

# Function to reformat the publish time


def reformat_publish_time(publish_time):
    try:
        # Parse the original format
        parsed_time = datetime.strptime(publish_time, "%B %d, %Y at %I:%M %p")
        # Convert to the desired format (YYYY-MM-DD)
        return parsed_time.strftime("%Y-%m-%d")
    except Exception:
        # Return the original value if parsing fails
        return publish_time

# Function to append data to Google Sheet in bulk with deduplication


def append_to_google_sheet(data, sheet_name):
    try:
        # Authenticate with Google Sheets
        print("Authenticating with Google Sheets API...")

        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        creds = Credentials.from_service_account_info(
            creds_dict, scopes=scopes)
        # creds = Credentials.from_service_account_file(
        #     'credentials.json', scopes=scopes)
        client = gspread.authorize(creds)

        print("Authentication successful!")

        # Open the Google Sheet
        print(f"Attempting to access Google Sheet: {sheet_name}")
        sheet = client.open(sheet_name).sheet1
        print(f"Successfully accessed Google Sheet: {sheet_name}")

        # Get existing data to avoid duplicates
        print("Checking for existing data...")
        # Retrieve all rows as a list of dictionaries
        existing_records = sheet.get_all_records()
        # Extract existing Post URLs
        existing_urls = {record["Post URL"] for record in existing_records}

        # Filter out duplicate posts
        print("Filtering out duplicate posts...")
        new_data = data[~data["Post URL"].isin(
            existing_urls)]  # Keep only new rows
        if new_data.empty:
            print("No new posts to append. All posts are already in the sheet.")
            return

        # Append new rows in bulk
        print(f"Appending {len(new_data)} new rows to the Google Sheet...")
        rows = new_data.values.tolist()  # Convert DataFrame to list of lists
        sheet.append_rows(rows)
        print("Data appended successfully!")
    except gspread.SpreadsheetNotFound:
        print("The specified Google Sheet was not found. Check the sheet name or ID.")
    except gspread.exceptions.APIError as api_error:
        print("API Error occurred:", api_error.response.text)
    except Exception as e:
        print("An unexpected error occurred:", e)


# Initialize WebDriver
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(
    ChromeDriverManager().install()), options=options)

try:
    # Step 1: Open the public Bluesky page
    print("Opening Bluesky page...")
    # Replace with the public page URL
    driver.get("https://bsky.app/profile/london.gov.uk")
    time.sleep(3)  # Allow time for the page to load

    # Step 2: Scroll to load all posts
    print("Scrolling to load posts...")
    scroll_to_load_posts(driver)

    # Step 3: Locate the parent container
    print("Locating the parent container...")
    parent_container = driver.find_element(
        By.CSS_SELECTOR, "div[data-testid='postsFeed-flatlist']")

    # Step 4: Identify post containers within the parent
    print("Identifying post containers...")
    post_containers = parent_container.find_elements(
        By.XPATH, ".//div[@data-testid='feedItem-by-london.gov.uk']")

    # Step 5: Scrape data for each post
    print("Scraping data from posts...")
    data = []
    for post in post_containers:
        try:
            # Extract and reformat publish time
            publish_time_element = post.find_element(
                By.CSS_SELECTOR, "a[aria-label][role='link'][href*='/post/']")
            publish_time = publish_time_element.get_attribute("aria-label")
            publish_time = reformat_publish_time(
                publish_time)  # Reformat the publish time
            post_url = publish_time_element.get_attribute(
                "href")  # Get the post URL
        except Exception:
            publish_time = "N/A"
            post_url = "N/A"

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

        data.append({
            "Publish Time": publish_time,
            "Post URL": post_url,
            "Post Text": post_text,
            "Comments": comment_count,
            "Reposts": repost_count,
            "Likes": like_count
        })

    # Step 6: Save data to a DataFrame
    print("Converting scraped data to DataFrame...")
    df = pd.DataFrame(data)
    print(df)

    # Step 7: Save to Google Sheets
    # Update with your JSON key path
    sheet_name = "Bluesky"  # Replace with your Google Sheet name
    append_to_google_sheet(df, sheet_name)

finally:
    driver.quit()
