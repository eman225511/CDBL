"""
CDBL Fast Flags Module
Contains all fast flag functionality for Roblox IxpSettings.json
"""

import os
import json
import stat
from datetime import datetime

def get_roblox_settings_path():
    """Get the path to Roblox ClientSettings directory"""
    appdata = os.getenv('LOCALAPPDATA')
    return os.path.join(appdata, 'Roblox', 'ClientSettings')

def get_ixp_settings_path():
    """Get the path to IxpSettings.json"""
    return os.path.join(get_roblox_settings_path(), 'IxpSettings.json')

def get_cdbl_tracking_path():
    """Get the path to CDBL tracking file"""
    appdata = os.getenv('LOCALAPPDATA')
    cdbl_dir = os.path.join(appdata, 'CDBL')
    os.makedirs(cdbl_dir, exist_ok=True)
    return os.path.join(cdbl_dir, 'fastflags_tracking.json')

def load_tracking_data():
    """Load CDBL fastflags tracking data"""
    tracking_path = get_cdbl_tracking_path()
    if os.path.exists(tracking_path):
        try:
            with open(tracking_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "applied_flags": {},
        "last_modified": None,
        "backup": {}
    }

def save_tracking_data(tracking_data):
    """Save CDBL fastflags tracking data"""
    tracking_path = get_cdbl_tracking_path()
    tracking_data["last_modified"] = datetime.now().isoformat()
    try:
        with open(tracking_path, 'w') as f:
            json.dump(tracking_data, f, indent=4)
        return True
    except Exception:
        return False

