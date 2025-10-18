"""
CDBL Textures Module
Contains all texture-related functionality
"""

import os
import shutil
from .core import cdbl_texture_data_path, get_versions_path

def apply_dark_textures(target_client_name):
    """
    Applies dark textures to client texture directories, excluding the sky folder.
    Args:
        target_client_name: The client type (Roblox, Bloxstrap, Fishstrap)
    """
    # Try different possible paths for dark textures
    possible_paths = [
        os.path.join(cdbl_texture_data_path, 'DarkTextures'),  # Direct folder
        os.path.join(cdbl_texture_data_path, 'DarkTextures', 'DarkTextures'),
        os.path.join(cdbl_texture_data_path, 'DarkTextures.zip', 'DarkTextures'),
    ]
    
    dark_textures_path = None
    for path in possible_paths:
        if os.path.exists(path):
            dark_textures_path = path
            break
    
    if not dark_textures_path:
        print("Dark textures not found in storage.")
        print(f"Searched in: {possible_paths}")
        return False
    
    print(f"Using dark textures from: {dark_textures_path}")
    
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
                texture_destination = os.path.join(version_path, 'PlatformContent', 'pc', 'textures')
                
                if os.path.exists(texture_destination):
                    print(f"Applying dark textures to {version_dir} (excluding sky)...")
                    
                    # Copy all files except sky folder
                    for root, dirs, files in os.walk(dark_textures_path):
                        # Skip sky directories
                        if 'sky' in dirs:
                            dirs.remove('sky')
                        
                        rel_path = os.path.relpath(root, dark_textures_path)
                        dest_dir = texture_destination if rel_path == '.' else os.path.join(texture_destination, rel_path)
                        
                        os.makedirs(dest_dir, exist_ok=True)
                        
                        for file in files:
                            src_file = os.path.join(root, file)
                            dest_file = os.path.join(dest_dir, file)
                            try:
                                shutil.copy2(src_file, dest_file)
                            except Exception as e:
                                print(f"Failed to copy {file} to {version_dir}: {e}")
                                return False
                    
                    print(f"Successfully applied to {version_dir}")
    
    elif client_name in ["bloxstrap", "fishstrap"]:
        # Bloxstrap and Fishstrap use Modifications folder
        if client_name == "bloxstrap":
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap')
        else:  # fishstrap
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap')
        
        texture_destination = os.path.join(base_path, 'Modifications', 'PlatformContent', 'pc', 'textures')
        
        # Create the directory structure if it doesn't exist
        os.makedirs(texture_destination, exist_ok=True)
        
        print(f"Applying dark textures to {target_client_name} (excluding sky)...")
        
        # Copy all files except sky folder
        for root, dirs, files in os.walk(dark_textures_path):
            # Skip sky directories
            if 'sky' in dirs:
                dirs.remove('sky')
            
            rel_path = os.path.relpath(root, dark_textures_path)
            dest_dir = texture_destination if rel_path == '.' else os.path.join(texture_destination, rel_path)
            
            os.makedirs(dest_dir, exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                try:
                    shutil.copy2(src_file, dest_file)
                except Exception as e:
                    print(f"Failed to copy {file} to {target_client_name}: {e}")
                    return False
        
        print(f"Successfully applied to {target_client_name}")
    
    else:
        print(f"Unknown client type: {target_client_name}")
        return False
    
    print(f"Successfully applied dark textures to '{target_client_name}'.")
    return True

def apply_light_textures(target_client_name):
    """
    Applies light textures to client texture directories, excluding the sky folder.
    Args:
        target_client_name: The client type (Roblox, Bloxstrap, Fishstrap)
    """
    # Try different possible paths for light textures
    possible_paths = [
        os.path.join(cdbl_texture_data_path, 'LightTextures'),  # Direct folder
        os.path.join(cdbl_texture_data_path, 'LightTextures', 'LightTextures'),
        os.path.join(cdbl_texture_data_path, 'LightTextures.zip', 'LightTextures'),
    ]
    
    light_textures_path = None
    for path in possible_paths:
        if os.path.exists(path):
            light_textures_path = path
            break
    
    if not light_textures_path:
        print("Light textures not found in storage.")
        print(f"Searched in: {possible_paths}")
        return False
    
    print(f"Using light textures from: {light_textures_path}")
    
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
                texture_destination = os.path.join(version_path, 'PlatformContent', 'pc', 'textures')
                
                if os.path.exists(texture_destination):
                    print(f"Applying light textures to {version_dir} (excluding sky)...")
                    
                    # Copy all files except sky folder
                    for root, dirs, files in os.walk(light_textures_path):
                        # Skip sky directories
                        if 'sky' in dirs:
                            dirs.remove('sky')
                        
                        rel_path = os.path.relpath(root, light_textures_path)
                        dest_dir = texture_destination if rel_path == '.' else os.path.join(texture_destination, rel_path)
                        
                        os.makedirs(dest_dir, exist_ok=True)
                        
                        for file in files:
                            src_file = os.path.join(root, file)
                            dest_file = os.path.join(dest_dir, file)
                            try:
                                shutil.copy2(src_file, dest_file)
                            except Exception as e:
                                print(f"Failed to copy {file} to {version_dir}: {e}")
                                return False
                    
                    print(f"Successfully applied to {version_dir}")
    
    elif client_name in ["bloxstrap", "fishstrap"]:
        # Bloxstrap and Fishstrap use Modifications folder
        if client_name == "bloxstrap":
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap')
        else:  # fishstrap
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap')
        
        texture_destination = os.path.join(base_path, 'Modifications', 'PlatformContent', 'pc', 'textures')
        
        # Create the directory structure if it doesn't exist
        os.makedirs(texture_destination, exist_ok=True)
        
        print(f"Applying light textures to {target_client_name} (excluding sky)...")
        
        # Copy all files except sky folder
        for root, dirs, files in os.walk(light_textures_path):
            # Skip sky directories
            if 'sky' in dirs:
                dirs.remove('sky')
            
            rel_path = os.path.relpath(root, light_textures_path)
            dest_dir = texture_destination if rel_path == '.' else os.path.join(texture_destination, rel_path)
            
            os.makedirs(dest_dir, exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                try:
                    shutil.copy2(src_file, dest_file)
                except Exception as e:
                    print(f"Failed to copy {file} to {target_client_name}: {e}")
                    return False
        
        print(f"Successfully applied to {target_client_name}")
    
    else:
        print(f"Unknown client type: {target_client_name}")
        return False
    
    print(f"Successfully applied light textures to '{target_client_name}'.")
    return True

def apply_default_textures(target_client_name):
    """
    Applies default textures with skybox to client texture directories.
    Args:
        target_client_name: The client type (Roblox, Bloxstrap, Fishstrap)
    """
    # Try different possible paths for default textures
    possible_paths = [
        os.path.join(cdbl_texture_data_path, 'DefaultTexturesWSky'),  # Direct folder
        os.path.join(cdbl_texture_data_path, 'DefaultTexturesWSky', 'DefaultTexturesWSky'),
        os.path.join(cdbl_texture_data_path, 'DefaultTexturesWSky.zip', 'DefaultTexturesWSky'),
    ]
    
    default_textures_path = None
    for path in possible_paths:
        if os.path.exists(path):
            default_textures_path = path
            break
    
    if not default_textures_path:
        print("Default textures with sky not found in storage.")
        print(f"Searched in: {possible_paths}")
        return False
    
    print(f"Using default textures from: {default_textures_path}")
    
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
                texture_destination = os.path.join(version_path, 'PlatformContent', 'pc', 'textures')
                
                if os.path.exists(texture_destination):
                    print(f"Applying default textures with sky to {version_dir}...")
                    
                    try:
                        # Copy entire directory tree
                        for root, dirs, files in os.walk(default_textures_path):
                            rel_path = os.path.relpath(root, default_textures_path)
                            dest_dir = texture_destination if rel_path == '.' else os.path.join(texture_destination, rel_path)
                            
                            os.makedirs(dest_dir, exist_ok=True)
                            
                            for file in files:
                                src_file = os.path.join(root, file)
                                dest_file = os.path.join(dest_dir, file)
                                shutil.copy2(src_file, dest_file)
                        
                        print(f"Successfully applied to {version_dir}")
                    except Exception as e:
                        print(f"Failed to apply default textures with sky to {version_dir}: {e}")
                        return False
    
    elif client_name in ["bloxstrap", "fishstrap"]:
        # Bloxstrap and Fishstrap use Modifications folder
        if client_name == "bloxstrap":
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap')
        else:  # fishstrap
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap')
        
        texture_destination = os.path.join(base_path, 'Modifications', 'PlatformContent', 'pc', 'textures')
        
        # Create the directory structure if it doesn't exist
        os.makedirs(texture_destination, exist_ok=True)
        
        print(f"Applying default textures with sky to {target_client_name}...")
        
        try:
            # Copy entire directory tree
            for root, dirs, files in os.walk(default_textures_path):
                rel_path = os.path.relpath(root, default_textures_path)
                dest_dir = texture_destination if rel_path == '.' else os.path.join(texture_destination, rel_path)
                
                os.makedirs(dest_dir, exist_ok=True)
                
                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dest_file)
            
            print(f"Successfully applied to {target_client_name}")
        except Exception as e:
            print(f"Failed to apply default textures with sky to {target_client_name}: {e}")
            return False
    
    else:
        print(f"Unknown client type: {target_client_name}")
        return False
    
    print(f"Successfully applied default textures with sky to '{target_client_name}'.")
    return True