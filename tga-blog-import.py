import requests
from bs4 import BeautifulSoup
import logging
import mimetypes

## scrape blogs from a wordpress site and upload them to a new wordpress site ##


# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize a session and set common headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
})

# Authentication details
username = ''  # Change this to wp-admin username
password = ''  # Change this to generated app password in user profile
website_url = 'https://texasgolfasdev.wpenginepowered.com/'  # Change this to your site's URL

def fetch_all_posts(base_url):
    all_posts = []
    per_page = 50  # Set a high number to minimize requests (max is usually 100)
    page = 1
    while True:
        api_url = f"{base_url}/wp-json/wp/v2/posts?per_page={per_page}&page={page}&_embed"
        response = session.get(api_url)
        if response.status_code == 200:
            posts = response.json()
            if not posts:
                break  # Exit loop if no more posts are returned
            all_posts.extend(posts)
            page += 1
        else:
            logging.error(f"Failed to fetch posts, status code: {response.status_code}")
            break
    return all_posts

def extract_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    content_elements = soup.find_all(['h2', 'p'])
    logging.debug(content_elements)
    return ''.join([str(element) for element in content_elements])

def get_category_id(name):
    categories_url = f"{website_url}/wp-json/wp/v2/categories"
    response = session.get(categories_url, params={'search': name}, auth=(username, password))
    if response.status_code == 200:
        json_data = response.json()
        if len(json_data) > 0:
            return json_data[0]['id']
        else:
            data = {'name': name}
            response = session.post(categories_url, json=data, auth=(username, password))
            if response.status_code == 201:
                return response.json()['id']
            else:
                logging.error(f"Failed to create category '{name}', status code: {response.status_code}, Response: {response.text}")
    else:
        logging.error(f"Failed to fetch category '{name}', status code: {response.status_code}, Response: {response.text}")
    return None

def upload_featured_image(image_url):
    # Get the image content
    image_data = session.get(image_url).content
    image_name = image_url.split("/")[-1]
    
    # Determine the MIME type of the image
    mime_type, _ = mimetypes.guess_type(image_url)
    if not mime_type:
        logging.error(f"Could not determine MIME type for image: {image_name}")
        return None

    # Set the filename and MIME type in the files parameter for the POST request
    files = {'file': (image_name, image_data, mime_type)}
    headers = {'Content-Disposition': f'attachment; filename="{image_name}"'}
    
    # Upload the image
    response = session.post(f"{website_url}/wp-json/wp/v2/media", headers=headers, files=files, auth=(username, password))
    if response.status_code == 201:
        logging.info(f"Image uploaded successfully: {image_name}")
        return response.json().get('id')
    else:
        logging.error(f"Failed to upload featured image {image_name}, status code: {response.status_code}, Response: {response.text}")
        return None

def create_post(title, content, category_ids, featured_image_id):
    data = {
        'title': title,
        'content': content,
        'categories': category_ids,
        'status': 'publish',
        'featured_media': featured_image_id
    }
    response = session.post(f"{website_url}/wp-json/wp/v2/posts", json=data, auth=(username, password))
    if response.status_code == 201:
        logging.info(f"Post created successfully: {response.json().get('link')}")
    else:
        logging.error(f"Failed to create post, status code: {response.status_code}, Response: {response.text}")

def main():
    logging.info("Starting to fetch and create posts...")
    posts = fetch_all_posts("https://www.txga.org")  # Updated to use fetch_all_posts
    skipped_posts = 1292  # Number of posts to skip
    processed_posts = 0  # Counter for processed (or skipped) posts

    for post in posts:
        processed_posts += 1  # Increment counter for each post

        if processed_posts <= skipped_posts:
            continue  # Skip processing this post
        title = post['title']['rendered']
        featured_image_url = None
        if 'wp:featuredmedia' in post['_embedded'] and len(post['_embedded']['wp:featuredmedia']) > 0:
            media = post['_embedded']['wp:featuredmedia'][0]
            if 'source_url' in media:
                featured_image_url = media['source_url']
        content = extract_content(post['content']['rendered'])
        category_names = [cat['name'] for cat in post['_embedded']['wp:term'][0]] if 'wp:term' in post['_embedded'] and len(post['_embedded']['wp:term']) > 0 else []

        category_ids = [get_category_id(name) for name in category_names if get_category_id(name) is not None]

        featured_image_id = upload_featured_image(featured_image_url) if featured_image_url else None

        create_post(title, content, category_ids, featured_image_id)

if __name__ == "__main__":
    main()
