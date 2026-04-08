import os
from typing import Any, Dict, List

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
            'Export it before running the scraper.'
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

def get_employee_ids() -> List[int]:
    """
    Fetches all employee IDs from the first URL.

    Returns:
        List[int]: A list of employee IDs.
    """
    url = f"{LUCCA_BASE_URL}/api/v3/users/scope?appInstanceId=14&operations=1&fields=id,name,firstName,lastName,mail,directLine,professionalMobile,jobTitle,birthDate,picture%5Bid,name,url,href,mimetype%5D,collection.count&orderBy=lastName,asc&paging=0,200"

    headers = get_auth_headers()

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()

        # Extract employee IDs from the response
        employee_ids = []
        for item in data.get("data", {}).get("items", []):
            employee_ids.append(item.get("id"))

        return employee_ids

    except requests.exceptions.RequestException as e:
        print(f"Error fetching employee IDs: {e}")
        return []

def get_employee_details(employee_id: int) -> Dict[str, Any]:
    """
    Fetches detailed information for a specific employee.

    Args:
        employee_id (int): The ID of the employee.

    Returns:
        Dict[str, Any]: A dictionary containing the employee's details.
    """
    url = f"{LUCCA_BASE_URL}/api/v3/users?id={employee_id}&fields=id,firstName,lastName,picture[id,name,href],jobTitle,department[name,id],legalEntity[name],dtContractStart,mail,manager[id,name,firstName,lastName,picture[id,name,href]],directLine,professionalMobile,birthDate"

    headers = get_auth_headers()

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        return data.get("data", {})

    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for employee ID {employee_id}: {e}")
        return {}

def determine_gender(first_name: str) -> str:
    """
    Simple heuristic to determine gender based on first name.
    This is a very basic approach and might not be accurate for all names.

    Args:
        first_name (str): The first name of the employee.

    Returns:
        str: 'man' or 'woman'
    """
    # This is a very simplified approach
    # In a real-world scenario, you might want to use a more sophisticated method
    # or an API that provides gender information based on names
    female_endings = ['a', 'e', 'ie', 'ine', 'ette', 'elle', 'ise', 'ane', 'enne']

    if first_name.lower().endswith(tuple(female_endings)):
        return "woman"
    return "man"

def create_employee_dataframe(employee_details_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Creates a DataFrame from a list of employee details.

    Args:
        employee_details_list (List[Dict[str, Any]]): A list of dictionaries containing employee details.

    Returns:
        pd.DataFrame: A DataFrame with the required columns.
    """
    data = []

    for employee in employee_details_list:
        if not employee:
            continue

        # Extract the required information
        first_name = employee.get("firstName", "")
        last_name = employee.get("lastName", "")
        name = f"{first_name} {last_name}"

        position = employee.get("jobTitle", "")

        # Determine gender based on first name
        sex = determine_gender(first_name)

        # Get image URL
        picture = employee.get("picture", {})
        image_url = picture.get("href", "") if picture else ""

        # Get department/team
        department = employee.get("department", {})
        team = department.get("name", "") if department else ""

        # Get company
        legal_entity = employee.get("legalEntity", {})
        company = legal_entity.get("name", "") if legal_entity else ""

        data.append({
            "company": company,
            "team": team,
            "name": name,
            "position": position,
            "sex": sex,
            "image_url": image_url
        })

    return pd.DataFrame(data)

def main():
    """
    Main function to run the scraper.
    """
    print("Starting Lucca HR scraper...")

    # Get all employee IDs
    print("Fetching employee IDs...")
    employee_ids = get_employee_ids()

    if not employee_ids:
        print("No employee IDs found. Exiting.")
        return

    print(f"Found {len(employee_ids)} employee IDs.")

    # Get details for each employee
    print("Fetching employee details...")
    employee_details_list = []

    for employee_id in employee_ids:
        print(f"Fetching details for employee ID {employee_id}...")
        employee_details = get_employee_details(employee_id)
        if employee_details:
            employee_details_list.append(employee_details)

    print(f"Fetched details for {len(employee_details_list)} employees.")

    # Create DataFrame
    print("Creating DataFrame...")
    df = create_employee_dataframe(employee_details_list)

    # Save to CSV
    output_file = "team_scraped.csv"
    print(f"Saving to {output_file}...")
    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"Scraping completed. Data saved to {output_file}.")

if __name__ == "__main__":
    main()
