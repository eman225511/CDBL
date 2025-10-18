"""
EGate Key System Integration for CDBL
Handles license key verification with HWID binding and email validation
"""

import hashlib
import platform
import uuid
import requests
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
