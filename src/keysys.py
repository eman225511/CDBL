"""
EGate Key System Integration for CDBL
Handles license key verification with HWID binding and email validation
"""

import hashlib
import platform
import uuid
import requests
import json
from pathlib import Path
from typing import Dict, Optional


class EGateKeySystem:
    """
    Integration with EGate license key system
    Provides HWID binding and email verification
    """
    
    def __init__(self, api_base_url: str):
        """
        Initialize EGate key system
        
        Args:
            api_base_url: Base URL of your EGate deployment
                         Should be in format: "https://your-app.vercel.app/api"
                         Note: Include the /api path
        """
        self.api_base = api_base_url.rstrip('/')
        self._hwid = None
        
    def get_hardware_id(self) -> str:
        """
        Generate a unique hardware ID based on system information
        
        Returns:
            str: Unique hardware identifier for this machine
        """
        if self._hwid:
            return self._hwid
            
        try:
            # Combine multiple system identifiers for a unique HWID
            machine_id = platform.machine()
            processor = platform.processor()
            system = platform.system()
            node = platform.node()
            
            # Create a consistent hardware fingerprint
            hwid_string = f"{machine_id}-{processor}-{system}-{node}"
            hwid_hash = hashlib.md5(hwid_string.encode()).hexdigest()
            self._hwid = f"HWID-{hwid_hash[:16].upper()}"
            return self._hwid
        except Exception as e:
            # Fallback to MAC address if available
            try:
                mac = hex(uuid.getnode())[2:].upper()
                self._hwid = f"MAC-{mac}"
                return self._hwid
            except:
                # Final fallback
                self._hwid = f"FALLBACK-{hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:16].upper()}"
                return self._hwid
    
    def verify_key(self, key: str) -> Dict[str, any]:
        """
        Verify a license key using the EGate /verify and /checkKey endpoints
        
        Validation logic:
        1. Check if key exists and has email bound (/checkKey)
        2. Verify key and bind/check HWID (/verify)
        3. Return True only if key is valid, has email, and HWID matches
        
        Args:
            key: License key to verify
            
        Returns:
            dict: Verification result with keys:
                - success (bool): True if key is valid with email and correct HWID
                - message (str): Status message
                - error (str, optional): Error type if failed
                - details (dict, optional): Additional key information
        """
        result = {
            "success": False,
            "message": "",
            "error": None,
            "details": {}
        }
        
        try:
            # Step 1: Check if key exists and has email using /checkKey
            # Full URL will be: {api_base}/checkKey?key=ABCD-1234-EFGH
            check_response = requests.get(
                f"{self.api_base}/checkKey",
                params={"key": key},
                timeout=10
            )
            
            # Parse checkKey response - it returns JSON
            # Expected format: {"exists": true/false, "hasEmail": true/false, "hasHwid": true/false, "email": "..."}
            try:
                key_info = check_response.json()
            except ValueError as e:
                # If JSON parsing fails, check the text response
                response_text = check_response.text.strip().lower()
                if "key not found" in response_text or "error" in response_text:
                    result["error"] = "KEY_NOT_FOUND"
                    result["message"] = "Invalid license key"
                    return result
                else:
                    result["error"] = "PARSE_ERROR"
                    result["message"] = f"Failed to parse key information (invalid JSON): {check_response.text[:100]}"
                    return result
            
            # Check if key has error in JSON response
            if "error" in key_info:
                result["error"] = "KEY_NOT_FOUND"
                result["message"] = f"Key error: {key_info.get('error', 'Unknown error')}"
                return result
            
            # Verify key exists
            if not key_info.get("exists", False):
                result["error"] = "KEY_NOT_FOUND"
                result["message"] = "License key does not exist"
                return result
            
            # Check if email is bound (REQUIRED)
            if not key_info.get("hasEmail", False):
                result["error"] = "NO_EMAIL"
                result["message"] = "License key does not have an email bound. Please contact support."
                result["details"] = key_info
                return result
            
            # Step 2: Verify HWID binding using /verify
            # Full URL will be: {api_base}/verify?key=ABCD-1234-EFGH&hwid=HWID-...
            hwid = self.get_hardware_id()
            verify_response = requests.get(
                f"{self.api_base}/verify",
                params={"key": key, "hwid": hwid},
                timeout=10
            )
            
            # Parse the /verify response - it returns TEXT, not JSON
            # Expected responses: "key bound to hwid", "key verified", "hwid mismatch", "key not found"
            verify_message = verify_response.text.strip().lower()
            
            # Check verification results based on RESPONSE TEXT, not just status codes
            # The API returns text responses, so we check the actual message content
            if "key bound to hwid" in verify_message:
                # First time binding - success
                result["success"] = True
                result["message"] = "License activated successfully on this device"
                result["details"] = {
                    "email": key_info.get("email"),
                    "bound": True,
                    "first_use": True
                }
            elif "key verified" in verify_message:
                # HWID matches - success
                result["success"] = True
                result["message"] = "License verified successfully"
                result["details"] = {
                    "email": key_info.get("email"),
                    "bound": True,
                    "first_use": False
                }
            elif "hwid mismatch" in verify_message:
                # HWID doesn't match - key is bound to different device
                result["error"] = "HWID_MISMATCH"
                result["message"] = "This license is already activated on another device. Please reset your HWID or contact support."
                result["details"] = {"has_hwid": key_info.get("hasHwid", False)}
            elif "key not found" in verify_message:
                # Key doesn't exist
                result["error"] = "KEY_NOT_FOUND"
                result["message"] = "Invalid license key"
            else:
                # Unexpected response - log the actual response for debugging
                result["error"] = "UNKNOWN_RESPONSE"
                result["message"] = f"Unexpected response from server: {verify_response.text.strip()[:200]}"
            
            return result
            
        except requests.exceptions.Timeout:
            result["error"] = "TIMEOUT"
            result["message"] = "Connection timeout. Please check your internet connection."
            return result
        except requests.exceptions.ConnectionError:
            result["error"] = "CONNECTION_ERROR"
            result["message"] = "Unable to connect to license server. Please check your internet connection."
            return result
        except Exception as e:
            result["error"] = "EXCEPTION"
            result["message"] = f"Unexpected error: {str(e)}"
            return result
    
    def check_key_info(self, key: str) -> Dict[str, any]:
        """
        Get public information about a key without verifying HWID
        Uses the /checkKey endpoint to get key metadata
        
        Args:
            key: License key to check
            
        Returns:
            dict: Key information with structure:
                - success (bool): True if request succeeded
                - data (dict): Key info (exists, hasEmail, hasHwid, email, etc.)
                - error (str): Error message if failed
        """
        try:
            response = requests.get(
                f"{self.api_base}/checkKey",
                params={"key": key},
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    # Parse JSON response
                    data = response.json()
                    return {
                        "success": True,
                        "data": data
                    }
                except ValueError as e:
                    # Failed to parse JSON
                    return {
                        "success": False,
                        "error": f"Invalid JSON response: {response.text[:100]}"
                    }
            else:
                # Non-200 status code
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:100]}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Helper function for easy verification
def verify_license(api_url: str, license_key: str) -> Dict[str, any]:
    """
    Quick helper function to verify a license key
    
    Args:
        api_url: EGate API base URL
        license_key: License key to verify
        
    Returns:
        dict: Verification result
    """
    egate = EGateKeySystem(api_url)
    return egate.verify_key(license_key)


