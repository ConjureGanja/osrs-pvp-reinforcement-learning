"""Task management tab component."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
    QComboBox, QProgressBar, QMessageBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal, pyqtSignal
import logging

# Import task system components - adjust path as needed
try:
    from ..tasks.task_system import TaskManager, TaskCategory, TaskDifficulty, Task
    from .environment_factory import EnvironmentFactory
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tasks.task_system import TaskManager, TaskCategory, TaskDifficulty, Task
    from core.environment_factory import EnvironmentFactory

logger = logging.getLogger(__name__)


class TaskManagementTab(QWidget):
    """Widget for managing OSRS tasks and natural language input."""
    
    # Signal emitted when a task is selected for training
    task_selected_for_training = Signal(dict)  # environment_config
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_manager = TaskManager()
        self.environment_factory = EnvironmentFactory()
        self.current_task = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create main splitter for better layout
        main_splitter = QSplitter(Qt.Vertical)
        layout.addWidget(main_splitter)
        
        # Task creation section
        creation_group = QGroupBox("Create New Task")
        creation_layout = QVBoxLayout(creation_group)
        
        # Natural language input
        input_label = QLabel("Describe your task in plain English:")
        creation_layout.addWidget(input_label)
        
        self.task_description_edit = QTextEdit()
        self.task_description_edit.setPlaceholderText(
            "Examples:\n"
            "- Kill 10 goblins in Lumbridge\n"
            "- Mine 50 iron ore and smelt into bars\n"
            "- Complete the Cook's Assistant quest\n"
            "- Train woodcutting to level 60\n"
            "- Fight other players in the wilderness"
        )
        self.task_description_edit.setMaximumHeight(100)
        creation_layout.addWidget(self.task_description_edit)
        
        # Create task button
        create_button_layout = QHBoxLayout()
        self.create_task_button = QPushButton("Create Task from Description")
        self.create_task_button.clicked.connect(self.create_task_from_description)
        create_button_layout.addWidget(self.create_task_button)
        create_button_layout.addStretch()
        creation_layout.addLayout(create_button_layout)
        
        main_splitter.addWidget(creation_group)
        
        # Task list and details section
        list_details_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(list_details_splitter)
        
        # Task list section
        list_group = QGroupBox("Created Tasks")
        list_layout = QVBoxLayout(list_group)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("All", None)
        for category in TaskCategory:
            self.category_filter.addItem(category.value.title(), category)
        self.category_filter.currentTextChanged.connect(self.filter_tasks)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addWidget(QLabel("Difficulty:"))
        self.difficulty_filter = QComboBox()
        self.difficulty_filter.addItem("All", None)
        for difficulty in TaskDifficulty:
            self.difficulty_filter.addItem(difficulty.value.title(), difficulty)
        self.difficulty_filter.currentTextChanged.connect(self.filter_tasks)
        filter_layout.addWidget(self.difficulty_filter)
        
        filter_layout.addStretch()
        list_layout.addLayout(filter_layout)
        
        # Task list
        self.task_list = QListWidget()
        self.task_list.itemSelectionChanged.connect(self.on_task_selected)
        list_layout.addWidget(self.task_list)
        
        list_details_splitter.addWidget(list_group)
        
        # Task details section
        details_group = QGroupBox("Task Details")
        details_layout = QVBoxLayout(details_group)
        
        # Task info display
        self.task_info_display = QTextEdit()
        self.task_info_display.setReadOnly(True)
        self.task_info_display.setMaximumHeight(200)
        details_layout.addWidget(self.task_info_display)
        
        # Progress section
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        
        self.progress_label = QLabel("Task Progress:")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        details_layout.addWidget(progress_frame)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.train_button = QPushButton("Train Agent on This Task")
        self.train_button.clicked.connect(self.start_training_for_task)
        self.train_button.setEnabled(False)
        action_layout.addWidget(self.train_button)
        
        self.delete_button = QPushButton("Delete Task")
        self.delete_button.clicked.connect(self.delete_task)
        self.delete_button.setEnabled(False)
        action_layout.addWidget(self.delete_button)
        
        action_layout.addStretch()
        details_layout.addLayout(action_layout)
        
        list_details_splitter.addWidget(details_group)
        
        # Set splitter proportions
        list_details_splitter.setSizes([300, 400])
        main_splitter.setSizes([150, 450])
    
    def create_task_from_description(self):
        """Create a new task from the natural language description."""
        description = self.task_description_edit.toPlainText().strip()
        
        if not description:
            QMessageBox.warning(
                self,
                "Empty Description",
                "Please enter a task description."
            )
            return
        
        try:
            # Create task using the task manager
            task = self.task_manager.create_task_from_description(description)
            
            # Add to the task list
            self.add_task_to_list(task)
            
            # Clear the input
            self.task_description_edit.clear()
            
            # Show success message
            QMessageBox.information(
                self,
                "Task Created",
                f"Successfully created task: {task.name}\n"
                f"Category: {task.category.value}\n"
                f"Difficulty: {task.difficulty.value}"
            )
            
            logger.info(f"Created task from description: {task.name}")
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            QMessageBox.critical(
                self,
                "Task Creation Failed",
                f"Failed to create task: {e}"
            )
    
    def add_task_to_list(self, task: Task):
        """Add a task to the task list widget."""
        item = QListWidgetItem()
        item.setText(f"{task.name} ({task.category.value})")
        item.setData(Qt.UserRole, task)
        
        # Set different colors based on difficulty
        if task.difficulty == TaskDifficulty.BEGINNER:
            item.setBackground(Qt.lightGray)
        elif task.difficulty == TaskDifficulty.INTERMEDIATE:
            item.setBackground(Qt.yellow)
        elif task.difficulty == TaskDifficulty.ADVANCED:
            item.setBackground(Qt.magenta)
        elif task.difficulty == TaskDifficulty.EXPERT:
            item.setBackground(Qt.red)
        
        self.task_list.addItem(item)
    
    def filter_tasks(self):
        """Filter tasks based on selected category and difficulty."""
        category_filter = self.category_filter.currentData()
        difficulty_filter = self.difficulty_filter.currentData()
        
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            task = item.data(Qt.UserRole)
            
            show_item = True
            
            if category_filter and task.category != category_filter:
                show_item = False
            
            if difficulty_filter and task.difficulty != difficulty_filter:
                show_item = False
            
            item.setHidden(not show_item)
    
    def on_task_selected(self):
        """Handle task selection."""
        selected_items = self.task_list.selectedItems()
        
        if not selected_items:
            self.current_task = None
            self.task_info_display.clear()
            self.train_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.progress_bar.setValue(0)
            return
        
        item = selected_items[0]
        task = item.data(Qt.UserRole)
        self.current_task = task
        
        # Display task information
        self.display_task_info(task)
        
        # Update progress
        self.update_task_progress(task)
        
        # Enable buttons
        self.train_button.setEnabled(True)
        self.delete_button.setEnabled(True)
    
    def display_task_info(self, task: Task):
        """Display detailed task information."""
        info_text = f"""
