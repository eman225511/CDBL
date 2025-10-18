"""
Admin privileges utility for CDBL
Handles Windows UAC elevation and admin checks
"""

import sys
import os
import ctypes
import subprocess


def is_admin():
    """Check if the current process has administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Restart the application with administrator privileges"""
    if is_admin():
        return True
    
    try:
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller EXE
            exe_path = sys.executable
            params = ' '.join(sys.argv[1:])  # Get command line args
        else:
            # Running as Python script
            exe_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            params = f'"{script_path}"'
        
        # Use ShellExecute with "runas" to prompt for admin
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",  # Request elevation
            exe_path,
            params,
            None,
            1  # SW_SHOW
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        return False


def prompt_for_admin():
    """
    Check if running as admin, prompt for elevation if not
    Returns True if admin privileges are available
    """
    if is_admin():
        return True
    
    print("Administrator privileges required for CDBL operations...")
    
    # Try to elevate
    if run_as_admin():
        # Exit current instance since we're restarting with admin
        sys.exit(0)
    else:
        print("Failed to obtain administrator privileges")
        return False


def check_admin_with_dialog(parent=None):
    """
    Check admin privileges and show dialog if needed
    Returns True if admin, False if user declines
    """
    if is_admin():
        return True
    
    # Import here to avoid circular imports
    from PySide6.QtWidgets import QMessageBox
    from PySide6.QtCore import Qt
    
    # Create message box
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle("Administrator Privileges Required")
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setText(
        "CDBL requires administrator privileges to modify Roblox files and settings.\n\n"
        "Click 'Restart as Admin' to restart CDBL with elevated privileges."
    )
    msg_box.setInformativeText(
        "Some features may not work properly without administrator access."
    )
    
    # Add custom buttons
    restart_btn = msg_box.addButton("Restart as Admin", QMessageBox.AcceptRole)
    continue_btn = msg_box.addButton("Continue Anyway", QMessageBox.RejectRole)
    msg_box.setDefaultButton(restart_btn)
    
    # Show dialog
    result = msg_box.exec()
    
    if msg_box.clickedButton() == restart_btn:
        # User chose to restart as admin
        if run_as_admin():
            sys.exit(0)
        else:
            # Failed to elevate, show error
            error_box = QMessageBox(parent)
            error_box.setWindowTitle("Elevation Failed")
            error_box.setIcon(QMessageBox.Critical)
            error_box.setText("Failed to restart with administrator privileges.")
            error_box.setInformativeText("Please manually run CDBL as administrator.")
            error_box.exec()
            return False
    
    # User chose to continue without admin
    return False


def check_and_display_admin_status(parent=None):
    """
    Check admin status and display notification
    Used when UAC manifest handles elevation automatically
    """
    if is_admin():
        print("✅ Running with administrator privileges")
        return True
    else:
        print("⚠️ Running without administrator privileges")
        
        # Import here to avoid circular imports
        from PySide6.QtWidgets import QMessageBox
        
        # Show informational message (non-blocking)
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle("Admin Privileges")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText("CDBL is running without administrator privileges.")
        msg_box.setInformativeText(
            "Some features may not work properly. "
            "Please restart CDBL as administrator if you encounter issues."
        )
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setModal(False)  # Non-blocking
        
        # Show and close automatically after 3 seconds
        msg_box.show()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, msg_box.close)
        
        return False