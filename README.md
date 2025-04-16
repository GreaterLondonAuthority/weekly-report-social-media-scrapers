# Weekly Report Social Media Scrapers

This repository holds automation scripts to scrape GLA data from social media platforms for performance analysis purposes. Data is appended to Google Sheets integrated with [Looker Studio](https://lookerstudio.google.com/u/0/reporting/795e52c4-4cd5-49c7-96f0-c1e02f55c979).

## Social Media Platforms

Scripts are available to target the following platforms:

- [Bluesky](https://bsky.app/profile/london.gov.uk) - [script](https://github.com/GreaterLondonAuthority/weekly-report-social-media-scrapers/tree/main/bluesky) - [Google Sheet](https://docs.google.com/spreadsheets/d/1j1MRzzga8cPkUUp500xaudOEfM_YUShq0rAaxrGhjVY/edit)

## Prerequisites

- Python 3.10+
- Google Service Account set up
- Google Sheet with service account's email granted Editor permissions. Sheet's name has to match the name used in the script.
- Service Account Key credentials available

### Creating environment credentials

To create a new Service Account Key follow steps outlined [here](https://developers.google.com/zero-touch/guides/customer/quickstart/python-service-account).

If running on GitHub, ensure that Google Service Account Key is added as a repository [environment variable](https://github.com/GreaterLondonAuthority/weekly-report-social-media-scrapers/settings/secrets/actions) **GOOGLE_CREDENTIALS**.

If running locally, save the Google Service Account Key as 'credentials.json' in the project root directory.

## Running the script on GitHub

Scripts are run periodically via GitHub actions, as set up in [.github/workflows/](https://github.com/GreaterLondonAuthority/weekly-report-social-media-scrapers/tree/main/.github/workflows).

To trigger an action manually go to [Actions tab](https://github.com/GreaterLondonAuthority/weekly-report-social-media-scrapers/actions) and select a workflow for the platform that you want to scrape data from. Click **Run workflow** to trigger a workflow run.

To investigate a workflow run and view logs, navigate to a specific run to access a log console. You can see all the steps and check for potential errors here.

## Installing the project locally

To install the project and run the scripts locally follow the steps below:

### 1. Clone the repo

```bash
git clone https://github.com/GreaterLondonAuthority/weekly-report-social-media-scrapers.git
cd weekly-report-social-media-scrapers
```

### 2. Create and activate a virtual environment:

```bash
python -m venv venv

# On Linux/MacOs:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Add google API credentials:

Save the service account key file as 'credentials.json' in the root directory

### 5. Modify the lines to run locally:

In your selected script's code you need to enable/disable some lines for it to access credentials correctly.

Comment out:

```python
# GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]
```

```python
# creds_dict = json.loads(GOOGLE_CREDENTIALS)
# creds = Credentials.from_service_account_info(
#   creds_dict, scopes=scopes)
```

Uncomment:

```python
creds = Credentials.from_service_account_file(
    'credentials.json', scopes=scopes)
```

## Running the script

To run a script run a command in a following format:

```bash
python3 [selected_script_directory]/[selected_script.py]
```

example:

```bash
python3 bluesky/bluesky.py
```
