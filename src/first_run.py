"""
First-run setup dialog for CDBL
Shows loading progress and downloads necessary files on first launch
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QTextEdit, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtGui import QFont, QPixmap

class FirstRunSetupWorker(QThread):
    """Worker thread for first-run setup operations"""
    progress = Signal(int, str)  # progress percentage, status message
    finished = Signal(bool, str)  # success, final message
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        """Perform first-run setup tasks"""
        try:
            self.progress.emit(5, "Starting CDBL setup...")
            time.sleep(0.5)  # Brief pause to show the message
            
            # Create necessary directories
            self.progress.emit(15, "Creating directories...")
            self.create_directories()
            
            # Download core files
            self.progress.emit(35, "Checking and downloading files...")
            self.download_core_files()
            
            # Set up configuration
            self.progress.emit(70, "Setting up configuration...")
            self.setup_configuration()
            
            # Download FastFlags data
            self.progress.emit(85, "Preparing FastFlags system...")
            self.setup_fastflags()
            
            # Mark setup as complete
            self.progress.emit(95, "Finalizing setup...")
            self.mark_setup_complete()
            
            self.progress.emit(100, "Setup complete!")
            self.finished.emit(True, "CDBL setup completed successfully!\n\nThe application will now restart.")
            
        except Exception as e:
            self.finished.emit(False, f"Setup failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def create_directories(self):
        """Create necessary application directories"""
        self.progress.emit(25, "Checking directories...")
        from src.core import ensure_directories
        ensure_directories()
    
    def download_core_files(self):
        """Download essential files"""
        try:
            self.progress.emit(45, "Checking existing files...")
            from src.core import download_needed_files
            download_needed_files()
        except Exception as e:
            # If core download fails, continue - it's not critical for basic operation
            print(f"Core files download warning: {e}")
    
    def setup_configuration(self):
        """Set up initial configuration"""
        self.progress.emit(65, "Setting up configuration...")
        config_dir = Path.home() / "AppData" / "Local" / "CDBL"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / "config.json"
        
        # Only create config if it doesn't exist
        if not config_file.exists():
            # Create basic config file
            config = {
                "version": "1.0.0",
                "first_run_complete": False,
                "settings": {
                    "check_for_updates": True,
                    "auto_detect_client": True
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        else:
            print("Configuration file already exists, keeping existing settings")
        
        # Create/update assets.json for sound swapper
        self.setup_assets_json()
    
    def setup_assets_json(self):
        """Create or update assets.json with required structure in CDBL cache"""
        from .assets import get_assets_cache_path
        
        # Use CDBL cache directory
        cache_dir = get_assets_cache_path()
        assets_file = Path(cache_dir) / "assets.json"
        
        # Check if assets.json exists and update it to add skins
        if assets_file.exists():
            try:
                with open(assets_file, 'r') as f:
                    assets_data = json.load(f)
                
                updated = False
                
                # Ensure Rivals structure exists
                if "Rivals" not in assets_data:
                    assets_data["Rivals"] = {}
                    updated = True
                
                # Ensure gun sounds exists
                if "gun sounds" not in assets_data["Rivals"]:
                    assets_data["Rivals"]["gun sounds"] = {}
                    updated = True
                
                # Add skins structure if missing
                if "skins" not in assets_data["Rivals"]["gun sounds"]:
                    assets_data["Rivals"]["gun sounds"]["skins"] = {}
                    updated = True
                
                # Add skin entries
                skins_data = assets_data["Rivals"]["gun sounds"]["skins"]
                
                # Add AR category if missing
                if "AR" not in skins_data:
                    skins_data["AR"] = {}
                    updated = True
                
                # Add individual skins
                ar_skins = {
                    "AUG": "5bcb64d6269f4c20515e8b7e7cc53504",
                    "Tommy Gun": "5bcb64d6269f4c20515e8b7e7cc53504",
                    "AK47": "5bcb64d6269f4c20515e8b7e7cc53504"
                }
                
                for skin_name, skin_hash in ar_skins.items():
                    if skin_name not in skins_data["AR"]:
                        skins_data["AR"][skin_name] = skin_hash
                        updated = True
                
                if updated:
                    with open(assets_file, 'w') as f:
                        json.dump(assets_data, f, indent=4)
                    print(f"✅ Updated assets.json with skins in {cache_dir}")
                else:
                    print(f"ℹ️ assets.json already has skins structure")
                    
            except Exception as e:
                print(f"⚠️ Error updating assets.json: {e}")
        else:
            print(f"⚠️ assets.json not found in {cache_dir}. Download assets first.")
    
    def setup_fastflags(self):
        """Initialize FastFlags system"""
        try:
            self.progress.emit(85, "Setting up FastFlags...")
            
            # Create initial backup of IxpSettings.json
            from src.fastflags import create_initial_backup
            backup_result = create_initial_backup()
            
            if backup_result["success"]:
                print(f"✅ {backup_result['message']}")
            else:
                print(f"⚠️ FastFlags backup warning: {backup_result['message']}")
                # Continue setup even if backup fails - it's not critical
            
            # Create FastFlags tracking directory
            fastflags_dir = Path.home() / "AppData" / "Local" / "CDBL"
            fastflags_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize tracking file if it doesn't exist
            tracking_file = fastflags_dir / "fastflags_tracking.json"
            if not tracking_file.exists():
                tracking_data = {
                    "applied_flags": {},
                    "backup_exists": backup_result["success"],
                    "skybox_fix_active": False
                }
                with open(tracking_file, 'w') as f:
                    json.dump(tracking_data, f, indent=2)
            else:
                print("FastFlags tracking file already exists, keeping existing data")
        except Exception as e:
            print(f"FastFlags setup warning: {e}")
    
    def mark_setup_complete(self):
        """Mark first-run setup as complete"""
        config_dir = Path.home() / "AppData" / "Local" / "CDBL"
        config_file = config_dir / "config.json"
        
        # Load existing config or create new one
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except:
                # If config is corrupted, create a new one
                config = {
                    "version": "1.0.0",
                    "settings": {
                        "check_for_updates": True,
                        "auto_detect_client": True
                    }
                }
        else:
            config = {
                "version": "1.0.0",
                "settings": {
                    "check_for_updates": True,
                    "auto_detect_client": True
                }
            }
        
        # Mark setup as complete
        config["first_run_complete"] = True
        
        # Save the updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)


class FirstRunSetupDialog(QDialog):
    """First-run setup dialog with progress bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CDBL - First Run Setup")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        self.setup_worker = None
        self.init_ui()
        self.apply_styles()
        
        # Auto-start setup after a brief delay
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_seconds = 2
        self.countdown_timer.start(1000)  # Update every second
        
        self.auto_start_timer = QTimer()
        self.auto_start_timer.timeout.connect(self.start_setup)
        self.auto_start_timer.setSingleShot(True)
        self.auto_start_timer.start(2000)  # Start after 2 seconds
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title and welcome message
        title = QLabel("Welcome to CDBL!")
        title.setObjectName("setupTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        welcome_text = QLabel(
            "This is your first time running CDBL.\n"
            "We need to set up a few things to get you started.\n\n"
            "Setup will begin automatically in a moment..."
        )
        welcome_text.setObjectName("welcomeText")
        welcome_text.setAlignment(Qt.AlignCenter)
        welcome_text.setWordWrap(True)
        layout.addWidget(welcome_text)
        
        # Progress section
        progress_label = QLabel("Setup Progress:")
        progress_label.setObjectName("progressLabel")
        layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("setupProgressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Preparing...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Log area (initially hidden)
        self.log_area = QTextEdit()
        self.log_area.setObjectName("logArea")
        self.log_area.setMaximumHeight(100)
        self.log_area.setVisible(False)
        layout.addWidget(self.log_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.show_log_btn = QPushButton("Show Details")
        self.show_log_btn.setObjectName("secondaryButton")
        self.show_log_btn.clicked.connect(self.toggle_log)
        self.show_log_btn.setVisible(False)
        button_layout.addWidget(self.show_log_btn)
        
        button_layout.addStretch()
        
        self.start_btn = QPushButton("Starting in 2 seconds...")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self.manual_start_setup)
        self.start_btn.setEnabled(False)  # Disabled during countdown
        button_layout.addWidget(self.start_btn)
        
        self.close_btn = QPushButton("Restart CDBL")
        self.close_btn.setObjectName("primaryButton") 
        self.close_btn.clicked.connect(self.restart_application)
        self.close_btn.setVisible(False)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def apply_styles(self):
        """Apply modern styling to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                           stop: 0 #1a1a1a, stop: 1 #2d1b3d);
                color: #ffffff;
                border: 2px solid rgba(168, 85, 247, 0.3);
                border-radius: 12px;
            }
            
            QLabel#setupTitle {
                color: #A855F7;
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 10px;
            }
            
            QLabel#welcomeText {
                color: #E5E7EB;
                font-size: 14px;
                line-height: 1.5;
                margin-bottom: 20px;
            }
            
            QLabel#progressLabel {
                color: #D1D5DB;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 5px;
            }
            
            QLabel#statusLabel {
                color: #A855F7;
                font-size: 12px;
                margin-top: 10px;
                font-style: italic;
            }
            
            QProgressBar#setupProgressBar {
                border: 2px solid rgba(168, 85, 247, 0.3);
                border-radius: 8px;
                background: rgba(55, 65, 81, 0.8);
                text-align: center;
                font-weight: 600;
                color: #ffffff;
                min-height: 25px;
            }
            
            QProgressBar#setupProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #A855F7, stop: 1 #8B5CF6);
                border-radius: 6px;
                margin: 2px;
            }
            
            QTextEdit#logArea {
                background: rgba(31, 41, 55, 0.8);
                border: 1px solid rgba(168, 85, 247, 0.2);
                border-radius: 6px;
                color: #E5E7EB;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
            
            QPushButton#primaryButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #A855F7, stop: 1 #8B5CF6);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 12px 24px;
                min-width: 120px;
            }
            
            QPushButton#primaryButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #9333EA, stop: 1 #7C3AED);
            }
            
            QPushButton#primaryButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #7C3AED, stop: 1 #6D28D9);
            }
            
            QPushButton#secondaryButton {
                background: rgba(55, 65, 81, 0.8);
                border: 1px solid rgba(168, 85, 247, 0.3);
                border-radius: 8px;
                color: #D1D5DB;
                font-weight: 500;
                font-size: 12px;
                padding: 8px 16px;
            }
            
            QPushButton#secondaryButton:hover {
                background: rgba(75, 85, 99, 0.9);
                border-color: rgba(168, 85, 247, 0.5);
            }
        """)
    
    def update_countdown(self):
        """Update countdown timer"""
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.start_btn.setText(f"Starting in {self.countdown_seconds} seconds...")
        else:
            self.countdown_timer.stop()
            self.start_btn.setText("Starting...")
    
    def manual_start_setup(self):
        """Allow manual start of setup (cancels countdown)"""
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        if hasattr(self, 'auto_start_timer'):
            self.auto_start_timer.stop()
        self.start_setup()
    
    def start_setup(self):
        """Start the setup process"""
        # Stop timers if they're still running
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        if hasattr(self, 'auto_start_timer'):
            self.auto_start_timer.stop()
            
        self.start_btn.setEnabled(False)
        self.start_btn.setText("Setting up...")
        self.show_log_btn.setVisible(True)
        
        # Start the setup worker
        self.setup_worker = FirstRunSetupWorker()
        self.setup_worker.progress.connect(self.update_progress)
        self.setup_worker.finished.connect(self.setup_finished)
        self.setup_worker.start()
    
    def update_progress(self, percentage, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
        
        # Add to log
        log_message = f"[{percentage:3d}%] {message}"
        self.log_area.append(log_message)
        
        # Auto-scroll log
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_area.setTextCursor(cursor)
    
    def setup_finished(self, success, message):
        """Handle setup completion"""
        if success:
            self.status_label.setText("Setup completed successfully!")
            self.progress_bar.setValue(100)
            
            # Show completion message
            self.log_area.append(f"\n✅ {message}")
            
            # Show restart button
            self.start_btn.setVisible(False)
            self.close_btn.setVisible(True)
            
            # Auto-restart after 3 seconds
            QTimer.singleShot(3000, self.restart_application)
            
        else:
            self.status_label.setText("Setup failed!")
            self.log_area.append(f"\n❌ {message}")
            
            # Re-enable start button for retry
            self.start_btn.setEnabled(True)
            self.start_btn.setText("Retry Setup")
    
    def toggle_log(self):
        """Toggle log area visibility"""
        if self.log_area.isVisible():
            self.log_area.setVisible(False)
            self.show_log_btn.setText("Show Details")
            self.setFixedSize(500, 400)
        else:
            self.log_area.setVisible(True)
            self.show_log_btn.setText("Hide Details")
            self.setFixedSize(500, 520)
    
    def restart_application(self):
        """Restart the CDBL application, preserving admin privileges"""
        self.accept()
        
        # Check if we're currently running as admin
        from src.admin import is_admin
        
        if is_admin():
            # We have admin privileges - restart with admin privileges preserved
            try:
                if getattr(sys, 'frozen', False):
                    # Running as compiled executable
                    exe_path = sys.executable
                    # Use ShellExecute with "runas" to maintain admin privileges
                    import ctypes
                    ctypes.windll.shell32.ShellExecuteW(
                        None,
                        "runas",  # Request elevation (maintains current admin status)
                        exe_path,
                        "",  # No arguments
                        os.getcwd(),
                        1  # SW_SHOW
                    )
                else:
                    # Running as Python script
                    python_exe = sys.executable
                    script_path = os.path.abspath(sys.argv[0])
                    import ctypes
                    ctypes.windll.shell32.ShellExecuteW(
                        None,
                        "runas",  # Request elevation (maintains current admin status)
                        python_exe,
                        f'"{script_path}"',
                        os.getcwd(),
                        1  # SW_SHOW
                    )
                print("🔄 Restarting with admin privileges...")
                    
            except Exception as e:
                print(f"Failed to restart with admin privileges: {e}")
                # Fallback to regular restart
                self.restart_without_admin()
                return
        else:
            # Not running as admin - regular restart
            print("🔄 Restarting without admin privileges...")
            self.restart_without_admin()
            return
        
        # Exit current instance
        QApplication.quit()
    
    def restart_without_admin(self):
        """Restart application without admin privileges (fallback)"""
        try:
            if getattr(sys, 'frozen', False):
                # If running as compiled executable
                exe_path = sys.executable
                subprocess.Popen([exe_path], cwd=os.getcwd())
            else:
                # If running as Python script
                python_exe = sys.executable
                script_path = sys.argv[0]
                subprocess.Popen([python_exe, script_path], cwd=os.getcwd())
        except Exception as e:
            print(f"Failed to restart application: {e}")


def is_first_run():
    """Check if this is the first run of CDBL"""
    config_dir = Path.home() / "AppData" / "Local" / "CDBL"
    config_file = config_dir / "config.json"
    
    if not config_file.exists():
        return True
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return not config.get("first_run_complete", False)
    except:
        return True


def show_first_run_setup(parent=None):
    """Show the first-run setup dialog if needed"""
    if is_first_run():
        dialog = FirstRunSetupDialog(parent)
        return dialog.exec()
    return None


def get_license_key():
    """
    Get the stored license key from config
    
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


def save_license_key(license_key: str):
    """
    Save license key to config
    
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


class UpdateAvailableDialog(QDialog):
    """Dialog shown when an update is available"""
    
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("CDBL - Update Available")
        self.setModal(True)
        self.setFixedSize(600, 550)  # Increased from 550x450 to 600x550
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        self.user_choice = None  # Will be 'download', 'skip', or None
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🎉 Update Available!")
        title.setObjectName("setupTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Version info
        version_text = QLabel(
            f"A new version of CDBL is available!\n\n"
            f"Current Version: {self.update_info['current_version']}\n"
            f"Latest Version: {self.update_info['latest_version']}"
        )
        version_text.setObjectName("welcomeText")
        version_text.setAlignment(Qt.AlignCenter)
        version_text.setWordWrap(True)
        layout.addWidget(version_text)
        
        # Release notes section
        notes_label = QLabel("📝 What's New:")
        notes_label.setObjectName("progressLabel")
        layout.addWidget(notes_label)
        
        self.notes_area = QTextEdit()
        self.notes_area.setObjectName("logArea")
        self.notes_area.setReadOnly(True)
        self.notes_area.setMinimumHeight(220)  # Increased from maxHeight 150 to minHeight 220
        
        # Format release notes
        release_notes = self.update_info.get('release_notes', 'No release notes available')
        self.notes_area.setPlainText(release_notes)
        layout.addWidget(self.notes_area)
        
        # Info text
        info_text = QLabel(
            "Click 'Download Update' to visit the download page,\n"
            "or 'Skip' to continue with the current version."
        )
        info_text.setObjectName("statusLabel")
        info_text.setAlignment(Qt.AlignCenter)
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.setObjectName("secondaryButton")
        self.skip_btn.clicked.connect(self.skip_update)
        button_layout.addWidget(self.skip_btn)
        
        self.download_btn = QPushButton("Download Update")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.clicked.connect(self.open_download)
        button_layout.addWidget(self.download_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def apply_styles(self):
        """Apply modern styling to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                           stop: 0 #1a1a1a, stop: 1 #2d1b3d);
                color: #ffffff;
                border: 2px solid rgba(168, 85, 247, 0.3);
                border-radius: 12px;
            }
            
            #setupTitle {
                font-size: 28px;
                font-weight: bold;
                color: #a855f7;
                margin-bottom: 10px;
            }
            
            #welcomeText {
                font-size: 14px;
                color: #e5e5e5;
                line-height: 1.6;
            }
            
            #progressLabel {
                font-size: 13px;
                font-weight: 600;
                color: #c084fc;
                margin-top: 5px;
            }
            
            #statusLabel {
                font-size: 12px;
                color: #d1d5db;
                font-style: italic;
            }
            
            #logArea {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(168, 85, 247, 0.2);
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                color: #e5e5e5;
            }
            
            #primaryButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #7c3aed, stop: 1 #a855f7);
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 140px;
            }
            
            #primaryButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #6d28d9, stop: 1 #9333ea);
            }
            
            #primaryButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #5b21b6, stop: 1 #7e22ce);
            }
            
            #secondaryButton {
                background-color: rgba(75, 85, 99, 0.8);
                color: white;
                border: 1px solid rgba(156, 163, 175, 0.3);
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 100px;
            }
            
            #secondaryButton:hover {
                background-color: rgba(107, 114, 128, 0.9);
                border-color: rgba(168, 85, 247, 0.4);
            }
            
            #secondaryButton:pressed {
                background-color: rgba(55, 65, 81, 0.9);
            }
        """)
    
    def open_download(self):
        """Open the download page"""
        self.user_choice = 'download'
        
        # Open the release page
        from src.update import open_release_page
        open_release_page()
        
        self.accept()
    
    def skip_update(self):
        """Skip the update"""
        self.user_choice = 'skip'
        self.accept()


def check_for_updates_on_startup():
    """
    Check for updates on startup and show dialog if update is available
    
    Returns:
        str: User choice ('download', 'skip', or None if no update)
    """
    try:
        from src.update import check_for_updates
        
        print("Checking for updates...")
        update_info = check_for_updates(timeout=5)
        
        if update_info.get('error'):
            print(f"Update check failed: {update_info['error']}")
            return None
        
        if update_info.get('update_available'):
            print(f"Update available: {update_info['latest_version']}")
            
            # Show update dialog
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            dialog = UpdateAvailableDialog(update_info)
            dialog.exec()
            
            return dialog.user_choice
        else:
            print("CDBL is up to date!")
            return None
            
    except Exception as e:
        print(f"Error checking for updates: {e}")
        import traceback
        traceback.print_exc()
        return None


def remove_license_key():
    """
    Remove license key from config
    
    Returns:
        bool: True if removed successfully, False otherwise
    """
    config_dir = Path.home() / "AppData" / "Local" / "CDBL"
    config_file = config_dir / "config.json"
    
    if not config_file.exists():
        return True  # Nothing to remove
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Remove license key if it exists
        if "license_key" in config:
            del config["license_key"]
            
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error removing license key: {e}")
        return False


def remove_license_key():
    """
    Remove license key from config
    
    Returns:
        bool: True if removed successfully, False otherwise
    """
    config_dir = Path.home() / "AppData" / "Local" / "CDBL"
    config_file = config_dir / "config.json"
    
    if not config_file.exists():
        return True  # Nothing to remove
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Remove license key if it exists
        if "license_key" in config:
            del config["license_key"]
            
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error removing license key: {e}")
        return False