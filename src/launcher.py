"""
CDBL Launcher Module
Contains functions to detect, launch, kill, and install Roblox clients
"""

import os
import subprocess
import webbrowser
import requests
import platform

def detect_roblox_clients():
    """
    Detect which Roblox clients are installed.
    
    Returns:
        dict: {
            "Roblox": bool,
            "Bloxstrap": bool,
            "Fishstrap": bool
        }
    """
    clients = {
        "Roblox": False,
        "Bloxstrap": False,
        "Fishstrap": False
    }
    
    # Check for standard Roblox installation
    roblox_path = os.path.join(os.environ['LOCALAPPDATA'], 'Roblox')
    if os.path.exists(roblox_path):
        # Look for RobloxPlayerBeta.exe in any version folder
        versions_path = os.path.join(roblox_path, 'Versions')
        if os.path.exists(versions_path):
            for version_dir in os.listdir(versions_path):
                version_path = os.path.join(versions_path, version_dir)
                if os.path.isdir(version_path):
                    exe_path = os.path.join(version_path, 'RobloxPlayerBeta.exe')
                    if os.path.exists(exe_path):
                        clients["Roblox"] = True
                        break
    
    # Check for Bloxstrap
    bloxstrap_path = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap')
    bloxstrap_exe = os.path.join(bloxstrap_path, 'Bloxstrap.exe')
    if os.path.exists(bloxstrap_exe):
        clients["Bloxstrap"] = True
    
    # Check for Fishstrap
    fishstrap_path = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap')
    fishstrap_exe = os.path.join(fishstrap_path, 'Fishstrap.exe')
    if os.path.exists(fishstrap_exe):
        clients["Fishstrap"] = True
    
    return clients

def get_default_client():
    """
    Get the default/recommended client to use.
    Priority: Roblox > Fishstrap > Bloxstrap
    
    Returns:
        str: Name of the default client or None if none found
    """
    clients = detect_roblox_clients()
    
    if clients["Roblox"]:
        return "Roblox"
    elif clients["Fishstrap"]:
        return "Fishstrap"
    elif clients["Bloxstrap"]:
        return "Bloxstrap"
    else:
        return None

def launch_roblox(client_name="auto"):
    """
    Launch Roblox using the specified client.
    
    Args:
        client_name (str): "Roblox", "Bloxstrap", "Fishstrap", or "auto"
    
    Returns:
        dict: {
            "success": bool,
            "message": str,
            "client_used": str
        }
    """
    result = {
        "success": False,
        "message": "",
        "client_used": ""
    }
    
    if client_name == "auto":
        client_name = get_default_client()
        if not client_name:
            result["message"] = "No Roblox clients found installed"
            return result
    
    try:
        if client_name == "Roblox":
            # Use the default Roblox Player shortcut
            roblox_shortcut = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Roblox', 'Roblox Player.lnk')
            
            if os.path.exists(roblox_shortcut):
                # Launch using the shortcut
                subprocess.Popen(['cmd', '/c', 'start', '', roblox_shortcut], shell=True)
                result["success"] = True
                result["message"] = "Launched Roblox (shortcut)"
                result["client_used"] = "Roblox"
            else:
                # Try alternative shortcut location
                desktop_shortcut = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Roblox Player.lnk')
                if os.path.exists(desktop_shortcut):
                    subprocess.Popen(['cmd', '/c', 'start', '', desktop_shortcut], shell=True)
                    result["success"] = True
                    result["message"] = "Launched Roblox (desktop shortcut)"
                    result["client_used"] = "Roblox"
                else:
                    # Fallback to protocol handler
                    webbrowser.open("roblox://")
                    result["success"] = True
                    result["message"] = "Launched Roblox (protocol)"
                    result["client_used"] = "Roblox"
            
        elif client_name == "Bloxstrap":
            bloxstrap_exe = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap', 'Bloxstrap.exe')
            if os.path.exists(bloxstrap_exe):
                subprocess.Popen([bloxstrap_exe])
                result["success"] = True
                result["message"] = "Launched Bloxstrap"
                result["client_used"] = "Bloxstrap"
            else:
                result["message"] = "Bloxstrap not found"
                
        elif client_name == "Fishstrap":
            fishstrap_exe = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap', 'Fishstrap.exe')
            if os.path.exists(fishstrap_exe):
                subprocess.Popen([fishstrap_exe])
                result["success"] = True
                result["message"] = "Launched Fishstrap"
                result["client_used"] = "Fishstrap"
            else:
                result["message"] = "Fishstrap not found"
        else:
            result["message"] = f"Unknown client: {client_name}"
            
    except Exception as e:
        result["message"] = f"Failed to launch {client_name}: {str(e)}"
    
    return result