<h3>{task.name}</h3>
<p><b>Description:</b> {task.description}</p>
<p><b>Category:</b> {task.category.value.title()}</p>
<p><b>Difficulty:</b> {task.difficulty.value.title()}</p>

<h4>Objectives:</h4>
<ul>
"""
        
        for i, objective in enumerate(task.objectives):
            status = "✓" if objective.completed else "○"
            info_text += f"<li>{status} {objective.description}</li>"
        
        info_text += "</ul>"
        
        if task.requirements.skill_levels:
            info_text += "<h4>Skill Requirements:</h4><ul>"
            for skill, level in task.requirements.skill_levels.items():
                info_text += f"<li>{skill.title()}: {level}</li>"
            info_text += "</ul>"
        
        if task.requirements.items:
            info_text += "<h4>Required Items:</h4><ul>"
            for item in task.requirements.items:
                info_text += f"<li>{item}</li>"
            info_text += "</ul>"
        
        self.task_info_display.setHtml(info_text)
    
    def update_task_progress(self, task: Task):
        """Update the progress bar for a task."""
        if not task.objectives:
            self.progress_bar.setValue(0)
            return
        
        completed_objectives = sum(1 for obj in task.objectives if obj.completed)
        total_objectives = len(task.objectives)
        progress = int((completed_objectives / total_objectives) * 100)
        
        self.progress_bar.setValue(progress)
        self.progress_label.setText(
            f"Task Progress: {completed_objectives}/{total_objectives} objectives completed"
        )
    
    def start_training_for_task(self):
        """Start training the agent for the selected task."""
        if not self.current_task:
            return
        
        try:
            # Create environment configuration for this task
            env_config = self.environment_factory.create_environment_for_task(self.current_task)
            
            # Emit signal to start training
            self.task_selected_for_training.emit(env_config)
            
            logger.info(f"Started training for task: {self.current_task.name}")
            
        except Exception as e:
            logger.error(f"Failed to start training: {e}")
            QMessageBox.critical(
                self,
                "Training Failed",
                f"Failed to start training for this task: {e}"
            )
    
    def delete_task(self):
        """Delete the selected task."""
        if not self.current_task:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Task",
            f"Are you sure you want to delete the task '{self.current_task.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from task manager
            if self.current_task in self.task_manager.tasks:
                self.task_manager.tasks.remove(self.current_task)
            
            # Remove from list widget
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                if item.data(Qt.UserRole) == self.current_task:
                    self.task_list.takeItem(i)
                    break
            
            self.current_task = None
            logger.info("Task deleted")