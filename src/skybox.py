"""
CDBL Skybox Module
Contains all skybox-related functionality
"""

import os
import shutil
import requests
import json
from .core import (
    cdbl_skybox_data_path, cdbl_skybox_pngs_path, cdbl_skybox_skys_path,
    cdbl_skybox_patch_path, download_and_extract, download_and_extract_with_progress, get_versions_path
)
from .cache import skybox_cache, popular_cache, preview_cache, api_rate_limiter

# Skybox API Configuration
SKYBOX_API_BASE_URL = "https://skys.vercel.app"
SKYBOX_API_KEY = "skyapi2651"  # Public key for regular skyboxes (no need to hide) 

# API timeout settings
API_TIMEOUT = 30
API_RETRY_COUNT = 2

# API Helper Functions
def make_api_request(endpoint, params=None, headers=None, timeout=API_TIMEOUT):
    """Make a request to the Skybox API with error handling and retries"""
    # Apply rate limiting
    api_rate_limiter.wait_if_needed()
    
    url = f"{SKYBOX_API_BASE_URL}{endpoint}"
    
    # Default headers with API key
    request_headers = {
        'x-api-key': SKYBOX_API_KEY,
        'User-Agent': 'CDBL/2.0'
    }
    if headers:
        request_headers.update(headers)
    
    for attempt in range(API_RETRY_COUNT):
        try:
            response = requests.get(url, params=params, headers=request_headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"API request attempt {attempt + 1} failed: {e}")
            if attempt == API_RETRY_COUNT - 1:
                raise
    
    return None

def get_skyboxes_from_api():
    """Get list of available skyboxes from API with caching"""
    cache_key = "skyboxes_list"
    
    # Check cache first
    cached_data = skybox_cache.get(cache_key)
    if cached_data is not None:
        print("📦 Using cached skyboxes list")
        return cached_data
    
    try:
        print("🌐 Fetching skyboxes from API...")
        response = make_api_request("/api/skyboxes")
        if response and response.status_code == 200:
            data = response.json()
            # Cache the result
            skybox_cache.set(cache_key, data)
            return data
        return None
    except Exception as e:
        print(f"Failed to fetch skyboxes from API: {e}")
        return None

def search_skyboxes_api(query):
    """Search skyboxes using the API with caching"""
    cache_key = f"search_skyboxes_{query.lower()}"
    
    # Check cache first
    cached_data = skybox_cache.get(cache_key)
    if cached_data is not None:
        print(f"📦 Using cached search results for: {query}")
        return cached_data
    
    try:
        print(f"🌐 Searching skyboxes for: {query}")
        response = make_api_request("/api/skyboxes/search", params={"q": query})
        if response and response.status_code == 200:
            data = response.json()
            # Cache search results
            skybox_cache.set(cache_key, data)
            return data
        return None
    except Exception as e:
        print(f"Failed to search skyboxes: {e}")
        return None

def get_popular_skyboxes_api(limit=None):
    """Get popular skyboxes from API with caching"""
    cache_key = f"popular_skyboxes_{limit}" if limit else "popular_skyboxes"
    
    # Check cache first
    cached_data = popular_cache.get(cache_key)
    if cached_data is not None:
        print("📦 Using cached popular skyboxes")
        return cached_data
    
    try:
        print("🌐 Fetching popular skyboxes from API...")
        params = {"limit": limit} if limit else None
        response = make_api_request("/api/skyboxes/popular", params=params)
        if response and response.status_code == 200:
            data = response.json()
            print(f"🔍 Popular API raw response: {data}")  # Debug output
            # Cache the result with longer TTL for popular lists
            popular_cache.set(cache_key, data)
            return data
        else:
            print(f"🔍 Popular API failed - Status: {response.status_code if response else 'No response'}")
        return None
    except Exception as e:
        print(f"Failed to fetch popular skyboxes: {e}")
        return None

