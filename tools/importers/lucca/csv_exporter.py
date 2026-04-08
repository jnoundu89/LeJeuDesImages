import os

import pandas as pd
import requests

LUCCA_AUTH_TOKEN = os.environ.get('LUCCA_AUTH_TOKEN', '')
LUCCA_BASE_URL = os.environ.get('LUCCA_BASE_URL', 'https://infolegale.ilucca.net')


def get_auth_headers():
    """
    Returns the authentication headers needed for the API requests.
    Reads the auth token from the LUCCA_AUTH_TOKEN environment variable.
    """
    if not LUCCA_AUTH_TOKEN:
        raise RuntimeError(
            'LUCCA_AUTH_TOKEN environment variable is not set. '
            'Export it before running the exporter.'
        )

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "cookie": f"authToken={LUCCA_AUTH_TOKEN}",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Opera GX\";v=\"118\", \"Chromium\";v=\"133\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 OPR/118.0.0.0 (Edition std-2)"
    }
    return headers

def get_users_list():
    """
    Fetches the list of users from the first URL.

    Returns:
        List[Dict]: A list of user data dictionaries.
    """
    url = f"{LUCCA_BASE_URL}/api/v3/users/scope?appInstanceId=14&operations=1&fields=id,name,firstName,lastName,mail,directLine,professionalMobile,jobTitle,birthDate,picture%5Bid,name,url,href,mimetype%5D,collection.count&orderBy=lastName,asc&paging=0,200"

    headers = get_auth_headers()

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data.get("data", {}).get("items", [])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching users list: {e}")
        return []

def get_user_details(user_id):
    """
    Fetches detailed information for a specific user.

    Args:
        user_id: The ID of the user.

    Returns:
        Dict: A dictionary containing the user's details.
    """
    url = f"{LUCCA_BASE_URL}/api/v3/users?id={user_id}&fields=id,firstName,lastName,picture[id,name,href],jobTitle,department[name,id],legalEntity[name],dtContractStart,mail,manager[id,name,firstName,lastName,picture[id,name,href]],directLine,professionalMobile,birthDate"

    headers = get_auth_headers()

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        if data.get("data", {}).get("items", []):
            return data.get("data", {}).get("items", [])[0]
        return {}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for user ID {user_id}: {e}")
        return {}

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flattens a nested dictionary.

    Args:
        d (dict): The dictionary to flatten.
        parent_key (str): The parent key for nested dictionaries.
        sep (str): The separator to use between keys.

    Returns:
        dict: A flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
            # Skip adding the original nested dictionary to avoid empty columns
        else:
            items.append((new_key, v))
    return dict(items)

def main():
    """
    Main function to run the scraper and export data to CSV.
    """
    print("Starting Lucca CSV exporter...")

    # Get the list of users
    print("Fetching users list...")
    users_list = get_users_list()

    if not users_list:
        print("No users found. Exiting.")
        return

    print(f"Found {len(users_list)} users.")

    # Get details for each user
    print("Fetching user details...")
    all_user_data = []

    for user in users_list:
        user_id = user.get("id")
        print(f"Fetching details for user ID {user_id}...")

        user_details = get_user_details(user_id)
        if user_details:
            # Flatten the nested dictionaries
            flattened_details = flatten_dict(user_details)
            all_user_data.append(flattened_details)

    print(f"Fetched details for {len(all_user_data)} users.")

    # Create DataFrame
    print("Creating DataFrame...")
    df = pd.DataFrame(all_user_data)

    # Drop columns that are completely empty (all values are NaN)
    print("Dropping empty columns...")
    df = df.dropna(axis=1, how='all')

    # Save to CSV
    output_file = "team.csv"
    print(f"Saving to {output_file}...")
    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"Export completed. Data saved to {output_file}.")

    # Display the first few rows of the DataFrame
    print("\nPreview of the exported data:")
    print(df.head())

    # Display DataFrame info
    print("\nDataFrame information:")
    print(df.info())

if __name__ == "__main__":
    main()
