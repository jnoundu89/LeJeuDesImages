import pandas as pd
import os
import requests
import time
from urllib.parse import urlparse
import shutil
from PIL import Image, ImageDraw, ImageFont
import io
import sys
# Add the parent directory to the path to import from sibling modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraping.infolegale_csv_exporter import get_auth_headers

def create_placeholder_image(save_path, sex='man'):
    """
    Create a simple placeholder image with the text 'No Image Available'.

    Args:
        save_path (str): The path where the image should be saved
        sex (str): 'man' or 'woman', used to determine the background color
    """
    try:
        # Create a new image with a colored background
        width, height = 200, 200
        if sex == 'woman':
            color = (255, 200, 200)  # Light pink for women
        else:
            color = (200, 200, 255)  # Light blue for men

        img = Image.new('RGB', (width, height), color=color)
        draw = ImageDraw.Draw(img)

        # Add text
        text = "No Image Available"
        draw.text((width/2, height/2), text, fill=(0, 0, 0), anchor="mm")

        # Save the image
        img.save(save_path)
        print(f"Created placeholder image at {save_path}")
        return True
    except Exception as e:
        print(f"Error creating placeholder image: {e}")
        # Create an empty file as a fallback
        with open(save_path, 'wb') as f:
            f.write(b'')
        return False

