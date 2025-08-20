import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QTextEdit,
    QHBoxLayout,
    QFileDialog,
    QComboBox,
    QTreeWidget,
    QTreeWidgetItem,
    QInputDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
)
from PySide6.QtCore import QSettings, QProcess, Qt, QVariant, QUrl # QProcess for better non-blocking
from PySide6.QtGui import QDesktopServices
from pathlib import Path
import shutil
import os
import subprocess
import json
import yaml
import logging

# Import our new modular components
from core.credentials_tab import CredentialsTab
from core.task_tab import TaskManagementTab

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("MyCompany", "OSRS_RL_GUI")
        self.training_process = None
        self.cleanup_process = None # For the separate cleanup command
        self.tensorboard_process = None
        self.tensorboard_url_opened = False

        self.setWindowTitle("OSRS AI RL Manager")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Placeholder for TV Frame
        tv_frame_placeholder = QLabel("Retro TV Frame Placeholder")
        main_layout.addWidget(tv_frame_placeholder)

        # Tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Create tabs
        self.setup_tab = QWidget()
        tab_widget.addTab(self.setup_tab, "Setup")
        setup_tab_outer_layout = QVBoxLayout(self.setup_tab) # Renamed to avoid conflict

        # Environment Setup Section
        env_setup_widget = QWidget()
        self.setup_tab_layout = QVBoxLayout(env_setup_widget) # This is the main layout for content
        setup_tab_outer_layout.addWidget(env_setup_widget)

        # Repo Path
        repo_path_layout = QHBoxLayout()
        repo_path_label = QLabel("OSRS PvP RL Repo Path:")
        self.repo_path_line_edit = QLineEdit()
        self.repo_path_line_edit.textChanged.connect(self.on_repo_path_changed) # Connect textChanged
        self.browse_repo_button = QPushButton("Browse...")
        self.browse_repo_button.clicked.connect(self.browse_repo_path)
        repo_path_layout.addWidget(repo_path_label)
        repo_path_layout.addWidget(self.repo_path_line_edit)
        repo_path_layout.addWidget(self.browse_repo_button)
        self.setup_tab_layout.addLayout(repo_path_layout)

        # Load saved repo path
        saved_repo_path = self.settings.value("repositoryPath")
        if saved_repo_path:
            self.repo_path_line_edit.setText(saved_repo_path)

        # Conda Status
        self.conda_status_label = QLabel("Conda status: Unknown")
        self.setup_tab_layout.addWidget(self.conda_status_label)

        # CPU Only Checkbox
        self.cpu_only_checkbox = QCheckBox("Use CPU only for training")
        self.setup_tab_layout.addWidget(self.cpu_only_checkbox)

        # Create Environment Button
        self.create_env_button = QPushButton("Setup Conda Environment")
        self.create_env_button.clicked.connect(self.handle_conda_env_setup)
        self.setup_tab_layout.addWidget(self.create_env_button)

        # Feedback Text Area
        self.setup_feedback_text = QTextEdit()
        self.setup_feedback_text.setReadOnly(True)
        self.setup_feedback_text.setPlaceholderText(
            "Please select the OSRS PvP RL repository path and then proceed to setup the Conda environment."
        )
        self.setup_tab_layout.addWidget(self.setup_feedback_text)

        self.check_conda_installation()

        self.training_tab = QWidget()
        tab_widget.addTab(self.training_tab, "Training")
        self.training_tab_layout = QVBoxLayout(self.training_tab) # This will be the main layout for content

        # Configuration Profile Section
        config_profile_layout = QHBoxLayout()
        config_profile_label = QLabel("Configuration Profile:")
        self.config_profile_combo = QComboBox()
        self.config_profile_combo.currentTextChanged.connect(self.display_selected_config)
        self.refresh_profiles_button = QPushButton("Refresh")
        self.refresh_profiles_button.clicked.connect(self.populate_config_profiles)
        config_profile_layout.addWidget(config_profile_label)
        config_profile_layout.addWidget(self.config_profile_combo)
        config_profile_layout.addWidget(self.refresh_profiles_button)
        self.training_tab_layout.addLayout(config_profile_layout)

        # Configuration Display Tree
        self.config_display_tree = QTreeWidget()
        self.config_display_tree.setColumnCount(2)
        self.config_display_tree.setHeaderLabels(["Parameter", "Value"])
        self.training_tab_layout.addWidget(self.config_display_tree)

        # Save buttons
        save_buttons_layout = QHBoxLayout()
        self.save_config_button = QPushButton("Save Configuration")
        self.save_config_as_button = QPushButton("Save Configuration As...")
        self.save_config_button.clicked.connect(self.save_configuration)
        self.save_config_as_button.clicked.connect(self.save_configuration_as)
        save_buttons_layout.addWidget(self.save_config_button)
        save_buttons_layout.addWidget(self.save_config_as_button)
        self.training_tab_layout.addLayout(save_buttons_layout)

        # Training Execution GroupBox
        training_execution_groupbox = QGroupBox("Training Execution")
        training_execution_layout = QVBoxLayout() # Layout for the GroupBox

        # Experiment Name
        exp_name_layout = QHBoxLayout()
        exp_name_label = QLabel("Experiment Name:")
        self.experiment_name_line_edit = QLineEdit()
        exp_name_layout.addWidget(exp_name_label)
        exp_name_layout.addWidget(self.experiment_name_line_edit)
        training_execution_layout.addLayout(exp_name_layout)

        # Start/Stop Buttons
        start_stop_layout = QHBoxLayout()
        self.start_training_button = QPushButton("Start Training")
        self.start_training_button.clicked.connect(self.start_training)
        self.stop_training_button = QPushButton("Stop Training (Cleanup)")
        self.stop_training_button.clicked.connect(self.stop_training)
        self.stop_training_button.setEnabled(False) # Initially disabled

        self.launch_tensorboard_button = QPushButton("Launch TensorBoard")
        self.launch_tensorboard_button.clicked.connect(self.launch_tensorboard)

        start_stop_layout.addWidget(self.start_training_button)
        start_stop_layout.addWidget(self.stop_training_button)
        start_stop_layout.addWidget(self.launch_tensorboard_button) # Add new button
        training_execution_layout.addLayout(start_stop_layout)

        # Training Status Label
        self.training_status_label = QLabel("Training Status: Idle")
        training_execution_layout.addWidget(self.training_status_label)

        # Training Log Text Edit
        self.training_log_text_edit = QTextEdit()
        self.training_log_text_edit.setReadOnly(True)
        training_execution_layout.addWidget(self.training_log_text_edit)

        training_execution_groupbox.setLayout(training_execution_layout)
        self.training_tab_layout.addWidget(training_execution_groupbox)

        # Stretch factor to push execution group to bottom if desired, or keep it compact
        # self.training_tab_layout.addStretch(1)


        self.populate_config_profiles() # Initial population

        self.monitoring_tab = QWidget()
        tab_widget.addTab(self.monitoring_tab, "Monitoring")
        self.monitoring_tab_layout = QVBoxLayout(self.monitoring_tab)
        self.monitoring_tab_layout.addWidget(QLabel("Monitoring content will go here."))

        self.admin_tab = QWidget()
        tab_widget.addTab(self.admin_tab, "Admin")
        self.admin_tab_layout = QVBoxLayout(self.admin_tab)
        self.admin_tab_layout.addWidget(QLabel("Admin content will go here."))

        # Task Management Tab (New!)
        self.task_tab = TaskManagementTab()
        self.task_tab.task_selected_for_training.connect(self.on_task_selected_for_training)
        tab_widget.addTab(self.task_tab, "Task Management")

        # Bot Credentials Tab (Secure)
        self.credentials_tab = CredentialsTab()
        tab_widget.addTab(self.credentials_tab, "Bot Credentials")


    def browse_repo_path(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select OSRS PvP RL Repository Path",
            self.repo_path_line_edit.text()  # Start directory
        )
        if directory:
            self.repo_path_line_edit.setText(directory)
            self.settings.setValue("repositoryPath", directory)
            self.populate_config_profiles() # Repopulate on path change
            # Optionally, re-check conda or other path-dependent things here

    def on_repo_path_changed(self, new_path):
        # This method can be used if immediate action is needed when text changes,
        # otherwise browse_repo_path already handles the update after selection.
        # For now, let's ensure profiles are updated if path is manually edited and valid.
        # A more robust way would be to validate the path before repopulating.
        self.populate_config_profiles()


    def check_conda_installation(self):
        conda_path = shutil.which("conda")
        if conda_path:
            try:
                # Further check if it's Miniconda/Anaconda by running a command
                # Use shell=True on Windows if conda is a bat file, or if it's in PATH and not directly executable
                # For cross-platform, it's safer to ensure conda is directly executable or handle OS-specifics
                is_windows = os.name == 'nt'
                result = subprocess.run(["conda", "--version"], capture_output=True, text=True, shell=is_windows, check=True, timeout=5)
                if result.stdout and "conda" in result.stdout.lower():
                    self.conda_status_label.setText(f"Conda detected: {result.stdout.strip()}")
                else:
                    self.conda_status_label.setText("Conda detected, but version unknown.")
            except subprocess.CalledProcessError:
                self.conda_status_label.setText("Conda found, but '--version' failed. Check installation.")
            except subprocess.TimeoutExpired:
                self.conda_status_label.setText("Conda version check timed out. Conda might be slow or unresponsive.")
            except FileNotFoundError: # Should be caught by shutil.which, but as a fallback
                self.conda_status_label.setText("Conda not found. Please install Conda and ensure it's in your PATH.")
        else:
            self.conda_status_label.setText("Conda not found. Please install Conda and ensure it's in your PATH.")

    def _append_feedback(self, message):
        self.setup_feedback_text.append(message)
        QApplication.processEvents()

    def check_env_exists(self, env_path_str):
        self._append_feedback(f"Checking if environment exists at {env_path_str}...")
        is_windows = os.name == 'nt'
        try:
            result = subprocess.run(
                ["conda", "env", "list", "--json"],
                capture_output=True, text=True, shell=is_windows, check=True, timeout=10
            )
            envs = json.loads(result.stdout)
            for env in envs.get("envs", []):
                if Path(env) == Path(env_path_str):
                    self._append_feedback(f"Found existing environment: {env}")
                    return True
            self._append_feedback("No existing environment found at the specified path.")
            return False
        except subprocess.CalledProcessError as e:
            self._append_feedback(f"Error checking conda environments: {e.stderr}")
            return False
        except json.JSONDecodeError:
            self._append_feedback("Error parsing conda environment list JSON.")
            return False
        except FileNotFoundError:
            self._append_feedback("Conda command not found while checking environment list.")
            return False


    def handle_conda_env_setup(self):
        self.setup_feedback_text.clear()
        is_windows = os.name == 'nt'

        repo_path_str = self.repo_path_line_edit.text()
        if not repo_path_str:
            self._append_feedback("Error: OSRS PvP RL Repository Path is not set.")
            return

        repo_path = Path(repo_path_str)
        pvp_ml_path = repo_path / "pvp-ml"
        env_yaml_path = pvp_ml_path / "environment.yml"
        env_name = "pvp-ml-env" # Consistent name for the environment
        env_path = pvp_ml_path / "env" # Target directory for the environment

        if not env_yaml_path.exists():
            self._append_feedback(f"Error: environment.yml not found at {env_yaml_path}")
            return

        if "Conda not found" in self.conda_status_label.text() or "failed" in self.conda_status_label.text():
            self._append_feedback("Error: Conda is not properly detected or configured. Please check Conda installation.")
            return

        self._append_feedback("Starting Conda environment setup...")

        if self.check_env_exists(str(env_path)):
            self._append_feedback(f"Conda environment already exists at {env_path}. Recreating...")
            # No need to explicitly delete, conda create --force -p should handle it

        self._append_feedback("Modifying environment.yml for selected configuration...")
        temp_env_yaml_path = pvp_ml_path / "environment.temp.yml"
        is_cpu_only = self.cpu_only_checkbox.isChecked()

        try:
            with open(env_yaml_path, "r") as f_in, open(temp_env_yaml_path, "w") as f_out:
                for line in f_in:
                    stripped_line = line.strip()
                    if "cpuonly" in stripped_line:
                        if is_cpu_only:
                            f_out.write(line.replace("#-", "-").replace("# -", "-"))
                        else:
                            if not stripped_line.startswith("#"):
                                f_out.write(f"# {line}")
                            else:
                                f_out.write(line)
                    elif "pytorch-cuda" in stripped_line:
                        if is_cpu_only:
                            if not stripped_line.startswith("#"):
                                f_out.write(f"# {line}")
                            else:
                                f_out.write(line)
                        else:
                            f_out.write(line.replace("#-", "-").replace("# -", "-"))
                    else:
                        f_out.write(line)
            self._append_feedback(f"Temporary environment file created at {temp_env_yaml_path}")

            self._append_feedback(f"Running Conda environment creation... This may take a while.")
            self._append_feedback(f"Command: conda env create -p {env_path} -f {temp_env_yaml_path.name} --force")

            # Using QProcess for non-blocking execution
            if not hasattr(self, 'conda_process'):
                self.conda_process = QProcess()
                self.conda_process.setProcessChannelMode(QProcess.MergedChannels)
                self.conda_process.readyReadStandardOutput.connect(self.on_conda_output)
                self.conda_process.finished.connect(self.on_conda_finished)

            # Disable button during process
            self.create_env_button.setEnabled(False)

            self.conda_process.setWorkingDirectory(str(pvp_ml_path))
            self.conda_process.start("conda", ["env", "create", "-p", str(env_path), "-f", temp_env_yaml_path.name, "--force"])

        except Exception as e:
            self._append_feedback(f"Error during setup preparation: {e}")
            if temp_env_yaml_path.exists():
                os.remove(temp_env_yaml_path)
            self.create_env_button.setEnabled(True)


    def on_conda_output(self):
        output = self.conda_process.readAllStandardOutput().data().decode().strip()
        if output:
            self._append_feedback(output)

    def on_conda_finished(self):
        pvp_ml_path = Path(self.repo_path_line_edit.text()) / "pvp-ml"
        temp_env_yaml_path = pvp_ml_path / "environment.temp.yml"
        env_path = pvp_ml_path / "env"
        env_name = "pvp-ml-env"

        exit_code = self.conda_process.exitCode()
        if exit_code == 0:
            self._append_feedback("Environment setup successful!")
            self.conda_status_label.setText(f"Conda env '{env_name}' at {env_path} ready.")
            # Verify again if it exists, as conda might succeed but not create the dir in some edge cases
            if not self.check_env_exists(str(env_path)):
                 self._append_feedback(f"Warning: Conda reported success, but env at {env_path} not found by env list.")
        else:
            self._append_feedback(f"Environment setup failed. Exit code: {exit_code}. Check logs above.")
            # Error output is already appended via on_conda_output

        if temp_env_yaml_path.exists():
            try:
                os.remove(temp_env_yaml_path)
                self._append_feedback(f"Temporary environment file {temp_env_yaml_path.name} deleted.")
            except OSError as e:
                self._append_feedback(f"Error deleting temporary environment file: {e}")

        self.create_env_button.setEnabled(True)

    def populate_config_profiles(self):
        self.config_profile_combo.clear()
        self.config_display_tree.clear()
        repo_path_str = self.repo_path_line_edit.text()

        if not repo_path_str:
            self._append_feedback("Repository path not set. Cannot load training profiles.")
            return

        config_base_path = Path(repo_path_str) / "pvp-ml" / "config"

        if not config_base_path.is_dir():
            self._append_feedback(f"Training config directory not found: {config_base_path}")
            # Potentially update a status label in Training tab if it existed
            return

        profile_files = []
        for p_file in config_base_path.rglob("*.yml"):
            # Store relative path from 'config' directory to display
            relative_path = p_file.relative_to(config_base_path)
            profile_files.append(relative_path)

        if not profile_files:
            self._append_feedback(f"No .yml configuration profiles found in {config_base_path} or its subdirectories.")
            return

        for rel_path in sorted(profile_files):
            self.config_profile_combo.addItem(str(rel_path), userData=config_base_path / rel_path)

        if self.config_profile_combo.count() > 0:
            self.display_selected_config(self.config_profile_combo.currentText())


    def display_selected_config(self, profile_text_or_index):
        self.config_display_tree.clear()

        current_index = self.config_profile_combo.currentIndex()
        if current_index < 0: # No item selected or combo is empty
            return

        selected_path = self.config_profile_combo.itemData(current_index)

        if not selected_path or not Path(selected_path).exists():
            self._append_feedback(f"Selected profile path is invalid or file does not exist: {selected_path}")
            return

        try:
            with open(selected_path, 'r') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self._append_feedback(f"Error parsing YAML file {selected_path.name}: {e}")
            # Add error item to tree?
            error_item = QTreeWidgetItem(self.config_display_tree)
            error_item.setText(0, "Error")
            error_item.setText(1, f"Could not parse {selected_path.name}: {e}")
            return
        except Exception as e:
            self._append_feedback(f"Error reading file {selected_path.name}: {e}")
            return

        if config_data:
            self.add_items_to_tree(self.config_display_tree.invisibleRootItem(), config_data)
            self.config_display_tree.expandAll() # Optional: expand all items

    def add_items_to_tree(self, parent_item, data):
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent_item)
                item.setText(0, str(key))
                item.setData(0, Qt.UserRole, "dict_item") # Mark as dictionary item key

                if isinstance(value, (dict, list)):
                    item.setData(1, Qt.UserRole, type(value).__name__) # Store type 'dict' or 'list'
                    self.add_items_to_tree(item, value)
                else:
                    item.setText(1, str(value))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setData(1, Qt.UserRole, type(value).__name__) # Store original type
        elif isinstance(data, list):
            parent_item.setData(0, Qt.UserRole, "list_container") # Mark parent as list container
            for index, value in enumerate(data):
                item = QTreeWidgetItem(parent_item)
                item.setText(0, str(index)) # Using index as key for list items
                item.setData(0, Qt.UserRole, "list_item") # Mark as list item key

                if isinstance(value, (dict, list)):
                    item.setData(1, Qt.UserRole, type(value).__name__) # Store type 'dict' or 'list'
                    self.add_items_to_tree(item, value)
                else:
                    item.setText(1, str(value))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    item.setData(1, Qt.UserRole, type(value).__name__) # Store original type

    def convert_tree_to_dict_or_list(self, parent_item):
        # Check the marker on the parent_item itself if it's a container for a list
        parent_marker = parent_item.data(0, Qt.UserRole)

        # Heuristic: if the parent_item is the invisible root, and its first child's key is "0",
        # it could be a list. This is less robust than marking.
        # For now, let's assume the top level from YAML is usually a dict.
        # The recursive calls will handle nested lists if their parent items are marked.

        is_list_container = parent_marker == "list_container"

        if is_list_container:
            result_list = []
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                # list items have their value in column 1, or are nested structures
                child_value_text = child.text(1)
                child_value_type = child.data(1, Qt.UserRole)

                if child.childCount() > 0: # Nested structure
                    nested_data = self.convert_tree_to_dict_or_list(child)
                    result_list.append(nested_data)
                else: # Leaf node
                    result_list.append(self.smart_convert(child_value_text, child_value_type))
            return result_list
        else: # Dictionary
            result_dict = {}
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                key = child.text(0)
                value_text = child.text(1)
                value_type = child.data(1, Qt.UserRole) # Original type for leaf

                # Try to convert key to int if it looks like an index from a list that wasn't properly marked
                # This is a fallback, explicit marking is better
                actual_key = int(key) if key.isdigit() and parent_marker != "dict_item" else key


                if child.childCount() > 0: # Nested structure
                    result_dict[actual_key] = self.convert_tree_to_dict_or_list(child)
                else: # Leaf node
                    result_dict[actual_key] = self.smart_convert(value_text, value_type)
            return result_dict

    def smart_convert(self, value_str, original_type_str):
        if original_type_str == 'bool':
            return value_str.lower() == 'true'
        elif original_type_str == 'int':
            try: return int(value_str)
            except ValueError: return value_str # Fallback
        elif original_type_str == 'float':
            try: return float(value_str)
            except ValueError: return value_str # Fallback
        elif original_type_str == 'NoneType' or value_str.lower() == 'none' or value_str == '':
            return None
        # Add handling for other types like 'list', 'dict' if they can be stringified directly
        # For now, assuming complex types are handled by recursion.
        return value_str # Default to string

    def save_configuration(self, save_as=False):
        current_index = self.config_profile_combo.currentIndex()
        if current_index < 0 and not save_as:
            QMessageBox.warning(self, "Save Error", "No configuration profile selected.")
            return

        original_profile_path = self.config_profile_combo.itemData(current_index) if current_index >=0 else None
        profile_name = self.config_profile_combo.currentText() if current_index >=0 else "untitled.yml"

        save_path = None

        if save_as:
            repo_path_str = self.repo_path_line_edit.text()
            if not repo_path_str:
                QMessageBox.warning(self, "Save Error", "Repository path not set.")
                return
            config_dir = Path(repo_path_str) / "pvp-ml" / "config"
            if not config_dir.is_dir():
                QMessageBox.warning(self, "Save Error", f"Config directory not found: {config_dir}")
                return

            new_name, ok = QInputDialog.getText(self, "Save Configuration As",
                                                "Enter new profile name (e.g., custom.yml):",
                                                text=profile_name)
            if ok and new_name:
                if not new_name.endswith(".yml"):
                    new_name += ".yml"
                # Check if new_name implies subdirectories e.g. "nh/custom.yml"
                # For simplicity, let's assume it's saved in the root of 'config' or user types the subfolder.
                # A more robust solution would use QFileDialog.getSaveFileName
                save_path = config_dir / new_name
                profile_name = new_name # for messages
            else:
                return # User cancelled
        else: # Regular save
            if not original_profile_path:
                 QMessageBox.warning(self, "Save Error", "Cannot save, original path unknown.")
                 return
            save_path = Path(original_profile_path)

        if save_path.exists() or save_as : # Always confirm for "Save As" or if path exists for "Save"
             # For "Save", original_profile_path must exist.
            confirm_msg = f"Are you sure you want to overwrite '{profile_name}'?"
            if save_as and not save_path.exists(): # New file for "Save As"
                 confirm_msg = f"Are you sure you want to save as '{profile_name}'?"

            reply = QMessageBox.confirm(self, "Confirm Save", confirm_msg,
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        try:
            # The root item of QTreeWidget is invisible, actual data is under its children
            data_to_save = self.convert_tree_to_dict_or_list(self.config_display_tree.invisibleRootItem())

            # Ensure pvp-ml/config path exists (especially for 'save as' into new subdirs if allowed)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'w') as f:
                yaml.dump(data_to_save, f, sort_keys=False, default_flow_style=False)

            self._append_feedback(f"Configuration saved to {save_path}")
            QMessageBox.information(self, "Save Successful", f"Configuration saved to {save_path.name}")

            if save_as: # Refresh profiles list and select the new one
                self.populate_config_profiles()
                # Try to find and select the newly saved file
                for i in range(self.config_profile_combo.count()):
                    if self.config_profile_combo.itemData(i) == save_path:
                        self.config_profile_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            self._append_feedback(f"Error saving configuration: {e}")
            QMessageBox.critical(self, "Save Error", f"Could not save configuration: {e}")

    def save_configuration_as(self):
        self.save_configuration(save_as=True)

    def _log_training_message(self, message):
        self.training_log_text_edit.append(message)
        QApplication.processEvents() # Keep GUI responsive

    def start_training(self):
        if self.training_process and self.training_process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "Training In Progress", "A training process is already running.")
            return

        repo_path_str = self.repo_path_line_edit.text()
        if not repo_path_str or not Path(repo_path_str).is_dir():
            self._log_training_message("Error: Repository path is not set or invalid.")
            QMessageBox.critical(self, "Setup Error", "Repository path is not set or invalid.")
            return

        pvp_ml_path = Path(repo_path_str) / "pvp-ml"
        env_path = pvp_ml_path / "env"
        if not (env_path / "conda-meta").is_dir(): # Basic check for conda env existence
            self._log_training_message(f"Error: Conda environment not found at {env_path}. Please run Setup first.")
            QMessageBox.critical(self, "Setup Error", f"Conda environment not found at {env_path}. Please run Setup first.")
            return

        profile_index = self.config_profile_combo.currentIndex()
        if profile_index < 0:
            self._log_training_message("Error: No training configuration profile selected.")
            QMessageBox.critical(self, "Config Error", "No training configuration profile selected.")
            return

        # Use itemText for display name, itemData for full path. Need relative path for preset.
        profile_rel_path = self.config_profile_combo.itemText(profile_index) # e.g. "nh/core.yml"
        preset_name = profile_rel_path.replace(".yml", "") # e.g. "nh/core"

        experiment_name = self.experiment_name_line_edit.text().strip()
        if not experiment_name:
            self._log_training_message("Error: Experiment name cannot be empty.")
            QMessageBox.critical(self, "Config Error", "Experiment name cannot be empty.")
            return

        self.training_log_text_edit.clear()
        self._log_training_message("Starting training...")

        command_parts = [
            "conda", "run", "-p", str(env_path),
            "python", "train",
            "--preset", preset_name,
            "--name", experiment_name
        ]
        self._log_training_message(f"Executing: {' '.join(command_parts)}")

        self.training_process = QProcess()
        self.training_process.setWorkingDirectory(str(pvp_ml_path))
        self.training_process.setProcessChannelMode(QProcess.MergedChannels) # Merge stdout and stderr
        self.training_process.readyReadStandardOutput.connect(self.on_training_output)
        self.training_process.finished.connect(self.on_training_finished)
        self.training_process.errorOccurred.connect(self.on_training_process_error) # For QProcess specific errors

        self.training_process.start(command_parts[0], command_parts[1:])

        if self.training_process.waitForStarted(5000): # Wait 5s for process to start
            self.training_status_label.setText("Training Status: Running")
            self.start_training_button.setEnabled(False)
            self.stop_training_button.setEnabled(True)
            self.config_profile_combo.setEnabled(False)
            self.experiment_name_line_edit.setEnabled(False)
            self.browse_repo_button.setEnabled(False) # also disable repo changes during training
            self.repo_path_line_edit.setEnabled(False)
            self.create_env_button.setEnabled(False) # disable setup button
        else:
            self._log_training_message("Error: Failed to start training process.")
            self.training_status_label.setText("Training Status: Failed to start")
            err_details = self.training_process.errorString()
            self._log_training_message(f"QProcess error: {err_details}")
            self.training_process = None # Clear the process


    def on_training_output(self):
        if self.training_process:
            output = self.training_process.readAllStandardOutput().data().decode().strip()
            if output:
                self._log_training_message(output)

    def on_training_process_error(self, error):
        if self.training_process: # Check if it's our current training process
            error_map = {
                QProcess.FailedToStart: "Failed to start", QProcess.Crashed: "Crashed",
                QProcess.Timedout: "Timed out", QProcess.ReadError: "Read error",
                QProcess.WriteError: "Write error", QProcess.UnknownError: "Unknown error"
            }
            self._log_training_message(f"Training process QProcess error: {error_map.get(error, 'Unknown error')}")
            self.training_status_label.setText(f"Training Status: Process Error ({error_map.get(error, '')})")
            # `on_training_finished` will also be called, so UI reset is handled there.

    def on_training_finished(self, exit_code, exit_status):
        # This signal is emitted even if the process fails to start or crashes.
        # Ensure self.training_process is the one that finished, not a stale one.
        # However, QProcess connects are instance specific, so this should be fine.

        status_text = "Training Status: "
        if exit_status == QProcess.CrashExit:
            status_text += "Crashed"
            self._log_training_message("Training process crashed.")
        elif exit_code != 0:
            status_text += f"Error (Code: {exit_code})"
            self._log_training_message(f"Training process failed with exit code {exit_code}.")
        else:
            status_text += "Finished successfully"
            self._log_training_message("Training process finished successfully.")

        self.training_status_label.setText(status_text)

        self.start_training_button.setEnabled(True)
        self.stop_training_button.setEnabled(False)
        self.config_profile_combo.setEnabled(True)
        self.experiment_name_line_edit.setEnabled(True)
        self.browse_repo_button.setEnabled(True)
        self.repo_path_line_edit.setEnabled(True)
        self.create_env_button.setEnabled(True)

        if self.training_process: # Make sure we are cleaning up the correct process
            self.training_process.deleteLater() # Schedule for deletion
            self.training_process = None


    def stop_training(self):
        if self.training_process and self.training_process.state() != QProcess.NotRunning:
            self._log_training_message("Attempting to stop training process...")
            self.training_status_label.setText("Training Status: Stopping...")
            self.training_process.terminate() # Politely ask to stop
            # Wait a bit, then kill if not stopped. QProcess.finished will be emitted.
            if not self.training_process.waitForFinished(5000): # 5 seconds
                self._log_training_message("Process did not terminate gracefully. Killing...")
                self.training_process.kill()
        else:
            self._log_training_message("No active training process to stop. Proceeding to cleanup check.")
            # If no process is running, or after it has been stopped (on_training_finished would have run)
            # We can run the cleanup command.
            self.run_cleanup_command()


    def run_cleanup_command(self):
        repo_path_str = self.repo_path_line_edit.text()
        if not repo_path_str or not Path(repo_path_str).is_dir():
            self._log_training_message("Error: Repository path is not set or invalid for cleanup.")
            QMessageBox.critical(self, "Setup Error", "Repository path is not set or invalid for cleanup.")
            return

        pvp_ml_path = Path(repo_path_str) / "pvp-ml"
        env_path = pvp_ml_path / "env"
        if not (env_path / "conda-meta").is_dir():
            self._log_training_message(f"Error: Conda environment not found at {env_path} for cleanup.")
            QMessageBox.critical(self, "Setup Error", f"Conda environment not found at {env_path} for cleanup.")
            return

        experiment_name = self.experiment_name_line_edit.text().strip()
        if not experiment_name:
            # Maybe ask user for experiment name if not available in line edit?
            # For now, require it to be in the line edit.
            exp_name_input, ok = QInputDialog.getText(self, "Cleanup Experiment",
                                                 "Enter Experiment Name to Cleanup (if different):",
                                                 text=self.experiment_name_line_edit.text())
            if ok and exp_name_input:
                experiment_name = exp_name_input.strip()
            else:
                self._log_training_message("Cleanup cancelled: Experiment name required.")
                QMessageBox.warning(self, "Cleanup Info", "Cleanup cancelled: Experiment name is required.")
                return

        self._log_training_message(f"Starting cleanup for experiment: {experiment_name}...")
        self.training_status_label.setText("Training Status: Cleaning up...")

        command_parts = [
            "conda", "run", "-p", str(env_path),
            "python", "train", "cleanup",
            "--name", experiment_name
        ]
        self._log_training_message(f"Executing cleanup: {' '.join(command_parts)}")

        # Use a separate QProcess for cleanup if training_process might still exist or for clarity
        if self.cleanup_process and self.cleanup_process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "Cleanup Info", "A cleanup process is already running.")
            return

        self.cleanup_process = QProcess()
        self.cleanup_process.setWorkingDirectory(str(pvp_ml_path))
        self.cleanup_process.setProcessChannelMode(QProcess.MergedChannels)

        # Connect signals for cleanup process
        self.cleanup_process.readyReadStandardOutput.connect(self.on_cleanup_output)
        self.cleanup_process.finished.connect(self.on_cleanup_finished)
        self.cleanup_process.errorOccurred.connect(self.on_cleanup_process_error)

        self.cleanup_process.start(command_parts[0], command_parts[1:])

        if not self.cleanup_process.waitForStarted(5000):
            self._log_training_message(f"Error: Failed to start cleanup process for {experiment_name}.")
            self.training_status_label.setText("Training Status: Cleanup failed to start")
            self.cleanup_process = None

    def on_cleanup_output(self):
        if self.cleanup_process:
            output = self.cleanup_process.readAllStandardOutput().data().decode().strip()
            if output:
                self._log_training_message(f"[Cleanup] {output}")

    def on_cleanup_process_error(self, error):
        if self.cleanup_process:
            error_map = {
                QProcess.FailedToStart: "Failed to start", QProcess.Crashed: "Crashed",
                QProcess.Timedout: "Timed out", QProcess.ReadError: "Read error",
                QProcess.WriteError: "Write error", QProcess.UnknownError: "Unknown error"
            }
            self._log_training_message(f"[Cleanup] QProcess error: {error_map.get(error, 'Unknown error')}")
            self.training_status_label.setText(f"Training Status: Cleanup Process Error ({error_map.get(error, '')})")

    def on_cleanup_finished(self, exit_code, exit_status):
        status_text = "Training Status: "
        if exit_status == QProcess.CrashExit:
            status_text += "Cleanup Crashed"
            self._log_training_message("[Cleanup] Process crashed.")
        elif exit_code != 0:
            status_text += f"Cleanup Error (Code: {exit_code})"
            self._log_training_message(f"[Cleanup] Process failed with exit code {exit_code}.")
        else:
            status_text += "Cleanup successful."
            self._log_training_message("[Cleanup] Process finished successfully.")

        self.training_status_label.setText(status_text) # Update status

        if self.cleanup_process:
            self.cleanup_process.deleteLater()
            self.cleanup_process = None

        # Reset main training buttons if no training is running
        if not (self.training_process and self.training_process.state() != QProcess.NotRunning):
            self.start_training_button.setEnabled(True)
            self.stop_training_button.setEnabled(False) # Should be false if no training is active
            self.config_profile_combo.setEnabled(True)
            self.experiment_name_line_edit.setEnabled(True)
            self.browse_repo_button.setEnabled(True)
            self.repo_path_line_edit.setEnabled(True)
            self.create_env_button.setEnabled(True)

    def launch_tensorboard(self):
        if self.tensorboard_process and self.tensorboard_process.state() != QProcess.NotRunning:
            QMessageBox.information(self, "TensorBoard Running",
                                    "TensorBoard process is already running. Check your terminal or browser (usually http://localhost:6006).")
            if self.tensorboard_url_opened:
                 QDesktopServices.openUrl(QUrl("http://localhost:6006")) # Re-open if already known
            return

        repo_path_str = self.repo_path_line_edit.text()
        if not repo_path_str or not Path(repo_path_str).is_dir():
            self._log_training_message("[TensorBoard] Error: Repository path is not set or invalid.")
            QMessageBox.critical(self, "Setup Error", "Repository path is not set or invalid for TensorBoard.")
            return

        pvp_ml_path = Path(repo_path_str) / "pvp-ml"
        env_path = pvp_ml_path / "env"
        tensorboard_log_dir = pvp_ml_path / "tensorboard"

        if not (env_path / "conda-meta").is_dir():
            self._log_training_message(f"[TensorBoard] Error: Conda environment not found at {env_path}.")
            QMessageBox.critical(self, "Setup Error", f"Conda environment not found at {env_path} for TensorBoard.")
            return

        if not tensorboard_log_dir.is_dir():
            # TensorBoard will create it, but good to inform user if it's missing initially
            self._log_training_message(f"[TensorBoard] Log directory {tensorboard_log_dir} does not exist yet. TensorBoard will attempt to create it.")
            # os.makedirs(tensorboard_log_dir, exist_ok=True) # Or create it

        self._log_training_message("[TensorBoard] Attempting to launch TensorBoard...")
        self.training_status_label.setText("Training Status: Launching TensorBoard...")
        self.tensorboard_url_opened = False # Reset flag

        command_parts = [
            "conda", "run", "-p", str(env_path),
            "tensorboard", "--logdir", str(tensorboard_log_dir)
            # Consider adding --port 6006 if not default or if issues arise
        ]
        self._log_training_message(f"[TensorBoard] Executing: {' '.join(command_parts)}")

        self.tensorboard_process = QProcess()
        self.tensorboard_process.setWorkingDirectory(str(pvp_ml_path))
        self.tensorboard_process.setProcessChannelMode(QProcess.MergedChannels)
        self.tensorboard_process.readyReadStandardOutput.connect(self.on_tensorboard_output)
        self.tensorboard_process.finished.connect(self.on_tensorboard_finished) # Generic finished handler
        self.tensorboard_process.errorOccurred.connect(self.on_tensorboard_process_error)

        self.tensorboard_process.start(command_parts[0], command_parts[1:])

        if not self.tensorboard_process.waitForStarted(5000):
            self._log_training_message("[TensorBoard] Error: Failed to start TensorBoard process.")
            self.training_status_label.setText("Training Status: TensorBoard failed to start")
            self.tensorboard_process = None
        else:
            self._log_training_message("[TensorBoard] Process started. Waiting for URL...")
            # Optionally disable launch_tensorboard_button here until it finishes
            # self.launch_tensorboard_button.setEnabled(False)


    def on_tensorboard_output(self):
        if self.tensorboard_process:
            output = self.tensorboard_process.readAllStandardOutput().data().decode().strip()
            if output:
                self._log_training_message(f"[TensorBoard] {output}")
                # Basic check for URL, might need to be more robust
                if "http://localhost:6006" in output and not self.tensorboard_url_opened:
                    try:
                        QDesktopServices.openUrl(QUrl("http://localhost:6006"))
                        self.tensorboard_url_opened = True
                        self._log_training_message("[TensorBoard] Opened URL http://localhost:6006 in browser.")
                        self.training_status_label.setText("Training Status: TensorBoard Running at http://localhost:6006")
                    except Exception as e:
                        self._log_training_message(f"[TensorBoard] Failed to open URL automatically: {e}")
                elif "E0701" in output or "Error" in output: # Example error check
                     self.training_status_label.setText("Training Status: TensorBoard Error (see log)")


    def on_tensorboard_process_error(self, error):
        if self.tensorboard_process:
            error_map = {
                QProcess.FailedToStart: "Failed to start", QProcess.Crashed: "Crashed",
                QProcess.Timedout: "Timed out", QProcess.ReadError: "Read error",
                QProcess.WriteError: "Write error", QProcess.UnknownError: "Unknown error"
            }
            tb_error_msg = error_map.get(error, 'Unknown QProcess error')
            self._log_training_message(f"[TensorBoard] QProcess error: {tb_error_msg}")
            self.training_status_label.setText(f"Training Status: TensorBoard Process Error ({tb_error_msg})")
            # self.launch_tensorboard_button.setEnabled(True) # Re-enable if start failed critically

    def on_tensorboard_finished(self, exit_code, exit_status):
        # TensorBoard is a server, so it finishing usually means it was stopped or crashed.
        self._log_training_message(f"[TensorBoard] Process terminated. Exit code: {exit_code}, Status: {exit_status}")
        if exit_status == QProcess.CrashExit:
            self.training_status_label.setText("Training Status: TensorBoard Crashed")
        elif exit_code != 0 and exit_code is not None : # None if killed perhaps
             self.training_status_label.setText(f"Training Status: TensorBoard Stopped (Code: {exit_code})")
        else: # Normal exit (e.g. if killed by user from terminal)
             self.training_status_label.setText("Training Status: TensorBoard Stopped")

        if self.tensorboard_process:
            self.tensorboard_process.deleteLater()
            self.tensorboard_process = None
        # self.launch_tensorboard_button.setEnabled(True) # Re-enable button

    def on_task_selected_for_training(self, env_config):
        """Handle when a task is selected for training."""
        logger.info("Task selected for training - creating custom environment configuration")
        
        # This could be enhanced to automatically set up training configuration
        # For now, just show a message with the environment info
        task_name = env_config.get('name', 'Unknown Task')
        QMessageBox.information(
            self,
            "Task Environment Created",
            f"Environment configuration created for: {task_name}\n\n"
            f"You can now use this configuration in the Training tab.\n"
            f"The environment has been customized for this specific task."
        )
        
        # TODO: Could automatically create/update training config files here


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
