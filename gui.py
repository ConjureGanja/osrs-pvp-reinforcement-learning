#!/usr/bin/env python3
"""
OSRS PvP Reinforcement Learning - GUI Launcher

A user-friendly GUI for managing the complete OSRS PvP RL workflow.
This launches the web-based GUI interface.
"""

import sys
import os
from pathlib import Path

def main():
    """Main entry point for the GUI application."""
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "pvp-ml").exists() or not (current_dir / "simulation-rsps").exists():
        print("❌ Please run this script from the project root directory")
        print("   Expected to find 'pvp-ml' and 'simulation-rsps' directories")
        sys.exit(1)
    
    # Launch web GUI
    try:
        print("🌐 Launching OSRS PvP RL Web GUI...")
        from web_gui import OSRSWebGUI
        
        import argparse
        parser = argparse.ArgumentParser(description="OSRS PvP RL GUI")
        parser.add_argument("--port", type=int, default=8080, help="Port for web GUI")
        args, unknown = parser.parse_known_args()
        
        app = OSRSWebGUI(port=args.port)
        app.run()
        
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        print("\n💡 Manual alternatives:")
        print("   ./launch.sh train --help    # Direct CLI training")
        print("   ./launch.sh setup           # Run setup script")
        print("   See SETUP_GUIDE.md for full instructions")
        sys.exit(1)


if __name__ == "__main__":
    main()


@dataclass
class TrainingJob:
    """Represents an active training job."""
    id: str
    preset: str
    process: Optional[subprocess.Popen]
    status: str = "Starting"
    start_time: Optional[float] = None