def load_ixp_settings():
    """Load current IxpSettings.json content"""
    ixp_path = get_ixp_settings_path()
    if os.path.exists(ixp_path):
        try:
            with open(ixp_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def set_file_readonly(file_path):
    """Set a file to readonly mode"""
    try:
        if os.path.exists(file_path):
            # Make file readonly
            os.chmod(file_path, stat.S_IREAD)
            return True
    except Exception:
        pass
    return False

def remove_file_readonly(file_path):
    """Remove readonly attribute from a file"""
    try:
        if os.path.exists(file_path):
            # Make file writable
            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
            return True
    except Exception:
        pass
    return False

def save_ixp_settings(data, set_readonly=True):
    """Save data to IxpSettings.json and optionally set readonly"""
    ixp_path = get_ixp_settings_path()
    settings_dir = get_roblox_settings_path()
    
    # Create directory if it doesn't exist
    os.makedirs(settings_dir, exist_ok=True)
    
    # Remove readonly if file exists (to allow writing)
    if os.path.exists(ixp_path):
        remove_file_readonly(ixp_path)
    
    try:
        with open(ixp_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        # Set readonly after successful write if requested
        if set_readonly:
            set_file_readonly(ixp_path)
        
        return True
    except Exception:
        return False

def apply_fastflags(fast_flags):
    """
    Apply fastflags to Roblox IxpSettings.json with tracking
    
    Args:
        fast_flags: Dictionary of fastflags to apply
    
    Returns:
        dict: Result data with success status and messages
    """
    result = {
        "success": False,
        "applied_flags": 0,
        "message": "",
        "errors": []
    }
    
    if not fast_flags:
        result["message"] = "No fastflags provided to apply"
        result["errors"].append(result["message"])
        return result
    
    try:
        # Load current IxpSettings
        current_settings = load_ixp_settings()
        
        # Load tracking data
        tracking_data = load_tracking_data()
        
        # Create backup of current state if we haven't already
        if not tracking_data.get("backup"):
            if current_settings:
                tracking_data["backup"] = current_settings.copy()
                tracking_data["backup_created"] = datetime.now().isoformat()
            else:
                # If no current settings, create empty backup
                tracking_data["backup"] = {}
                tracking_data["backup_created"] = datetime.now().isoformat()
        
        # Apply new fastflags
        for flag_name, flag_value in fast_flags.items():
            current_settings[flag_name] = flag_value
            tracking_data["applied_flags"][flag_name] = flag_value
        
        # Save updated settings
        if save_ixp_settings(current_settings):
            # Save tracking data
            if save_tracking_data(tracking_data):
                result["success"] = True
                result["applied_flags"] = len(fast_flags)
                result["message"] = f"Successfully applied {len(fast_flags)} fastflags to Roblox"
            else:
                result["errors"].append("Warning: Fastflags applied but tracking data could not be saved")
                result["success"] = True
                result["applied_flags"] = len(fast_flags)
                result["message"] = f"Applied {len(fast_flags)} fastflags (tracking failed)"
        else:
            result["message"] = "Failed to save fastflags to IxpSettings.json"
            result["errors"].append(result["message"])
            
    except Exception as e:
        result["message"] = f"Error applying fastflags: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def remove_fastflags(flag_names=None):
    """
    Remove specific fastflags or all CDBL fastflags from IxpSettings.json
    
    Args:
        flag_names: List of specific flag names to remove, or None to remove all CDBL flags
    
    Returns:
        dict: Result data with success status and messages
    """
    result = {
        "success": False,
        "removed_flags": 0,
        "message": "",
        "errors": []
    }
    
    try:
        # Load current settings and tracking data
        current_settings = load_ixp_settings()
        tracking_data = load_tracking_data()
        
        if not tracking_data["applied_flags"]:
            result["message"] = "No CDBL fastflags found to remove"
            return result
        
        # Determine which flags to remove
        if flag_names is None:
            # Remove all CDBL flags
            flags_to_remove = list(tracking_data["applied_flags"].keys())
        else:
            # Remove specific flags
            flags_to_remove = [name for name in flag_names if name in tracking_data["applied_flags"]]
        
        if not flags_to_remove:
            result["message"] = "No matching CDBL fastflags found to remove"
            return result
        
        # Remove flags from settings
        removed_count = 0
        for flag_name in flags_to_remove:
            if flag_name in current_settings:
                del current_settings[flag_name]
                removed_count += 1
            if flag_name in tracking_data["applied_flags"]:
                del tracking_data["applied_flags"][flag_name]
        
        # Save updated settings
        if save_ixp_settings(current_settings):
            # Save updated tracking data
            if save_tracking_data(tracking_data):
                result["success"] = True
                result["removed_flags"] = removed_count
                result["message"] = f"Successfully removed {removed_count} CDBL fastflags"
            else:
                result["errors"].append("Warning: Fastflags removed but tracking data could not be updated")
                result["success"] = True
                result["removed_flags"] = removed_count
                result["message"] = f"Removed {removed_count} fastflags (tracking update failed)"
        else:
            result["message"] = "Failed to save updated settings to IxpSettings.json"
            result["errors"].append(result["message"])
            
    except Exception as e:
        result["message"] = f"Error removing fastflags: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def restore_original_settings():
    """
    Restore original IxpSettings.json from backup (before CDBL changes)
    
    Returns:
        dict: Result data with success status and messages
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    try:
        tracking_data = load_tracking_data()
        
        if not tracking_data.get("backup"):
            result["message"] = "No backup found to restore from. Please run CDBL setup first to create an initial backup."
            result["errors"].append(result["message"])
            return result
        
        # Restore from backup
        if save_ixp_settings(tracking_data["backup"]):
            # Clear tracking data
            tracking_data["applied_flags"] = {}
            tracking_data["backup"] = {}
            
            if save_tracking_data(tracking_data):
                result["success"] = True
                result["message"] = "Successfully restored original Roblox settings"
            else:
                result["errors"].append("Warning: Settings restored but tracking data could not be cleared")
                result["success"] = True
                result["message"] = "Settings restored (tracking clear failed)"
        else:
            result["message"] = "Failed to restore original settings"
            result["errors"].append(result["message"])
            
    except Exception as e:
        result["message"] = f"Error restoring settings: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def restore_ixp_settings_permissions():
    """
    Restore normal write permissions to IxpSettings.json (remove readonly)
    
    Returns:
        dict: Result with success status and message
    """
    result = {
        "success": False,
        "message": ""
    }
    
    ixp_path = get_ixp_settings_path()
    
    if not os.path.exists(ixp_path):
        result["message"] = "IxpSettings.json does not exist"
        return result
    
    try:
        if remove_file_readonly(ixp_path):
            result["success"] = True
            result["message"] = "IxpSettings.json permissions restored (readonly removed)"
        else:
            result["message"] = "Failed to remove readonly attribute from IxpSettings.json"
    except Exception as e:
        result["message"] = f"Error restoring permissions: {str(e)}"
    
    return result

def get_applied_fastflags():
    """
    Get list of currently applied CDBL fastflags
    
    Returns:
        dict: Result data with applied flags information
    """
    result = {
        "success": False,
        "applied_flags": {},
        "count": 0,
        "message": "",
        "last_modified": None
    }
    
    try:
        tracking_data = load_tracking_data()
        result["applied_flags"] = tracking_data["applied_flags"]
        result["count"] = len(tracking_data["applied_flags"])
        result["last_modified"] = tracking_data["last_modified"]
        result["success"] = True
        
        if result["count"] > 0:
            result["message"] = f"Found {result['count']} applied CDBL fastflags"
        else:
            result["message"] = "No CDBL fastflags currently applied"
            
    except Exception as e:
        result["message"] = f"Error reading applied fastflags: {str(e)}"
    
    return result

def get_current_ixp_settings():
    """
    Get current IxpSettings.json content
    
    Returns:
        dict: Result data with current settings
    """
    result = {
        "success": False,
        "settings": {},
        "message": ""
    }
    
    try:
        settings = load_ixp_settings()
        result["settings"] = settings
        result["success"] = True
        result["message"] = f"Loaded IxpSettings.json with {len(settings)} entries"
        
    except Exception as e:
        result["message"] = f"Error reading IxpSettings.json: {str(e)}"
    
    return result

# FastFlag for skybox fix
FLEASION_FLAG = {
    "FFlagHttpUseRbxStorage10": "false"
}

def apply_skybox_fastflag():
    """
    Apply the skybox fix FastFlag with separate tracking
    
    Returns:
        dict: Result data with success status and messages
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    try:
        # Load current settings and tracking data
        current_settings = load_ixp_settings()
        tracking_data = load_tracking_data()
        
        # Create backup of current state if we haven't already
        if not tracking_data["backup"]:
            tracking_data["backup"] = current_settings.copy()
        
        # Apply skybox fastflag
        flag_name = "FFlagHttpUseRbxStorage10"
        flag_value = "false"
        
        current_settings[flag_name] = flag_value
        tracking_data["applied_flags"][flag_name] = flag_value
        
        # Mark that skybox fix is active
        if "skybox_fix" not in tracking_data:
            tracking_data["skybox_fix"] = {}
        tracking_data["skybox_fix"]["active"] = True
        tracking_data["skybox_fix"]["flag_applied"] = flag_name
        
        # Save updated settings
        if save_ixp_settings(current_settings):
            if save_tracking_data(tracking_data):
                result["success"] = True
                result["message"] = "Skybox fix FastFlag applied successfully"
            else:
                result["errors"].append("Warning: FastFlag applied but tracking failed")
                result["success"] = True
                result["message"] = "Skybox FastFlag applied (tracking failed)"
        else:
            result["message"] = "Failed to save skybox FastFlag to IxpSettings.json"
            result["errors"].append(result["message"])
            
    except Exception as e:
        result["message"] = f"Error applying skybox FastFlag: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def remove_skybox_fastflag():
    """
    Remove the skybox fix FastFlag
    
    Returns:
        dict: Result data with success status and messages
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    try:
        # Load current settings and tracking data
        current_settings = load_ixp_settings()
        tracking_data = load_tracking_data()
        
        # Check if skybox fix is active
        if "skybox_fix" not in tracking_data or not tracking_data["skybox_fix"].get("active", False):
            result["message"] = "Skybox fix FastFlag is not currently active"
            return result
        
        flag_name = tracking_data["skybox_fix"].get("flag_applied", "FFlagHttpUseRbxStorage10")
        
        # Remove flag from settings
        removed = False
        if flag_name in current_settings:
            del current_settings[flag_name]
            removed = True
        
        # Remove from tracking
        if flag_name in tracking_data["applied_flags"]:
            del tracking_data["applied_flags"][flag_name]
        
        # Mark skybox fix as inactive
        tracking_data["skybox_fix"]["active"] = False
        
        # Save updated settings
        if save_ixp_settings(current_settings):
            if save_tracking_data(tracking_data):
                result["success"] = True
                result["message"] = f"Skybox fix FastFlag removed successfully"
            else:
                result["errors"].append("Warning: FastFlag removed but tracking update failed")
                result["success"] = True
                result["message"] = "Skybox FastFlag removed (tracking failed)"
        else:
            result["message"] = "Failed to save updated settings"
            result["errors"].append(result["message"])
            
    except Exception as e:
        result["message"] = f"Error removing skybox FastFlag: {str(e)}"
        result["errors"].append(result["message"])
    
    return result

def is_skybox_fix_active():
    """
    Check if skybox fix FastFlag is currently active
    
    Returns:
        dict: Result data with skybox fix status
    """
    result = {
        "success": False,
        "active": False,
        "flag_name": None,
        "message": ""
    }
    
    try:
        tracking_data = load_tracking_data()
        
        if "skybox_fix" in tracking_data:
            result["active"] = tracking_data["skybox_fix"].get("active", False)
            result["flag_name"] = tracking_data["skybox_fix"].get("flag_applied", "FFlagHttpUseRbxStorage10")
        
        result["success"] = True
        if result["active"]:
            result["message"] = f"Skybox fix is active (flag: {result['flag_name']})"
        else:
            result["message"] = "Skybox fix is not active"
            
    except Exception as e:
        result["message"] = f"Error checking skybox fix status: {str(e)}"
    
    return result


def apply_no_arms_fastflag():
    """
    Apply no arms FastFlag with tracking
    
    Returns:
        dict: Result data with success status and message
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    try:
        flag_name = "FFlagHttpUseRbxStorage10"
        flag_value = "false"
        
        # Apply the FastFlag
        fastflag_result = apply_fastflags({flag_name: flag_value})
        if not fastflag_result["success"]:
            result["message"] = "Failed to apply no arms FastFlag"
            result["errors"].extend(fastflag_result["errors"])
            return result
        
        # Update tracking data to mark no arms fix as active
        tracking_data = load_tracking_data()
        if "no_arms_fix" not in tracking_data:
            tracking_data["no_arms_fix"] = {}
        tracking_data["no_arms_fix"]["active"] = True
        tracking_data["no_arms_fix"]["flag_applied"] = flag_name
        
        if save_tracking_data(tracking_data):
            result["success"] = True
            result["message"] = f"No arms FastFlag applied successfully ({flag_name}: {flag_value})"
        else:
            result["message"] = "FastFlag applied but failed to update tracking data"
            result["errors"].append(result["message"])
            
    except Exception as e:
        result["message"] = f"Error applying no arms FastFlag: {str(e)}"
        result["errors"].append(result["message"])
    
    return result


def remove_no_arms_fastflag():
    """
    Remove no arms FastFlag and restore original settings
    
    Returns:
        dict: Result data with success status and message
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    try:
        tracking_data = load_tracking_data()
        
        # Check if no arms fix is active
        if "no_arms_fix" not in tracking_data or not tracking_data["no_arms_fix"].get("active", False):
            result["message"] = "No arms fix is not currently active"
            result["errors"].append(result["message"])
            return result
        
        # Get the flag name that was applied
        flag_name = tracking_data["no_arms_fix"].get("flag_applied", "FFlagHttpUseRbxStorage10")
        
        # Remove the FastFlag
        remove_result = remove_fastflags([flag_name])
        if not remove_result["success"]:
            result["message"] = "Failed to remove no arms FastFlag"
            result["errors"].extend(remove_result["errors"])
            return result
        
        # Update tracking data to mark no arms fix as inactive
        tracking_data["no_arms_fix"]["active"] = False
        
        if save_tracking_data(tracking_data):
            result["success"] = True
            result["message"] = f"No arms FastFlag removed successfully ({flag_name})"
        else:
            result["message"] = "FastFlag removed but failed to update tracking data"
            result["errors"].append(result["message"])
            
    except Exception as e:
        result["message"] = f"Error removing no arms FastFlag: {str(e)}"
        result["errors"].append(result["message"])
    
    return result


def is_no_arms_fix_active():
    """
    Check if no arms fix FastFlag is currently active
    
    Returns:
        dict: Result data with no arms fix status
    """
    result = {
        "success": False,
        "active": False,
        "flag_name": None,
        "message": ""
    }
    
    try:
        tracking_data = load_tracking_data()
        
        if "no_arms_fix" in tracking_data:
            result["active"] = tracking_data["no_arms_fix"].get("active", False)
            result["flag_name"] = tracking_data["no_arms_fix"].get("flag_applied", "FFlagHttpUseRbxStorage10")
        
        result["success"] = True
        if result["active"]:
            result["message"] = f"No arms fix is active (flag: {result['flag_name']})"
        else:
            result["message"] = "No arms fix is not active"
            
    except Exception as e:
        result["message"] = f"Error checking no arms fix status: {str(e)}"
    
    return result


def create_initial_backup():
    """
    Create initial backup of IxpSettings.json for first-run setup
    This ensures FastFlags can be properly restored later
    
    Returns:
        dict: Result data with success status and messages
    """
    result = {
        "success": False,
        "message": "",
        "errors": []
    }
    
    try:
        # Check if IxpSettings.json exists
        ixp_path = get_ixp_settings_path()
        
        # Load tracking data
        tracking_data = load_tracking_data()
        
        # If backup already exists, don't overwrite it
        if tracking_data.get("backup"):
            result["success"] = True
            result["message"] = "Backup already exists, skipping creation"
            return result
        
        # Load current settings (or create empty if file doesn't exist)
        if os.path.exists(ixp_path):
            current_settings = load_ixp_settings()
            if current_settings is None:
                current_settings = {}
        else:
            # Create empty IxpSettings.json if it doesn't exist
            current_settings = {}
            settings_dir = get_roblox_settings_path()
            os.makedirs(settings_dir, exist_ok=True)
            
            # Save empty settings file
            if not save_ixp_settings(current_settings, set_readonly=False):
                result["message"] = "Failed to create initial IxpSettings.json"
                result["errors"].append(result["message"])
                return result
        
        # Create backup
        tracking_data["backup"] = current_settings.copy()
        tracking_data["backup_created"] = datetime.now().isoformat()
        
        # Save tracking data
        if save_tracking_data(tracking_data):
            result["success"] = True
            result["message"] = f"Initial backup created successfully ({len(current_settings)} settings)"
        else:
            result["message"] = "Failed to save backup tracking data"
            result["errors"].append(result["message"])
            
    except Exception as e:
        result["message"] = f"Error creating initial backup: {str(e)}"
        result["errors"].append(result["message"])
    
    return result


def ensure_backup_exists():
    """
    Ensure a backup exists, create one if it doesn't
    This is a convenience function for other modules
    
    Returns:
        bool: True if backup exists or was created successfully
    """
    tracking_data = load_tracking_data()
    if tracking_data.get("backup"):
        return True
    
    result = create_initial_backup()
    return result["success"]