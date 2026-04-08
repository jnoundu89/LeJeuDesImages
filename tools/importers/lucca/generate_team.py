import os
import shutil
import sys
import time

import pandas as pd
import requests
from PIL import Image, ImageDraw

# Add the project root to the path so we can import sibling modules
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from tools.importers.lucca.csv_exporter import get_auth_headers


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
        draw.text((width / 2, height / 2), text, fill=(0, 0, 0), anchor="mm")

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
    Generate team CSV using the Lucca backup as the source of truth.
    Downloads images from picture_href URLs and adds an image_path column mapping to the local files.
    Preserves all original data from the Lucca backup.
    """
    print("Starting team CSV generation...")

    # Read the Lucca CSV file -- path relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    lucca_file = os.path.join(project_root, "infolegale_team_bckp_lucca.csv")

    print(f"Reading {lucca_file}...")
    lucca_df = pd.read_csv(lucca_file)

    # Create a copy of the Lucca dataframe to preserve all original data
    combined_df = lucca_df.copy()

    # Add a new column for image_path that will map to the downloaded images
    combined_df['image_path'] = None

    # Create a full_name column for easier reference
    combined_df['full_name'] = combined_df['firstName'] + ' ' + combined_df['lastName']

    # Ensure all entries have a picture_href value
    # If picture_href is missing, use a placeholder based on sex
    for i, row in combined_df.iterrows():
        # Determine sex based on firstName (simplified approach)
        # This is a very basic approach and might not be accurate for all names
        if pd.isna(row.get('sex')):
            if row.get('firstName'):
                if row.get('firstName').endswith('e') or row.get('firstName').endswith('a'):
                    combined_df.at[i, 'sex'] = 'woman'
                else:
                    combined_df.at[i, 'sex'] = 'man'
            else:
                combined_df.at[i, 'sex'] = 'man'  # Default

        # Set picture_href if it's missing
        if pd.isna(row.get('picture_href')):
            # Use a placeholder image based on sex
            sex = combined_df.at[i, 'sex']
            if sex == 'woman':
                combined_df.at[i, 'picture_href'] = 'placeholder_woman.png'
            else:
                combined_df.at[i, 'picture_href'] = 'placeholder_man.png'

    # Create a directory for downloaded images if it doesn't exist
    images_dir = os.path.join(project_root, "static", "images")
    os.makedirs(images_dir, exist_ok=True)

    # Download images and update image_path to point to local files
    print("Downloading images...")
    for i, row in combined_df.iterrows():
        if not pd.isna(row.get('picture_href')):
            # Get the URL
            url = row['picture_href']

            # Create a filename based on the employee's ID and full name
            employee_id = row.get('id', '')
            full_name = row['full_name']
            if employee_id:
                filename = f"{employee_id}_{full_name.replace(' ', '_')}.jpg"
            else:
                # Use a hash of the URL if no ID is available
                filename = f"{hash(url) % 10000}_{full_name.replace(' ', '_')}.jpg"

            # Full path to save the image
            save_path = os.path.join(images_dir, filename)

            # Check if the URL is from ilucca.net (which now has proper authentication)
            if "ilucca.net" in url:
                # Try to download directly from the Lucca API URL
                print(f"Attempting to download from Lucca API for {full_name}: {url}")
                success = download_image(url, save_path)

                if success:
                    # Update the image_path to point to the local file
                    combined_df.at[i, 'image_path'] = f"/static/images/{filename}"
                    print(f"Successfully downloaded image from Lucca API for {full_name}")
                else:
                    # If download fails, use a placeholder
                    sex = row.get('sex', 'man')
                    placeholder = os.path.join(images_dir, f"placeholder_{sex}.jpg")
                    if not os.path.exists(placeholder):
                        # Create a placeholder image if it doesn't exist
                        create_placeholder_image(placeholder, sex)
                    combined_df.at[i, 'image_path'] = f"/static/images/placeholder_{sex}.jpg"
                    print(f"Using placeholder for {full_name} as Lucca API download failed")
            else:
                # For non-ilucca URLs, try to download directly
                success = download_image(url, save_path)

                if success:
                    # Update the image_path to point to the local file
                    combined_df.at[i, 'image_path'] = f"/static/images/{filename}"
                    print(f"Successfully downloaded image for {full_name}")
                else:
                    # If download fails, use a placeholder
                    sex = row.get('sex', 'man')
                    placeholder = os.path.join(images_dir, f"placeholder_{sex}.jpg")
                    if not os.path.exists(placeholder):
                        # Create a placeholder image if it doesn't exist
                        create_placeholder_image(placeholder, sex)
                    combined_df.at[i, 'image_path'] = f"/static/images/placeholder_{sex}.jpg"
                    print(f"Using placeholder for {full_name} as download failed")

            # Add a small delay to avoid overwhelming the server
            time.sleep(0.1)

    # Drop the temporary full_name column before saving
    if 'full_name' in combined_df.columns:
        combined_df = combined_df.drop(columns=['full_name'])

    # Save the combined dataframe to a new CSV file
    output_file = os.path.join(project_root, "infolegale_team.csv")
    print(f"Saving to {output_file}...")
    combined_df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"Generation completed. Data saved to {output_file}.")
    print(f"The CSV file contains all original data from {lucca_file} plus a new 'image_path' column.")

    # Display the first few rows of the DataFrame
    print("\nPreview of the generated data:")
    print(combined_df[['id', 'firstName', 'lastName', 'picture_href', 'image_path']].head())

    # Display DataFrame info
    print("\nDataFrame information:")
    print(combined_df.info())


if __name__ == "__main__":
    main()