class ProcessManager:
    """Manages background processes for the GUI."""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.conda_env_path = Path(__file__).parent / "pvp-ml" / "env"
        
    def start_process(self, name: str, command: List[str], cwd: Optional[Path] = None) -> bool:
        """Start a background process."""
        if name in self.processes and self.processes[name].poll() is None:
            return False  # Process already running
            
        try:
            # Use conda environment
            conda_cmd = ["conda", "run", "-p", str(self.conda_env_path)] + command
            
            process = subprocess.Popen(
                conda_cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[name] = process
            return True
            
        except Exception as e:
            print(f"Failed to start {name}: {e}")
            return False
            
    def stop_process(self, name: str) -> bool:
        """Stop a background process."""
        if name not in self.processes:
            return False
            
        process = self.processes[name]
        if process.poll() is None:  # Still running
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                
        del self.processes[name]
        return True
        
    def is_running(self, name: str) -> bool:
        """Check if a process is running."""
        if name not in self.processes:
            return False
        return self.processes[name].poll() is None
        
    def get_output(self, name: str) -> tuple[str, str]:
        """Get stdout and stderr from a process."""
        if name not in self.processes:
            return "", ""
            
        process = self.processes[name]
        try:
            stdout, stderr = process.communicate(timeout=0.1)
            return stdout, stderr
        except subprocess.TimeoutExpired:
            return "", ""
            
    def cleanup(self):
        """Clean up all processes."""
        for name in list(self.processes.keys()):
            self.stop_process(name)


class OSRSPvPGUI:
    """Main GUI application for OSRS PvP Reinforcement Learning."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OSRS PvP Reinforcement Learning")
        self.root.geometry("1000x700")
        
        # Set up paths
        self.project_root = Path(__file__).parent
        self.pvp_ml_dir = self.project_root / "pvp-ml"
        self.simulation_dir = self.project_root / "simulation-rsps" / "ElvargServer"
        self.config_dir = self.pvp_ml_dir / "config"
        self.models_dir = self.pvp_ml_dir / "models"
        
        # Initialize process manager
        self.process_manager = ProcessManager()
        
        # Training state
        self.current_training_job: Optional[TrainingJob] = None
        
        # Create GUI
        self.setup_gui()
        
        # Set up periodic updates
        self.root.after(1000, self.update_status)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_gui(self):
        """Set up the main GUI layout."""
        # Configure styles
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="OSRS PvP Reinforcement Learning", 
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_setup_tab()
        self.create_training_tab()
        self.create_evaluation_tab()
        self.create_monitoring_tab()
        self.create_api_tab()
        self.create_simulation_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def create_setup_tab(self):
        """Create the setup and validation tab."""
        setup_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(setup_frame, text="Setup & Validation")
        
        # Environment status
        ttk.Label(setup_frame, text="Environment Status", style='Subtitle.TLabel').grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        # Status indicators
        self.setup_status_frame = ttk.Frame(setup_frame)
        self.setup_status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Create status labels
        self.status_labels = {}
        status_items = [
            ("conda", "Conda Environment"),
            ("python", "Python Packages"),
            ("java", "Java Runtime"),
            ("simulation", "Simulation Server"),
        ]
        
        for i, (key, label) in enumerate(status_items):
            ttk.Label(self.setup_status_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, padx=(0, 10))
            status_label = ttk.Label(self.setup_status_frame, text="Checking...")
            status_label.grid(row=i, column=1, sticky=tk.W)
            self.status_labels[key] = status_label
            
        # Action buttons
        button_frame = ttk.Frame(setup_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(
            button_frame, 
            text="Check Environment", 
            command=self.check_environment
        ).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="Repair/Reinstall", 
            command=self.repair_environment
        ).grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="Open Setup Guide", 
            command=self.open_setup_guide
        ).grid(row=0, column=2)
        
        # Setup log
        ttk.Label(setup_frame, text="Setup Log", style='Subtitle.TLabel').grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(20, 10)
        )
        
        self.setup_log = scrolledtext.ScrolledText(
            setup_frame, 
            width=80, 
            height=15, 
            state=tk.DISABLED
        )
        self.setup_log.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        setup_frame.grid_rowconfigure(4, weight=1)
        setup_frame.grid_columnconfigure(0, weight=1)
        
    def create_training_tab(self):
        """Create the training management tab."""
        train_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(train_frame, text="Training")
        
        # Training configuration
        config_frame = ttk.LabelFrame(train_frame, text="Training Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Preset selection
        ttk.Label(config_frame, text="Preset:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(
            config_frame, 
            textvariable=self.preset_var,
            state="readonly",
            width=30
        )
        self.preset_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(
            config_frame, 
            text="Refresh", 
            command=self.refresh_presets
        ).grid(row=0, column=2)
        
        # Training options
        options_frame = ttk.Frame(config_frame)
        options_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        self.distributed_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, 
            text="Distributed Training", 
            variable=self.distributed_var
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(options_frame, text="Parallel Workers:").grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.workers_var = tk.StringVar(value="auto")
        workers_entry = ttk.Entry(options_frame, textvariable=self.workers_var, width=10)
        workers_entry.grid(row=0, column=2, sticky=tk.W)
        
        # Training control
        control_frame = ttk.LabelFrame(train_frame, text="Training Control", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, columnspan=2)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Start Training", 
            command=self.start_training,
            style='Accent.TButton'
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="Stop Training", 
            command=self.stop_training,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="View Progress", 
            command=self.open_tensorboard
        ).grid(row=0, column=2)
        
        # Training status
        self.training_status_var = tk.StringVar(value="No training active")
        ttk.Label(control_frame, textvariable=self.training_status_var).grid(
            row=1, column=0, columnspan=2, pady=(10, 0)
        )
        
        # Training log
        ttk.Label(train_frame, text="Training Log", style='Subtitle.TLabel').grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        
        self.training_log = scrolledtext.ScrolledText(
            train_frame, 
            width=80, 
            height=20, 
            state=tk.DISABLED
        )
        self.training_log.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        train_frame.grid_rowconfigure(3, weight=1)
        train_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize presets
        self.refresh_presets()
        
    def create_evaluation_tab(self):
        """Create the model evaluation tab."""
        eval_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(eval_frame, text="Evaluation")
        
        # Model selection
        model_frame = ttk.LabelFrame(eval_frame, text="Model Selection", padding="10")
        model_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(model_frame, text="Model:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.model_var,
            state="readonly",
            width=40
        )
        self.model_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Button(
            model_frame, 
            text="Browse...", 
            command=self.browse_model
        ).grid(row=0, column=2, padx=(0, 10))
        
        ttk.Button(
            model_frame, 
            text="Refresh", 
            command=self.refresh_models
        ).grid(row=0, column=3)
        
        # Evaluation control
        eval_control_frame = ttk.LabelFrame(eval_frame, text="Evaluation Control", padding="10")
        eval_control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Control buttons
        eval_button_frame = ttk.Frame(eval_control_frame)
        eval_button_frame.grid(row=0, column=0, columnspan=2)
        
        self.start_eval_button = ttk.Button(
            eval_button_frame, 
            text="Start Evaluation", 
            command=self.start_evaluation
        )
        self.start_eval_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_eval_button = ttk.Button(
            eval_button_frame, 
            text="Stop Evaluation", 
            command=self.stop_evaluation,
            state=tk.DISABLED
        )
        self.stop_eval_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(
            eval_button_frame, 
            text="Start Simulation", 
            command=self.start_simulation
        ).grid(row=0, column=2)
        
        # Evaluation status
        self.eval_status_var = tk.StringVar(value="Ready for evaluation")
        ttk.Label(eval_control_frame, textvariable=self.eval_status_var).grid(
            row=1, column=0, columnspan=2, pady=(10, 0)
        )
        
        # Evaluation log
        ttk.Label(eval_frame, text="Evaluation Log", style='Subtitle.TLabel').grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        
        self.eval_log = scrolledtext.ScrolledText(
            eval_frame, 
            width=80, 
            height=20, 
            state=tk.DISABLED
        )
        self.eval_log.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        eval_frame.grid_rowconfigure(3, weight=1)
        eval_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize models
        self.refresh_models()
        
    def create_monitoring_tab(self):
        """Create the monitoring and tensorboard tab."""
        monitor_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(monitor_frame, text="Monitoring")
        
        # Tensorboard control
        tb_frame = ttk.LabelFrame(monitor_frame, text="Tensorboard", padding="10")
        tb_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        tb_button_frame = ttk.Frame(tb_frame)
        tb_button_frame.grid(row=0, column=0)
        
        self.start_tb_button = ttk.Button(
            tb_button_frame, 
            text="Start Tensorboard", 
            command=self.start_tensorboard
        )
        self.start_tb_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_tb_button = ttk.Button(
            tb_button_frame, 
            text="Stop Tensorboard", 
            command=self.stop_tensorboard,
            state=tk.DISABLED
        )
        self.stop_tb_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(
            tb_button_frame, 
            text="Open in Browser", 
            command=self.open_tensorboard
        ).grid(row=0, column=2)
        
        self.tb_status_var = tk.StringVar(value="Tensorboard not running")
        ttk.Label(tb_frame, textvariable=self.tb_status_var).grid(
            row=1, column=0, pady=(10, 0)
        )
        
        # System metrics
        metrics_frame = ttk.LabelFrame(monitor_frame, text="System Metrics", padding="10")
        metrics_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create metrics display
        self.metrics_text = tk.Text(
            metrics_frame, 
            width=60, 
            height=8, 
            state=tk.DISABLED,
            font=('Courier', 10)
        )
        self.metrics_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Experiment log
        ttk.Label(monitor_frame, text="Experiment Log", style='Subtitle.TLabel').grid(
            row=2, column=0, sticky=tk.W, pady=(10, 5)
        )
        
        self.experiment_log = scrolledtext.ScrolledText(
            monitor_frame, 
            width=80, 
            height=15, 
            state=tk.DISABLED
        )
        self.experiment_log.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        monitor_frame.grid_rowconfigure(3, weight=1)
        monitor_frame.grid_columnconfigure(0, weight=1)
        
    def create_api_tab(self):
        """Create the API server management tab."""
        api_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(api_frame, text="API Server")
        
        # Server configuration
        config_frame = ttk.LabelFrame(api_frame, text="Server Configuration", padding="10")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Host and port settings
        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.api_host_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(config_frame, textvariable=self.api_host_var, width=15).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 20)
        )
        
        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.api_port_var = tk.StringVar(value="9999")
        ttk.Entry(config_frame, textvariable=self.api_port_var, width=10).grid(
            row=0, column=3, sticky=tk.W
        )
        
        # Server control
        control_frame = ttk.LabelFrame(api_frame, text="Server Control", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        api_button_frame = ttk.Frame(control_frame)
        api_button_frame.grid(row=0, column=0)
        
        self.start_api_button = ttk.Button(
            api_button_frame, 
            text="Start API Server", 
            command=self.start_api_server
        )
        self.start_api_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_api_button = ttk.Button(
            api_button_frame, 
            text="Stop API Server", 
            command=self.stop_api_server,
            state=tk.DISABLED
        )
        self.stop_api_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(
            api_button_frame, 
            text="Test Connection", 
            command=self.test_api_connection
        ).grid(row=0, column=2)
        
        self.api_status_var = tk.StringVar(value="API server not running")
        ttk.Label(control_frame, textvariable=self.api_status_var).grid(
            row=1, column=0, pady=(10, 0)
        )
        
        # API documentation
        docs_frame = ttk.LabelFrame(api_frame, text="API Documentation", padding="10")
        docs_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        docs_text = tk.Text(docs_frame, width=80, height=8, state=tk.DISABLED)
        docs_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Insert API documentation
        docs_content = """API Endpoints:
- Connect: Send JSON request with model name and observation data
- Response: JSON with predicted actions and probabilities

Example Python client:
import socket, json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 9999))
request = {'model': 'GeneralizedNh', 'observation': [...], 'action_masks': [...]}
sock.send(json.dumps(request).encode())
response = json.loads(sock.recv(4096).decode())
print(response['action'])
"""
        
        docs_text.config(state=tk.NORMAL)
        docs_text.insert(tk.END, docs_content)
        docs_text.config(state=tk.DISABLED)
        
        # API log
        ttk.Label(api_frame, text="API Server Log", style='Subtitle.TLabel').grid(
            row=3, column=0, sticky=tk.W, pady=(10, 5)
        )
        
        self.api_log = scrolledtext.ScrolledText(
            api_frame, 
            width=80, 
            height=15, 
            state=tk.DISABLED
        )
        self.api_log.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        api_frame.grid_rowconfigure(4, weight=1)
        api_frame.grid_columnconfigure(0, weight=1)
        
    def create_simulation_tab(self):
        """Create the simulation server tab."""
        sim_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(sim_frame, text="Simulation")
        
        # Simulation control
        control_frame = ttk.LabelFrame(sim_frame, text="Simulation Control", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        sim_button_frame = ttk.Frame(control_frame)
        sim_button_frame.grid(row=0, column=0)
        
        self.start_sim_button = ttk.Button(
            sim_button_frame, 
            text="Start Simulation", 
            command=self.start_simulation
        )
        self.start_sim_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_sim_button = ttk.Button(
            sim_button_frame, 
            text="Stop Simulation", 
            command=self.stop_simulation,
            state=tk.DISABLED
        )
        self.stop_sim_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(
            sim_button_frame, 
            text="Open Client Guide", 
            command=self.open_client_guide
        ).grid(row=0, column=2)
        
        self.sim_status_var = tk.StringVar(value="Simulation not running")
        ttk.Label(control_frame, textvariable=self.sim_status_var).grid(
            row=1, column=0, pady=(10, 0)
        )
        
        # Connection info
        info_frame = ttk.LabelFrame(sim_frame, text="Connection Information", padding="10")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        info_text = tk.Text(info_frame, width=80, height=6, state=tk.DISABLED)
        info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        info_content = """Game Server: localhost:43595 (for RSPS clients)