# ========== License Management Integration ==========

# Configuration
EGATE_API_URL = "https://key-sys-web.vercel.app/api"  # Replace with your actual EGate deployment URL

def get_stored_license_key() -> Optional[str]:
    """
    Get the stored license key from config (compatible with existing system)
    
    Returns:
        str or None: License key if exists, None otherwise
    """
    config_dir = Path.home() / "AppData" / "Local" / "CDBL"
    config_file = config_dir / "config.json"
    
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config.get("license_key", None)
    except Exception as e:
        print(f"Error reading license key: {e}")
        return None

def save_license_key(license_key: str) -> bool:
    """
    Save license key to config (compatible with existing system)
    
    Args:
        license_key: The license key to save
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    config_dir = Path.home() / "AppData" / "Local" / "CDBL"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    
    # Load existing config or create new one
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except:
            config = {
                "version": "1.0.0",
                "first_run_complete": False,
                "settings": {
                    "check_for_updates": True,
                    "auto_detect_client": True
                }
            }
    else:
        config = {
            "version": "1.0.0",
            "first_run_complete": False,
            "settings": {
                "check_for_updates": True,
                "auto_detect_client": True
            }
        }
    
    # Save the license key
    config["license_key"] = license_key
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving license key: {e}")
        return False

def validate_stored_license() -> Dict[str, any]:
    """
    Validate the stored license key on startup using the same validation as activation
    
    Returns:
        dict: Validation result with keys:
            - success (bool): True if license is valid and premium access granted
            - message (str): Status message
            - premium_enabled (bool): True if premium features should be enabled
            - error (str, optional): Error type if failed
            - details (dict, optional): Additional validation information
    """
    result = {
        "success": False,
        "message": "",
        "premium_enabled": False,
        "error": None,
        "details": {}
    }
    
    try:
        # Get stored license key
        license_key = get_stored_license_key()
        if not license_key:
            result["error"] = "NO_LICENSE"
            result["message"] = "No license key found. Premium features disabled."
            return result
        
        print(f"🔍 Validating stored license key: {license_key[:8]}...")
        
        # Verify the license using the same validation as activation
        egate = EGateKeySystem(EGATE_API_URL)
        verification_result = egate.verify_key(license_key)
        
        if verification_result["success"]:
            # License is valid - enable premium features
            result["success"] = True
            result["premium_enabled"] = True
            result["message"] = f"✅ License verified successfully. Premium features enabled."
            result["details"] = verification_result["details"]
            
            # Automatically set premium API key for skyboxes
            try:
                from .premium import set_premium_api_key, get_premium_api_key_value
                premium_key = get_premium_api_key_value()
                if premium_key:
                    set_premium_api_key(premium_key)
                    print(f"🔑 Premium API key automatically configured")
                else:
                    print(f"⚠️ Warning: Premium API key not available")
            except Exception as e:
                print(f"⚠️ Warning: Could not set premium API key: {e}")
            
            print(f"🎉 Premium access granted for user: {verification_result['details'].get('email', 'Unknown')}")
            
        else:
            # License validation failed
            result["error"] = verification_result.get("error", "VALIDATION_FAILED")
            result["message"] = f"❌ License validation failed: {verification_result['message']}"
            result["details"] = verification_result.get("details", {})
            
            # Handle specific error cases
            if verification_result.get("error") == "HWID_MISMATCH":
                result["message"] += "\n💡 This license is bound to another device. Contact support to reset HWID."
            elif verification_result.get("error") == "KEY_NOT_FOUND":
                result["message"] += "\n💡 License key is invalid or expired."
            elif verification_result.get("error") in ["CONNECTION_ERROR", "TIMEOUT"]:
                result["message"] += "\n💡 Could not connect to license server. Premium features temporarily disabled."
                # Don't mark as critical failure for connection issues
                result["success"] = True  # Allow app to continue without premium
                result["premium_enabled"] = False
            
            print(f"❌ License validation failed: {verification_result['message']}")
        
        return result
        
    except Exception as e:
        result["error"] = "EXCEPTION"
        result["message"] = f"Unexpected error during license validation: {str(e)}"
        print(f"❌ License validation exception: {e}")
        return result

def activate_license(license_key: str) -> Dict[str, any]:
    """
    Activate a new license key (performs validation and saves if successful)
    
    Args:
        license_key: License key to activate
        
    Returns:
        dict: Activation result with same structure as validate_stored_license
    """
    result = {
        "success": False,
        "message": "",
        "premium_enabled": False,
        "error": None,
        "details": {}
    }
    
    try:
        print(f"🔍 Activating license key: {license_key[:8]}...")
        
        # Verify the license using EGate system
        egate = EGateKeySystem(EGATE_API_URL)
        verification_result = egate.verify_key(license_key)
        
        if verification_result["success"]:
            # License is valid - save it and enable premium features
            if save_license_key(license_key):
                result["success"] = True
                result["premium_enabled"] = True
                result["message"] = f"✅ License activated successfully! Premium features enabled."
                result["details"] = verification_result["details"]
                
                # Automatically set premium API key for skyboxes
                try:
                    from .premium import set_premium_api_key, get_premium_api_key_value
                    premium_key = get_premium_api_key_value()
                    if premium_key:
                        set_premium_api_key(premium_key)
                        print(f"🔑 Premium API key automatically configured")
                    else:
                        print(f"⚠️ Warning: Premium API key not available")
                except Exception as e:
                    print(f"⚠️ Warning: Could not set premium API key: {e}")
                
                print(f"🎉 License activated for user: {verification_result['details'].get('email', 'Unknown')}")
            else:
                result["error"] = "SAVE_FAILED"
                result["message"] = "License is valid but could not be saved to config."
        else:
            # License activation failed
            result["error"] = verification_result.get("error", "ACTIVATION_FAILED")
            result["message"] = f"❌ License activation failed: {verification_result['message']}"
            result["details"] = verification_result.get("details", {})
            
            print(f"❌ License activation failed: {verification_result['message']}")
        
        return result
        
    except Exception as e:
        result["error"] = "EXCEPTION"
        result["message"] = f"Unexpected error during license activation: {str(e)}"
        print(f"❌ License activation exception: {e}")
        return result

def check_premium_status() -> bool:
    """
    Quick check if premium features are currently available
    
    Returns:
        bool: True if premium features are enabled
    """
    try:
        from .premium import has_premium_access
        return has_premium_access()
    except:
        return False

def startup_license_validation() -> Dict[str, any]:
    """
    Perform license validation on application startup
    This function should be called every time the application launches
    
    Returns:
        dict: Startup validation result
    """
    print("🚀 Starting CDBL license validation...")
    
    validation_result = validate_stored_license()
    
    if validation_result["success"]:
        if validation_result["premium_enabled"]:
            print("✅ Startup validation successful - Premium features available")
        else:
            print("⚠️ Startup validation - Running in free mode (connection issue)")
    else:
        print(f"❌ Startup validation failed - {validation_result['message']}")
    
    return validation_result
