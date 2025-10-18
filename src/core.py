"""
CDBL Core Functions Module
Contains all the main functionality for CDBL operations
"""

import os
import requests
import zipfile
import shutil
import sys
import subprocess
import platform
import time
import xml.etree.ElementTree as ET
import json
import webbrowser
from tqdm import tqdm

# SSL certificate handling for PyInstaller EXE
def get_ssl_context():
    """Get SSL certificate bundle path for requests"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller EXE
        try:
            import certifi
            # Try to find bundled certificates
            bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            cert_path = os.path.join(bundle_dir, 'certifi', 'cacert.pem')
            if os.path.exists(cert_path):
                return cert_path
            else:
                # Fallback to certifi default
                return certifi.where()
        except ImportError:
            return None
    else:
        # Running as Python script
        try:
            import certifi
            return certifi.where()
        except ImportError:
            return None

# Configure requests session with SSL certificates
def get_requests_session():
    """Get a configured requests session with proper SSL handling"""
    session = requests.Session()
    
    # Set SSL certificate bundle
    cert_bundle = get_ssl_context()
    if cert_bundle and os.path.exists(cert_bundle):
        session.verify = cert_bundle
        print(f"Using SSL certificates: {cert_bundle}")
    else:
        print("Warning: SSL certificates not found, using system default")
    
    # Set reasonable timeouts
    session.timeout = (10, 30)  # (connect_timeout, read_timeout)
    
    # Set user agent
    session.headers.update({
        'User-Agent': 'CDBL/2.0 (Windows; requests)'
    })
    
    return session

# Global session for reuse
_session = None

def get_session():
    """Get or create the global requests session"""
    global _session
    if _session is None:
        _session = get_requests_session()
    return _session

# ========== Set Paths for Roblox, Bloxstrap, and Fishstrap ==========

roblox_path = os.path.join(os.environ['LOCALAPPDATA'], 'Roblox')
bloxstrap_path = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap')
fishstrap_path = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap')

# ========== Set Paths for CDBL ==========

cdbllite_path = os.path.join(os.environ['LOCALAPPDATA'], 'CDBL')
cdbl_temp_path = os.path.join(cdbllite_path, 'Temp')
cdbl_skybox_data_path = os.path.join(cdbllite_path, 'SkyboxData')
cdbl_skybox_pngs_path = os.path.join(cdbl_skybox_data_path, 'SkyPNGs')
cdbl_skybox_skys_path = os.path.join(cdbl_skybox_data_path, 'Skys')
cdbl_skybox_patch_path = os.path.join(cdbllite_path, 'SkyboxPatch')
cdbl_texture_data_path = os.path.join(cdbllite_path, 'TextureData')
cdbl_sound_data_path = os.path.join(cdbllite_path, 'SoundData')
cdbl_other_data_path = os.path.join(cdbllite_path, 'OtherData')

# ========== http Cache Directorie ========== 
httpcache_path = os.path.join(os.environ['TEMP'], 'Roblox', 'http')

# ========== Fast Flag Directories ==========
flag_path = os.path.join("ClientSettings", "ClientAppSettings.json")

# Ensure directories exist
paths = [
    cdbllite_path,
    cdbl_temp_path,
    cdbl_skybox_data_path,
    cdbl_skybox_pngs_path,
    cdbl_skybox_skys_path,
    cdbl_skybox_patch_path,
    cdbl_texture_data_path,
    cdbl_sound_data_path,
    cdbl_other_data_path
]

def ensure_directories():
    """Ensure all CDBL directories exist"""
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"Created directory: {os.path.basename(path)}")
        else:
            print(f"Directory already exists: {os.path.basename(path)}")

# Initialize directories on module import
for path in paths:
    os.makedirs(path, exist_ok=True)
    
# ========== File URLs ==========

# Skybox Files
global sky_name
global skybox_zips
global skybox_pngs_zip1
global skybox_pngs_zip2
global skys_list
global skybox_patch
global default_sky

sky_name = "Aurora"
skybox_zips = f"https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/SkyboxData/SkyZIPs/{sky_name}.zip"
skybox_pngs_zip1 = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/SkyboxData/SkyPNGs_part1.zip"
skybox_pngs_zip2 = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/SkyboxData/SkyPNGs_part2.zip"
skys_list = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/SkyboxData/Sky-list.txt"
skybox_patch = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/DataZIPs/SkyboxPatch.zip"
default_sky = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/DataZIPs/DefaultSky.zip"

# Texture Files
global dark_textures
global light_textures
global default_textures

dark_textures = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/DataZIPs/DarkTextures.zip"
light_textures = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/DataZIPs/LightTextures.zip"
default_textures = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/DataZIPs/DefaultTexturesWSky.zip"

# Sound Files (Not needed anymore, but keeping for legacy reasons)
global og_oof
global default_oof

og_oof = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/OofSoundData/og-oof.ogg"
default_oof = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/OofSoundData/DefaultOOF.ogg"

# RBX Settings XML File
global rbx_settings_xml

rbx_settings_xml = "https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/GlobalBasicSettings_13.xml"

# ========== Version Data ==========
APP_VERSION = "Beta"  # your current version
GITHUB_USERNAME = "eman225511"  # your GitHub username
GITHUB_REPO = "CDBL"  # your repo name
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/releases/latest"

# ========== File Functions ==========

def download_file(url, destination):
    """Download a file from a URL to a specified destination."""
    try:
        session = get_session()
        response = session.get(url, timeout=30)
        response.raise_for_status()  # Raise an error for bad responses
        with open(destination, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded {os.path.basename(url)}")
        return True
    except requests.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        print(f"Error saving file {destination}: {e}")
        return False

def download_file_with_progress(url, destination, progress_callback=None):
    """Download a file from a URL to a specified destination with a progress bar."""
    try:
        session = get_session()
        
        # Make a HEAD request to get the file size
        head_response = session.head(url, allow_redirects=True, timeout=10)
        total_size = int(head_response.headers.get('content-length', 0))
        
        # Start the download with streaming
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        filename = os.path.basename(url)
        downloaded = 0
        
        # Create progress bar if no callback provided (for CLI)
        if progress_callback is None:
            progress_bar = tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                desc=f"Downloading {filename}",
                ncols=80
            )
        
        with open(destination, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback is None:
                        progress_bar.update(len(chunk))
                    else:
                        # Calculate percentage and call the callback
                        if total_size > 0:
                            percentage = int((downloaded / total_size) * 100)
                            progress_callback(percentage, f"Downloading {filename}")
        
        if progress_callback is None:
            progress_bar.close()
            print(f"✅ Downloaded {filename}")
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ Failed to download {url}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during download: {e}")
        return False
        
def unzip_file(zip_path, extract_to):
    """Unzip a file to a specified directory."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {os.path.basename(zip_path)}")
        return True
    except zipfile.BadZipFile as e:
        print(f"Failed to unzip {zip_path}: {e}")
        return False
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")
        return False
        