# Premium API Functions
def make_premium_api_request(endpoint, params=None, headers=None, timeout=API_TIMEOUT):
    """Make a request to the Premium Skybox API with error handling and retries"""
    from .premium import get_premium_api_key
    
    # Apply rate limiting
    api_rate_limiter.wait_if_needed()
    
    premium_key = get_premium_api_key()
    if not premium_key:
        raise Exception("Premium API key not set")
    
    url = f"{SKYBOX_API_BASE_URL}{endpoint}"
    
    # Default headers with premium API key
    request_headers = {
        'x-premium-key': premium_key,
        'User-Agent': 'CDBL/2.0'
    }
    if headers:
        request_headers.update(headers)
    
    for attempt in range(API_RETRY_COUNT):
        try:
            response = requests.get(url, params=params, headers=request_headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Premium API request attempt {attempt + 1} failed: {e}")
            if attempt == API_RETRY_COUNT - 1:
                raise
    
    return None

def get_premium_skyboxes_from_api():
    """Get list of available premium skyboxes from API with caching"""
    cache_key = "premium_skyboxes_list"
    
    # Check cache first
    cached_data = skybox_cache.get(cache_key)
    if cached_data is not None:
        print("📦 Using cached premium skyboxes list")
        return cached_data
    
    try:
        print("🌐 Fetching premium skyboxes from API...")
        response = make_premium_api_request("/api/premium")
        if response and response.status_code == 200:
            data = response.json()
            # Cache the result
            skybox_cache.set(cache_key, data)
            return data
        return None
    except Exception as e:
        print(f"Failed to fetch premium skyboxes from API: {e}")
        return None

def get_popular_premium_skyboxes_api(limit=None):
    """Get popular premium skyboxes from API with caching"""
    cache_key = f"popular_premium_skyboxes_{limit}" if limit else "popular_premium_skyboxes"
    
    # Check cache first
    cached_data = popular_cache.get(cache_key)
    if cached_data is not None:
        print("📦 Using cached popular premium skyboxes")
        return cached_data
    
    try:
        print("🌐 Fetching popular premium skyboxes from API...")
        params = {"limit": limit} if limit else None
        response = make_premium_api_request("/api/premium/popular", params=params)
        if response and response.status_code == 200:
            data = response.json()
            print(f"🔍 Premium Popular API raw response: {data}")  # Debug output
            # Cache the result with longer TTL for popular lists
            popular_cache.set(cache_key, data)
            return data
        else:
            print(f"🔍 Premium Popular API failed - Status: {response.status_code if response else 'No response'}")
        return None
    except Exception as e:
        print(f"Failed to fetch popular premium skyboxes: {e}")
        return None

def search_premium_skyboxes_api(query):
    """Search premium skyboxes using the API with caching"""
    cache_key = f"search_premium_skyboxes_{query.lower()}"
    
    # Check cache first
    cached_data = skybox_cache.get(cache_key)
    if cached_data is not None:
        print(f"📦 Using cached premium search results for: {query}")
        return cached_data
    
    try:
        print(f"🌐 Searching premium skyboxes for: {query}")
        response = make_premium_api_request("/api/premium/search", params={"q": query})
        if response and response.status_code == 200:
            data = response.json()
            # Cache search results
            skybox_cache.set(cache_key, data)
            return data
        return None
    except Exception as e:
        print(f"Failed to search premium skyboxes: {e}")
        return None

def download_skybox_from_api(sky_name, destination_path, progress_callback=None):
    """Download a skybox ZIP file from the API"""
    try:
        if progress_callback:
            progress_callback(10, f"Requesting download for {sky_name}...")
        
        # Get download URL from API
        response = make_api_request("/api/skyboxes", params={"download": sky_name})
        if not response or response.status_code != 200:
            return False
        
        if progress_callback:
            progress_callback(30, f"Starting download of {sky_name}...")
        
        # Download the file with progress tracking
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = 30 + int((downloaded / total_size) * 60)
                        progress_callback(progress, f"Downloading {sky_name}... {downloaded//1024}KB")
        
        if progress_callback:
            progress_callback(95, f"Download complete, extracting {sky_name}...")
        
        return True
        
    except Exception as e:
        print(f"Failed to download {sky_name} from API: {e}")
        return False

# Skybox Name Functions
def make_skyname_list(force_local=False):
    """
    Get list of all sky names, prioritizing New API but falling back to Old API file.
    Always ensures "Default-Sky" is included for both APIs.
    
    Args:
        force_local: If True, skip New API and load from Old API file only
    """
    # If Old API mode is forced, skip New API
    if force_local:
        print("� Old API mode: Skipping New API, loading from Old API file")
    else:
        # Try New API first
        try:
            skyboxes = get_skyboxes_from_api()
            if skyboxes:
                skynames = [skybox.get('sky_name', '') for skybox in skyboxes if skybox.get('sky_name')]
                if skynames:
                    print(f"🆕 Loaded {len(skynames)} skyboxes from New API")
                    # Ensure "Default-Sky" is included for New API
                    cleaned_names = [name.replace(" ", "") for name in skynames]
                    if "Default-Sky" not in cleaned_names:
                        cleaned_names.insert(0, "Default-Sky")
                        print("✅ Added 'Default-Sky' to New API list")
                    return cleaned_names
        except Exception as e:
            print(f"New API unavailable, falling back to Old API file: {e}")
    
    # Fallback to Old API file
    sky_list_file = os.path.join(cdbl_skybox_data_path, 'Sky-list.txt')
    local_skyboxes = []
    
    # First, try to load from Sky-list.txt
    if os.path.exists(sky_list_file):
        print("📁 Loading skyboxes from Old API Sky-list.txt")
        with open(sky_list_file, 'r', encoding='utf-8') as f:
            local_skyboxes = [line.strip().replace(" ", "") for line in f if line.strip()]
    else:
        print(f"Sky-list.txt not found at {sky_list_file}")
    
    # Also scan local PNG files for additional skyboxes
    try:
        print("🖼️ Scanning local PNG files for skyboxes...")
        png_skyboxes = []
        if os.path.exists(cdbl_skybox_pngs_path):
            for file in os.listdir(cdbl_skybox_pngs_path):
                if file.lower().endswith('.png'):
                    # Remove .png extension and clean the name
                    skybox_name = file[:-4].replace(" ", "")
                    if skybox_name not in local_skyboxes:  # Avoid duplicates
                        png_skyboxes.append(skybox_name)
            
            if png_skyboxes:
                print(f"�️ Found {len(png_skyboxes)} additional skyboxes from PNG files")
                local_skyboxes.extend(png_skyboxes)
        else:
            print(f"PNG directory not found at {cdbl_skybox_pngs_path}")
    except Exception as e:
        print(f"Error scanning PNG files: {e}")
    
    # If no skyboxes found, return at least Default-Sky
    if not local_skyboxes:
        print("⚠️ No local skyboxes found, returning Default-Sky only")
        return ["Default-Sky"]
    
    # Ensure "Default-Sky" is included
    if "Default-Sky" not in local_skyboxes:
        local_skyboxes.insert(0, "Default-Sky")
        print("✅ Added 'Default-Sky' to local skybox list")
    
    print(f"📁 Total local skyboxes loaded: {len(local_skyboxes)}")
    return local_skyboxes

def make_skyname_dict():
    """
    Reads the Sky-list.txt file and returns a dict mapping numbers to sky names in alphabetical order.
    Example: {1: "Aurora", 2: "Cloudy", ...}
    """
    skynames = make_skyname_list()
    skynames_sorted = sorted(skynames, key=lambda x: x.lower())
    return {i + 1: name for i, name in enumerate(skynames_sorted)}

def search_skyboxes(query, limit=50):
    """
    Search for skyboxes by name using API or local fallback
    
    Args:
        query: Search term
        limit: Maximum number of results to return
        
    Returns:
        List of matching skybox names
    """
    if not query or len(query.strip()) < 2:
        return make_skyname_list()[:limit]
    
    query = query.strip()
    
    # Try API search first
    try:
        api_results = search_skyboxes_api(query)
        if api_results:
            skynames = [result.get('sky_name', '').replace(" ", "") for result in api_results if result.get('sky_name')]
            if skynames:
                print(f"🔍 Found {len(skynames)} skyboxes matching '{query}' via API")
                return skynames[:limit]
    except Exception as e:
        print(f"API search failed, using local search: {e}")
    
    # Fallback to local search
    all_skyboxes = make_skyname_list()
    query_lower = query.lower()
    matches = [name for name in all_skyboxes if query_lower in name.lower()]
    
    print(f"📁 Found {len(matches)} local matches for '{query}'")
    return matches[:limit]

def get_popular_skyboxes(limit=10):
    """
    Get popular skyboxes with download counts
    
    Args:
        limit: Maximum number of results to return
        
    Returns:
        List of popular skybox names
    """
    try:
        popular_data = get_popular_skyboxes_api()
        if popular_data:
            print(f"🔍 Processing popular data: {popular_data}")  # Debug output
            
            # Handle the response format: [{"sky_name": "Sunset", "downloads": 42}, ...]
            if isinstance(popular_data, list) and len(popular_data) > 0:
                popular_names = []
                for item in popular_data:
                    if isinstance(item, dict) and 'sky_name' in item:
                        sky_name = item['sky_name'].replace(" ", "")
                        downloads = item.get('downloads', 0)
                        popular_names.append(sky_name)
                        print(f"  📈 {sky_name}: {downloads} downloads")
                
                if popular_names:
                    print(f"📈 Successfully loaded {len(popular_names)} popular skyboxes from API")
                    return popular_names[:limit]
                else:
                    print("📝 No valid popular skyboxes found in API response")
            else:
                print(f"📝 API returned empty or invalid popular data: {type(popular_data)}")
    except Exception as e:
        print(f"Failed to get popular skyboxes: {e}")
    
    print("📝 Falling back to empty popular list (no popular skyboxes available)")
    return []  # Return empty list instead of fallback to avoid confusion

def download_sky_with_progress(sky_name, progress_callback=None):
    """Download a specific sky by name with progress callback support for GUI."""
    sky_name_clean = sky_name.replace(" ", "")  # Remove spaces for folder name
    sky_folder = os.path.join(cdbl_skybox_skys_path, sky_name_clean)
    
    # Check if folder exists and contains any files
    if os.path.isdir(sky_folder) and os.listdir(sky_folder):
        print(f"🔍 Sky '{sky_name}' already exists, skipping download.")
        if progress_callback:
            progress_callback(100, f"Skybox {sky_name} already exists")
        return True
    
    print(f"📥 Downloading skybox: {sky_name}")
    if progress_callback:
        progress_callback(0, f"Starting download of {sky_name}...")
    
    # Ensure the destination folder exists
    os.makedirs(sky_folder, exist_ok=True)
    
    # Try API download first
    temp_file_path = None
    try:
        import tempfile
        import zipfile
        
        # Create temporary file (delete=False means we manage deletion manually)
        temp_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        temp_file_path = temp_file.name
        temp_file.close()  # Close the file handle immediately so it can be used on Windows
        
        if download_skybox_from_api(sky_name_clean, temp_file_path, progress_callback):
            if progress_callback:
                progress_callback(95, f"Extracting {sky_name}...")
            
            # Extract the ZIP file
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(sky_folder)
            
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_err:
                print(f"Warning: Could not delete temp file: {cleanup_err}")
            
            if progress_callback:
                progress_callback(100, f"Successfully downloaded {sky_name}")
            
            print(f"✅ Successfully downloaded skybox via API: {sky_name}")
            return True
        else:
            raise Exception("API download failed")
                
    except Exception as e:
        print(f"API download failed for {sky_name}: {e}")
        # Clean up temp file on failure
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_err:
                print(f"Warning: Could not delete temp file: {cleanup_err}")
        print("🔄 Falling back to direct GitHub download...")
        
        # Fallback to original direct download method
        sky_url = f"https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/SkyboxData/SkyZIPs/{sky_name_clean}.zip"
        
        success = download_and_extract_with_progress(sky_url, sky_folder, progress_callback)
        
        if success:
            print(f"✅ Successfully downloaded skybox via fallback: {sky_name}")
        else:
            print(f"❌ Failed to download skybox: {sky_name}")
            # Clean up empty folder if download failed
            try:
                if os.path.exists(sky_folder) and not os.listdir(sky_folder):
                    os.rmdir(sky_folder)
            except Exception:
                pass
        
        return success

def download_sky(sky_name):
    """Download a specific sky by name into a folder with the same name, skip if already exists."""
    return download_sky_with_progress(sky_name, None)
    
def get_sky_preview(sky_name, force_local=False, is_premium=False):
    """
    Get the preview image for a specific sky by name with caching.
    
    Args:
        sky_name: The name of the sky to get the preview for.
        force_local: If True, only use local files, skip API
        is_premium: If True, use premium API endpoint for previews
    
    Returns:
        str: Path to the preview image, or None if not found.
    """
    sky_name_clean = sky_name.replace(" ", "")  # Remove spaces for folder name
    
    # If force_local is True (Old API mode), check local first and skip API
    if force_local:
        preview_path = os.path.join(cdbl_skybox_pngs_path, f"{sky_name_clean}.png")
        if os.path.exists(preview_path):
            print(f"📁 Using local preview for '{sky_name}' (Old API mode)")
            return preview_path
        else:
            print(f"Local preview image for '{sky_name}' not found in Old API mode.")
            return None
    
    # Check preview cache first
    tier = "premium" if is_premium else "regular"
    cache_key = f"preview_{tier}_{sky_name_clean}"
    cached_preview = preview_cache.get(cache_key)
    if cached_preview and os.path.exists(cached_preview):
        print(f"📦 Using cached {tier} preview for '{sky_name}'")
        return cached_preview
    
    # Try to get preview from API first (New API mode)
    try:
        # Use premium endpoint if is_premium is True
        if is_premium:
            preview_url = f"{SKYBOX_API_BASE_URL}/api/premium/preview?name={sky_name_clean}"
        else:
            preview_url = f"{SKYBOX_API_BASE_URL}/api/skyboxes/preview?name={sky_name_clean}"
        
        # Apply rate limiting for preview downloads
        api_rate_limiter.wait_if_needed()
        
        # Download preview to temporary location
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file_path = temp_file.name
        
        try:
            response = requests.get(preview_url, timeout=10)
            if response.status_code == 200:
                temp_file.write(response.content)
                temp_file.flush()
                temp_file.close()  # Close the file handle
                print(f"📡 Loaded {tier} preview for '{sky_name}' from API")
                
                # Cache the preview path
                preview_cache.set(cache_key, temp_file_path)
                return temp_file_path
            else:
                temp_file.close()
                os.unlink(temp_file_path)
        except Exception as download_err:
            temp_file.close()
            if os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            raise download_err
            
    except Exception as e:
        print(f"Failed to get preview from API for '{sky_name}': {e}")
    
    # Fallback to local preview
    preview_path = os.path.join(cdbl_skybox_pngs_path, f"{sky_name_clean}.png")
    if os.path.exists(preview_path):
        print(f"📁 Using local preview for '{sky_name}'")
        return preview_path
    else:
        print(f"Preview image for '{sky_name}' not found locally or via API.")
        return None

def get_custom_skybox_preview(path_to_sky_files):
    """
    Get the preview image for a custom skybox (returns any .png if preview.png not found).
    
    Args:
        path_to_sky_files: Path to the folder containing the custom skybox files
    
    Returns:
        str: Path to the preview image, or None if not found
    """
    preview_path = os.path.join(path_to_sky_files, 'preview.png')
    if os.path.exists(preview_path):
        return preview_path
    # Fallback: return any .png file in the folder
    try:
        for file in os.listdir(path_to_sky_files):
            if file.lower().endswith('.png'):
                return os.path.join(path_to_sky_files, file)
    except Exception:
        pass
    print(f"No preview image (.png) found in {path_to_sky_files}.")
    return None

def apply_skybox_patch(target_client_name):
    """
    Installs the skybox patch files to the selected client storage.
    target_client_name: "Roblox", "Bloxstrap", or "Fishstrap"
    """
    # Determine storage path
    storage = None
    client_name = target_client_name.lower()
    if client_name == "roblox":
        storage = os.path.join(os.environ['LOCALAPPDATA'], 'Roblox', 'rbx-storage')
    elif client_name == "bloxstrap":
        storage = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap', 'rbx-storage')
    elif client_name == "fishstrap":
        storage = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap', 'rbx-storage')
    else:
        print(f"Could not determine storage path for {target_client_name}.")
        return False

    # Assets path
    assets = os.path.join(cdbl_skybox_patch_path, "SkyboxPatch")
    if not os.path.isdir(assets):
        print("Required assets folder not found!")
        print("Please make sure the SkyboxPatch folder is present in CDBL-Lite data.")
        return False

    print(f"Installing skybox patch files to {target_client_name}...")

    # Create storage directory and subdirectories if they don't exist
    os.makedirs(storage, exist_ok=True)
    subdirs = ["a5", "73", "6c", "92", "78"]
    for d in subdirs:
        os.makedirs(os.path.join(storage, d), exist_ok=True)

    # Patch files and their destinations
    patch_files = [
        ("a564ec8aeef3614e788d02f0090089d8", "a5"),
        ("7328622d2d509b95dd4dd2c721d1ca8b", "73"),
        ("a50f6563c50ca4d5dcb255ee5cfab097", "a5"),
        ("6c94b9385e52d221f0538aadaceead2d", "6c"),
        ("9244e00ff9fd6cee0bb40a262bb35d31", "92"),
        ("78cb2e93aee0cdbd79b15a866bc93a54", "78"),
    ]

    success = True
    for filename, subdir in patch_files:
        src = os.path.join(assets, filename)
        dst_dir = os.path.join(storage, subdir)
        dst = os.path.join(dst_dir, filename)
        if os.path.isfile(src):
            try:
                # If file exists and is read-only, remove read-only attribute first
                if os.path.exists(dst):
                    try:
                        os.chmod(dst, 0o666)  # Make writable
                    except Exception:
                        pass
                
                shutil.copy2(src, dst)
                
                # Set file as read-only
                try:
                    os.chmod(dst, 0o444)
                except Exception:
                    pass  # Ignore if unable to set read-only
                    
            except PermissionError:
                # File exists and we can't overwrite it - that's actually okay for patches
                print(f"Patch file {filename} already exists and is protected.")
                # Don't mark as failure if the file already exists
                continue
            except Exception as e:
                print(f"Failed to copy {filename}: {e}")
                success = False
        else:
            print(f"Patch file {filename} not found.")
            success = False

    if success:
        print("Skybox patch installed successfully!")
    else:
        print("Skybox patch installed with warnings. Some files may be missing.")
    return success

def apply_skybox(target_client_name, sky_name):
    """
    Applies a skybox by copying its contents to client texture directories.
    Args:
        target_client_name: The client type (Roblox, Bloxstrap, Fishstrap)
        sky_name: The name of the skybox to apply
    """
    # Clean sky name and set source path
    sky_name_clean = sky_name.replace(" ", "")
    sky_source_path = os.path.join(cdbl_skybox_skys_path, sky_name_clean)
    
    # Check if skybox exists locally, download if not
    if not os.path.exists(sky_source_path) or not os.listdir(sky_source_path):
        print(f"🔍 Skybox '{sky_name}' does not exist in local storage.")
        print("📥 Attempting to download...")
        
        # Try to download the skybox
        if not download_sky(sky_name):
            print(f"❌ Failed to download skybox '{sky_name}'. Cannot apply.")
            return False
    
    # Auto-install skybox patch before applying skybox
    if not apply_skybox_patch(target_client_name):
        print("Failed to install skybox patch files. Aborting skybox application.")
        return False
    
    client_name = target_client_name.lower()
    applied = False
    
    if client_name == "roblox":
        # Roblox uses version-specific folders
        versions_path = get_versions_path(target_client_name)
        if not versions_path or not os.path.exists(versions_path):
            print(f"Versions path not found for {target_client_name}.")
            return False
        
        for version_dir in os.listdir(versions_path):
            version_path = os.path.join(versions_path, version_dir)
            if os.path.isdir(version_path):
                textures_path = os.path.join(version_path, 'PlatformContent', 'pc', 'textures')
                sky_destination_path = os.path.join(textures_path, 'sky')
                
                if os.path.exists(textures_path):
                    print(f"Applying skybox to {version_dir}...")
                    
                    # Remove old skybox if it exists
                    if os.path.exists(sky_destination_path):
                        try:
                            shutil.rmtree(sky_destination_path)
                        except Exception as e:
                            print(f"Failed to completely remove old skybox in {version_dir}: {e}")
                    
                    # Copy new skybox
                    try:
                        shutil.copytree(sky_source_path, sky_destination_path)
                        applied = True
                        print(f"Successfully applied to {version_dir}")
                    except Exception as e:
                        print(f"Failed to apply skybox '{sky_name}' to {version_dir}: {e}")
                        return False
    
    elif client_name in ["bloxstrap", "fishstrap"]:
        # Bloxstrap and Fishstrap use Modifications folder
        if client_name == "bloxstrap":
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap')
        else:  # fishstrap
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap')
        
        textures_path = os.path.join(base_path, 'Modifications', 'PlatformContent', 'pc', 'textures')
        sky_destination_path = os.path.join(textures_path, 'sky')
        
        # Create the directory structure if it doesn't exist
        os.makedirs(textures_path, exist_ok=True)
        
        print(f"Applying skybox to {target_client_name}...")
        
        # Remove old skybox if it exists
        if os.path.exists(sky_destination_path):
            try:
                shutil.rmtree(sky_destination_path)
            except Exception as e:
                print(f"Failed to completely remove old skybox: {e}")
        
        # Copy new skybox
        try:
            shutil.copytree(sky_source_path, sky_destination_path)
            applied = True
            print(f"Successfully applied to {target_client_name}")
        except Exception as e:
            print(f"Failed to apply skybox '{sky_name}' to {target_client_name}: {e}")
            return False
    
    else:
        print(f"Unknown client type: {target_client_name}")
        return False
    
    if not applied:
        print(f"No valid directories found to apply the skybox to.")
        return False
    
    print(f"Successfully applied skybox '{sky_name}' to '{target_client_name}'.")
    return True

def apply_custom_skybox(target_client_name, path_to_sky_files):
    """
    Applies a custom skybox by copying its contents to all Roblox version skybox directories.
    Only copies files with .png or .tex extensions.
    Also applies the skybox patch before copying files.

    Args:
        target_client_name: The client type (Roblox, Bloxstrap, Fishstrap)
        path_to_sky_files: Path to the folder containing the custom skybox files
    """
    # Get versions path
    versions_path = get_versions_path(target_client_name)
    if not versions_path:
        print(f"Could not determine versions path for {target_client_name}.")
        return False

    if not os.path.exists(path_to_sky_files):
        print(f"Custom skybox folder '{path_to_sky_files}' does not exist.")
        return False

    if not os.path.exists(versions_path):
        print(f"Versions path {versions_path} does not exist.")
        return False

    # Apply the skybox patch before copying files
    if not apply_skybox_patch(target_client_name):
        print("Failed to install skybox patch files. Aborting custom skybox application.")
        return False

    allowed_exts = ('.png','.tex')
    applied = False
    for version_dir in os.listdir(versions_path):
        version_path = os.path.join(versions_path, version_dir)
        if os.path.isdir(version_path):
            textures_path = os.path.join(version_path, 'PlatformContent', 'pc', 'textures')
            sky_destination_path = os.path.join(textures_path, 'sky')

            if os.path.exists(textures_path):
                print(f"Applying custom skybox to {version_dir}...")

                # Remove old skybox if it exists
                if os.path.exists(sky_destination_path):
                    try:
                        shutil.rmtree(sky_destination_path)
                    except Exception as e:
                        print(f"Failed to completely remove old skybox in {version_dir}: {e}")

                # Copy only allowed files from custom skybox
                try:
                    os.makedirs(sky_destination_path, exist_ok=True)
                    for file in os.listdir(path_to_sky_files):
                        if file.lower().endswith(allowed_exts):
                            src_file = os.path.join(path_to_sky_files, file)
                            dst_file = os.path.join(sky_destination_path, file)
                            shutil.copy2(src_file, dst_file)
                    applied = True
                    print(f"Successfully applied custom skybox to {version_dir}")
                except Exception as e:
                    print(f"Failed to apply custom skybox to {version_dir}: {e}")

    if applied:
        print("Custom skybox applied successfully!")
    else:
        print("No versions were updated with the custom skybox.")

    return applied

def apply_default_sky(target_client_name):
    """
    Applies the default skybox to client texture directories.
    Args:
        target_client_name: The client type (Roblox, Bloxstrap, Fishstrap)
    """
    default_sky_path = os.path.join(cdbl_skybox_data_path, 'DefaultSky', 'DefaultSky')
    if not os.path.exists(default_sky_path):
        print("Default sky not found in storage.")
        return False
    
    client_name = target_client_name.lower()
    
    if client_name == "roblox":
        # Roblox uses version-specific folders
        versions_path = get_versions_path(target_client_name)
        if not versions_path or not os.path.exists(versions_path):
            print(f"Versions path not found for {target_client_name}.")
            return False
        
        for version_dir in os.listdir(versions_path):
            version_path = os.path.join(versions_path, version_dir)
            if os.path.isdir(version_path):
                textures_path = os.path.join(version_path, 'PlatformContent', 'pc', 'textures')
                sky_destination = os.path.join(textures_path, 'sky')
                
                if os.path.exists(textures_path):
                    print(f"Applying default sky to {version_dir}...")
                    
                    try:
                        # Remove existing sky folder if it exists
                        if os.path.exists(sky_destination):
                            shutil.rmtree(sky_destination)
                        
                        # Copy default sky
                        shutil.copytree(default_sky_path, sky_destination)
                        print(f"Successfully applied to {version_dir}")
                    except Exception as e:
                        print(f"Failed to apply default sky to {version_dir}: {e}")
                        return False
    
    elif client_name in ["bloxstrap", "fishstrap"]:
        # Bloxstrap and Fishstrap use Modifications folder
        if client_name == "bloxstrap":
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap')
        else:  # fishstrap
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap')
        
        textures_path = os.path.join(base_path, 'Modifications', 'PlatformContent', 'pc', 'textures')
        sky_destination = os.path.join(textures_path, 'sky')
        
        # Create the directory structure if it doesn't exist
        os.makedirs(textures_path, exist_ok=True)
        
        print(f"Applying default sky to {target_client_name}...")
        
        try:
            # Remove existing sky folder if it exists
            if os.path.exists(sky_destination):
                shutil.rmtree(sky_destination)
            
            # Copy default sky
            shutil.copytree(default_sky_path, sky_destination)
            print(f"Successfully applied to {target_client_name}")
        except Exception as e:
            print(f"Failed to apply default sky to {target_client_name}: {e}")
            return False
    
    else:
        print(f"Unknown client type: {target_client_name}")
        return False
    
    print(f"Successfully applied default sky to '{target_client_name}'.")
    return True

def get_api_status():
    """
    Check if the Skybox API is available and get basic info
    
    Returns:
        dict: API status information
    """
    try:
        response = requests.get(f"{SKYBOX_API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Try to get actual skybox count from the skyboxes endpoint instead of health
            # This avoids premium counting issues
            try:
                skyboxes_response = requests.get(f"{SKYBOX_API_BASE_URL}/api/skyboxes", 
                                               headers={'x-api-key': SKYBOX_API_KEY}, 
                                               timeout=5)
                if skyboxes_response.status_code == 200:
                    skyboxes_data = skyboxes_response.json()
                    actual_count = len(skyboxes_data) if isinstance(skyboxes_data, list) else 0
                else:
                    actual_count = data.get("skyboxes", {}).get("count", 0)
            except:
                actual_count = data.get("skyboxes", {}).get("count", 0)
            
            return {
                "available": True,
                "status": data.get("status", "unknown"),
                "skybox_count": actual_count,
                "response_time": data.get("responseTime", 0)
            }
    except Exception as e:
        print(f"API health check failed: {e}")
    
    return {
        "available": False,
        "status": "unavailable", 
        "skybox_count": 0,
        "response_time": 0
    }

def get_premium_api_status():
    """
    Check if the Premium Skybox API is available and get premium skybox count
    First checks health endpoint to see if premium content exists
    
    Returns:
        dict: Premium API status information
    """
    try:
        from .premium import has_premium_access, get_premium_api_key
        
        # Check if user has premium access
        if not has_premium_access():
            return {
                "available": False,
                "status": "no_access",
                "premium_skybox_count": 0,
                "message": "Premium access required"
            }
        
        # Check premium API health
        premium_key = get_premium_api_key()
        if not premium_key:
            return {
                "available": False,
                "status": "no_key",
                "premium_skybox_count": 0,
                "message": "Premium API key not configured"
            }
        
        # First check the health endpoint to see if premium content exists
        try:
            health_response = requests.get(f"{SKYBOX_API_BASE_URL}/api/health", timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                # Access nested structure: skyboxes.premium.count
                skyboxes_data = health_data.get('skyboxes', {})
                premium_data = skyboxes_data.get('premium', {})
                premium_count = premium_data.get('count', 0)
                premium_status = premium_data.get('status', 'unknown')
                
                print(f"🔍 Health endpoint - Premium count: {premium_count}, status: {premium_status}")
                
                # If no premium skyboxes exist in the health endpoint, don't try to fetch them
                if premium_count == 0:
                    return {
                        "available": False,
                        "status": "no_content",
                        "premium_skybox_count": 0,
                        "message": "No premium skyboxes have been released yet"
                    }
        except Exception as health_error:
            print(f"Health check failed, proceeding with premium API check: {health_error}")
        
        # Try to get premium skyboxes count from the actual premium endpoint
        try:
            response = make_premium_api_request("/api/premium")
            if response and response.status_code == 200:
                premium_data = response.json()
                premium_count = len(premium_data) if isinstance(premium_data, list) else 0
                
                return {
                    "available": True,
                    "status": "available",
                    "premium_skybox_count": premium_count,
                    "message": f"{premium_count} premium skyboxes available"
                }
            elif response and response.status_code == 500:
                # Server error - likely no premium content available yet
                return {
                    "available": False,
                    "status": "no_content",
                    "premium_skybox_count": 0,
                    "message": "No premium skyboxes have been released yet"
                }
            else:
                status_code = response.status_code if response else "No response"
                return {
                    "available": False,
                    "status": "api_error",
                    "premium_skybox_count": 0,
                    "message": f"Premium API error (Status: {status_code})"
                }
        except Exception as e:
            # Check if it's a server error in the exception message
            error_msg = str(e)
            if "500" in error_msg or "Server Error" in error_msg:
                return {
                    "available": False,
                    "status": "no_content",
                    "premium_skybox_count": 0,
                    "message": "No premium skyboxes have been released yet"
                }
            else:
                return {
                    "available": False,
                    "status": "connection_error", 
                    "premium_skybox_count": 0,
                    "message": f"Connection error: {str(e)}"
                }
            
    except Exception as e:
        return {
            "available": False,
            "status": "error",
            "premium_skybox_count": 0,
            "message": f"Error: {str(e)}"
        }

def set_premium_api_key(api_key):
    """
    Set the premium API key for accessing premium skyboxes
    
    Args:
        api_key: Premium API key string
    """
    global SKYBOX_PREMIUM_API_KEY
    SKYBOX_PREMIUM_API_KEY = api_key
    print("🔑 Premium API key configured")

# Cache Management Functions
def get_cache_stats():
    """Get statistics about cache usage"""
    from .cache import get_cache_stats
    return get_cache_stats()

def clear_skybox_caches():
    """Clear all skybox-related caches"""
    from .cache import clear_all_caches
    clear_all_caches()
    print("🗑️ All skybox caches cleared")

def get_cache_info():
    """Get detailed cache information for debugging"""
    stats = get_cache_stats()
    return {
        "cache_sizes": stats,
        "total_cached_items": sum(stats.values()),
        "cache_info": "Skybox lists cached for 5min, Popular lists for 30min, Previews for 24h"
    }