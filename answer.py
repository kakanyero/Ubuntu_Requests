import requests
import os
from urllib.parse import urlparse
import hashlib
from datetime import datetime
import mimetypes

def calculate_file_hash(filepath):
    """Calculate SHA-256 hash of a file for duplicate detection."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def is_valid_image_content_type(content_type):
    """Check if the content type is a valid image type."""
    valid_types = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp']
    return content_type.lower() in valid_types

def download_image(url, output_dir, existing_hashes):
    """Download a single image with safety checks and duplicate detection."""
    try:
        # Set headers for safe downloading
        headers = {
            'User-Agent': 'Ubuntu-Image-Fetcher/1.0 (Educational; Compatible)',
            'Accept': 'image/*',
            'Connection': 'keep-alive'
        }
        
        # Make request with timeout and headers
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()

        # Check Content-Type header
        content_type = response.headers.get('content-type', '')
        if not is_valid_image_content_type(content_type):
            print(f"✗ Invalid content type for {url}: {content_type}")
            return False

        # Check Content-Length header
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            print(f"✗ File too large for {url}: {content_length} bytes")
            return False

        # Extract filename
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Generate default filename if none exists
        if not filename or not mimetypes.guess_extension(content_type):
            extension = mimetypes.guess_extension(content_type) or '.jpg'
            filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
        
        filepath = os.path.join(output_dir, filename)
        
        # Download and check for duplicates
        temp_filepath = filepath + '.tmp'
        with open(temp_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Calculate hash to check for duplicates
        file_hash = calculate_file_hash(temp_filepath)
        if file_hash in existing_hashes:
            os.remove(temp_filepath)
            print(f"✗ Duplicate image detected: {filename}")
            return False
        
        # Rename temp file to final filename
        os.rename(temp_filepath, filepath)
        existing_hashes.add(file_hash)
        
        print(f"✓ Successfully fetched: {filename}")
        print(f"✓ Image saved to: {filepath}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error for {url}: {e}")
        return False
    except Exception as e:
        print(f"✗ Error processing {url}: {e}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return False

def main():
    print("Welcome to the Ubuntu Image Fetcher")
    print("A tool for mindfully collecting images from the web")
    print("Built with respect for community and responsible use\n")
    
    # Create output directory
    output_dir = "Fetched_Images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load existing image hashes
    existing_hashes = set()
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        if os.path.isfile(filepath):
            existing_hashes.add(calculate_file_hash(filepath))
    
    # Get URLs from user
    print("Enter image URLs (one per line, press Enter twice to finish):")
    urls = []
    while True:
        url = input("> ").strip()
        if url == "":
            break
        if url.startswith(('http://', 'https://')):
            urls.append(url)
        else:
            print(f"✗ Invalid URL format: {url}")
    
    if not urls:
        print("✗ No valid URLs provided")
        return
    
    # Download images
    success_count = 0
    for url in urls:
        if download_image(url, output_dir, existing_hashes):
            success_count += 1
    
    # Summary
    print(f"\nDownload Summary:")
    print(f"✓ Successfully downloaded: {success_count} image(s)")
    print(f"✗ Failed: {len(urls) - success_count} image(s)")
    print("\nConnection strengthened. Community enriched.")

if __name__ == "__main__":
    main()
