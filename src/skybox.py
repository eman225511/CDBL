"""
CDBL Skybox Module
Contains all skybox-related functionality
"""

import os
import shutil
from .core import (
    cdbl_skybox_data_path, cdbl_skybox_pngs_path, cdbl_skybox_skys_path,
    cdbl_skybox_patch_path, download_and_extract, download_and_extract_with_progress, get_versions_path
)

# Skybox Name Functions
def make_skyname_list():
    """
    Reads the Sky-list.txt file and returns a list of all sky names.
    """
    sky_list_file = os.path.join(cdbl_skybox_data_path, 'Sky-list.txt')
    if not os.path.exists(sky_list_file):
        print(f"Sky-list.txt not found at {sky_list_file}")
        return []
    with open(sky_list_file, 'r', encoding='utf-8') as f:
        skynames = [line.strip().replace(" ", "") for line in f if line.strip()]
    return skynames

def make_skyname_dict():
    """
    Reads the Sky-list.txt file and returns a dict mapping numbers to sky names in alphabetical order.
    Example: {1: "Aurora", 2: "Cloudy", ...}
    """
    skynames = make_skyname_list()
    skynames_sorted = sorted(skynames, key=lambda x: x.lower())
    return {i + 1: name for i, name in enumerate(skynames_sorted)}

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
    
    sky_url = f"https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/SkyboxData/SkyZIPs/{sky_name_clean}.zip"
    
    # Ensure the destination folder exists
    os.makedirs(sky_folder, exist_ok=True)
    
    # Use the progress-enabled download function
    success = download_and_extract_with_progress(sky_url, sky_folder, progress_callback)
    
    if success:
        print(f"✅ Successfully downloaded skybox: {sky_name}")
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
    sky_name_clean = sky_name.replace(" ", "")  # Remove spaces for folder name
    sky_folder = os.path.join(cdbl_skybox_skys_path, sky_name_clean)
    
    # Check if folder exists and contains any files
    if os.path.isdir(sky_folder) and os.listdir(sky_folder):
        print(f"🔍 Sky '{sky_name}' already exists, skipping download.")
        return True
    
    print(f"📥 Downloading skybox: {sky_name}")
    sky_url = f"https://github.com/eman225511/CDBL-CLI/raw/refs/heads/main/data/SkyboxData/SkyZIPs/{sky_name_clean}.zip"
    
    # Ensure the destination folder exists
    os.makedirs(sky_folder, exist_ok=True)
    
    # Use the progress-enabled download function
    success = download_and_extract_with_progress(sky_url, sky_folder)
    
    if success:
        print(f"✅ Successfully downloaded skybox: {sky_name}")
    else:
        print(f"❌ Failed to download skybox: {sky_name}")
        # Clean up empty folder if download failed
        try:
            if os.path.exists(sky_folder) and not os.listdir(sky_folder):
                os.rmdir(sky_folder)
        except Exception:
            pass
    
    return success
    
def get_sky_preview(sky_name):
    """
    Get the preview image for a specific sky by name.
    
    Args:
        sky_name: The name of the sky to get the preview for.
    
    Returns:
        str: Path to the preview image, or None if not found.
    """
    sky_name_clean = sky_name.replace(" ", "")  # Remove spaces for folder name
    preview_path = os.path.join(cdbl_skybox_pngs_path, f"{sky_name_clean}.png")
    if os.path.exists(preview_path):
        return preview_path
    else:
        print(f"Preview image for '{sky_name}' not found.")
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