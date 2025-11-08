"""
CDBL Assets Module
Handles asset downloading and swapping for Roblox cache
"""

import os
import json
import zipfile
import requests
import hashlib
import shutil
from urllib.parse import urlparse

def get_assets_cache_path():
    """Get the path to CDBL assets cache directory"""
    appdata = os.getenv('LOCALAPPDATA')
    cache_dir = os.path.join(appdata, 'CDBL', 'assets_cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_roblox_cache_path():
    """Get the path to Roblox cache directory"""
    appdata = os.getenv('LOCALAPPDATA')
    temp_dir = os.getenv('TEMP')
    
    # Try multiple possible Roblox cache locations
    possible_paths = [
        os.path.join(temp_dir, 'Roblox', 'http'),  # Most common location in Temp
        os.path.join(appdata, 'Temp', 'Roblox', 'http'),  # Alternative Temp location
        os.path.join(appdata, 'Roblox', 'http'),   # Original location
        os.path.join(appdata, 'Roblox', 'ClientSettings'),
        os.path.join(appdata, 'Roblox'),
        os.path.join(appdata, 'RobloxPlayerBeta'),
        os.path.join(appdata, 'RobloxPlayerBeta', 'http'),
        os.path.join(temp_dir, 'RobloxPlayerBeta', 'http')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Return the most common path even if it doesn't exist
    return os.path.join(temp_dir, 'Roblox', 'http')

def check_roblox_installation():
    """Check if Roblox is installed and return installation info"""
    appdata = os.getenv('LOCALAPPDATA')
    temp_dir = os.getenv('TEMP')
    
    # Check for Roblox directories in both AppData and Temp
    roblox_dirs = []
    possible_dirs = [
        os.path.join(appdata, 'Roblox'),
        os.path.join(appdata, 'RobloxPlayerBeta'),
        os.path.join(temp_dir, 'Roblox'),
        os.path.join(temp_dir, 'RobloxPlayerBeta')
    ]
    
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            roblox_dirs.append(dir_path)
    
    cache_path = get_roblox_cache_path()
    
    return {
        "roblox_installed": len(roblox_dirs) > 0,
        "roblox_directories": roblox_dirs,
        "cache_path": cache_path,
        "cache_exists": os.path.exists(cache_path)
    }

def download_file(url, destination):
    """Download a file from URL to destination"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_assets_json():
    """Download the assets.json file"""
    cache_dir = get_assets_cache_path()
    assets_json_path = os.path.join(cache_dir, 'assets.json')
    
    url = 'https://raw.githubusercontent.com/gastrophobic/Rivals/refs/heads/main/assets.json'
    
    if download_file(url, assets_json_path):
        return assets_json_path
    return None

def download_archive_files():
    """Download and extract all archive files to a single folder"""
    cache_dir = get_assets_cache_path()
    archives_dir = os.path.join(cache_dir, 'archives')
    
    # Create a single extraction directory for all archive contents
    extract_dir = os.path.join(archives_dir, 'extracted_assets')
    os.makedirs(extract_dir, exist_ok=True)
    
    # Clean up old separate archive directories if they exist
    cleanup_old_archive_directories(archives_dir, extract_dir)
    
    archive_urls = [
        'https://github.com/gastrophobic/Rivals-dump/raw/refs/heads/main/archive_0004.zip',
        'https://github.com/gastrophobic/Rivals-dump/raw/refs/heads/main/archive_001.zip',
        'https://github.com/gastrophobic/Rivals-dump/raw/refs/heads/main/archive_002.zip',
        'https://github.com/gastrophobic/Rivals-dump/raw/refs/heads/main/archive_003.zip'
    ]
    
    extracted_files = []
    
    for url in archive_urls:
        filename = os.path.basename(urlparse(url).path)
        zip_path = os.path.join(archives_dir, filename)
        
        # Download the zip file
        if download_file(url, zip_path):
            # Extract the zip file to the single extraction directory
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Extract all files to the single directory
                    for member in zip_ref.namelist():
                        # Extract the file
                        zip_ref.extract(member, extract_dir)
                        extracted_file_path = os.path.join(extract_dir, member)
                        
                        # Only add files (not directories) to the list
                        if os.path.isfile(extracted_file_path):
                            extracted_files.append(extracted_file_path)
                
                # Remove the zip file after extraction
                os.remove(zip_path)
                print(f"Extracted {filename} to unified assets folder")
                
            except Exception as e:
                print(f"Error extracting {zip_path}: {e}")
                continue
    
    print(f"Total extracted files in unified folder: {len(extracted_files)}")
    return extracted_files

def cleanup_old_archive_directories(archives_dir, extract_dir):
    """Remove old separate archive directories to consolidate into unified folder"""
    old_archive_names = ['archive_0004', 'archive_001', 'archive_002', 'archive_003']
    
    for archive_name in old_archive_names:
        old_dir = os.path.join(archives_dir, archive_name)
        if os.path.exists(old_dir) and os.path.isdir(old_dir):
            try:
                # Move files from old directory to unified directory
                for root, dirs, files in os.walk(old_dir):
                    for file in files:
                        old_file_path = os.path.join(root, file)
                        # Create relative path structure in unified directory
                        rel_path = os.path.relpath(old_file_path, old_dir)
                        new_file_path = os.path.join(extract_dir, rel_path)
                        
                        # Create directory structure if needed
                        os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                        
                        # Move file if it doesn't already exist
                        if not os.path.exists(new_file_path):
                            shutil.move(old_file_path, new_file_path)
                
                # Remove the old directory
                shutil.rmtree(old_dir)
                print(f"Consolidated {archive_name} into unified assets folder")
                
            except Exception as e:
                print(f"Warning: Could not consolidate {archive_name}: {e}")

def get_file_hash(file_path):
    """Get SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def find_asset_by_hash(target_hash, search_directory):
    """Find a file in directory by its hash"""
    for root, dirs, files in os.walk(search_directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = get_file_hash(file_path)
            if file_hash and file_hash.lower() == target_hash.lower():
                return file_path
    return None

def find_replacement_asset(replacement_hash):
    """Find replacement asset in the unified extracted assets directory"""
    cache_dir = get_assets_cache_path()
    extract_dir = os.path.join(cache_dir, 'archives', 'extracted_assets')
    
    if not os.path.exists(extract_dir):
        return None
    
    # Since assets are stored with their hash as filename, check directly
    asset_path = os.path.join(extract_dir, replacement_hash)
    if os.path.exists(asset_path):
        return asset_path
    
    # Fallback to hash-based search if direct filename lookup fails
    return find_asset_by_hash(replacement_hash, extract_dir)

def swap_asset(original_hash, replacement_hash):
    """
    Swap an asset in Roblox cache by hash
    
    Args:
        original_hash: The hash of the original asset to replace
        replacement_hash: The hash of the replacement asset to use
    
    Returns:
        dict: Result with success status and message
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    roblox_cache = get_roblox_cache_path()
    if not os.path.exists(roblox_cache):
        result["message"] = "Roblox cache directory not found"
        result["errors"].append(result["message"])
        return result
    
    # Find the replacement asset in unified directory
    replacement_asset_path = find_replacement_asset(replacement_hash)
    if not replacement_asset_path:
        result["message"] = f"Replacement asset with hash {replacement_hash} not found in extracted assets"
        result["errors"].append(result["message"])
        return result
    
    # Find the original asset in cache by hash
    original_asset_path = None
    for root, dirs, files in os.walk(roblox_cache):
        for file in files:
            file_path = os.path.join(root, file)
            if file == original_hash or file.lower() == original_hash.lower():
                original_asset_path = file_path
                break
        if original_asset_path:
            break
    
    if not original_asset_path:
        result["message"] = f"Original asset with hash {original_hash} not found in Roblox cache"
        result["errors"].append(result["message"])
        return result
    
    try:
        # Create backup of original
        backup_path = original_asset_path + '.cdbl_backup'
        if not os.path.exists(backup_path):
            shutil.copy2(original_asset_path, backup_path)
        
        # Replace with new asset
        shutil.copy2(replacement_asset_path, original_asset_path)
        
        result["success"] = True
        result["message"] = f"Successfully swapped asset {original_hash}"
        
    except Exception as e:
        result["message"] = f"Error swapping asset: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def place_asset_in_cache(asset_hash, replacement_hash):
    """
    Place an asset directly into Roblox cache, creating it if it doesn't exist
    This is useful for assets that may not be in cache yet
    
    Args:
        asset_hash: The hash name to use in the cache
        replacement_hash: The hash of the replacement asset to copy
    
    Returns:
        dict: Result with success status and message
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    roblox_cache = get_roblox_cache_path()
    if not os.path.exists(roblox_cache):
        result["message"] = "Roblox cache directory not found"
        result["errors"].append(result["message"])
        return result
    
    # Find the replacement asset
    replacement_asset_path = find_replacement_asset(replacement_hash)
    if not replacement_asset_path:
        result["message"] = f"Replacement asset with hash {replacement_hash} not found in extracted assets"
        result["errors"].append(result["message"])
        return result
    
    # Check if original asset exists in cache
    original_asset_path = None
    for root, dirs, files in os.walk(roblox_cache):
        for file in files:
            if file == asset_hash or file.lower() == asset_hash.lower():
                original_asset_path = os.path.join(root, file)
                break
        if original_asset_path:
            break
    
    try:
        if original_asset_path:
            # Asset exists - create backup and replace
            backup_path = original_asset_path + '.cdbl_backup'
            if not os.path.exists(backup_path):
                shutil.copy2(original_asset_path, backup_path)
            shutil.copy2(replacement_asset_path, original_asset_path)
            result["message"] = f"Replaced existing asset {asset_hash}"
        else:
            # Asset doesn't exist - place it directly in cache
            destination_path = os.path.join(roblox_cache, asset_hash)
            shutil.copy2(replacement_asset_path, destination_path)
            result["message"] = f"Placed new asset {asset_hash} in cache"
        
        result["success"] = True
        
    except Exception as e:
        result["message"] = f"Error placing asset: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def restore_asset(asset_hash):
    """
    Restore an asset from backup
    
    Args:
        asset_hash: The hash of the asset to restore
    
    Returns:
        dict: Result with success status and message
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    roblox_cache = get_roblox_cache_path()
    if not os.path.exists(roblox_cache):
        result["message"] = "Roblox cache directory not found"
        result["errors"].append(result["message"])
        return result
    
    # Find the asset and its backup
    for root, dirs, files in os.walk(roblox_cache):
        for file in files:
            if file == asset_hash or file.lower() == asset_hash.lower():
                asset_path = os.path.join(root, file)
                backup_path = asset_path + '.cdbl_backup'
                
                if os.path.exists(backup_path):
                    try:
                        shutil.copy2(backup_path, asset_path)
                        result["success"] = True
                        result["message"] = f"Successfully restored asset {asset_hash}"
                        return result
                    except Exception as e:
                        result["message"] = f"Error restoring asset: {str(e)}"
                        result["errors"].append(result["message"])
                        return result
                else:
                    result["message"] = f"No backup found for asset {asset_hash}"
                    result["errors"].append(result["message"])
                    return result
    
    result["message"] = f"Asset {asset_hash} not found in cache"
    result["errors"].append(result["message"])
    return result

def download_and_prepare_assets_with_progress(progress_callback=None):
    """
    Download assets.json and archive files with progress reporting
    
    Args:
        progress_callback: Function to call for progress updates (percentage, message)
    
    Returns:
        dict: Result with success status, assets info, and available files
    """
    result = {
        "success": False,
        "message": "",
        "assets_json": None,
        "available_files": [],
        "errors": []
    }
    
    def report_progress(percentage, message):
        if progress_callback:
            progress_callback(percentage, message)
    
    try:
        report_progress(10, "Starting asset download...")
        
        # Download assets.json
        report_progress(20, "Downloading assets.json...")
        assets_json_path = download_assets_json()
        if not assets_json_path:
            result["message"] = "Failed to download assets.json"
            result["errors"].append(result["message"])
            return result
        
        report_progress(40, "Loading assets.json...")
        # Load assets.json
        with open(assets_json_path, 'r') as f:
            assets_data = json.load(f)
            result["assets_json"] = assets_data
        
        report_progress(60, "Downloading archive files...")
        # Download and extract archive files
        extracted_files = download_archive_files()
        result["available_files"] = extracted_files
        
        report_progress(90, "Finalizing asset preparation...")
        
        result["success"] = True
        result["message"] = f"Successfully downloaded assets.json and {len(extracted_files)} archive files"
        
        report_progress(100, "Asset download completed!")
        
    except Exception as e:
        result["message"] = f"Error downloading assets: {str(e)}"
        result["errors"].append(result["message"])
        report_progress(0, f"Error: {str(e)}")
    
    return result

def download_and_prepare_assets():
    """
    Download assets.json and archive files, prepare for swapping
    
    Returns:
        dict: Result with success status, assets info, and available files
    """
    result = {
        "success": False,
        "message": "",
        "assets_json": None,
        "available_files": [],
        "errors": []
    }
    
    try:
        # Download assets.json
        assets_json_path = download_assets_json()
        if not assets_json_path:
            result["message"] = "Failed to download assets.json"
            result["errors"].append(result["message"])
            return result
        
        # Load assets.json
        with open(assets_json_path, 'r') as f:
            assets_data = json.load(f)
            result["assets_json"] = assets_data
        
        # Download and extract archive files
        extracted_files = download_archive_files()
        result["available_files"] = extracted_files
        
        result["success"] = True
        result["message"] = f"Successfully downloaded assets.json and {len(extracted_files)} archive files"
        
    except Exception as e:
        result["message"] = f"Error downloading assets: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def apply_skybox_fix():
    """
    Apply skybox fix by swapping assets and applying fastflags
    
    Returns:
        dict: Result with success status and message
    """
    result = {
        "success": False,
        "message": "",
        "swapped_assets": [],
        "errors": []
    }
    
    try:
        # First ensure we have the assets downloaded
        download_result = download_and_prepare_assets()
        if not download_result["success"]:
            result["message"] = "Failed to download required assets"
            result["errors"].extend(download_result["errors"])
            return result
        
        # Load assets.json to get the mapping
        cache_dir = get_assets_cache_path()
        assets_json_path = os.path.join(cache_dir, 'assets.json')
        
        if not os.path.exists(assets_json_path):
            result["message"] = "assets.json not found"
            result["errors"].append(result["message"])
            return result
        
        # Read the assets mapping
        try:
            with open(assets_json_path, 'r') as f:
                assets_data = json.load(f)
        except Exception as e:
            result["message"] = f"Failed to load assets.json: {str(e)}"
            result["errors"].append(result["message"])
            return result
        
        # Swap each asset defined in assets.json
        # Using place_asset_in_cache which works even if the original doesn't exist
        swapped_count = 0
        failed_count = 0
        
        for original_hash, replacement_hash in assets_data.items():
            swap_result = place_asset_in_cache(original_hash, replacement_hash)
            if swap_result["success"]:
                result["swapped_assets"].append(original_hash)
                swapped_count += 1
                print(f"✅ {swap_result['message']}")
            else:
                failed_count += 1
                error_msg = f"Failed to swap {original_hash}: {swap_result['message']}"
                result["errors"].append(error_msg)
                print(f"⚠️ {error_msg}")
        
        # Apply fastflag for skybox fix
        from .fastflags import apply_fastflags
        
        skybox_fix_flags = {
            "FFlagRenderSkyboxUseIBL": "False",
            "FFlagRenderSkyboxUseEnvMap": "False"
        }
        
        fastflag_result = apply_fastflags(skybox_fix_flags)
        if not fastflag_result["success"]:
            result["message"] = "Failed to apply skybox fix fastflags"
            result["errors"].extend(fastflag_result["errors"])
            return result
        
        # Determine overall success
        if swapped_count > 0:
            result["success"] = True
            if failed_count > 0:
                result["message"] = f"Skybox fix applied with {swapped_count} assets swapped ({failed_count} failed)"
            else:
                result["message"] = f"Skybox fix applied successfully ({swapped_count} assets swapped)"
        else:
            result["message"] = "No assets were swapped"
            if failed_count > 0:
                result["message"] += f" ({failed_count} failed)"
        
    except Exception as e:
        result["message"] = f"Error applying skybox fix: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def get_cache_info():
    """Get information about cached assets"""
    cache_dir = get_assets_cache_path()
    archives_dir = os.path.join(cache_dir, 'archives')
    extract_dir = os.path.join(archives_dir, 'extracted_assets')
    
    info = {
        "cache_directory": cache_dir,
        "assets_json_exists": os.path.exists(os.path.join(cache_dir, 'assets.json')),
        "archives_directory": archives_dir,
        "extracted_assets_directory": extract_dir,
        "total_cached_files": 0,
        "extracted_assets_count": 0
    }
    
    if os.path.exists(cache_dir):
        for root, dirs, files in os.walk(cache_dir):
            info["total_cached_files"] += len(files)
    
    # Count files in the unified extracted assets directory
    if os.path.exists(extract_dir):
        for root, dirs, files in os.walk(extract_dir):
            info["extracted_assets_count"] += len(files)
    
    return info