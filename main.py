"""
CDBL Modern GUI Application
A modern PySide6 interface for CDBL functionality
"""

import sys
import os
import json
import atexit
import tempfile
import shutil
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QComboBox, QLabel, QFrame, QGridLayout,
    QSpinBox, QDoubleSpinBox, QSlider, QListWidget, QTextEdit, QFileDialog,
    QMessageBox, QGroupBox, QScrollArea, QSizePolicy, QProgressBar, QDialog,
    QLineEdit, QMenu
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, Signal, QThread, QObject, QUrl
from PySide6.QtGui import QPixmap, QFont, QPalette, QColor, QIcon, QPainterPath, QRegion, QDesktopServices

# Try to import pygame for audio playback
try:
    import pygame
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available. Install with: pip install pygame")

# Cleanup handler for PyInstaller temp directories
def cleanup_temp_dirs():
    """Clean up temporary directories that might not be auto-cleaned"""
    if getattr(sys, 'frozen', False):
        try:
            # Get the PyInstaller temp directory
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass and os.path.exists(meipass):
                # Don't delete the current _MEIPASS while running
                # Instead, clean up old temp directories
                temp_base = os.path.dirname(meipass)
                for item in os.listdir(temp_base):
                    if item.startswith('_MEI') and item != os.path.basename(meipass):
                        old_temp = os.path.join(temp_base, item)
                        try:
                            if os.path.isdir(old_temp):
                                shutil.rmtree(old_temp, ignore_errors=True)
                        except:
                            pass  # Ignore cleanup errors
        except Exception:
            pass  # Ignore all cleanup errors

# Register cleanup function
atexit.register(cleanup_temp_dirs)

# Import our modules
from src.launcher import detect_roblox_clients, launch_roblox, kill_roblox, install_roblox, install_bloxstrap, install_fishstrap
from src.settings import change_settings
from src.skybox import make_skyname_list, get_sky_preview, apply_skybox, apply_default_sky, download_sky
from src.textures import apply_dark_textures, apply_light_textures, apply_default_textures
from src.core import download_needed_files
from src.fastflags import apply_fastflags, remove_fastflags
from src.assets import download_and_prepare_assets, apply_skybox_fix, get_cache_info
from src.first_run import show_first_run_setup, is_first_run, get_license_key, save_license_key, remove_license_key, check_for_updates_on_startup
from src.admin import is_admin, check_admin_with_dialog, check_and_display_admin_status


class SkyboxDownloadWorker(QThread):
    """Worker thread specifically for skybox downloads with progress"""
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int, str)  # progress percentage, status message
    
    def __init__(self, sky_name):
        super().__init__()
        self.sky_name = sky_name
    
    def progress_callback(self, percentage, message):
        """Callback function for progress updates"""
        self.progress.emit(percentage, message)
    
    def run(self):
        try:
            from src.skybox import download_sky_with_progress
            success = download_sky_with_progress(self.sky_name, self.progress_callback)
            if success:
                self.finished.emit(f"Successfully downloaded {self.sky_name}")
            else:
                self.error.emit(f"Failed to download {self.sky_name}")
        except Exception as e:
            self.error.emit(f"Error downloading {self.sky_name}: {str(e)}")


class WorkerThread(QThread):
    """Worker thread for background operations"""
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int, str)  # progress percentage, status message
    
    def __init__(self, operation, *args):
        super().__init__()
        self.operation = operation
        self.args = args
    
    def run(self):
        try:
            if self.operation == "download_files":
                download_needed_files()
                self.finished.emit("Files downloaded successfully")
            elif self.operation == "apply_skybox":
                client, skybox = self.args
                result = apply_skybox(client, skybox)
                if result:
                    self.finished.emit(f"Applied {skybox} skybox successfully")
                else:
                    self.error.emit("Failed to apply skybox")
            elif self.operation == "apply_texture":
                func, client = self.args
                result = func(client)
                if result:
                    self.finished.emit("Texture applied successfully")
                else:
                    self.error.emit("Failed to apply texture")
        except Exception as e:
            self.error.emit(str(e))


class AudioWorker(QObject):
    """Worker for audio playback in separate thread"""
    finished = Signal()
    error = Signal(str)

    def __init__(self, file_path: str, volume: float = 0.2):
        super().__init__()
        self.file_path = file_path
        self.volume = volume  # Volume from 0.0 to 1.0
        self.should_stop = False

    def play(self):
        """Play audio file"""
        try:
            if PYGAME_AVAILABLE:
                sound = pygame.mixer.Sound(self.file_path)
                sound.set_volume(self.volume)  # Set volume for this sound
                sound.play()
                while pygame.mixer.get_busy() and not self.should_stop:
                    pygame.time.wait(100)
            else:
                self.error.emit("pygame not available for audio preview")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def stop(self):
        """Stop audio playback"""
        self.should_stop = True
        if PYGAME_AVAILABLE:
            pygame.mixer.stop()


