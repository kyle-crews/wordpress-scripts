import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re


## script to scrape certail elements from a wordpress webpage ##

# Ensure images directory exists
images_dir = 'images'
os.makedirs(images_dir, exist_ok=True)

# Headers to mimic a real user visit
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Function to download image
def download_image(url):
    image_name = os.path.basename(url)
    image_path = os.path.join(images_dir, image_name)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            f.write(response.content)
    return image_path


def extract_email(text):
    match = re.search(r'href="mailto:(.*?)"', text, re.IGNORECASE)
    return match.group(1).strip() if match else 'Not Found'

def extract_phone_number(text):
    pattern = r'\(\d{3}\) \d{3}-\d{4}'
    match = re.search(pattern, text)
    return match.group() if match else 'Not Found'

def extract_address(text):
    match = re.search(r'Address:\s*(.*?)<br', text, re.IGNORECASE)
    return match.group(1).strip() if match else 'Not Found'

# Main data extraction function
def extract_data_from_url(url):
    response = requests.get(url, headers=headers)
    data = {}
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract general information HTML
        general_info = soup.select_one('[id="mc-row-6"] [class="col-sm-12 col-12"]')
        data['information'] = general_info.prettify() if general_info else 'Not Found'

        # Extract and format date
        date_element = soup.select_one('[class] .edit_content_wrap h3:nth-child(3)')
        data['date'] = date_element.get_text(strip=True) if date_element else 'Not Found'

        # Extract host club link and name
        host_club_element = soup.select_one('[id] p:nth-child(2) a:nth-child(4)')
        if host_club_element:
            data['host_club'] = host_club_element.get_text(strip=True)
            data['host_club_link'] = host_club_element['href']
        
        # Download logo image
        logo_element = soup.select_one('.position-relative:nth-of-type(1) p a img')
        if logo_element and 'src' in logo_element.attrs:
            image_url = logo_element['src']
            data['logo_path'] = download_image(image_url)

        # Extract address and phone number
        contact_element_html = str(soup.select_one('[id] .edit_content_wrap p:nth-child(2)'))
        data['phone'] = extract_phone_number(contact_element_html)
        data['address'] = extract_address(contact_element_html)
        data['director_email'] = extract_email(contact_element_html)
    
    return data

# List of URLs
urls = ["https://some-url.com/page1", "https://some-url.com/page2", "https://some-url.com/page3"]
all_data = [extract_data_from_url(url) for url in urls]

# Convert the list of data into a pandas DataFrame
df = pd.DataFrame(all_data)

# Save the DataFrame to a CSV file
df.to_csv('extracted_data.csv', index=False)

print("Data extraction completed and saved to extracted_data.csv")