def kill_roblox():
    """
    Kill all Roblox-related processes.
    
    Returns:
        dict: {
            "success": bool,
            "message": str,
            "killed_processes": list
        }
    """
    result = {
        "success": False,
        "message": "",
        "killed_processes": []
    }
    
    # List of process names to kill
    roblox_processes = [
        "RobloxPlayerBeta.exe",
        "RobloxPlayer.exe", 
        "Roblox.exe",
        "Bloxstrap.exe",
        "Fishstrap.exe"
    ]
    
    try:
        if platform.system() == "Windows":
            for process_name in roblox_processes:
                try:
                    # Use taskkill to terminate the process (without showing console window)
                    subprocess.run(
                        ["taskkill", "/f", "/im", process_name],
                        capture_output=True,
                        check=False,  # Don't raise exception if process not found
                        creationflags=subprocess.CREATE_NO_WINDOW  # Prevent terminal window from opening
                    )
                    result["killed_processes"].append(process_name)
                except:
                    pass  # Process might not be running
            
            if result["killed_processes"]:
                result["success"] = True
                result["message"] = f"Killed {len(result['killed_processes'])} Roblox processes"
            else:
                result["success"] = True
                result["message"] = "No Roblox processes were running"
        else:
            result["message"] = "Kill function only supported on Windows"
            
    except Exception as e:
        result["message"] = f"Failed to kill Roblox processes: {str(e)}"
    
    return result

def install_roblox():
    """
    Open the Roblox installation page.
    
    Returns:
        dict: {
            "success": bool,
            "message": str
        }
    """
    result = {
        "success": False,
        "message": ""
    }
    
    try:
        webbrowser.open("https://www.roblox.com/download")
        result["success"] = True
        result["message"] = "Opened Roblox download page"
    except Exception as e:
        result["message"] = f"Failed to open download page: {str(e)}"
    
    return result

def install_bloxstrap():
    """
    Open the Bloxstrap installation page.
    
    Returns:
        dict: {
            "success": bool,
            "message": str
        }
    """
    result = {
        "success": False,
        "message": ""
    }
    
    try:
        webbrowser.open("https://github.com/bloxstraplabs/bloxstrap")
        result["success"] = True
        result["message"] = "Opened Bloxstrap download page"
    except Exception as e:
        result["message"] = f"Failed to open Bloxstrap download page: {str(e)}"
    
    return result

def install_fishstrap():
    """
    Open the Fishstrap installation page.
    
    Returns:
        dict: {
            "success": bool,
            "message": str
        }
    """
    result = {
        "success": False,
        "message": ""
    }
    
    try:
        webbrowser.open("https://github.com/fishstrap/fishstrap")
        result["success"] = True
        result["message"] = "Opened Fishstrap download page"
    except Exception as e:
        result["message"] = f"Failed to open Fishstrap download page: {str(e)}"
    
    return result

def get_client_status():
    """
    Get comprehensive status of all Roblox clients.
    
    Returns:
        dict: {
            "installed": dict,
            "default": str,
            "running": list
        }
    """
    status = {
        "installed": detect_roblox_clients(),
        "default": get_default_client(),
        "running": []
    }
    
    # Check for running processes
    roblox_processes = [
        "RobloxPlayerBeta.exe",
        "RobloxPlayer.exe", 
        "Roblox.exe",
        "Bloxstrap.exe",
        "Fishstrap.exe"
    ]
    
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["tasklist", "/fo", "csv"],
                capture_output=True,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW  # Prevent terminal window
            )
            
            if result.returncode == 0:
                running_processes = result.stdout.lower()
                for process in roblox_processes:
                    if process.lower() in running_processes:
                        status["running"].append(process)
                        
    except Exception:
        pass  # If we can't check running processes, just continue
    
    return status

def debug_client_detection():
    """
    Debug function to show what clients are detected and why.
    """
    print("=== CDBL Client Detection Debug ===")
    
    clients = detect_roblox_clients()
    print(f"Detected clients: {clients}")
    
    default = get_default_client()
    print(f"Default client selected: {default}")
    
    # Check paths
    roblox_path = os.path.join(os.environ['LOCALAPPDATA'], 'Roblox')
    bloxstrap_path = os.path.join(os.environ['LOCALAPPDATA'], 'Bloxstrap')
    fishstrap_path = os.path.join(os.environ['LOCALAPPDATA'], 'Fishstrap')
    
    print(f"Roblox path exists: {os.path.exists(roblox_path)}")
    print(f"Bloxstrap path exists: {os.path.exists(bloxstrap_path)}")
    print(f"Fishstrap path exists: {os.path.exists(fishstrap_path)}")
    
    if os.path.exists(roblox_path):
        versions_path = os.path.join(roblox_path, 'Versions')
        print(f"Roblox versions path exists: {os.path.exists(versions_path)}")
        if os.path.exists(versions_path):
            versions = [d for d in os.listdir(versions_path) if os.path.isdir(os.path.join(versions_path, d))]
            print(f"Roblox versions found: {versions}")
    
    print("=== End Debug ===")
    return clients, default

# Uncomment the line below to run debug when module is imported
# debug_client_detection()