def delete_file(file_path):
    """Delete a file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Cleaned up {os.path.basename(file_path)}")
    else:
        print(f"{file_path} does not exist, skipping deletion.")
        
def download_and_extract(url, destination):
    """Download a file and extract it if it's a zip file. 
    If files are in a subfolder, move them up to the destination and remove the subfolder."""
    zip_path = os.path.join(destination, os.path.basename(url))
    download_file(url, zip_path)
    unzip_file(zip_path, destination)
    delete_file(zip_path)  # Clean up the zip file after extraction

def download_and_extract_with_progress(url, destination, progress_callback=None):
    """Download a file with progress bar and extract it if it's a zip file. 
    If files are in a subfolder, move them up to the destination and remove the subfolder."""
    zip_path = os.path.join(destination, os.path.basename(url))
    
    # Use the progress-enabled download function
    if not download_file_with_progress(url, zip_path, progress_callback):
        return False
    
    # Update progress for extraction
    if progress_callback:
        progress_callback(90, "Extracting files...")
    
    # Extract the downloaded file
    if unzip_file(zip_path, destination):
        delete_file(zip_path)  # Clean up the zip file after extraction
        if progress_callback:
            progress_callback(100, "Download complete!")
        return True
    else:
        return False
    
def download_needed_files():
    """Download and extract all necessary files for CDBL-Lite, only if they don't already exist."""

    # Helper to check if a file exists in a directory
    def file_exists_in_dir(filename, directory):
        return os.path.exists(os.path.join(directory, filename))
    
    # Helper to check if directory has files with specific extensions
    def has_files_with_extensions(directory, extensions):
        try:
            files = os.listdir(directory)
            matching_files = [f for f in files if any(f.lower().endswith(ext.lower()) for ext in extensions)]
            if matching_files:
                print(f"Found {len(matching_files)} files in {os.path.basename(directory)}")
            return len(matching_files) > 0
        except FileNotFoundError:
            print(f"Directory {directory} not found")
            return False

    print("🔍 Checking existing files...")
    
    # Skybox PNGs - check if we already have PNG files
    if not has_files_with_extensions(cdbl_skybox_pngs_path, ['.png']):
        print("SkyPNGs part 1...")
        download_and_extract(skybox_pngs_zip1, cdbl_skybox_pngs_path)
        print("SkyPNGs part 2...")
        download_and_extract(skybox_pngs_zip2, cdbl_skybox_pngs_path)
    else:
        print("SkyPNGs already exist, skipping download")
    
    # Sky-list.txt
    if not file_exists_in_dir('Sky-list.txt', cdbl_skybox_data_path):
        print("Sky-list.txt...")
        download_file(skys_list, os.path.join(cdbl_skybox_data_path, 'Sky-list.txt'))
    else:
        print("Sky-list.txt already exists, skipping download")
    
    # SkyboxPatch.zip
    try:
        patch_files = os.listdir(cdbl_skybox_patch_path)
        if not patch_files:
            print("SkyboxPatch...")
            download_and_extract(skybox_patch, cdbl_skybox_patch_path)
        else:
            print("SkyboxPatch already exists, skipping download")
    except OSError:
        print("SkyboxPatch...")
        download_and_extract(skybox_patch, cdbl_skybox_patch_path)
    
    # DefaultSky.zip - check for specific sky files
    if not has_files_with_extensions(cdbl_skybox_data_path, ['.sky', '.rbxm']):
        print("DefaultSky...")
        download_and_extract(default_sky, cdbl_skybox_data_path)
    else:
        print("DefaultSky files already exist, skipping download")

    # Texture files - check if we already have texture files
    texture_files_exist = (
        has_files_with_extensions(cdbl_texture_data_path, ['.zip']) or
        any(os.path.exists(os.path.join(cdbl_texture_data_path, folder)) 
            for folder in ['DarkTextures', 'DefaultTexturesWSky', 'LightTextures'])
    )
    
    if not texture_files_exist:
        print("Downloading texture files...")
        download_and_extract(dark_textures, cdbl_texture_data_path)
        download_and_extract(light_textures, cdbl_texture_data_path)
        download_and_extract(default_textures, cdbl_texture_data_path)
    else:
        print("Texture files already exist, skipping download")
    
    # Sound files
    if not file_exists_in_dir('og-oof.ogg', cdbl_sound_data_path):
        print("og-oof.ogg...")
        download_file(og_oof, os.path.join(cdbl_sound_data_path, 'og-oof.ogg'))
    else:
        print("og-oof.ogg already exists, skipping download")
        
    if not file_exists_in_dir('DefaultOOF.ogg', cdbl_sound_data_path):
        print("DefaultOOF.ogg...")
        download_file(default_oof, os.path.join(cdbl_sound_data_path, 'DefaultOOF.ogg'))
    else:
        print("DefaultOOF.ogg already exists, skipping download")

    # RBX Settings XML file
    if not file_exists_in_dir('GlobalBasicSettings_13.xml', cdbl_other_data_path):
        print("GlobalBasicSettings_13.xml...")
        download_file(rbx_settings_xml, os.path.join(cdbl_other_data_path, 'GlobalBasicSettings_13.xml'))
    else:
        print("GlobalBasicSettings_13.xml already exists, skipping download")

# ========== Utility Functions ==========

def get_versions_path(target_client_name):
    """Get the versions path for the specified client."""
    client_name = target_client_name.lower()
    if client_name == "roblox":
        return os.path.join(os.environ['LOCALAPPDATA'], 'Roblox', 'Versions')
    elif client_name == "bloxstrap":
        return os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap', 'Versions')
    elif client_name == "fishstrap":
        return os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap', 'Versions')
    else:
        return None
    
def get_all_version_folders(target_client_name):
    """Get a list of all version folders for the specified client."""
    versions_path = get_versions_path(target_client_name)
    if not versions_path or not os.path.exists(versions_path):
        return []
    return [d for d in os.listdir(versions_path) if os.path.isdir(os.path.join(versions_path, d))]