class ModernButton(QPushButton):
    """Custom button with modern styling and animations"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(45)
        self.setCursor(Qt.PointingHandCursor)
        
        # Animation setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def enterEvent(self, event):
        # Subtle scale animation on hover - only height to avoid text cutoff
        current_rect = self.geometry()
        target_rect = QRect(
            current_rect.x(),
            current_rect.y() - 1,
            current_rect.width(),  # Keep width constant
            current_rect.height() + 2
        )
        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(target_rect)
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        # Return to original size - only height to avoid text cutoff
        current_rect = self.geometry()
        target_rect = QRect(
            current_rect.x(),
            current_rect.y() + 1,
            current_rect.width(),  # Keep width constant
            current_rect.height() - 2
        )
        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(target_rect)
        self.animation.start()
        super().leaveEvent(event)


class GeneralTab(QWidget):
    """Tab 1 - General functionality"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.update_client_status()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title
        title = QLabel("General")
        title.setObjectName("tabTitle")
        layout.addWidget(title)
        
        # Client selection group
        client_group = QGroupBox("Roblox Client")
        client_group.setObjectName("groupBox")
        client_layout = QVBoxLayout()
        client_layout.setSpacing(20)
        client_layout.setContentsMargins(25, 30, 25, 25)
        
        # Bootstrap selector
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(15)
        
        bootstrap_label = QLabel("Bootstrap:")
        bootstrap_label.setObjectName("label")
        bootstrap_label.setMinimumWidth(100)
        selector_layout.addWidget(bootstrap_label)
        
        self.client_combo = QComboBox()
        self.client_combo.addItems(["Auto-detect", "Roblox", "Bloxstrap", "Fishstrap"])
        self.client_combo.setObjectName("comboBox")
        self.client_combo.currentTextChanged.connect(self.on_client_changed)
        self.client_combo.setMinimumWidth(200)
        selector_layout.addWidget(self.client_combo)
        
        selector_layout.addSpacing(20)
        
        self.status_label = QLabel("Detecting clients...")
        self.status_label.setObjectName("statusLabel")
        selector_layout.addWidget(self.status_label)
        
        selector_layout.addStretch()
        client_layout.addLayout(selector_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.launch_btn = ModernButton("Launch Roblox")
        self.launch_btn.setObjectName("primaryButton")
        self.launch_btn.clicked.connect(self.launch_roblox)
        button_layout.addWidget(self.launch_btn)
        
        self.kill_btn = ModernButton("Kill Roblox")
        self.kill_btn.setObjectName("dangerButton")
        self.kill_btn.clicked.connect(self.kill_roblox)
        button_layout.addWidget(self.kill_btn)
        
        self.install_btn = ModernButton("Install Client")
        self.install_btn.setObjectName("secondaryButton")
        self.install_btn.clicked.connect(self.install_client)
        button_layout.addWidget(self.install_btn)
        
        button_layout.addStretch()
        client_layout.addLayout(button_layout)
        client_group.setLayout(client_layout)
        layout.addWidget(client_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def update_client_status(self):
        """Update the status of installed clients"""
        clients = detect_roblox_clients()
        installed = [name for name, installed in clients.items() if installed]
        
        if installed:
            self.status_label.setText(f"Installed: {', '.join(installed)}")
            self.status_label.setStyleSheet("color: #8B5CF6;")
        else:
            self.status_label.setText("No clients found")
            self.status_label.setStyleSheet("color: #EF4444;")
            
    def on_client_changed(self):
        """Handle client selection change"""
        selected = self.client_combo.currentText()
        if selected == "Auto-detect":
            self.update_client_status()
        else:
            clients = detect_roblox_clients()
            if clients.get(selected, False):
                self.status_label.setText(f"{selected} is installed")
                self.status_label.setStyleSheet("color: #8B5CF6;")
            else:
                self.status_label.setText(f"{selected} not found")
                self.status_label.setStyleSheet("color: #EF4444;")
                
    def launch_roblox(self):
        """Launch the selected Roblox client"""
        selected = self.client_combo.currentText()
        client = "auto" if selected == "Auto-detect" else selected
        
        result = launch_roblox(client)
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
        else:
            QMessageBox.warning(self, "Error", result["message"])
            
    def kill_roblox(self):
        """Kill all Roblox processes"""
        result = kill_roblox()
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
        else:
            QMessageBox.warning(self, "Error", result["message"])
            
    def install_client(self):
        """Open installation page for selected client"""
        selected = self.client_combo.currentText()
        
        if selected == "Roblox" or selected == "Auto-detect":
            result = install_roblox()
        elif selected == "Bloxstrap":
            result = install_bloxstrap()
        elif selected == "Fishstrap":
            result = install_fishstrap()
        else:
            QMessageBox.information(self, "Info", "Please select a specific client to install")
            return
            
        if result["success"]:
            QMessageBox.information(self, "Success", result["message"])
        else:
            QMessageBox.warning(self, "Error", result["message"])


class SettingsTab(QWidget):
    """Tab 2 - Roblox Settings"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title
        title = QLabel("Roblox Settings")
        title.setObjectName("tabTitle")
        layout.addWidget(title)
        
        # Settings form
        settings_group = QGroupBox("Game Settings (Roblox Client Only)")
        settings_group.setObjectName("groupBox")
        form_layout = QGridLayout()
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(24, 32, 24, 24)
        form_layout.setColumnMinimumWidth(0, 160)
        form_layout.setColumnMinimumWidth(1, 180)
        
        # Mouse Sensitivity
        sens_label = QLabel("Mouse Sensitivity:")
        sens_label.setObjectName("settingLabel")
        form_layout.addWidget(sens_label, 0, 0)
        self.sensitivity_spin = QDoubleSpinBox()
        self.sensitivity_spin.setRange(0.00001, 100.0)
        self.sensitivity_spin.setDecimals(5)
        self.sensitivity_spin.setValue(1.0)
        self.sensitivity_spin.setObjectName("spinBox")
        form_layout.addWidget(self.sensitivity_spin, 0, 1)
        
        # FPS Cap
        fps_label = QLabel("FPS Cap:")
        fps_label.setObjectName("settingLabel")
        form_layout.addWidget(fps_label, 1, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 99999)
        self.fps_spin.setValue(60)
        self.fps_spin.setObjectName("spinBox")
        form_layout.addWidget(self.fps_spin, 1, 1)
        
        # Graphics Quality
        graphics_label = QLabel("Graphics Quality:")
        graphics_label.setObjectName("settingLabel")
        form_layout.addWidget(graphics_label, 2, 0)
        self.graphics_spin = QSpinBox()
        self.graphics_spin.setRange(1, 20)
        self.graphics_spin.setValue(10)
        self.graphics_spin.setObjectName("spinBox")
        form_layout.addWidget(self.graphics_spin, 2, 1)
        
        # Volume
        volume_label = QLabel("Volume:")
        volume_label.setObjectName("settingLabel")
        form_layout.addWidget(volume_label, 3, 0)
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(1, 10)
        self.volume_spin.setValue(5)
        self.volume_spin.setObjectName("spinBox")
        form_layout.addWidget(self.volume_spin, 3, 1)
        
        settings_group.setLayout(form_layout)
        layout.addWidget(settings_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 20, 0, 0)
        
        self.load_btn = ModernButton("Load Current")
        self.load_btn.setObjectName("secondaryButton")
        self.load_btn.clicked.connect(self.load_current_settings)
        button_layout.addWidget(self.load_btn)
        
        self.apply_btn = ModernButton("Apply Settings")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Modification Status group
        status_group = QGroupBox("Modification Status")
        status_group.setObjectName("groupBox")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(12)
        status_layout.setContentsMargins(24, 32, 24, 24)
        
        # Skybox fix status
        self.skybox_status_label = QLabel("Skybox Fix: Checking...")
        self.skybox_status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.skybox_status_label)
        
        # No arms fix status
        self.no_arms_status_label = QLabel("No Arms Fix: Checking...")
        self.no_arms_status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.no_arms_status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Load status information
        self.update_modification_status()
        
    def load_current_settings(self):
        """Load current Roblox settings"""
        try:
            settings = change_settings(get_current=True)
            if isinstance(settings, dict):
                if settings["sensitivity"] != "N/A":
                    self.sensitivity_spin.setValue(float(settings["sensitivity"]))
                if settings["fps_cap"] != "N/A":
                    self.fps_spin.setValue(int(settings["fps_cap"]))
                if settings["graphics"] != "N/A":
                    self.graphics_spin.setValue(int(settings["graphics"]))
                if settings["volume"] != "N/A":
                    self.volume_spin.setValue(int(settings["volume"]))
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not load current settings: {str(e)}")
            
    def apply_settings(self):
        """Apply the configured settings"""
        try:
            result = change_settings(
                sensitivity=self.sensitivity_spin.value(),
                fps_cap=self.fps_spin.value(),
                graphics=self.graphics_spin.value(),
                volume=self.volume_spin.value()
            )
            
            if result:
                QMessageBox.information(self, "Success", "Settings applied successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to apply settings")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying settings: {str(e)}")
    
    def update_modification_status(self):
        """Update the status of modifications"""
        try:
            # Check skybox fix status
            from src.fastflags import is_skybox_fix_active, is_no_arms_fix_active
            
            skybox_status = is_skybox_fix_active()
            if skybox_status["success"]:
                if skybox_status["active"]:
                    self.skybox_status_label.setText("✅ Skybox Fix: Active")
                    self.skybox_status_label.setStyleSheet("color: #4CAF50;")
                else:
                    self.skybox_status_label.setText("❌ Skybox Fix: Inactive")
                    self.skybox_status_label.setStyleSheet("color: #F44336;")
            else:
                self.skybox_status_label.setText("⚠️ Skybox Fix: Error checking status")
                self.skybox_status_label.setStyleSheet("color: #FF9800;")
            
            # Check no arms fix status
            no_arms_status = is_no_arms_fix_active()
            if no_arms_status["success"]:
                if no_arms_status["active"]:
                    self.no_arms_status_label.setText("✅ No Arms Fix: Active")
                    self.no_arms_status_label.setStyleSheet("color: #4CAF50;")
                else:
                    self.no_arms_status_label.setText("❌ No Arms Fix: Inactive")
                    self.no_arms_status_label.setStyleSheet("color: #F44336;")
            else:
                self.no_arms_status_label.setText("⚠️ No Arms Fix: Error checking status")
                self.no_arms_status_label.setStyleSheet("color: #FF9800;")
                
        except Exception as e:
            self.skybox_status_label.setText("⚠️ Skybox Fix: Error loading status")
            self.skybox_status_label.setStyleSheet("color: #FF9800;")
            self.no_arms_status_label.setText("⚠️ No Arms Fix: Error loading status")
            self.no_arms_status_label.setStyleSheet("color: #FF9800;")


class ModificationsTab(QWidget):
    """Tab 3 - Skybox and Texture modifications"""
    
    def __init__(self):
        super().__init__()
        self.current_client = "Roblox"
        self.init_ui()
        self.load_skybox_list()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title
        title = QLabel("Modifications")
        title.setObjectName("tabTitle")
        layout.addWidget(title)
        
        # Client selector
        client_layout = QHBoxLayout()
        client_layout.setSpacing(12)
        target_label = QLabel("Target Client:")
        target_label.setMinimumWidth(100)
        client_layout.addWidget(target_label)
        self.client_combo = QComboBox()
        self.client_combo.addItems(["Roblox", "Bloxstrap", "Fishstrap"])
        self.client_combo.setObjectName("comboBox")
        self.client_combo.currentTextChanged.connect(self.on_client_changed)
        self.client_combo.setMinimumWidth(180)
        client_layout.addWidget(self.client_combo)
        client_layout.addStretch()
        layout.addLayout(client_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left side - Skybox selection
        skybox_group = QGroupBox("Skybox Selection")
        skybox_group.setObjectName("groupBox")
        skybox_layout = QVBoxLayout()
        skybox_layout.setSpacing(12)
        skybox_layout.setContentsMargins(16, 24, 16, 16)
        
        # Search bar for skybox filtering
        search_label = QLabel("Search Skyboxes:")
        search_label.setObjectName("controlLabel")
        skybox_layout.addWidget(search_label)
        
        self.skybox_search = QLineEdit()
        self.skybox_search.setObjectName("lineEdit")
        self.skybox_search.setPlaceholderText("Type to search skyboxes...")
        self.skybox_search.textChanged.connect(self.filter_skybox_list)
        skybox_layout.addWidget(self.skybox_search)
        
        # Skybox count label
        self.skybox_count_label = QLabel("Loading skyboxes...")
        self.skybox_count_label.setObjectName("infoLabel")
        skybox_layout.addWidget(self.skybox_count_label)
        
        self.skybox_list = QListWidget()
        self.skybox_list.setObjectName("listWidget")
        self.skybox_list.itemClicked.connect(self.on_skybox_selected)
        self.skybox_list.setMinimumHeight(300)
        skybox_layout.addWidget(self.skybox_list)
        
        # Custom skybox button
        self.custom_skybox_btn = ModernButton("Load Custom Skybox")
        self.custom_skybox_btn.setObjectName("secondaryButton")
        self.custom_skybox_btn.clicked.connect(self.load_custom_skybox)
        skybox_layout.addWidget(self.custom_skybox_btn)
        
        skybox_group.setLayout(skybox_layout)
        content_layout.addWidget(skybox_group, 1)
        
        # Right side - Preview and controls
        preview_group = QGroupBox("Preview & Controls")
        preview_group.setObjectName("groupBox")
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(16)
        preview_layout.setContentsMargins(16, 24, 16, 16)
        
        # Preview image
        self.preview_label = QLabel("Select a skybox to preview")
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setMinimumSize(320, 220)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel#previewLabel {
                border: 2px solid rgba(168, 85, 247, 0.4);
                border-radius: 8px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                           stop: 0 rgba(168, 85, 247, 0.05), 
                                           stop: 1 rgba(139, 92, 246, 0.1));
                font-size: 13px;
                font-weight: 500;
                color: #A855F7;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        
        # Progress bar for downloads
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modernProgressBar")
        self.progress_bar.setVisible(False)  # Hidden by default
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        preview_layout.addWidget(self.progress_bar)
        
        # Progress status label
        self.progress_status = QLabel("")
        self.progress_status.setObjectName("progressStatus")
        self.progress_status.setVisible(False)  # Hidden by default
        self.progress_status.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.progress_status)
        
        # Skybox controls
        skybox_controls = QHBoxLayout()
        skybox_controls.setSpacing(10)
        self.apply_skybox_btn = ModernButton("Apply Skybox")
        self.apply_skybox_btn.setObjectName("primaryButton")
        self.apply_skybox_btn.clicked.connect(self.apply_selected_skybox)
        skybox_controls.addWidget(self.apply_skybox_btn)
        
        self.default_skybox_btn = ModernButton("Default Sky")
        self.default_skybox_btn.setObjectName("secondaryButton")
        self.default_skybox_btn.clicked.connect(self.apply_default_skybox)
        skybox_controls.addWidget(self.default_skybox_btn)
        
        preview_layout.addLayout(skybox_controls)
        
        # Texture controls
        texture_group = QGroupBox("Textures")
        texture_group.setObjectName("groupBox")
        texture_layout = QVBoxLayout()
        texture_layout.setSpacing(12)
        texture_layout.setContentsMargins(12, 20, 12, 12)
        
        texture_controls = QHBoxLayout()
        texture_controls.setSpacing(10)
        self.dark_texture_btn = ModernButton("Dark")
        self.dark_texture_btn.setObjectName("secondaryButton")
        self.dark_texture_btn.clicked.connect(lambda: self.apply_texture(apply_dark_textures))
        texture_controls.addWidget(self.dark_texture_btn)
        
        self.light_texture_btn = ModernButton("Default (exclude sky)")
        self.light_texture_btn.setObjectName("secondaryButton")
        self.light_texture_btn.clicked.connect(lambda: self.apply_texture(apply_light_textures))
        texture_controls.addWidget(self.light_texture_btn)
        
        self.default_texture_btn = ModernButton("Default (include sky)")
        self.default_texture_btn.setObjectName("secondaryButton")
        self.default_texture_btn.clicked.connect(lambda: self.apply_texture(apply_default_textures))
        texture_controls.addWidget(self.default_texture_btn)
        
        texture_layout.addLayout(texture_controls)
        texture_group.setLayout(texture_layout)
        
        preview_layout.addWidget(texture_group)
        preview_group.setLayout(preview_layout)
        content_layout.addWidget(preview_group, 1)
        
        layout.addLayout(content_layout)
        self.setLayout(layout)
        
    def on_client_changed(self):
        """Handle client selection change"""
        self.current_client = self.client_combo.currentText()
        
    def load_skybox_list(self):
        """Load available skyboxes"""
        try:
            skyboxes = make_skyname_list()
            self.all_skyboxes = sorted(skyboxes)  # Store all skyboxes for filtering
            self.update_skybox_display()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not load skybox list: {str(e)}")
            self.all_skyboxes = []
            
    def update_skybox_display(self):
        """Update the skybox list display based on current filter"""
        self.skybox_list.clear()
        
        # Get current search text
        search_text = getattr(self, 'skybox_search', None)
        filter_text = search_text.text().lower() if search_text else ""
        
        # Filter skyboxes based on search text
        if filter_text:
            filtered_skyboxes = [
                skybox for skybox in self.all_skyboxes 
                if filter_text in skybox.lower()
            ]
        else:
            filtered_skyboxes = self.all_skyboxes
        
        # Add filtered skyboxes to list
        for skybox in filtered_skyboxes:
            self.skybox_list.addItem(skybox)
            
        # Update count label if we have one
        count_text = f"Showing {len(filtered_skyboxes)} of {len(self.all_skyboxes)} skyboxes"
        if hasattr(self, 'skybox_count_label'):
            self.skybox_count_label.setText(count_text)
            
    def filter_skybox_list(self):
        """Filter skybox list based on search text"""
        self.update_skybox_display()
            
    def on_skybox_selected(self, item):
        """Handle skybox selection"""
        skybox_name = item.text()
        try:
            preview_path = get_sky_preview(skybox_name)
            if preview_path and os.path.exists(preview_path):
                pixmap = QPixmap(preview_path)
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText(f"Preview not available for {skybox_name}")
        except Exception as e:
            self.preview_label.setText(f"Error loading preview: {str(e)}")
            
    def load_custom_skybox(self):
        """Load a custom skybox folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Custom Skybox Folder")
        if folder:
            # Add to list with [Custom] prefix
            custom_name = f"[Custom] {os.path.basename(folder)}"
            self.skybox_list.addItem(custom_name)
            # Store the path for later use
            if not hasattr(self, 'custom_skyboxes'):
                self.custom_skyboxes = {}
            self.custom_skyboxes[custom_name] = folder
            
    def apply_selected_skybox(self):
        """Apply the selected skybox"""
        current_item = self.skybox_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a skybox first")
            return
            
        skybox_name = current_item.text()
        
        # Start background operation
        if skybox_name.startswith("[Custom]"):
            # Handle custom skybox
            if hasattr(self, 'custom_skyboxes') and skybox_name in self.custom_skyboxes:
                folder_path = self.custom_skyboxes[skybox_name]
                # Apply custom skybox logic here
                QMessageBox.information(self, "Info", "Custom skybox application not implemented yet")
            else:
                QMessageBox.warning(self, "Error", "Custom skybox path not found")
        else:
            # Check if skybox exists locally first
            from src.skybox import cdbl_skybox_skys_path
            import os
            
            sky_name_clean = skybox_name.replace(" ", "")
            sky_source_path = os.path.join(cdbl_skybox_skys_path, sky_name_clean)
            
            if not os.path.exists(sky_source_path) or not os.listdir(sky_source_path):
                # Need to download first, show progress bar
                self.show_progress_bar(True)
                self.progress_bar.setValue(0)
                self.progress_status.setText("Preparing download...")
                
                # Start download worker
                self.download_worker = SkyboxDownloadWorker(skybox_name)
                self.download_worker.progress.connect(self.update_progress)
                self.download_worker.finished.connect(self.on_download_finished)
                self.download_worker.error.connect(self.on_download_error)
                self.download_worker.start()
                
                # Disable button during operation
                self.apply_skybox_btn.setEnabled(False)
                self.apply_skybox_btn.setText("Downloading...")
            else:
                # Skybox exists, apply directly
                self.apply_skybox_directly(skybox_name)
    
    def apply_skybox_directly(self, skybox_name):
        """Apply skybox directly without downloading"""
        # Regular skybox
        self.worker = WorkerThread("apply_skybox", self.current_client, skybox_name)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.error.connect(self.on_operation_error)
        self.worker.start()
        
        # Disable button during operation
        self.apply_skybox_btn.setEnabled(False)
        self.apply_skybox_btn.setText("Applying...")
    
    def show_progress_bar(self, show=True):
        """Show or hide the progress bar and status"""
        self.progress_bar.setVisible(show)
        self.progress_status.setVisible(show)
    
    def update_progress(self, percentage, message):
        """Update the progress bar and status"""
        self.progress_bar.setValue(percentage)
        self.progress_status.setText(message)
    
    def on_download_finished(self, message):
        """Handle download completion and then apply skybox"""
        print(message)
        self.show_progress_bar(False)
        
        # Now apply the downloaded skybox
        current_item = self.skybox_list.currentItem()
        if current_item:
            skybox_name = current_item.text()
            self.apply_skybox_directly(skybox_name)
        else:
            # Re-enable button if no item selected
            self.apply_skybox_btn.setEnabled(True)
            self.apply_skybox_btn.setText("Apply Skybox")
    
    def on_download_error(self, error_message):
        """Handle download error"""
        print(f"Download error: {error_message}")
        self.show_progress_bar(False)
        
        # Show error message to user
        QMessageBox.critical(self, "Download Error", f"Failed to download skybox:\n{error_message}")
        
        # Re-enable button
        self.apply_skybox_btn.setEnabled(True)
        self.apply_skybox_btn.setText("Apply Skybox")
            
    def apply_default_skybox(self):
        """Apply default skybox"""
        try:
            result = apply_default_sky(self.current_client)
            if result:
                QMessageBox.information(self, "Success", "Default skybox applied successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to apply default skybox")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying default skybox: {str(e)}")
            
    def apply_texture(self, texture_func):
        """Apply texture using background thread"""
        self.worker = WorkerThread("apply_texture", texture_func, self.current_client)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.error.connect(self.on_operation_error)
        self.worker.start()
        
    def on_operation_finished(self, message):
        """Handle successful operation completion"""
        # Check if this was a skybox operation
        if hasattr(self, 'worker') and self.worker.operation == "apply_skybox":
            # Show success message first
            QMessageBox.information(self, "Success", message)
            
            # Then show skybox fix reminder
            reply = QMessageBox.question(self, "Skybox Fix Recommended", 
                "Skybox applied successfully!\n\n"
                "For best results, it's recommended to apply the Skybox Fix from the Tools tab.\n\n"
                "Would you like to go to the Tools tab now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes)
            
            if reply == QMessageBox.StandardButton.Yes:
                # Switch to Tools tab (index 3) - access parent's tab_widget
                parent = self.parent()
                while parent is not None:
                    if hasattr(parent, 'tab_widget'):
                        parent.tab_widget.setCurrentIndex(3)
                        break
                    parent = parent.parent()
        else:
            # For non-skybox operations, just show the regular success message
            QMessageBox.information(self, "Success", message)
        
        self.apply_skybox_btn.setEnabled(True)
        self.apply_skybox_btn.setText("Apply Skybox")
        
    def on_operation_error(self, error_message):
        """Handle operation error"""
        QMessageBox.critical(self, "Error", error_message)
        self.apply_skybox_btn.setEnabled(True)
        self.apply_skybox_btn.setText("Apply Skybox")


class FastFlagsDialog(QDialog):
    """Popup dialog for editing FastFlags JSON"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FastFlags Editor")
        self.setModal(True)
        self.resize(700, 500)
        self.init_ui()
        self.apply_dialog_styles()
        
        # Auto-load current FastFlags on open
        self.auto_load_current_fastflags()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title and description
        title = QLabel("FastFlags JSON Editor")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        
        desc = QLabel(
            "Edit FastFlags in JSON format. You can copy from Bloxstrap or enter custom ones.\n"
            "Changes will be applied directly to Roblox IxpSettings.json."
        )
        desc.setWordWrap(True)
        desc.setObjectName("aboutText")
        layout.addWidget(desc)
        
        # JSON Editor
        editor_label = QLabel("FastFlags JSON:")
        editor_label.setObjectName("settingLabel")
        layout.addWidget(editor_label)
        
        self.fastflags_editor = QTextEdit()
        self.fastflags_editor.setObjectName("jsonEditor")
        self.fastflags_editor.setMinimumHeight(250)
        self.fastflags_editor.setPlaceholderText('{\n    "DFIntMaxFrameRate": "999",\n    "FFlagRenderD3D11": "True",\n    "DFFlagTextureQualityOverrideValue": "0"\n}')
        layout.addWidget(self.fastflags_editor)
        
        # Load current button
        presets_label = QLabel("Current FastFlags:")
        presets_label.setObjectName("settingLabel")
        layout.addWidget(presets_label)
        
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(12)
        
        load_current_btn = ModernButton("Load Current")
        load_current_btn.setObjectName("secondaryButton")
        load_current_btn.clicked.connect(self.load_current_fastflags)
        presets_layout.addWidget(load_current_btn)
        
        presets_layout.addStretch()
        layout.addLayout(presets_layout)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        validate_btn = ModernButton("Validate JSON")
        validate_btn.setObjectName("secondaryButton")
        validate_btn.clicked.connect(self.validate_fastflags_json)
        buttons_layout.addWidget(validate_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = ModernButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        self.apply_btn = ModernButton("Apply FastFlags")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self.apply_fastflags)
        buttons_layout.addWidget(self.apply_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def apply_dialog_styles(self):
        """Apply styles specific to the dialog"""
        self.setStyleSheet("""
        QDialog {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #1a1a1a, stop: 1 #2d1b3d);
            color: #ffffff;
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 12px;
        }
        
        QLabel#dialogTitle {
            color: #A855F7;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        """)
    
    def load_current_fastflags(self):
        """Load current CDBL fastflags"""
        try:
            from src.fastflags import get_applied_fastflags
            result = get_applied_fastflags()
            if result["success"] and result["applied_flags"]:
                self.fastflags_editor.setPlainText(json.dumps(result["applied_flags"], indent=4))
                QMessageBox.information(self, "Loaded", f"Loaded {result['count']} current fastflags")
            else:
                QMessageBox.information(self, "No FastFlags", "No CDBL fastflags are currently applied")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load current fastflags: {str(e)}")
    
    def auto_load_current_fastflags(self):
        """Automatically load current CDBL fastflags on dialog open (silent)"""
        try:
            from src.fastflags import get_applied_fastflags
            result = get_applied_fastflags()
            if result["success"] and result["applied_flags"]:
                self.fastflags_editor.setPlainText(json.dumps(result["applied_flags"], indent=4))
                # Don't show popup - this is automatic loading
            else:
                # If no flags exist, show placeholder text
                self.fastflags_editor.setPlainText('{\n    "DFIntMaxFrameRate": "999",\n    "FFlagRenderD3D11": "True"\n}')
        except Exception:
            # On any error, just show placeholder - don't popup error messages
            self.fastflags_editor.setPlainText('{\n    "DFIntMaxFrameRate": "999",\n    "FFlagRenderD3D11": "True"\n}')
    
    def validate_fastflags_json(self):
        """Validate JSON syntax"""
        try:
            text = self.fastflags_editor.toPlainText().strip()
            if not text:
                QMessageBox.information(self, "Empty", "JSON editor is empty")
                return
            
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                QMessageBox.warning(self, "Invalid", "JSON must be an object/dictionary")
                return
            
            flag_count = len(parsed)
            QMessageBox.information(self, "Valid JSON", f"JSON is valid with {flag_count} fastflags")
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"JSON syntax error:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Validation error: {str(e)}")
    
    def apply_fastflags(self):
        """Apply the fastflags and close dialog"""
        try:
            text = self.fastflags_editor.toPlainText().strip()
            if not text:
                QMessageBox.warning(self, "Empty", "Please enter fastflags JSON first")
                return
            
            # Parse JSON
            try:
                fastflags = json.loads(text)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON syntax error:\n{str(e)}")
                return
            
            if not isinstance(fastflags, dict):
                QMessageBox.warning(self, "Invalid", "JSON must be an object/dictionary")
                return
            
            if not fastflags:
                QMessageBox.warning(self, "Empty", "No fastflags found in JSON")
                return
            
            # Apply fastflags
            self.apply_btn.setEnabled(False)
            self.apply_btn.setText("Applying...")
            
            from src.fastflags import apply_fastflags
            result = apply_fastflags(fastflags)
            
            if result["success"]:
                QMessageBox.information(self, "Success", f"{result['message']}\n\nApplied {result['applied_flags']} fastflags")
                self.accept()  # Close dialog on success
            else:
                QMessageBox.warning(self, "Error", result["message"])
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply fastflags: {str(e)}")
        finally:
            self.apply_btn.setEnabled(True)
            self.apply_btn.setText("Apply FastFlags")


class ToolsTab(QWidget):
    """Tab 4 - Tools for Roblox (fastflags bypass and skybox fix)"""
    
    def __init__(self):
        super().__init__()
        self.download_worker = None  # Skybox download worker thread
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title
        title = QLabel("Tools")
        title.setObjectName("tabTitle")
        layout.addWidget(title)
        
        # Notice about Roblox only
        notice = QLabel("⚠️ These tools only work with regular Roblox client")
        notice.setObjectName("warningLabel")
        notice.setAlignment(Qt.AlignCenter)
        layout.addWidget(notice)
        
        # Fastflags Bypass section
        fastflags_group = QGroupBox("FastFlags Bypass")
        fastflags_group.setObjectName("groupBox")
        fastflags_layout = QVBoxLayout()
        fastflags_layout.setSpacing(16)
        fastflags_layout.setContentsMargins(24, 32, 24, 24)
        
        fastflags_desc = QLabel(
            "Apply performance and FPS unlock fastflags directly to Roblox IxpSettings.json.\n"
            "Use the editor to paste FastFlags from Bloxstrap or create custom configurations."
        )
        fastflags_desc.setWordWrap(True)
        fastflags_desc.setObjectName("aboutText")
        fastflags_layout.addWidget(fastflags_desc)
        
        # FastFlags buttons
        fastflags_buttons = QHBoxLayout()
        fastflags_buttons.setSpacing(15)
        
        self.open_editor_btn = ModernButton("Open FastFlags Editor")
        self.open_editor_btn.setObjectName("primaryButton")
        self.open_editor_btn.setFixedWidth(250)  # Fixed width to prevent text cutoff
        self.open_editor_btn.clicked.connect(self.open_fastflags_editor)
        fastflags_buttons.addWidget(self.open_editor_btn)
        
        self.remove_fastflags_btn = ModernButton("Remove All FastFlags")
        self.remove_fastflags_btn.setObjectName("dangerButton")
        self.remove_fastflags_btn.setFixedWidth(250)  # Fixed width to prevent text cutoff
        self.remove_fastflags_btn.clicked.connect(self.remove_all_fastflags)
        fastflags_buttons.addWidget(self.remove_fastflags_btn)
        
        fastflags_buttons.addStretch()
        fastflags_layout.addLayout(fastflags_buttons)
        fastflags_group.setLayout(fastflags_layout)
        layout.addWidget(fastflags_group)
        
        # Skybox Fix section
        skybox_group = QGroupBox("Skybox Fix")
        skybox_group.setObjectName("groupBox")
        skybox_layout = QVBoxLayout()
        skybox_layout.setSpacing(16)
        skybox_layout.setContentsMargins(24, 32, 24, 24)
        
        skybox_desc = QLabel(
            "Download and apply skybox fixes by swapping cached assets and applying fastflags.\n"
            "This fixes skybox rendering issues in certain Roblox games."
        )
        skybox_desc.setWordWrap(True)
        skybox_desc.setObjectName("aboutText")
        skybox_layout.addWidget(skybox_desc)
        
        # Cache info
        self.cache_info_label = QLabel("Cache: Not loaded")
        self.cache_info_label.setObjectName("statusLabel")
        skybox_layout.addWidget(self.cache_info_label)
        
        # Progress bar (initially hidden)
        self.download_progress = QProgressBar()
        self.download_progress.setObjectName("progressBar")
        self.download_progress.setVisible(False)
        self.download_progress.setTextVisible(True)
        skybox_layout.addWidget(self.download_progress)
        
        # Progress status label
        self.progress_status_label = QLabel("")
        self.progress_status_label.setObjectName("statusLabel")
        self.progress_status_label.setVisible(False)
        skybox_layout.addWidget(self.progress_status_label)
        
        # Skybox buttons
        skybox_buttons = QHBoxLayout()
        skybox_buttons.setSpacing(15)
        
        self.apply_skybox_fix_btn = ModernButton("Apply Skybox Fix")
        self.apply_skybox_fix_btn.setObjectName("primaryButton")
        self.apply_skybox_fix_btn.clicked.connect(self.apply_skybox_fix)
        skybox_buttons.addWidget(self.apply_skybox_fix_btn)
        
        skybox_buttons.addStretch()
        skybox_layout.addLayout(skybox_buttons)
        skybox_group.setLayout(skybox_layout)
        layout.addWidget(skybox_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Update cache info on load
        self.update_cache_info()
        
    def update_cache_info(self):
        """Update cache information display"""
        try:
            cache_info = get_cache_info()
            if cache_info["assets_json_exists"] and cache_info["extracted_assets_count"] > 0:
                self.cache_info_label.setText(
                    f"Cache: {cache_info['extracted_assets_count']} assets ready for swapping"
                )
                self.cache_info_label.setStyleSheet("color: #10B981;")
            elif cache_info["assets_json_exists"]:
                self.cache_info_label.setText("Cache: Assets.json ready, no extracted files")
                self.cache_info_label.setStyleSheet("color: #F59E0B;")
            else:
                self.cache_info_label.setText("Cache: No assets downloaded")
                self.cache_info_label.setStyleSheet("color: #EF4444;")
        except Exception:
            self.cache_info_label.setText("Cache: Error reading cache")
            self.cache_info_label.setStyleSheet("color: #EF4444;")
    
    def open_fastflags_editor(self):
        """Open the FastFlags editor dialog"""
        dialog = FastFlagsDialog(self)
        dialog.exec()
    
    def remove_all_fastflags(self):
        """Remove all CDBL fastflags including skybox fix"""
        reply = QMessageBox.question(
            self, 
            "Remove FastFlags", 
            "Are you sure you want to remove all CDBL fastflags?\n\nThis includes the skybox fix FastFlag and will restore the original IxpSettings.json state.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from src.fastflags import remove_fastflags, remove_skybox_fastflag, is_skybox_fix_active
                
                # Check if skybox fix is active and remove it properly
                skybox_status = is_skybox_fix_active()
                skybox_removed = False
                
                if skybox_status["success"] and skybox_status["active"]:
                    skybox_result = remove_skybox_fastflag()
                    if skybox_result["success"]:
                        skybox_removed = True
                
                # Remove any other CDBL fastflags
                result = remove_fastflags()
                
                # Report results
                if result["success"] or skybox_removed:
                    removed_count = result.get("removed_flags", 0)
                    if skybox_removed:
                        removed_count += 1
                    
                    if removed_count > 0:
                        message = f"Successfully removed {removed_count} CDBL fastflags"
                        if skybox_removed:
                            message += " (including skybox fix)"
                        QMessageBox.information(self, "Success", message)
                    else:
                        QMessageBox.information(self, "No FastFlags", "No CDBL fastflags were found to remove")
                else:
                    QMessageBox.warning(self, "Error", result["message"])
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove fastflags: {str(e)}")
    
    def apply_skybox_fix(self):
        """Apply skybox fix with FLEASION_FLAG and asset swapping"""
        self.apply_skybox_fix_btn.setEnabled(False)
        self.apply_skybox_fix_btn.setText("Applying...")
        
        try:
            from src.assets import swap_asset
            from src.fastflags import apply_skybox_fastflag
            
            # First apply the skybox fix FastFlag
            flag_result = apply_skybox_fastflag()
            
            if not flag_result["success"]:
                QMessageBox.warning(self, "Error", f"Failed to apply skybox FastFlag: {flag_result['message']}")
                return
            
            # Define assets to swap with replacement
            assets_to_swap = [
                'fa556eefa6748fc43e732b3e617e8921',
                'c2377e4ff38043c6e433d73d6e75cfeb', 
                '43da220df9e120f7e9aef3498b64e4dd',
                '41a30c95746b3f2c2209cc5043deea0f',
                '15115b83e512f17ae963dbb942fc8b01',
                '1041bfb5a03c1861ccd4c1c513812e82'
            ]
            replacement_hash = '75205be5a167842c7ed931d9d5a904ca'
            
            success_count = 0
            failed_swaps = []
            
            for asset_hash in assets_to_swap:
                result = swap_asset(asset_hash, replacement_hash)
                if result["success"]:
                    success_count += 1
                else:
                    failed_swaps.append(f"{asset_hash}: {result['message']}")
            
            # Report results
            if success_count == len(assets_to_swap):
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Skybox fix applied successfully!\n\n"
                    f"• Skybox FastFlag applied\n"
                    f"• {success_count} assets swapped\n\n"
                    f"Restart Roblox for changes to take effect."
                )
            elif success_count > 0:
                failed_msg = "\n".join(failed_swaps[:3])  # Show first 3 failures
                if len(failed_swaps) > 3:
                    failed_msg += f"\n... and {len(failed_swaps) - 3} more"
                
                QMessageBox.warning(
                    self,
                    "Partial Success",
                    f"Skybox fix partially applied:\n\n"
                    f"• Skybox FastFlag applied\n"
                    f"• {success_count}/{len(assets_to_swap)} assets swapped\n\n"
                    f"Failed swaps:\n{failed_msg}"
                )
            else:
                failed_msg = "\n".join(failed_swaps[:5])  # Show first 5 failures
                QMessageBox.critical(
                    self,
                    "Failed",
                    f"Skybox fix failed:\n\n"
                    f"• Skybox FastFlag applied\n"
                    f"• No assets could be swapped\n\n"
                    f"Errors:\n{failed_msg}"
                )
            
            self.update_cache_info()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply skybox fix: {str(e)}")
        finally:
            self.apply_skybox_fix_btn.setEnabled(True)
            self.apply_skybox_fix_btn.setText("Apply Skybox Fix")


class PremiumTab(QWidget):
    """Tab 5 - Premium features with license verification"""
    
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.is_verified = False
        self.license_key = None
        
        # API URL for EGate - UPDATE THIS WITH YOUR DEPLOYMENT URL
        self.api_url = "https://key-sys-web.vercel.app/api"
        
        # Audio preview state
        self.temp_files = []
        self.current_audio_worker = None
        self.current_audio_thread = None
        self.is_playing = False
        self.preview_volume = 0.2  # Default quiet volume (20%)
        
        self.init_ui()
        
        # Try to load and verify saved license key
        self.load_saved_license()
        
    def init_ui(self):
        """Initialize the UI - will show either license input or premium features"""
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_container = QWidget()
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(40, 40, 40, 20)
        title = QLabel("Premium Features")
        title.setObjectName("tabTitle")
        title_layout.addWidget(title)
        title_container.setLayout(title_layout)
        self.main_layout.addWidget(title_container)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for dynamic content (license input or premium features)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        self.content_layout.setContentsMargins(40, 0, 40, 40)
        self.content_widget.setLayout(self.content_layout)
        
        scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(scroll_area)
        
        self.setLayout(self.main_layout)
        
        # Show license input by default
        self.show_license_input()
    
    def load_saved_license(self):
        """Load and verify saved license key on startup"""
        from src.first_run import get_license_key
        
        saved_key = get_license_key()
        if saved_key:
            # Verify the saved key
            self.verify_license_key(saved_key, silent=True)
    
    def show_license_input(self):
        """Show license key input UI"""
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # License input group
        license_group = QGroupBox("License Activation")
        license_group.setObjectName("settingsGroup")
        license_layout = QVBoxLayout()
        license_layout.setSpacing(20)
        
        # Description
        description = QLabel(
            "Enter your CDBL Premium license key to unlock exclusive features:\n\n"
            "• No Arms Modification\n"
            "• Exclusive Skyboxes (Coming Soon)\n"
            "• Custom Sounds\n"
            "• And More!\n\n"
            "Your license will be bound to this device."
        )
        description.setObjectName("settingsDescription")
        description.setWordWrap(True)
        license_layout.addWidget(description)
        
        # License key input
        input_layout = QHBoxLayout()
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Enter your license key (e.g., ABCD-1234-EFGH-5678)")
        self.license_input.setObjectName("modernInput")
        self.license_input.setMinimumHeight(40)
        input_layout.addWidget(self.license_input)
        
        # Submit button
        self.submit_btn = ModernButton("Activate License")
        self.submit_btn.setObjectName("primaryButton")
        self.submit_btn.setFixedWidth(180)
        self.submit_btn.clicked.connect(self.on_submit_license)
        input_layout.addWidget(self.submit_btn)
        
        license_layout.addLayout(input_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        license_layout.addWidget(self.status_label)
        
        license_group.setLayout(license_layout)
        self.content_layout.addWidget(license_group)
        
        # Add some help text
        help_group = QGroupBox("Need Help?")
        help_group.setObjectName("settingsGroup")
        help_layout = QVBoxLayout()
        
        help_text = QLabel(
            "Don't have a license key?\n"
            "You can purchase a Premium key from: "
        )
        help_text.setObjectName("settingsDescription")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        
        # Clickable link
        shop_link = QLabel('<a href="https://emanshop.mysellauth.com/" style="color: #A855F7;">https://emanshop.mysellauth.com/</a>')
        shop_link.setOpenExternalLinks(True)
        shop_link.setObjectName("settingsDescription")
        help_layout.addWidget(shop_link)
        
        help_text2 = QLabel(
            "\nHaving issues activating your license?\n"
            "• Make sure you're connected to the internet\n"
            "• Check that your license key is correct\n"
            "• Each license can only be activated on one device"
        )
        help_text2.setObjectName("settingsDescription")
        help_text2.setWordWrap(True)
        help_layout.addWidget(help_text2)
        
        help_group.setLayout(help_layout)
        self.content_layout.addWidget(help_group)
    
    def show_premium_features(self):
        """Show premium features UI when license is verified"""
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # License status banner - Compact
        status_group = QGroupBox()
        status_group.setObjectName("settingsGroup")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(15, 10, 15, 10)
        
        status_text = QLabel(f"✅ Premium Active • {self.license_key[:12]}...{self.license_key[-4:]}")
        status_text.setObjectName("successText")
        status_layout.addWidget(status_text)
        
        status_layout.addStretch()
        
        # Deactivate button
        deactivate_btn = ModernButton("Deactivate")
        deactivate_btn.setObjectName("dangerButton")
        deactivate_btn.setFixedWidth(100)
        deactivate_btn.clicked.connect(self.deactivate_license)
        status_layout.addWidget(deactivate_btn)
        
        status_group.setLayout(status_layout)
        self.content_layout.addWidget(status_group)
        
        # No Arms Feature - Compact
        no_arms_group = QGroupBox("No Arms Modification")
        no_arms_group.setObjectName("settingsGroup")
        no_arms_layout = QVBoxLayout()
        no_arms_layout.setSpacing(10)
        
        # Button layout - horizontal compact
        button_layout = QHBoxLayout()
        
        # Apply No Arms button
        self.apply_no_arms_btn = ModernButton("✓ Apply")
        self.apply_no_arms_btn.setObjectName("primaryButton")
        self.apply_no_arms_btn.setFixedWidth(120)
        self.apply_no_arms_btn.clicked.connect(self.apply_no_arms)
        button_layout.addWidget(self.apply_no_arms_btn)
        
        # Remove No Arms button
        self.remove_no_arms_btn = ModernButton("✕ Remove")
        self.remove_no_arms_btn.setObjectName("dangerButton")
        self.remove_no_arms_btn.setFixedWidth(120)
        self.remove_no_arms_btn.clicked.connect(self.remove_no_arms)
        button_layout.addWidget(self.remove_no_arms_btn)
        
        # Description inline
        description = QLabel("Removes character arms visibility")
        description.setObjectName("settingsDescription")
        button_layout.addWidget(description)
        button_layout.addStretch()
        
        no_arms_layout.addLayout(button_layout)
        
        no_arms_group.setLayout(no_arms_layout)
        self.content_layout.addWidget(no_arms_group)
        
        # Sound Swapper Feature
        sound_swapper_group = QGroupBox("Sound Swapper")
        sound_swapper_group.setObjectName("settingsGroup")
        sound_swapper_layout = QVBoxLayout()
        sound_swapper_layout.setSpacing(12)
        
        # Side-by-side lists layout
        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(15)
        lists_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Left side - Target sounds to replace
        target_layout = QVBoxLayout()
        target_layout.setSpacing(8)
        target_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        target_label = QLabel("🎯 Target Sound")
        target_label.setObjectName("settingsLabel")
        target_label.setFixedHeight(25)
        target_layout.addWidget(target_label)
        
        # Category selector
        self.target_category_combo = QComboBox()
        self.target_category_combo.setObjectName("comboBox")
        self.target_category_combo.addItems(['Default Gun Sounds', 'Hit Sounds', 'Skin Sounds'])
        self.target_category_combo.currentTextChanged.connect(self.on_target_category_changed)
        self.target_category_combo.setFixedHeight(32)
        target_layout.addWidget(self.target_category_combo)
        
        # Search bar for target
        self.target_search = QLineEdit()
        self.target_search.setPlaceholderText("🔍 Search target sounds...")
        self.target_search.textChanged.connect(self.filter_target_sounds)
        self.target_search.setFixedHeight(32)
        target_layout.addWidget(self.target_search)
        
        # Sound list
        self.target_sound_list = QListWidget()
        self.target_sound_list.setFixedHeight(300)
        self.target_sound_list.setAlternatingRowColors(False)  # Disable system alternating colors
        self.target_sound_list.setStyleSheet("""
            QListWidget {
                background: rgba(30, 30, 30, 0.9);
                border: 1px solid rgba(168, 85, 247, 0.3);
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                margin: 1px;
                color: #ffffff;
                background: rgba(35, 35, 35, 0.9);
            }
            QListWidget::item:selected {
                background: rgba(168, 85, 247, 0.5);
                color: #ffffff;
                font-weight: 600;
            }
            QListWidget::item:hover {
                background: rgba(168, 85, 247, 0.3);
                color: #ffffff;
            }
        """)
        target_layout.addWidget(self.target_sound_list)
        
        # Add Restore Selected button
        self.restore_selected_btn = QPushButton("Restore Selected")
        self.restore_selected_btn.setFixedHeight(35)
        self.restore_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5aa3f0;
            }
            QPushButton:pressed {
                background-color: #3a7bc8;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.restore_selected_btn.clicked.connect(self.restore_selected_sound)
        target_layout.addWidget(self.restore_selected_btn)
        
        # Add spacer to match preview buttons height on the right side
        target_spacer = QWidget()
        target_spacer.setFixedHeight(5)  # Reduced height since we added button
        target_layout.addWidget(target_spacer)
        
        lists_layout.addLayout(target_layout, 1)
        
        # Right side - Replacement sounds
        replacement_layout = QVBoxLayout()
        replacement_layout.setSpacing(8)
        replacement_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        replacement_label = QLabel("🔄 Replacement Sound")
        replacement_label.setObjectName("settingsLabel")
        replacement_label.setFixedHeight(25)
        replacement_layout.addWidget(replacement_label)
        
        # Category selector
        self.replacement_category_combo = QComboBox()
        self.replacement_category_combo.setObjectName("comboBox")
        self.replacement_category_combo.addItems(['Gun Sounds', 'Hit Sounds', 'Kill Sounds'])
        self.replacement_category_combo.currentTextChanged.connect(self.on_replacement_category_changed)
        self.replacement_category_combo.setFixedHeight(32)
        replacement_layout.addWidget(self.replacement_category_combo)
        
        # Search bar for replacement
        self.replacement_search = QLineEdit()
        self.replacement_search.setPlaceholderText("🔍 Search replacement sounds...")
        self.replacement_search.textChanged.connect(self.filter_replacement_sounds)
        self.replacement_search.setFixedHeight(32)
        replacement_layout.addWidget(self.replacement_search)
        
        # Sound list
        self.replacement_sound_list = QListWidget()
        self.replacement_sound_list.setFixedHeight(300)
        self.replacement_sound_list.setAlternatingRowColors(False)  # Disable system alternating colors
        self.replacement_sound_list.setStyleSheet("""
            QListWidget {
                background: rgba(30, 30, 30, 0.9);
                border: 1px solid rgba(168, 85, 247, 0.3);
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                margin: 1px;
                color: #ffffff;
                background: rgba(35, 35, 35, 0.9);
            }
            QListWidget::item:selected {
                background: rgba(168, 85, 247, 0.5);
                color: #ffffff;
                font-weight: 600;
            }
            QListWidget::item:hover {
                background: rgba(168, 85, 247, 0.3);
                color: #ffffff;
            }
        """)
        replacement_layout.addWidget(self.replacement_sound_list)
        
        
        # Buttons row - Preview and Swap on same line
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_replacement_btn = ModernButton("▶ Preview")
        self.preview_replacement_btn.setObjectName("primaryButton")
        self.preview_replacement_btn.setFixedWidth(100)
        self.preview_replacement_btn.clicked.connect(self.preview_replacement_sound)
        buttons_layout.addWidget(self.preview_replacement_btn)
        
        self.stop_preview_btn = ModernButton("⏹ Stop")
        self.stop_preview_btn.setObjectName("dangerButton")
        self.stop_preview_btn.setFixedWidth(100)
        self.stop_preview_btn.setEnabled(False)
        self.stop_preview_btn.clicked.connect(self.stop_preview)
        buttons_layout.addWidget(self.stop_preview_btn)
        
        buttons_layout.addSpacing(15)
        
        # Volume slider
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(5)
        
        volume_label = QLabel("🔊")
        volume_label.setFixedWidth(20)
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(20)  # Default 20%
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setToolTip("Preview Volume")
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("20%")
        self.volume_label.setFixedWidth(30)
        self.volume_label.setObjectName("settingsDescription")
        volume_layout.addWidget(self.volume_label)
        
        buttons_layout.addLayout(volume_layout)
        buttons_layout.addSpacing(15)
        
        self.swap_sound_btn = ModernButton("🔄 Swap Sounds")
        self.swap_sound_btn.setObjectName("primaryButton")
        self.swap_sound_btn.setFixedWidth(150)
        self.swap_sound_btn.clicked.connect(self.swap_sounds)
        buttons_layout.addWidget(self.swap_sound_btn)
        
        buttons_layout.addStretch()
        
        replacement_layout.addLayout(buttons_layout)
        
        lists_layout.addLayout(replacement_layout, 1)
        
        sound_swapper_layout.addLayout(lists_layout)
        
        # Status text below
        status_layout = QHBoxLayout()
        self.sound_swap_status = QLabel("")
        self.sound_swap_status.setObjectName("settingsDescription")
        self.sound_swap_status.setWordWrap(True)
        status_layout.addWidget(self.sound_swap_status)
        status_layout.addStretch()
        
        sound_swapper_layout.addLayout(status_layout)
        
        sound_swapper_group.setLayout(sound_swapper_layout)
        self.content_layout.addWidget(sound_swapper_group)
        
        # Initialize sound swapper
        try:
            from src.premium import SoundSwapper
            self.sound_swapper = SoundSwapper()  # Uses CDBL cache directory by default
            self.load_sound_categories()
        except Exception as e:
            self.sound_swap_status.setText(f"⚠️ Failed to initialize Sound Swapper: {str(e)}")
            self.sound_swapper = None
    
    def on_submit_license(self):
        """Handle license key submission"""
        license_key = self.license_input.text().strip()
        
        if not license_key:
            self.status_label.setText("❌ Please enter a license key")
            self.status_label.setStyleSheet("color: #ff6b6b;")
            return
        
        self.verify_license_key(license_key, silent=False)
    
    def verify_license_key(self, license_key, silent=False):
        """
        Verify license key with EGate API
        
        Args:
            license_key: The key to verify
            silent: If True, don't show message boxes (for auto-verification on startup)
        """
        # Disable input during verification
        if not silent:
            self.submit_btn.setEnabled(False)
            self.submit_btn.setText("Verifying...")
            self.status_label.setText("🔄 Verifying license key...")
            self.status_label.setStyleSheet("color: #74b9ff;")
        
        try:
            from src.keysys import EGateKeySystem
            
            # Initialize key system
            keysys = EGateKeySystem(self.api_url)
            
            # Verify the key
            result = keysys.verify_key(license_key)
            
            if result["success"]:
                # License is valid!
                self.is_verified = True
                self.license_key = license_key
                
                # Save to config
                from src.first_run import save_license_key
                save_license_key(license_key)
                
                if not silent:
                    # Show success message
                    email = result.get("details", {}).get("email", "N/A")
                    first_use = result.get("details", {}).get("first_use", False)
                    
                    if first_use:
                        QMessageBox.information(
                            self,
                            "License Activated!",
                            f"✅ {result['message']}\n\n"
                            f"Email: {email}\n"
                            f"HWID: {keysys.get_hardware_id()}\n\n"
                            f"Welcome to CDBL Premium!"
                        )
                    else:
                        QMessageBox.information(
                            self,
                            "License Verified!",
                            f"✅ {result['message']}\n\n"
                            f"Email: {email}\n\n"
                            f"Welcome back to CDBL Premium!"
                        )
                
                # Show premium features
                self.show_premium_features()
                
            else:
                # License verification failed
                self.is_verified = False
                self.license_key = None
                
                error_type = result.get("error", "UNKNOWN")
                error_message = result.get("message", "Unknown error")
                
                if not silent:
                    # Show error based on type
                    if error_type == "KEY_NOT_FOUND":
                        QMessageBox.warning(
                            self,
                            "Invalid License",
                            "❌ The license key you entered is invalid.\n\n"
                            "Please check your key and try again."
                        )
                    elif error_type == "NO_EMAIL":
                        QMessageBox.warning(
                            self,
                            "Email Required",
                            "❌ This license key does not have an email bound.\n\n"
                            "Please contact support to bind your email to this license."
                        )
                    elif error_type == "HWID_MISMATCH":
                        QMessageBox.warning(
                            self,
                            "Device Mismatch",
                            "❌ This license is already activated on another device.\n\n"
                            "Each license can only be used on one device.\n"
                            "Contact support to reset your HWID if you've changed devices."
                        )
                    elif error_type == "CONNECTION_ERROR" or error_type == "TIMEOUT":
                        QMessageBox.warning(
                            self,
                            "Connection Error",
                            "❌ Unable to connect to the license server.\n\n"
                            "Please check your internet connection and try again."
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Verification Failed",
                            f"❌ {error_message}\n\n"
                            f"Error type: {error_type}"
                        )
                    
                    self.status_label.setText(f"❌ {error_message}")
                    self.status_label.setStyleSheet("color: #ff6b6b;")
                
        except Exception as e:
            self.is_verified = False
            self.license_key = None
            
            if not silent:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An unexpected error occurred:\n\n{str(e)}"
                )
                self.status_label.setText(f"❌ Error: {str(e)}")
                self.status_label.setStyleSheet("color: #ff6b6b;")
        
        finally:
            if not silent:
                self.submit_btn.setEnabled(True)
                self.submit_btn.setText("Activate License")
    
    def deactivate_license(self):
        """Deactivate the current license"""
        reply = QMessageBox.question(
            self,
            "Deactivate License",
            "Are you sure you want to deactivate your premium license?\n\n"
            "You will need to re-enter your key to access premium features.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from config
            from src.first_run import remove_license_key
            remove_license_key()
            
            # Reset state
            self.is_verified = False
            self.license_key = None
            
            # Show license input again
            self.show_license_input()
            
            QMessageBox.information(
                self,
                "License Deactivated",
                "Your license has been deactivated from this device."
            )
    
    def apply_no_arms(self):
        """Apply no arms fix"""
        self.apply_no_arms_btn.setEnabled(False)
        self.apply_no_arms_btn.setText("Applying...")
        
        try:
            from src.premium import no_arms
            
            result = no_arms()
            
            if result["success"]:
                # Build success message
                assets_swapped = result.get("swapped_assets", 0)
                
                if assets_swapped > 0:
                    QMessageBox.information(
                        self, 
                        "Success", 
                        f"No arms fix applied successfully!\n\n"
                        f"• No arms FastFlag applied\n"
                        f"• {assets_swapped} assets swapped\n\n"
                        f"Restart Roblox for changes to take effect."
                    )
                else:
                    # Partial or FastFlag-only success
                    error_details = ""
                    if result["errors"]:
                        error_details = "\n\nWarnings:\n" + "\n".join(result["errors"][:3])
                    
                    QMessageBox.information(
                        self,
                        "Success",
                        f"{result['message']}{error_details}\n\n"
                        f"Restart Roblox for changes to take effect."
                    )
                
                # Update settings tab status if parent window is available
                if self.parent_window and hasattr(self.parent_window, 'settings_tab'):
                    self.parent_window.settings_tab.update_modification_status()
            else:
                error_details = ""
                if result["errors"]:
                    error_details = "\n\nDetails:\n" + "\n".join(result["errors"][:3])
                
                QMessageBox.warning(
                    self,
                    "Failed", 
                    f"{result['message']}{error_details}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply no arms fix: {str(e)}")
        finally:
            self.apply_no_arms_btn.setEnabled(True)
            self.apply_no_arms_btn.setText("Apply No Arms")
    
    def remove_no_arms(self):
        """Remove no arms fix by deleting asset files"""
        self.remove_no_arms_btn.setEnabled(False)
        self.remove_no_arms_btn.setText("Removing...")
        
        try:
            from src.premium import remove_no_arms
            
            result = remove_no_arms()
            
            if result["success"]:
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"{result['message']}\n\n"
                    f"The FastFlag remains active. Restart Roblox to re-download the original assets."
                )
                
                # Update settings tab status if parent window is available
                if self.parent_window and hasattr(self.parent_window, 'settings_tab'):
                    self.parent_window.settings_tab.update_modification_status()
            else:
                error_details = ""
                if result["errors"]:
                    error_details = "\n\nDetails:\n" + "\n".join(result["errors"][:3])
                
                QMessageBox.warning(
                    self,
                    "Failed", 
                    f"{result['message']}{error_details}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove no arms fix: {str(e)}")
        finally:
            self.remove_no_arms_btn.setEnabled(True)
            self.remove_no_arms_btn.setText("Remove No Arms")
    
    def load_sound_categories(self):
        """Load sound categories when swapper is initialized"""
        if not self.sound_swapper:
            return
        
        try:
            # Load replacement sounds for first category
            self.on_replacement_category_changed()
            # Load target sounds for first category
            self.on_target_category_changed()
        except Exception as e:
            self.sound_swap_status.setText(f"⚠️ Error loading categories: {str(e)}")
    
    def on_replacement_category_changed(self):
        """Handle replacement category change"""
        if not self.sound_swapper:
            return
        
        try:
            category = self.replacement_category_combo.currentText()
            # Map display name to internal name
            category_map = {
                'Gun Sounds': 'gun_sounds',
                'Hit Sounds': 'hit_sounds',
                'Kill Sounds': 'kill_sounds'
            }
            internal_category = category_map.get(category, '')
            
            if internal_category:
                sounds = self.sound_swapper.get_available_sounds(internal_category)
                self.replacement_sounds_full_list = sorted(sounds)
                self.replacement_sound_list.clear()
                self.replacement_sound_list.addItems(self.replacement_sounds_full_list)
                self.replacement_search.clear()
        except Exception as e:
            self.sound_swap_status.setText(f"⚠️ Error loading replacement sounds: {str(e)}")
    
    def on_target_category_changed(self):
        """Handle target category change"""
        if not self.sound_swapper:
            return
        
        try:
            category = self.target_category_combo.currentText()
            # Map display name to internal name
            category_map = {
                'Default Gun Sounds': 'default_gun_sounds',
                'Hit Sounds': 'hitsounds',
                'Skin Sounds': 'rivals_skin_sounds'
            }
            internal_category = category_map.get(category, '')
            
            if internal_category:
                sounds = self.sound_swapper.get_available_sounds(internal_category)
                self.target_sounds_full_list = sorted(sounds)
                self.target_sound_list.clear()
                self.target_sound_list.addItems(self.target_sounds_full_list)
                self.target_search.clear()
        except Exception as e:
            self.sound_swap_status.setText(f"⚠️ Error loading target sounds: {str(e)}")
    
    def filter_target_sounds(self):
        """Filter target sounds list based on search text"""
        if not hasattr(self, 'target_sounds_full_list'):
            return
        
        search_text = self.target_search.text().lower()
        self.target_sound_list.clear()
        
        if not search_text:
            self.target_sound_list.addItems(self.target_sounds_full_list)
        else:
            filtered = [sound for sound in self.target_sounds_full_list if search_text in sound.lower()]
            self.target_sound_list.addItems(filtered)
    
    def filter_replacement_sounds(self):
        """Filter replacement sounds list based on search text"""
        if not hasattr(self, 'replacement_sounds_full_list'):
            return
        
        search_text = self.replacement_search.text().lower()
        self.replacement_sound_list.clear()
        
        if not search_text:
            self.replacement_sound_list.addItems(self.replacement_sounds_full_list)
        else:
            filtered = [sound for sound in self.replacement_sounds_full_list if search_text in sound.lower()]
            self.replacement_sound_list.addItems(filtered)
    
    def extract_ogg_from_roblox_format(self, file_path: str):
        """Extract OGG audio from Roblox format file"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Find OGG header
            ogg_header = b'OggS'
            ogg_start = data.find(ogg_header)
            
            if ogg_start == -1:
                return None
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
            temp_file.write(data[ogg_start:])
            temp_file.close()
            
            self.temp_files.append(temp_file.name)
            return temp_file.name
            
        except Exception as e:
            print(f"Error extracting OGG: {str(e)}")
            return None
    
    def preview_replacement_sound(self):
        """Preview the selected replacement sound"""
        if not PYGAME_AVAILABLE:
            QMessageBox.warning(self, "Audio Preview Unavailable", 
                "pygame is not installed. Install it with: pip install pygame")
            return
        
        replacement_item = self.replacement_sound_list.currentItem()
        if not replacement_item:
            QMessageBox.warning(self, "No Selection", "Please select a replacement sound to preview.")
            return
        
        replacement_sound = replacement_item.text()
        replacement_category_map = {
            'Gun Sounds': 'gun_sounds',
            'Hit Sounds': 'hit_sounds',
            'Kill Sounds': 'kill_sounds'
        }
        
        replacement_category = replacement_category_map.get(self.replacement_category_combo.currentText(), '')
        if not replacement_category:
            QMessageBox.warning(self, "Error", "Invalid category selection!")
            return
        
        try:
            # Get hash for the replacement sound
            if replacement_category in ['gun_sounds', 'hit_sounds', 'kill_sounds']:
                hash_value = self.sound_swapper.get_replacement_sound_hash(replacement_sound, replacement_category)
            else:
                data = self.sound_swapper.get_data(replacement_category)
                hash_value = data.get(replacement_sound) if data else None
            
            if not hash_value:
                QMessageBox.warning(self, "Error", f"Could not find hash for sound: {replacement_sound}")
                return
            
            # Handle list of hashes (use first one)
            if isinstance(hash_value, list):
                hash_value = hash_value[0]
            
            # Get the file path from extracted_assets
            from src.assets import get_assets_cache_path
            cache_path = get_assets_cache_path()
            cached_file = os.path.join(cache_path, 'archives', 'extracted_assets', hash_value)
            
            if not os.path.exists(cached_file):
                QMessageBox.warning(self, "File Not Found", 
                    f"Cached file not found: {hash_value}\n\n"
                    "Make sure you have downloaded the assets.")
                return
            
            # Extract OGG from Roblox format
            ogg_path = self.extract_ogg_from_roblox_format(cached_file)
            if not ogg_path:
                QMessageBox.warning(self, "Error", f"Could not extract audio from file: {hash_value}")
                return
            
            self.play_audio_file(ogg_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to preview sound:\n{str(e)}")
    
    def play_audio_file(self, file_path: str):
        """Play audio file using pygame mixer"""
        try:
            if self.is_playing:
                self.stop_preview()
            
            self.current_audio_thread = QThread()
            self.current_audio_worker = AudioWorker(file_path, self.preview_volume)
            self.current_audio_worker.moveToThread(self.current_audio_thread)
            
            # Connect signals
            self.current_audio_thread.started.connect(self.current_audio_worker.play)
            self.current_audio_worker.finished.connect(self.on_audio_finished)
            self.current_audio_worker.error.connect(self.on_audio_error)
            
            # Update UI state
            self.set_preview_state(True)
            
            # Start playback
            self.current_audio_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error playing audio:\n{str(e)}")
    
    def stop_preview(self):
        """Stop current audio playback"""
        if self.current_audio_worker:
            self.current_audio_worker.stop()
        
        if self.current_audio_thread and self.current_audio_thread.isRunning():
            self.current_audio_thread.quit()
            self.current_audio_thread.wait()
        
        self.set_preview_state(False)
    
    def on_audio_finished(self):
        """Handle audio playback completion"""
        self.set_preview_state(False)
        if self.current_audio_thread:
            self.current_audio_thread.quit()
            self.current_audio_thread.wait()
    
    def on_audio_error(self, error: str):
        """Handle audio playback error"""
        self.set_preview_state(False)
        QMessageBox.warning(self, "Audio Error", f"Audio playback error: {error}")
    
    def set_preview_state(self, playing: bool):
        """Update UI state during preview"""
        self.is_playing = playing
        self.preview_replacement_btn.setEnabled(not playing)
        self.stop_preview_btn.setEnabled(playing)
    
    def on_volume_changed(self, value: int):
        """Handle volume slider change"""
        self.preview_volume = value / 100.0  # Convert to 0.0-1.0 range
        self.volume_label.setText(f"{value}%")
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        self.stop_preview()
        
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass
    
    def swap_sounds(self):
        """Execute sound swap"""
        if not self.sound_swapper:
            QMessageBox.warning(self, "Error", "Sound Swapper not initialized!")
            return
        
        # Get selected items from list widgets
        replacement_item = self.replacement_sound_list.currentItem()
        target_item = self.target_sound_list.currentItem()
        
        if not replacement_item or not target_item:
            QMessageBox.warning(self, "Invalid Selection", 
                "Please select both a replacement sound and a target sound from the lists.")
            return
        
        replacement_sound = replacement_item.text()
        target_sound = target_item.text()
        
        # Get internal category names
        replacement_category_map = {
            'Gun Sounds': 'gun_sounds',
            'Hit Sounds': 'hit_sounds',
            'Kill Sounds': 'kill_sounds'
        }
        target_category_map = {
            'Default Gun Sounds': 'default_gun_sounds',
            'Hit Sounds': 'hitsounds',
            'Skin Sounds': 'rivals_skin_sounds'
        }
        
        replacement_category = replacement_category_map.get(self.replacement_category_combo.currentText(), '')
        target_category = target_category_map.get(self.target_category_combo.currentText(), '')
        
        if not replacement_category or not target_category:
            QMessageBox.warning(self, "Error", "Invalid category selection!")
            return
        
        # Disable button during operation
        self.swap_sound_btn.setEnabled(False)
        self.swap_sound_btn.setText("Swapping...")
        self.sound_swap_status.setText("⏳ Swapping sounds...")
        
        try:
            success, message = self.sound_swapper.replace_sound_by_name(
                replacement_sound=replacement_sound,
                replacement_category=replacement_category,
                default_sound=target_sound,
                default_category=target_category
            )
            
            if success:
                self.sound_swap_status.setText(f"✅ {message}")
                QMessageBox.information(self, "Success", 
                    f"Sound swap completed successfully!\n\n"
                    f"Replacement: {replacement_sound}\n"
                    f"Target: {target_sound}\n\n"
                    f"Changes will take effect the next time the sound plays in Roblox.")
            else:
                self.sound_swap_status.setText(f"❌ {message}")
                QMessageBox.warning(self, "Failed", f"Sound swap failed:\n\n{message}")
                
        except Exception as e:
            error_msg = f"Error swapping sounds: {str(e)}"
            self.sound_swap_status.setText(f"❌ {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            self.swap_sound_btn.setEnabled(True)
            self.swap_sound_btn.setText("🔄 Swap Sounds")

    def restore_selected_sound(self):
        """Restore selected sound to original from archive"""
        if not self.sound_swapper:
            QMessageBox.warning(self, "Error", "Sound Swapper not initialized!")
            return
        
        # Get selected target sound
        target_item = self.target_sound_list.currentItem()
        
        if not target_item:
            QMessageBox.warning(self, "Invalid Selection", 
                "Please select a target sound from the list to restore.")
            return
        
        target_sound = target_item.text()
        
        # Get internal category name
        target_category_map = {
            'Default Gun Sounds': 'default_gun_sounds',
            'Hit Sounds': 'hitsounds',
            'Skin Sounds': 'rivals_skin_sounds'
        }
        
        target_category = target_category_map.get(self.target_category_combo.currentText(), '')
        
        if not target_category:
            QMessageBox.warning(self, "Error", "Invalid category selection!")
            return
        
        # Confirm restoration
        reply = QMessageBox.question(self, "Restore Sound", 
            f"Are you sure you want to restore '{target_sound}' to its original sound?\n\n"
            f"This will replace any custom sound with the original from the archive.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable button during operation
        self.restore_selected_btn.setEnabled(False)
        self.restore_selected_btn.setText("Restoring...")
        
        try:
            # Import and call the restore function from premium.py
            from src.premium import restore_selected_sound
            
            result = restore_selected_sound(target_sound, target_category)
            
            if result["success"]:
                QMessageBox.information(self, "Success", 
                    f"Sound restoration completed successfully!\n\n"
                    f"Restored: {target_sound}\n\n"
                    f"{result['message']}\n\n"
                    f"Changes will take effect the next time the sound plays in Roblox.")
            else:
                QMessageBox.warning(self, "Failed", f"Sound restoration failed:\n\n{result['message']}")
                
        except Exception as e:
            error_msg = f"Error restoring sound: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            self.restore_selected_btn.setEnabled(True)
            self.restore_selected_btn.setText("Restore Selected")


class CustomTitleBar(QWidget):
    """Custom title bar with window controls"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(40)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 0, 8, 0)
        layout.setSpacing(0)
        
        # App title and version
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        app_title = QLabel("CDBL")
        app_title.setObjectName("appTitle")
        title_layout.addWidget(app_title)
        
        version_label = QLabel("v2.0 Beta")
        version_label.setObjectName("versionLabel")
        title_layout.addWidget(version_label)
        
        # Discord button with menu - using QLabel for better icon control
        discord_container = QWidget()
        discord_container.setFixedSize(34, 32)
        discord_container.setCursor(Qt.CursorShape.PointingHandCursor)
        discord_container.setToolTip("Join our Discord servers")
        discord_container.setObjectName("discordContainer")
        discord_container.setStyleSheet("""
            QWidget#discordContainer {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #5865F2, 
                                           stop: 1 #7289DA);
                border: none;
                border-radius: 6px;
                margin-left: 8px;
            }
            QWidget#discordContainer:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #4752C4, 
                                           stop: 1 #5865F2);
            }
        """)
        
        discord_layout = QVBoxLayout(discord_container)
        discord_layout.setContentsMargins(10, 6, 2, 6)  # Even more left margin, less right margin
        discord_layout.setSpacing(0)
        
        self.discord_btn = QLabel()
        self.discord_btn.setObjectName("discordIcon")
        self.discord_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.discord_btn.setFixedSize(20, 20)  # Exact size for 20px icon
        discord_layout.addWidget(self.discord_btn)
        
        # Create Discord menu
        self.discord_menu = QMenu(self)
        self.discord_menu.setStyleSheet("""
            QMenu {
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(168, 85, 247, 0.4);
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
                margin: 2px;
            }
            QMenu::item:selected {
                background: rgba(168, 85, 247, 0.3);
            }
        """)
        
        # Add menu items
        emans_empire_action = self.discord_menu.addAction("Emans Empire")
        emans_empire_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://discord.gg/W5DgDZ4Hu6")))
        
        illusion_action = self.discord_menu.addAction("Illusion")
        illusion_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://discord.gg/5QfcUP2GBq")))
        
        # Make the container clickable
        discord_container.mousePressEvent = self.show_discord_menu
        
        title_layout.addWidget(discord_container)
        # Load Discord icon from web
        self.load_discord_icon()
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Window controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(0)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Minimize button
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setObjectName("windowControl")
        self.minimize_btn.setFixedSize(45, 40)
        self.minimize_btn.clicked.connect(self.minimize_window)
        controls_layout.addWidget(self.minimize_btn)
        
        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("windowControlClose")
        self.close_btn.setFixedSize(45, 40)
        self.close_btn.clicked.connect(self.close_window)
        controls_layout.addWidget(self.close_btn)
        
        layout.addLayout(controls_layout)
        self.setLayout(layout)
        
        # Make the title bar draggable
        self.old_pos = None
    
    def load_discord_icon(self):
        """Load Discord icon from web URL"""
        try:
            import requests
            from io import BytesIO
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtGui import QPixmap, QPainter
            
            # Discord logo SVG - using a public CDN that allows requests
            # This is the official Discord logo from their brand assets
            discord_icon_url = "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/discord.svg"
            
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Download the SVG
            response = requests.get(discord_icon_url, headers=headers, timeout=5)
            response.raise_for_status()
            
            # Create SVG renderer
            svg_renderer = QSvgRenderer(response.content)
            
            # Create pixmap and render SVG to it - 20x20 for perfect centering in 32x32 button
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            svg_renderer.render(painter)
            painter.end()
            
            # Set pixmap to QLabel with perfect centering
            self.discord_btn.setPixmap(pixmap)
            self.discord_btn.setScaledContents(False)  # Keep original size
            
        except Exception as e:
            # Fallback to Discord emoji if download fails
            print(f"Failed to load Discord icon: {e}")
            self.discord_btn.setText("💬")
            self.discord_btn.setStyleSheet("font-size: 16px; color: white;")
    
    def show_discord_menu(self, event):
        """Show Discord menu when clicked"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Show menu at the bottom of the button
            pos = self.discord_btn.mapToGlobal(self.discord_btn.rect().bottomLeft())
            self.discord_menu.exec(pos)
        
    def minimize_window(self):
        if self.parent_window:
            self.parent_window.showMinimized()
            
    def close_window(self):
        if self.parent_window:
            self.parent_window.close()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        if self.old_pos is not None and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            if self.parent_window:
                self.parent_window.move(self.parent_window.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        self.old_pos = None


class CDBlauncher(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove default window frame
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.init_ui()
        self.apply_styles()
        
        # Download files on startup
        QTimer.singleShot(1000, self.download_initial_files)
        
    def init_ui(self):
        self.setWindowTitle("CDBL - Custom Debloated Blox Launcher")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = CustomTitleBar(self)
        layout.addWidget(self.title_bar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        
        # Add tabs
        self.general_tab = GeneralTab()
        self.settings_tab = SettingsTab()
        self.modifications_tab = ModificationsTab()
        self.tools_tab = ToolsTab()
        self.premium_tab = PremiumTab(self)
        
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.settings_tab, "Settings") 
        self.tab_widget.addTab(self.modifications_tab, "Modifications")
        self.tab_widget.addTab(self.tools_tab, "Tools")
        self.tab_widget.addTab(self.premium_tab, "Premium")
        
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        
    def create_rounded_window(self):
        """Create rounded corners for the window"""
        radius = 12
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        
    def resizeEvent(self, event):
        """Update window mask when window is resized"""
        super().resizeEvent(event)
        self.create_rounded_window()
        
    def apply_styles(self):
        """Apply professional Microsoft Fluent Design inspired styling"""
        style = """
        QMainWindow {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #1a1a1a, stop: 1 #2d1b3d);
            color: #ffffff;
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 12px;
        }
        
        QWidget {
            background-color: transparent;
            color: #ffffff;
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-weight: 400;
        }
        
        /* Custom Title Bar */
        QLabel#appTitle {
            color: #ffffff;
            font-size: 18px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        
        QLabel#versionLabel {
            color: rgba(255, 255, 255, 0.7);
            font-size: 10px;
            font-weight: 400;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 2px 6px;
        }
        
        /* Discord Button */
        QPushButton#discordButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #5865F2, 
                                       stop: 1 #7289DA);
            border: none;
            border-radius: 6px;
            color: #ffffff;
            font-size: 16px;
            font-weight: 600;
            margin-left: 8px;
            padding: 0px;
        }
        
        QPushButton#discordButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #4752C4, 
                                       stop: 1 #5865F2);
        }
        
        QPushButton#discordButton:pressed {
            background: #4752C4;
        }
        
        QPushButton#discordButton::menu-indicator {
            image: none;
            width: 0px;
            height: 0px;
        }
        
        /* Window Controls */
        QPushButton#windowControl {
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 16px;
            font-weight: 400;
            border-radius: 0;
        }
        
        QPushButton#windowControl:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        QPushButton#windowControlClose {
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 14px;
            font-weight: 400;
            border-radius: 0;
        }
        
        QPushButton#windowControlClose:hover {
            background: #e74c3c;
            color: #ffffff;
        }
        
        QLabel#tabTitle {
            color: #A855F7;
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 16px;
        }
        
        QLabel#comingSoonTitle {
            color: #A855F7;
            font-size: 24px;
            font-weight: 500;
            margin: 32px 0 20px 0;
        }
        
        QLabel#comingSoonText {
            color: #D1D5DB;
            font-size: 14px;
            line-height: 1.5;
            margin: 16px 32px;
            font-weight: 400;
        }
        
        QLabel#statusLabel {
            font-weight: 500;
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 12px;
            background-color: rgba(139, 92, 246, 0.15);
            border: 1px solid rgba(139, 92, 246, 0.2);
        }
        
        QLabel#warningLabel {
            font-weight: 500;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 8px;
            background-color: rgba(251, 191, 36, 0.15);
            border: 1px solid rgba(251, 191, 36, 0.3);
            color: #FCD34D;
            margin-bottom: 16px;
        }
        
        /* Tab Styling */
        QTabWidget#mainTabs::pane {
            border: 1px solid rgba(168, 85, 247, 0.2);
            background: rgba(30, 30, 30, 0.95);
            border-radius: 0px 0px 12px 12px;
            margin-top: 0px;
        }
        
        QTabWidget#mainTabs QTabBar::tab {
            background: rgba(40, 40, 40, 0.8);
            color: #D1D5DB;
            border: none;
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-weight: 500;
            font-size: 13px;
            min-width: 100px;
        }
        
        QTabWidget#mainTabs QTabBar::tab:selected {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 rgba(168, 85, 247, 0.3), 
                                       stop: 1 rgba(139, 92, 246, 0.2));
            color: #ffffff;
            border-bottom: 2px solid #A855F7;
        }
        
        QTabWidget#mainTabs QTabBar::tab:hover:!selected {
            background: rgba(168, 85, 247, 0.1);
            color: #E5E7EB;
        }
        
        /* Button Styling */
        QPushButton#primaryButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #8B5CF6, stop: 1 #A855F7);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 13px;
            min-width: 100px;
            min-height: 16px;
        }
        
        QPushButton#primaryButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #7C3AED, stop: 1 #9333EA);
        }
        
        QPushButton#primaryButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #6D28D9, stop: 1 #7C3AED);
        }
        
        QPushButton#secondaryButton {
            background: rgba(55, 65, 81, 0.8);
            color: #E5E7EB;
            border: 1px solid rgba(75, 85, 99, 0.8);
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 13px;
            min-width: 100px;
            min-height: 16px;
        }
        
        QPushButton#secondaryButton:hover {
            background: rgba(75, 85, 99, 0.8);
            border-color: rgba(168, 85, 247, 0.5);
            color: #ffffff;
        }
        
        QPushButton#dangerButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #EF4444, stop: 1 #DC2626);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 13px;
            min-width: 100px;
            min-height: 16px;
        }
        
        QPushButton#dangerButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #DC2626, stop: 1 #B91C1C);
        }
        
        /* Group Box Styling */
        QGroupBox {
            font-weight: 500;
            border: 1px solid rgba(168, 85, 247, 0.2);
            border-radius: 8px;
            margin-top: 8px;
            padding-top: 12px;
            background: rgba(40, 40, 40, 0.6);
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #A855F7;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
        }
        
        /* Input Controls */
        QComboBox#comboBox {
            background: rgba(55, 65, 81, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 6px;
            padding: 6px 10px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 400;
            min-height: 18px;
        }
        
        QComboBox#comboBox:hover {
            border-color: rgba(168, 85, 247, 0.5);
            background: rgba(75, 85, 99, 0.8);
        }
        
        QComboBox#comboBox:focus {
            border-color: #A855F7;
        }
        
        QComboBox#comboBox::drop-down {
            border: none;
            width: 18px;
        }
        
        QComboBox#comboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #A855F7;
            margin-right: 6px;
        }
        
        QComboBox#comboBox QAbstractItemView {
            background: rgba(30, 30, 30, 0.95);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 6px;
            selection-background-color: rgba(168, 85, 247, 0.3);
            color: #ffffff;
            padding: 4px;
            font-weight: 400;
        }
        
        /* Fallback styling for all QComboBox widgets */
        QComboBox {
            background: rgba(55, 65, 81, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 6px;
            padding: 6px 10px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 400;
            min-height: 18px;
        }
        
        QComboBox:hover {
            border-color: rgba(168, 85, 247, 0.5);
            background: rgba(75, 85, 99, 0.8);
        }
        
        QComboBox:focus {
            border-color: #A855F7;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 18px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #A855F7;
            margin-right: 6px;
        }
        
        QComboBox QAbstractItemView {
            background: rgba(30, 30, 30, 0.95);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 6px;
            selection-background-color: rgba(168, 85, 247, 0.3);
            selection-color: #ffffff;
            color: #ffffff;
            padding: 4px;
            font-weight: 400;
        }
        
        QComboBox QAbstractItemView::item {
            color: #ffffff;
            background: transparent;
            padding: 4px 8px;
            border: none;
        }
        
        QComboBox QAbstractItemView::item:selected {
            background: rgba(168, 85, 247, 0.3);
            color: #ffffff;
        }
        
        QComboBox QAbstractItemView::item:hover {
            background: rgba(168, 85, 247, 0.2);
            color: #ffffff;
        }
        
        QSpinBox#spinBox, QDoubleSpinBox#spinBox {
            background: rgba(55, 65, 81, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 6px;
            padding: 6px 10px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 400;
            min-height: 18px;
        }
        
        QSpinBox#spinBox:hover, QDoubleSpinBox#spinBox:hover {
            border-color: rgba(168, 85, 247, 0.5);
            background: rgba(75, 85, 99, 0.8);
        }
        
        QSpinBox#spinBox:focus, QDoubleSpinBox#spinBox:focus {
            border-color: #A855F7;
        }
        
        /* List Widget */
        QListWidget#listWidget {
            background: rgba(30, 30, 30, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.2);
            border-radius: 6px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 400;
            padding: 4px;
        }
        
        QListWidget#listWidget::item {
            padding: 6px 10px;
            border: none;
            border-radius: 4px;
            margin: 1px;
        }
        
        QListWidget#listWidget::item:selected {
            background: rgba(168, 85, 247, 0.3);
            color: #ffffff;
            font-weight: 500;
        }
        
        QListWidget#listWidget::item:hover {
            background: rgba(168, 85, 247, 0.15);
        }
        
        /* JSON Editor */
        QTextEdit#jsonEditor {
            background: rgba(30, 30, 30, 0.9);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 8px;
            color: #ffffff;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            font-weight: 400;
            padding: 12px;
            line-height: 1.4;
        }
        
        QTextEdit#jsonEditor:hover {
            border-color: rgba(168, 85, 247, 0.5);
            background: rgba(40, 40, 40, 0.9);
        }
        
        QTextEdit#jsonEditor:focus {
            border-color: #A855F7;
            background: rgba(45, 45, 45, 0.95);
        }
        
        /* Line Edit (Search Bar) */
        QLineEdit#lineEdit {
            background: rgba(30, 30, 30, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.2);
            border-radius: 6px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 400;
            padding: 8px 12px;
            selection-background-color: rgba(168, 85, 247, 0.3);
        }
        
        QLineEdit#lineEdit:hover {
            border-color: rgba(168, 85, 247, 0.4);
            background: rgba(35, 35, 35, 0.8);
        }
        
        QLineEdit#lineEdit:focus {
            border-color: #A855F7;
            background: rgba(40, 40, 40, 0.9);
        }
        
        /* Modern Input (License Key) */
        QLineEdit#modernInput {
            background: rgba(30, 30, 30, 0.9);
            border: 2px solid rgba(168, 85, 247, 0.3);
            border-radius: 8px;
            color: #ffffff;
            font-size: 14px;
            font-weight: 400;
            padding: 10px 16px;
            selection-background-color: rgba(168, 85, 247, 0.4);
        }
        
        QLineEdit#modernInput:hover {
            border-color: rgba(168, 85, 247, 0.5);
            background: rgba(35, 35, 35, 0.9);
        }
        
        QLineEdit#modernInput:focus {
            border-color: #A855F7;
            background: rgba(40, 40, 40, 0.95);
            border-width: 2px;
        }
        
        /* Status Label */
        QLabel#statusLabel {
            color: #A855F7;
            font-size: 13px;
            font-weight: 500;
            padding: 4px 0;
        }
        
        /* Success Text */
        QLabel#successText {
            color: #10B981;
            font-size: 13px;
            font-weight: 600;
        }
        
        /* Info Label */
        QLabel#infoLabel {
            color: #9CA3AF;
            font-size: 12px;
            font-weight: 400;
            font-style: italic;
        }
        
        /* Labels and Text */
        QLabel {
            color: #E5E7EB;
            font-size: 13px;
            font-weight: 400;
        }
        
        QLabel#settingLabel {
            color: #F3F4F6;
            font-size: 14px;
            font-weight: 500;
            padding: 3px 0;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            background-color: rgba(31, 41, 55, 0.8);
            width: 8px;
            border-radius: 4px;
        }
        
        QScrollBar::handle:vertical {
            background-color: rgba(168, 85, 247, 0.6);
            border-radius: 4px;
            min-height: 20px;
            margin: 1px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: rgba(168, 85, 247, 0.8);
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
            height: 0px;
        }
        
        /* Progress Bar Styling */
        QProgressBar#modernProgressBar {
            background: rgba(55, 65, 81, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 8px;
            text-align: center;
            color: #ffffff;
            font-size: 12px;
            font-weight: 500;
            min-height: 20px;
            max-height: 20px;
        }
        
        QProgressBar#modernProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #8B5CF6, 
                                       stop: 0.5 #A855F7, 
                                       stop: 1 #C084FC);
            border-radius: 7px;
            margin: 1px;
        }
        
        /* Asset Download Progress Bar */
        QProgressBar#progressBar {
            background: rgba(55, 65, 81, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 8px;
            text-align: center;
            color: #ffffff;
            font-size: 11px;
            font-weight: 500;
            min-height: 24px;
            max-height: 24px;
        }
        
        QProgressBar#progressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #10B981, 
                                       stop: 0.5 #34D399, 
                                       stop: 1 #6EE7B7);
            border-radius: 7px;
            margin: 1px;
        }
        
        QLabel#progressStatus {
            color: #A855F7;
            font-size: 11px;
            font-weight: 500;
            padding: 2px 0;
        }
        
        /* Volume Slider */
        QSlider:horizontal {
            height: 20px;
        }
        
        QSlider::groove:horizontal {
            background: rgba(55, 65, 81, 0.8);
            border: 1px solid rgba(168, 85, 247, 0.3);
            height: 6px;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #A855F7, 
                                       stop: 1 #8B5CF6);
            border: 1px solid rgba(168, 85, 247, 0.5);
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #C084FC, 
                                       stop: 1 #A855F7);
            border-color: rgba(168, 85, 247, 0.8);
        }
        
        QSlider::handle:horizontal:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                       stop: 0 #8B5CF6, 
                                       stop: 1 #7C3AED);
        }
        
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #8B5CF6, 
                                       stop: 1 #A855F7);
            border-radius: 3px;
        }
        
        QSlider::add-page:horizontal {
            background: rgba(55, 65, 81, 0.6);
            border-radius: 3px;
        }
        """
        
        self.setStyleSheet(style)
        
    def download_initial_files(self):
        """Download initial files in background"""
        self.download_worker = WorkerThread("download_files")
        self.download_worker.finished.connect(lambda msg: print("Initial files downloaded"))
        self.download_worker.error.connect(lambda err: print(f"Download error: {err}"))
        self.download_worker.start()
    
    def closeEvent(self, event):
        """Handle window closing - cleanup temporary files"""
        # Clean up premium tab temp files
        if hasattr(self, 'premium_tab'):
            self.premium_tab.cleanup_temp_files()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CDBL")
    app.setApplicationVersion("2.0 Beta")
    
    # Set application icon if available
    # app.setWindowIcon(QIcon("icon.ico"))
    
    # Check for admin privileges FIRST - before any other setup
    if not is_admin():
        print("Administrator privileges required. Attempting to restart with elevation...")
        try:
            # Get the correct executable path
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller EXE
                exe_path = sys.executable
                # Use ShellExecute to restart with admin privileges
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",  # Request elevation
                    exe_path,
                    "",  # No arguments needed
                    None,
                    1  # SW_SHOW
                )
            else:
                # Running as Python script
                python_exe = sys.executable
                script_path = sys.argv[0]
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",  # Request elevation
                    python_exe,
                    f'"{script_path}"',
                    None,
                    1  # SW_SHOW
                )
            
            # Exit the current non-admin instance
            sys.exit(0)
            
        except Exception as e:
            print(f"Failed to restart with admin privileges: {e}")
            print("Continuing without admin privileges - some features may not work properly.")
    
    # Check for first run and show setup if needed
    if is_first_run():
        print("First run detected - showing setup dialog...")
        setup_result = show_first_run_setup()
        if setup_result is None:
            # User cancelled setup or it failed
            sys.exit(0)
        # Setup completed, the dialog will restart the app
        return
    
    # Check for updates after first run is complete
    print("Checking for updates...")
    update_choice = check_for_updates_on_startup()
    if update_choice == 'download':
        print("User chose to download update. Opening download page...")
        # User opened download page, continue to app
    elif update_choice == 'skip':
        print("User chose to skip update.")
    
    # Ensure assets.json structure exists on every launch
    print("Ensuring assets.json structure...")
    try:
        from src.first_run import ensure_assets_json_structure
        ensure_assets_json_structure()
    except Exception as e:
        print(f"⚠️ Warning: Could not ensure assets.json structure: {e}")
    
    # Normal application startup
    window = CDBlauncher()
    
    # Display admin status (should be admin at this point)
    if is_admin():
        print("✅ Running with administrator privileges")
    else:
        print("⚠️ Running without administrator privileges")
    
    window.show()
    
    # Apply rounded corners after window is shown
    QTimer.singleShot(200, window.create_rounded_window)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()