RL API Server: localhost:43594 (for training/evaluation)

To connect with game client:
1. Clone: git clone https://github.com/RSPSApp/elvarg-rsps.git
2. cd elvarg-rsps/ElvargClient
3. ./gradlew run
4. Connect to localhost:43595
"""
        
        info_text.config(state=tk.NORMAL)
        info_text.insert(tk.END, info_content)
        info_text.config(state=tk.DISABLED)
        
        # Simulation log
        ttk.Label(sim_frame, text="Simulation Log", style='Subtitle.TLabel').grid(
            row=2, column=0, sticky=tk.W, pady=(10, 5)
        )
        
        self.sim_log = scrolledtext.ScrolledText(
            sim_frame, 
            width=80, 
            height=20, 
            state=tk.DISABLED
        )
        self.sim_log.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        sim_frame.grid_rowconfigure(3, weight=1)
        sim_frame.grid_columnconfigure(0, weight=1)
        
    def log_to_widget(self, widget: scrolledtext.ScrolledText, message: str, level: str = "INFO"):
        """Log a message to a text widget."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}\n"
        
        widget.config(state=tk.NORMAL)
        widget.insert(tk.END, formatted_message)
        widget.see(tk.END)
        widget.config(state=tk.DISABLED)
        
    def update_status(self):
        """Update GUI status periodically."""
        # Update process statuses
        self.update_process_statuses()
        
        # Update system metrics
        self.update_system_metrics()
        
        # Schedule next update
        self.root.after(5000, self.update_status)
        
    def update_process_statuses(self):
        """Update the status of all running processes."""
        # Training status
        if self.current_training_job:
            if self.process_manager.is_running("training"):
                elapsed = time.time() - (self.current_training_job.start_time or 0)
                self.training_status_var.set(
                    f"Training '{self.current_training_job.preset}' - Running for {elapsed/60:.1f} minutes"
                )
            else:
                self.training_status_var.set("Training completed or stopped")
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.current_training_job = None
                
        # API status
        if self.process_manager.is_running("api"):
            host = self.api_host_var.get()
            port = self.api_port_var.get()
            self.api_status_var.set(f"API server running on {host}:{port}")
            self.start_api_button.config(state=tk.DISABLED)
            self.stop_api_button.config(state=tk.NORMAL)
        else:
            self.api_status_var.set("API server not running")
            self.start_api_button.config(state=tk.NORMAL)
            self.stop_api_button.config(state=tk.DISABLED)
            
        # Simulation status
        if self.process_manager.is_running("simulation"):
            self.sim_status_var.set("Simulation server running")
            self.start_sim_button.config(state=tk.DISABLED)
            self.stop_sim_button.config(state=tk.NORMAL)
        else:
            self.sim_status_var.set("Simulation server not running")
            self.start_sim_button.config(state=tk.NORMAL)
            self.stop_sim_button.config(state=tk.DISABLED)
            
        # Tensorboard status
        if self.process_manager.is_running("tensorboard"):
            self.tb_status_var.set("Tensorboard running on http://localhost:6006")
            self.start_tb_button.config(state=tk.DISABLED)
            self.stop_tb_button.config(state=tk.NORMAL)
        else:
            self.tb_status_var.set("Tensorboard not running")
            self.start_tb_button.config(state=tk.NORMAL)
            self.stop_tb_button.config(state=tk.DISABLED)
            
        # Evaluation status
        if self.process_manager.is_running("evaluation"):
            self.eval_status_var.set("Evaluation in progress...")
            self.start_eval_button.config(state=tk.DISABLED)
            self.stop_eval_button.config(state=tk.NORMAL)
        else:
            self.eval_status_var.set("Ready for evaluation")
            self.start_eval_button.config(state=tk.NORMAL)
            self.stop_eval_button.config(state=tk.DISABLED)
            
    def update_system_metrics(self):
        """Update system metrics display."""
        try:
            # Get basic system info
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics_text = f"""CPU Usage: {cpu_percent:5.1f}%
Memory:    {memory.percent:5.1f}% ({memory.used / (1024**3):4.1f}GB / {memory.total / (1024**3):4.1f}GB)
Disk:      {disk.percent:5.1f}% ({disk.used / (1024**3):5.1f}GB / {disk.total / (1024**3):5.1f}GB)

Active Processes:
"""
            
            # List active ML processes
            for name in ["training", "api", "simulation", "tensorboard", "evaluation"]:
                status = "Running" if self.process_manager.is_running(name) else "Stopped"
                metrics_text += f"  {name.title():12} {status}\n"
                
            self.metrics_text.config(state=tk.NORMAL)
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, metrics_text)
            self.metrics_text.config(state=tk.DISABLED)
            
        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            # Other errors
            pass
            
    def check_environment(self):
        """Check the environment setup."""
        self.log_to_widget(self.setup_log, "Checking environment...")
        
        # Check conda environment
        try:
            result = subprocess.run(
                ["conda", "info", "--envs"],
                capture_output=True, text=True, timeout=30
            )
            if str(self.process_manager.conda_env_path) in result.stdout:
                self.status_labels["conda"].config(text="✅ OK", style='Success.TLabel')
            else:
                self.status_labels["conda"].config(text="❌ Missing", style='Error.TLabel')
        except Exception:
            self.status_labels["conda"].config(text="❌ Error", style='Error.TLabel')
            
        # Check Python packages
        try:
            result = subprocess.run([
                "conda", "run", "-p", str(self.process_manager.conda_env_path),
                "python", "-c", "import pvp_ml; print('OK')"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.status_labels["python"].config(text="✅ OK", style='Success.TLabel')
            else:
                self.status_labels["python"].config(text="❌ Missing", style='Error.TLabel')
        except Exception:
            self.status_labels["python"].config(text="❌ Error", style='Error.TLabel')
            
        # Check Java
        try:
            result = subprocess.run([
                "conda", "run", "-p", str(self.process_manager.conda_env_path),
                "java", "--version"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "17" in result.stdout:
                self.status_labels["java"].config(text="✅ OK (Java 17)", style='Success.TLabel')
            else:
                self.status_labels["java"].config(text="⚠️ Version issue", style='Warning.TLabel')
        except Exception:
            self.status_labels["java"].config(text="❌ Error", style='Error.TLabel')
            
        # Check simulation
        gradlew = self.simulation_dir / "gradlew"
        if gradlew.exists():
            self.status_labels["simulation"].config(text="✅ OK", style='Success.TLabel')
        else:
            self.status_labels["simulation"].config(text="❌ Missing", style='Error.TLabel')
            
        self.log_to_widget(self.setup_log, "Environment check completed")
        
    def repair_environment(self):
        """Repair the environment by running setup script."""
        if messagebox.askquestion(
            "Confirm Repair", 
            "This will reinstall the conda environment. Continue?"
        ) == "yes":
            self.log_to_widget(self.setup_log, "Starting environment repair...")
            
            # Run setup script in background
            def run_repair():
                try:
                    setup_script = self.project_root / "setup.py"
                    process = subprocess.Popen([
                        sys.executable, str(setup_script)
                    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                    
                    for line in process.stdout:
                        self.root.after(0, lambda l=line: self.log_to_widget(self.setup_log, l.strip()))
                        
                    process.wait()
                    if process.returncode == 0:
                        self.root.after(0, lambda: self.log_to_widget(self.setup_log, "✅ Repair completed successfully"))
                        self.root.after(0, self.check_environment)
                    else:
                        self.root.after(0, lambda: self.log_to_widget(self.setup_log, "❌ Repair failed", "ERROR"))
                        
                except Exception as e:
                    self.root.after(0, lambda: self.log_to_widget(self.setup_log, f"❌ Repair error: {e}", "ERROR"))
                    
            threading.Thread(target=run_repair, daemon=True).start()
            
    def open_setup_guide(self):
        """Open the setup guide in default application."""
        setup_guide = self.project_root / "SETUP_GUIDE.md"
        if setup_guide.exists():
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', str(setup_guide)])
            elif sys.platform.startswith('win'):  # Windows
                os.startfile(str(setup_guide))
            else:  # Linux
                subprocess.run(['xdg-open', str(setup_guide)])
        else:
            messagebox.showerror("Error", "SETUP_GUIDE.md not found")
            
    def refresh_presets(self):
        """Refresh the list of available training presets."""
        presets = []
        
        if self.config_dir.exists():
            for yaml_file in self.config_dir.glob("*.yml"):
                try:
                    with open(yaml_file, 'r') as f:
                        config_data = yaml.safe_load(f)
                        if isinstance(config_data, dict):
                            presets.extend(config_data.keys())
                except Exception:
                    pass
                    
        self.preset_combo['values'] = sorted(presets)
        if presets and not self.preset_var.get():
            self.preset_var.set(presets[0])
            
    def refresh_models(self):
        """Refresh the list of available models."""
        models = []
        
        if self.models_dir.exists():
            for model_dir in self.models_dir.iterdir():
                if model_dir.is_dir():
                    models.append(f"models/{model_dir.name}")
                    
        self.model_combo['values'] = sorted(models)
        if models and not self.model_var.get():
            self.model_var.set(models[0])
            
    def browse_model(self):
        """Browse for a model file."""
        filename = filedialog.askdirectory(
            title="Select Model Directory",
            initialdir=str(self.models_dir) if self.models_dir.exists() else str(self.project_root)
        )
        if filename:
            # Convert to relative path if possible
            try:
                rel_path = Path(filename).relative_to(self.project_root)
                self.model_var.set(str(rel_path))
            except ValueError:
                self.model_var.set(filename)
                
    def start_training(self):
        """Start a training job."""
        preset = self.preset_var.get()
        if not preset:
            messagebox.showerror("Error", "Please select a training preset")
            return
            
        # Build command
        command = ["train", "--preset", preset]
        
        if self.distributed_var.get():
            command.append("--distribute")
            workers = self.workers_var.get().strip()
            if workers and workers != "auto":
                try:
                    int(workers)  # Validate it's a number
                    command.append(workers)
                except ValueError:
                    messagebox.showerror("Error", "Worker count must be a number or 'auto'")
                    return
                    
        # Start training process
        if self.process_manager.start_process("training", command):
            self.current_training_job = TrainingJob(
                id=f"gui_{int(time.time())}",
                preset=preset,
                process=self.process_manager.processes.get("training"),
                start_time=time.time()
            )
            
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.training_status_var.set(f"Starting training with preset '{preset}'...")
            self.log_to_widget(self.training_log, f"Started training: {' '.join(command)}")
        else:
            messagebox.showerror("Error", "Failed to start training process")
            
    def stop_training(self):
        """Stop the current training job."""
        if self.process_manager.stop_process("training"):
            self.log_to_widget(self.training_log, "Training stopped by user")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.current_training_job = None
            self.training_status_var.set("Training stopped")
            
    def start_evaluation(self):
        """Start model evaluation."""
        model_path = self.model_var.get()
        if not model_path:
            messagebox.showerror("Error", "Please select a model")
            return
            
        command = ["eval", "--model-path", model_path]
        
        if self.process_manager.start_process("evaluation", command):
            self.log_to_widget(self.eval_log, f"Started evaluation: {model_path}")
        else:
            messagebox.showerror("Error", "Failed to start evaluation")
            
    def stop_evaluation(self):
        """Stop model evaluation."""
        if self.process_manager.stop_process("evaluation"):
            self.log_to_widget(self.eval_log, "Evaluation stopped by user")
            
    def start_api_server(self):
        """Start the API server."""
        host = self.api_host_var.get()
        port = self.api_port_var.get()
        
        command = ["serve-api", "--host", host, "--port", port]
        
        if self.process_manager.start_process("api", command):
            self.log_to_widget(self.api_log, f"API server started on {host}:{port}")
        else:
            messagebox.showerror("Error", "Failed to start API server")
            
    def stop_api_server(self):
        """Stop the API server."""
        if self.process_manager.stop_process("api"):
            self.log_to_widget(self.api_log, "API server stopped")
            
    def test_api_connection(self):
        """Test API server connection."""
        host = self.api_host_var.get()
        port = self.api_port_var.get()
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            
            if result == 0:
                messagebox.showinfo("Connection Test", f"✅ Successfully connected to {host}:{port}")
            else:
                messagebox.showerror("Connection Test", f"❌ Failed to connect to {host}:{port}")
        except Exception as e:
            messagebox.showerror("Connection Test", f"❌ Error: {e}")
            
    def start_simulation(self):
        """Start the simulation server."""
        # Check if gradlew exists
        gradlew = self.simulation_dir / "gradlew"
        if not gradlew.exists():
            messagebox.showerror("Error", "Gradle wrapper not found in simulation directory")
            return
            
        # Make executable
        os.chmod(gradlew, 0o755)
        
        # Start simulation
        command = ["./gradlew", "run"]
        
        if self.process_manager.start_process("simulation", command, cwd=self.simulation_dir):
            self.log_to_widget(self.sim_log, "Simulation server started")
        else:
            messagebox.showerror("Error", "Failed to start simulation server")
            
    def stop_simulation(self):
        """Stop the simulation server."""
        if self.process_manager.stop_process("simulation"):
            self.log_to_widget(self.sim_log, "Simulation server stopped")
            
    def open_client_guide(self):
        """Open client connection guide."""
        messagebox.showinfo(
            "Client Connection", 
            "To connect a game client:\n\n"
            "1. git clone https://github.com/RSPSApp/elvarg-rsps.git\n"
            "2. cd elvarg-rsps/ElvargClient\n"
            "3. ./gradlew run\n"
            "4. Connect to localhost:43595"
        )
        
    def start_tensorboard(self):
        """Start Tensorboard."""
        command = ["train", "tensorboard"]
        
        if self.process_manager.start_process("tensorboard", command):
            self.log_to_widget(self.experiment_log, "Tensorboard started")
            # Open in browser after a short delay
            self.root.after(3000, lambda: webbrowser.open("http://localhost:6006"))
        else:
            messagebox.showerror("Error", "Failed to start Tensorboard")
            
    def stop_tensorboard(self):
        """Stop Tensorboard."""
        if self.process_manager.stop_process("tensorboard"):
            self.log_to_widget(self.experiment_log, "Tensorboard stopped")
            
    def open_tensorboard(self):
        """Open Tensorboard in browser."""
        webbrowser.open("http://localhost:6006")
        
    def on_closing(self):
        """Handle application closing."""
        if messagebox.askokcancel("Quit", "Stop all processes and quit?"):
            self.process_manager.cleanup()
            self.root.destroy()
            
    def run(self):
        """Run the GUI application."""
        # Initial environment check
        self.root.after(1000, self.check_environment)
        
        # Start the main loop
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "pvp-ml").exists() or not (current_dir / "simulation-rsps").exists():
        print("❌ Please run this script from the project root directory")
        print("   Expected to find 'pvp-ml' and 'simulation-rsps' directories")
        sys.exit(1)
        
    # Check for required dependencies
    missing_deps = []
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter")
        
    try:
        import yaml
    except ImportError:
        missing_deps.append("pyyaml")
        
    if missing_deps:
        print(f"❌ Missing required dependencies: {', '.join(missing_deps)}")
        print("   Install with: conda install tk pyyaml")
        sys.exit(1)
        
    # Create and run GUI
    app = OSRSPvPGUI()
    app.run()


if __name__ == "__main__":
    main()