def download_image(url, save_path):
    """
    Download an image from a URL and save it to the specified path.

    Args:
        url (str): The URL of the image to download
        save_path (str): The path where the image should be saved

    Returns:
        bool: True if the download was successful, False otherwise
    """
    try:
        # Check if the URL is from ilucca.net
        if "ilucca.net" in url:
            # Modify the URL to request 400x400 images
            if "?a=0" in url:
                url = url.replace("?a=0", "?a=0&width=400")
            elif "?" in url:
                url = url + "&width=400"
            else:
                url = url + "?a=0&width=400"

            print(f"Modified URL for Lucca API: {url}")

            # Use the authentication headers for Lucca API
            headers = get_auth_headers()
            print(f"Using Lucca authentication headers for {url}")
        else:
            # Add headers to mimic a browser request for other URLs
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }

        # Make the request
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Save the image
        with open(save_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        print(f"Downloaded image from {url} to {save_path}")
        return True
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return False

def main():
    """
    Generate infolegale_team.csv by mapping columns from the onboarding backup
    and adding additional information from the Lucca backup.
    Also adds missing people from the Lucca file.
    """
    print("Starting generation of infolegale_team.csv...")

    # Read the CSV files
    # Use paths relative to the parent directory
    onboarding_file = "../infolegale_team_bckp_onboarding.csv"
    lucca_file = "../infolegale_team_bckp_lucca.csv"

    print(f"Reading {onboarding_file}...")
    onboarding_df = pd.read_csv(onboarding_file)

    print(f"Reading {lucca_file}...")
    lucca_df = pd.read_csv(lucca_file)

    # Create a mapping between the two datasets
    # We'll use the name field to match records
    print("Creating mapping between datasets...")

    # Create a combined dataframe starting with the onboarding data
    # This ensures we have the required columns for the game
    combined_df = onboarding_df.copy()

    # Create a mapping dictionary to match names between datasets
    # In onboarding: "name" column
    # In lucca: "firstName" + "lastName" columns
    lucca_df['full_name'] = lucca_df['firstName'] + ' ' + lucca_df['lastName']

    # Add all columns from lucca_df to combined_df based on name matching
    print("Adding additional information from Lucca data...")

    # Create a dictionary to store additional data for each person
    additional_data = {}

    # For each person in the Lucca data
    for _, lucca_row in lucca_df.iterrows():
        full_name = lucca_row['full_name']
        # Store all columns as additional data
        additional_data[full_name] = lucca_row.to_dict()

    # Add additional columns to the combined dataframe
    for column in lucca_df.columns:
        if column not in combined_df.columns:
            combined_df[column] = None

    # Keep track of which Lucca entries have been matched
    matched_lucca_entries = set()

    # Update the combined dataframe with additional data
    for i, row in combined_df.iterrows():
        name = row['name']
        # Find the closest match in the Lucca data
        for lucca_name, data in additional_data.items():
            # Simple matching - could be improved with fuzzy matching if needed
            if name.lower() in lucca_name.lower() or lucca_name.lower() in name.lower():
                # Update all columns with data from Lucca
                for column in lucca_df.columns:
                    if column not in ['full_name']:  # Skip the temporary column
                        combined_df.at[i, column] = data.get(column)
                matched_lucca_entries.add(lucca_name)
                break

    # Add missing people from Lucca file
    print("Adding missing people from Lucca file...")
    for lucca_name, data in additional_data.items():
        if lucca_name not in matched_lucca_entries:
            # Create a new row for this person
            new_row = {col: None for col in combined_df.columns}

            # Add data from Lucca
            for column in lucca_df.columns:
                if column != 'full_name' and column in combined_df.columns:
                    new_row[column] = data.get(column)

            # Set required columns for the game
            new_row['name'] = lucca_name

            # Determine company based on legalEntity_name
            if data.get('legalEntity_name') == 'ELOFICASH':
                new_row['company'] = 'Eloficash'
                new_row['team'] = 'Eloficash'
            else:
                new_row['company'] = 'Infolegale'
                # Use department_name as team if available
                if data.get('department_name'):
                    new_row['team'] = data.get('department_name')
                else:
                    new_row['team'] = 'Autre'

            # Set position from jobTitle
            if data.get('jobTitle'):
                new_row['position'] = data.get('jobTitle')
            else:
                new_row['position'] = 'Non spécifié'

            # Determine sex based on firstName (simplified approach)
            # This is a very basic approach and might not be accurate for all names
            if data.get('firstName'):
                if data.get('firstName').endswith('e') or data.get('firstName').endswith('a'):
                    new_row['sex'] = 'woman'
                else:
                    new_row['sex'] = 'man'
            else:
                new_row['sex'] = 'man'  # Default

            # Set picture_href if available, otherwise use a placeholder
            if data.get('picture_href'):
                new_row['picture_href'] = data.get('picture_href')
            else:
                # Use a placeholder image based on sex
                if new_row['sex'] == 'woman':
                    new_row['picture_href'] = 'https://www.infolegale.fr/hubfs/placeholder_woman.png'
                else:
                    new_row['picture_href'] = 'https://www.infolegale.fr/hubfs/placeholder_man.png'

            # Add the new row to the combined dataframe
            combined_df = pd.concat([combined_df, pd.DataFrame([new_row])], ignore_index=True)

    # Drop the temporary full_name column if it exists
    if 'full_name' in combined_df.columns:
        combined_df = combined_df.drop(columns=['full_name'])

    # Ensure all entries have a picture_href value
    # If picture_href is missing but image_url is present, copy from image_url
    for i, row in combined_df.iterrows():
        if pd.isna(row.get('picture_href')) and not pd.isna(row.get('image_url')):
            combined_df.at[i, 'picture_href'] = row['image_url']

    # Create a directory for downloaded images if it doesn't exist
    images_dir = "../static/images"
    os.makedirs(images_dir, exist_ok=True)

    # Download images and update picture_href to point to local files
    print("Downloading images...")
    for i, row in combined_df.iterrows():
        if not pd.isna(row.get('picture_href')):
            # Get the URL
            url = row['picture_href']

            # Create a filename based on the employee's name and ID
            employee_id = row.get('id', '')
            if employee_id:
                filename = f"{employee_id}_{row['name'].replace(' ', '_')}.jpg"
            else:
                # Use a hash of the URL if no ID is available
                filename = f"{hash(url) % 10000}_{row['name'].replace(' ', '_')}.jpg"

            # Full path to save the image
            save_path = os.path.join(images_dir, filename)

            # Check if the URL is from ilucca.net (which now has proper authentication)
            if "ilucca.net" in url:
                # Try to download directly from the Lucca API URL
                print(f"Attempting to download from Lucca API for {row['name']}: {url}")
                success = download_image(url, save_path)

                if success:
                    # Update the picture_href to point to the local file
                    combined_df.at[i, 'picture_href'] = f"/static/images/{filename}"
                    print(f"Successfully downloaded image from Lucca API for {row['name']}")
                else:
                    # If Lucca API download fails, try image_url if available
                    if not pd.isna(row.get('image_url')):
                        alt_url = row['image_url']
                        print(f"Lucca API download failed, trying image_url instead for {row['name']}: {alt_url}")
                        success = download_image(alt_url, save_path)

                        if success:
                            # Update the picture_href to point to the local file
                            combined_df.at[i, 'picture_href'] = f"/static/images/{filename}"
                        else:
                            # If both downloads fail, use a placeholder
                            sex = row.get('sex', 'man')
                            placeholder = f"../static/images/placeholder_{sex}.jpg"
                            if not os.path.exists(placeholder):
                                # Create a placeholder image if it doesn't exist
                                create_placeholder_image(placeholder, sex)
                            combined_df.at[i, 'picture_href'] = f"/static/images/placeholder_{sex}.jpg"
                            print(f"Using placeholder for {row['name']} after all download attempts failed")
                    else:
                        # If no image_url is available, use a placeholder
                        sex = row.get('sex', 'man')
                        placeholder = f"../static/images/placeholder_{sex}.jpg"
                        if not os.path.exists(placeholder):
                            # Create a placeholder image if it doesn't exist
                            create_placeholder_image(placeholder, sex)
                        combined_df.at[i, 'picture_href'] = f"/static/images/placeholder_{sex}.jpg"
                        print(f"Using placeholder for {row['name']} as Lucca API download failed and no image_url available")
            else:
                # For non-ilucca URLs, try to download directly
                success = download_image(url, save_path)

                if success:
                    # Update the picture_href to point to the local file
                    combined_df.at[i, 'picture_href'] = f"/static/images/{filename}"
                else:
                    # If download fails, try image_url if available
                    if not pd.isna(row.get('image_url')):
                        alt_url = row['image_url']
                        print(f"Trying image_url instead for {row['name']}: {alt_url}")
                        success = download_image(alt_url, save_path)

                        if success:
                            # Update the picture_href to point to the local file
                            combined_df.at[i, 'picture_href'] = f"/static/images/{filename}"
                        else:
                            # If that also fails, use a placeholder
                            sex = row.get('sex', 'man')
                            placeholder = f"../static/images/placeholder_{sex}.jpg"
                            if not os.path.exists(placeholder):
                                # Create a placeholder image if it doesn't exist
                                create_placeholder_image(placeholder, sex)
                            combined_df.at[i, 'picture_href'] = f"/static/images/placeholder_{sex}.jpg"
                            print(f"Using placeholder for {row['name']}")
                    else:
                        # Use a placeholder based on sex
                        sex = row.get('sex', 'man')
                        placeholder = f"../static/images/placeholder_{sex}.jpg"
                        if not os.path.exists(placeholder):
                            # Create a placeholder image if it doesn't exist
                            create_placeholder_image(placeholder, sex)
                        combined_df.at[i, 'picture_href'] = f"/static/images/placeholder_{sex}.jpg"
                        print(f"Using placeholder for {row['name']}")

            # Add a small delay to avoid overwhelming the server
            time.sleep(0.1)

    # Save the combined dataframe to a new CSV file
    output_file = "../infolegale_team.csv"
    print(f"Saving to {output_file}...")
    combined_df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"Generation completed. Data saved to {output_file}.")

    # Display the first few rows of the DataFrame
    print("\nPreview of the generated data:")
    print(combined_df.head())

    # Display DataFrame info
    print("\nDataFrame information:")
    print(combined_df.info())

if __name__ == "__main__":
    main()
