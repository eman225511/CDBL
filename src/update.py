"""
CDBL Update Checker Module
Checks for updates using GitHub Releases API
"""

import requests
import webbrowser
from packaging import version
import json

# ========== Version Data ==========
APP_VERSION = "1.3-Beta"  # your current version
GITHUB_USERNAME = "eman225511"  # your GitHub username
GITHUB_REPO = "CDBL"  # your repo name
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/releases/latest"


def check_for_updates(timeout=5):
    """
    Check for updates using GitHub Releases API
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        dict: Update information with keys:
            - update_available (bool): Whether an update is available
            - latest_version (str): Latest version tag
            - current_version (str): Current app version
            - release_url (str): URL to the release page
            - download_url (str): Direct download URL for the asset
            - release_notes (str): Release notes/changelog
            - error (str): Error message if check failed
    """
    result = {
        "update_available": False,
        "latest_version": None,
        "current_version": APP_VERSION,
        "release_url": None,
        "download_url": None,
        "release_notes": None,
        "error": None
    }
    
    try:
        # Make request to GitHub API
        response = requests.get(GITHUB_RELEASES_API, timeout=timeout)
        response.raise_for_status()
        
        release_data = response.json()
        
        # Extract version information
        latest_tag = release_data.get("tag_name", "")
        result["latest_version"] = latest_tag
        result["release_url"] = release_data.get("html_url", "")
        result["release_notes"] = release_data.get("body", "No release notes available")
        
        # Find the main executable download
        assets = release_data.get("assets", [])
        for asset in assets:
            asset_name = asset.get("name", "").lower()
            # Look for main exe (not portable or installer)
            if asset_name.endswith(".exe") and "full" not in asset_name and "portable" not in asset_name:
                result["download_url"] = asset.get("browser_download_url")
                break
        
        # If no direct exe found, look for full package zip
        if not result["download_url"]:
            for asset in assets:
                asset_name = asset.get("name", "").lower()
                if "full" in asset_name and asset_name.endswith(".zip"):
                    result["download_url"] = asset.get("browser_download_url")
                    break
        
        # Compare versions
        # Handle "Beta" or other non-standard version strings
        if APP_VERSION.lower() == "beta" or APP_VERSION.lower() == "dev":
            # Always show update available for beta/dev versions
            result["update_available"] = True
        else:
            try:
                # Try to parse as semantic version (remove 'v' prefix if present)
                current_ver = APP_VERSION.lstrip('vV')
                latest_ver = latest_tag.lstrip('vV')
                
                if version.parse(latest_ver) > version.parse(current_ver):
                    result["update_available"] = True
            except Exception:
                # If version parsing fails, compare as strings
                if latest_tag != APP_VERSION:
                    result["update_available"] = True
        
    except requests.exceptions.Timeout:
        result["error"] = "Update check timed out"
    except requests.exceptions.RequestException as e:
        result["error"] = f"Network error: {str(e)}"
    except json.JSONDecodeError:
        result["error"] = "Failed to parse GitHub API response"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
    
    return result


def open_release_page():
    """Open the latest release page in the default browser"""
    release_url = f"https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO}/releases/latest"
    webbrowser.open(release_url)


def open_download_url(url):
    """
    Open a specific download URL in the default browser
    
    Args:
        url: The download URL to open
    """
    if url:
        webbrowser.open(url)


def get_version():
    """Get the current app version"""
    return APP_VERSION


def get_all_releases(timeout=5):
    """
    Get all releases from GitHub
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        list: List of release objects, or None if failed
    """
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/releases"
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch releases: {e}")
        return None


if __name__ == "__main__":
    # Test the update checker
    print(f"Current Version: {APP_VERSION}")
    print(f"Checking for updates from: {GITHUB_RELEASES_API}")
    print("-" * 60)
    
    result = check_for_updates()
    
    if result["error"]:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✓ Latest Version: {result['latest_version']}")
        print(f"✓ Update Available: {result['update_available']}")
        if result["update_available"]:
            print(f"✓ Release URL: {result['release_url']}")
            print(f"✓ Download URL: {result['download_url']}")
            print(f"\n📝 Release Notes:\n{result['release_notes'][:200]}...")
