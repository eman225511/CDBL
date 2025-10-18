"""
CDBL Settings Module
Contains all settings-related functionality for Roblox
"""

import os
import xml.etree.ElementTree as ET

def change_settings(sensitivity=None, fps_cap=None, graphics=None, volume=None, get_current=False):
    """
    Edit Roblox's GlobalBasicSettings_13.xml (mouse sensitivity, FPS cap, graphics, volume).
    
    ONLY WORKS ON REGULAR ROBLOX CLIENT, NOT BLOXSTRAP OR FISHSTRAP.
    
    Args:
        sensitivity (float, optional): Mouse sensitivity (0.00001 - 100)
        fps_cap (int/str, optional): FPS cap (1-99999 or 'inf' for unlimited)
        graphics (int, optional): Graphics quality level (1-20)
        volume (int, optional): Volume level (1-10)
        get_current (bool, optional): If True, return current settings in JSON format
    
    Returns:
        dict: Current settings in JSON format if get_current=True
        bool: Success/failure status if get_current=False
    
    Created by: https://github.com/KickfnGIT/DebloatedBloxLauncher (converted to Python)
    """
    # Use the actual Roblox settings file, not the downloaded copy
    settings_path = os.path.join(os.environ['LOCALAPPDATA'], 'Roblox', 'GlobalBasicSettings_13.xml')
    if not os.path.exists(settings_path):
        print(f"ERROR: Settings file not found at {settings_path}")
        print("INFO: Make sure Roblox has generated the file before running this script.")
        return False

    # Load XML
    try:
        tree = ET.parse(settings_path)
        root = tree.getroot()
    except Exception as e:
        print(f"ERROR: Failed to load settings XML: {e}")
        return False

    # Helper functions using exact XPath selectors from PowerShell script
    def update_sensitivity(sensitivity_value):
        try:
            sensitivity_float = float(sensitivity_value)
            if sensitivity_float >= 0.00001 and sensitivity_float <= 100:
                # Update all sensitivity elements exactly like PowerShell script
                updated_count = 0
                
                mouse_sens = root.find(".//float[@name='MouseSensitivity']")
                if mouse_sens is not None:
                    mouse_sens.text = str(sensitivity_float)
                    updated_count += 1
                
                fp_x = root.find(".//Vector2[@name='MouseSensitivityFirstPerson']/X")
                if fp_x is not None:
                    fp_x.text = str(sensitivity_float)
                    updated_count += 1
                
                fp_y = root.find(".//Vector2[@name='MouseSensitivityFirstPerson']/Y")
                if fp_y is not None:
                    fp_y.text = str(sensitivity_float)
                    updated_count += 1
                
                tp_x = root.find(".//Vector2[@name='MouseSensitivityThirdPerson']/X")
                if tp_x is not None:
                    tp_x.text = str(sensitivity_float)
                    updated_count += 1
                
                tp_y = root.find(".//Vector2[@name='MouseSensitivityThirdPerson']/Y")
                if tp_y is not None:
                    tp_y.text = str(sensitivity_float)
                    updated_count += 1
                
                if updated_count > 0:
                    print(f"SUCCESS: Sensitivity set to: {sensitivity_float} ({updated_count} elements updated)")
                    return True
                else:
                    print("ERROR: No sensitivity elements found in XML")
                    return False
            else:
                print("ERROR: Sensitivity must be between 0.00001 and 100")
                return False
        except (ValueError, TypeError):
            print("ERROR: Invalid sensitivity input. Must be a number.")
            return False

    def update_fps_cap(fps_cap_value):
        try:
            if isinstance(fps_cap_value, str) and fps_cap_value.lower() in ['inf', 'infinity']:
                fpscap = 9999999
            else:
                fpscap = int(fps_cap_value)
                if not (1 <= fpscap <= 99999):
                    print("ERROR: FPS cap must be between 1 and 99999, or 'inf' for unlimited")
                    return False
            
            framerate_cap = root.find(".//int[@name='FramerateCap']")
            if framerate_cap is not None:
                framerate_cap.text = str(fpscap)
                if fpscap == 9999999:
                    print("SUCCESS: FPS cap set to: Unlimited")
                else:
                    print(f"SUCCESS: FPS cap set to: {fpscap}")
                return True
            else:
                print("ERROR: No FramerateCap element found in XML")
                return False
        except (ValueError, TypeError):
            print("ERROR: Invalid FPS cap input. Must be a number or 'inf'.")
            return False

    def update_graphics(graphics_value):
        try:
            graphics_int = int(graphics_value)
            # Check if graphics is 1-20 (equivalent to PowerShell validation)
            if 1 <= graphics_int <= 20:
                updated_count = 0
                
                gql = root.find(".//int[@name='GraphicsQualityLevel']")
                if gql is not None:
                    gql.text = str(graphics_int)
                    updated_count += 1
                
                sql = root.find(".//token[@name='SavedQualityLevel']")
                if sql is not None:
                    sql.text = str(graphics_int)
                    updated_count += 1
                
                if updated_count > 0:
                    print(f"SUCCESS: Graphics quality set to: {graphics_int} ({updated_count} elements updated)")
                    return True
                else:
                    print("ERROR: No graphics quality elements found in XML")
                    return False
            else:
                print("ERROR: Graphics quality must be between 1 and 20")
                return False
        except (ValueError, TypeError):
            print("ERROR: Invalid graphics input. Must be a number.")
            return False

    def update_volume(volume_value):
        try:
            volume_int = int(volume_value)
            # Check if volume is 1-10 (equivalent to PowerShell validation)
            if 1 <= volume_int <= 10:
                scaled_volume = round(volume_int / 10.0, 1)
                master_vol = root.find(".//float[@name='MasterVolume']")
                if master_vol is not None:
                    master_vol.text = str(scaled_volume)
                    print(f"SUCCESS: Volume set to: {volume_int} (scaled to {scaled_volume})")
                    return True
                else:
                    print("ERROR: No MasterVolume element found in XML")
                    return False
            else:
                print("ERROR: Volume must be between 1 and 10")
                return False
        except (ValueError, TypeError):
            print("ERROR: Invalid volume input. Must be a number.")
            return False

    # Get current values functions
    def get_current_sensitivity():
        elem = root.find(".//float[@name='MouseSensitivity']")
        return elem.text if elem is not None and elem.text else "N/A"

    def get_current_fps_cap():
        elem = root.find(".//int[@name='FramerateCap']")
        return elem.text if elem is not None and elem.text else "N/A"

    def get_current_graphics():
        elem = root.find(".//int[@name='GraphicsQualityLevel']")
        return elem.text if elem is not None and elem.text else "N/A"

    def get_current_volume():
        elem = root.find(".//float[@name='MasterVolume']")
        if elem is not None and elem.text:
            try:
                return str(int(float(elem.text) * 10))
            except:
                return "N/A"
        return "N/A"

    # If get_current is True, return current settings as JSON
    if get_current:
        current_settings = {
            "sensitivity": get_current_sensitivity(),
            "fps_cap": get_current_fps_cap(),
            "graphics": get_current_graphics(),
            "volume": get_current_volume()
        }
        return current_settings

    # Apply settings based on provided arguments
    changes_made = False
    
    if sensitivity is not None:
        if update_sensitivity(sensitivity):
            changes_made = True
    
    if fps_cap is not None:
        if update_fps_cap(fps_cap):
            changes_made = True
    
    if graphics is not None:
        if update_graphics(graphics):
            changes_made = True
    
    if volume is not None:
        if update_volume(volume):
            changes_made = True
    
    # Save changes if any were made
    if changes_made:
        try:
            tree.write(settings_path, encoding='utf-8', xml_declaration=True)
            print("SUCCESS: Settings updated successfully!")
            return True
        except Exception as e:
            print(f"ERROR: Failed to save settings: {e}")
            return False
    else:
        print("INFO: No settings were provided to update.")
        return True