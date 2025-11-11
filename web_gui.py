#!/usr/bin/env python3
"""
OSRS PvP Reinforcement Learning - Web-Based GUI Interface

A user-friendly web GUI for managing the complete OSRS PvP RL workflow.
This version uses a simple web interface instead of tkinter for better compatibility.
"""

import sys
import os
import subprocess
import threading
import time
import json
import yaml
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import urllib.parse


@dataclass
class ProcessInfo:
    """Information about a running process."""
    name: str
    pid: int
    status: str
    start_time: float


class WebGUIHandler(SimpleHTTPRequestHandler):
    """Custom handler for the web GUI."""
    
    def __init__(self, *args, gui_app=None, **kwargs):
        self.gui_app = gui_app
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self.send_html_response(self.get_main_html())
        elif self.path == '/api/status':
            self.send_json_response(self.gui_app.get_status())
        elif self.path == '/api/presets':
            self.send_json_response(self.gui_app.get_presets())
        elif self.path == '/api/models':
            self.send_json_response(self.gui_app.get_models())
        elif self.path.startswith('/api/logs/'):
            log_type = self.path.split('/')[-1]
            self.send_json_response(self.gui_app.get_logs(log_type))
        elif self.path == '/api/check_environment':
            self.send_json_response(self.gui_app.check_environment())
        else:
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        if self.path == '/api/start_training':
            result = self.gui_app.start_training(data)
            self.send_json_response(result)
        elif self.path == '/api/stop_training':
            result = self.gui_app.stop_training()
            self.send_json_response(result)
        elif self.path == '/api/start_evaluation':
            result = self.gui_app.start_evaluation(data)
            self.send_json_response(result)
        elif self.path == '/api/stop_evaluation':
            result = self.gui_app.stop_evaluation()
            self.send_json_response(result)
        elif self.path == '/api/start_api':
            result = self.gui_app.start_api_server(data)
            self.send_json_response(result)
        elif self.path == '/api/stop_api':
            result = self.gui_app.stop_api_server()
            self.send_json_response(result)
        elif self.path == '/api/start_simulation':
            result = self.gui_app.start_simulation()
            self.send_json_response(result)
        elif self.path == '/api/stop_simulation':
            result = self.gui_app.stop_simulation()
            self.send_json_response(result)
        elif self.path == '/api/start_tensorboard':
            result = self.gui_app.start_tensorboard()
            self.send_json_response(result)
        elif self.path == '/api/stop_tensorboard':
            result = self.gui_app.stop_tensorboard()
            self.send_json_response(result)
        else:
            self.send_error(404)
    
    def send_html_response(self, html):
        """Send HTML response."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def get_main_html(self):
        """Generate the main HTML interface."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSRS PvP Reinforcement Learning</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5;
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .tabs { display: flex; border-bottom: 2px solid #ddd; margin-bottom: 20px; }
        .tab { padding: 10px 20px; cursor: pointer; border: none; background: none; font-size: 16px; }
        .tab.active { border-bottom: 2px solid #007bff; color: #007bff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .status-item { padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745; }
        .status-item.error { border-left-color: #dc3545; }
        .status-item.warning { border-left-color: #ffc107; }
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; margin: 5px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn:hover { opacity: 0.8; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group select, .form-group input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .logs { background: #000; color: #0f0; padding: 15px; border-radius: 5px; height: 300px; overflow-y: scroll; font-family: monospace; }
        .process-status { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .process-running { background: #d4edda; color: #155724; }
        .process-stopped { background: #f8d7da; color: #721c24; }
        .metrics { background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗡️ OSRS PvP Reinforcement Learning</h1>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('setup')">Setup & Status</button>
            <button class="tab" onclick="showTab('training')">Training</button>
            <button class="tab" onclick="showTab('evaluation')">Evaluation</button>
            <button class="tab" onclick="showTab('monitoring')">Monitoring</button>
            <button class="tab" onclick="showTab('api')">API Server</button>
            <button class="tab" onclick="showTab('simulation')">Simulation</button>
        </div>

        <!-- Setup Tab -->
        <div id="setup" class="tab-content active">
            <div class="section">
                <h3>1. Environment Validation</h3>
                <p>This tab checks if your system is correctly configured to run the project. Click the button below to validate your environment.</p>
                <div id="status-grid" class="status-grid">
                    <div class="status-item" id="conda-status">
                        <h4>Conda Environment</h4>
                        <p>Checks for the project-specific conda environment.</p>
                        <div><strong>Status:</strong> <span id="conda-status-text">Not checked</span></div>
                    </div>
                    <div class="status-item" id="python-status">
                        <h4>Python Packages</h4>
                        <p>Verifies that core Python libraries (PyTorch, Ray) are installed.</p>
                        <div><strong>Status:</strong> <span id="python-status-text">Not checked</span></div>
                    </div>
                    <div class="status-item" id="java-status">
                        <h4>Java Runtime</h4>
                        <p>Ensures Java 17 is installed for the simulation server.</p>
                        <div><strong>Status:</strong> <span id="java-status-text">Not checked</span></div>
                    </div>
                    <div class="status-item" id="simulation-status">
                        <h4>Simulation Server</h4>
                        <p>Confirms the simulation server's build files are present.</p>
                        <div><strong>Status:</strong> <span id="simulation-status-text">Not checked</span></div>
                    </div>
                </div>
                <button class="btn btn-primary" onclick="checkEnvironment()">Check Environment</button>
                <button class="btn btn-secondary" onclick="openSetupGuide()">Open Full Setup Guide</button>
            </div>
            <div class="section">
                <h3>Troubleshooting</h3>
                <p>If any checks fail, please refer to the <strong>SETUP_GUIDE.md</strong> for detailed instructions. The most common fix is to re-run the setup script from your terminal:</p>
                <pre style="background: #eee; padding: 10px; border-radius: 5px;"><code>python setup.py</code></pre>
            </div>
        </div>

        <!-- Training Tab -->
        <div id="training" class="tab-content">
            <div class="section">
                <h3>1. Select Training Preset</h3>
                <p>Choose a configuration for the training session. 'fast' presets are for testing, while others are for full training runs.</p>
                <div class="form-group">
                    <label for="preset-select">Training Preset:</label>
                    <select id="preset-select">
                        <option value="">Loading presets...</option>
                    </select>
                </div>
            </div>
            <div class="section">
                <h3>2. Configure Training Options</h3>
                <p>For advanced users, enable distributed training to use multiple CPU cores.</p>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="distributed-training"> Distributed Training (uses all CPU cores)
                    </label>
                </div>
                <div class="form-group">
                    <label for="workers-input">Override Parallel Workers:</label>
                    <input type="text" id="workers-input" value="auto" placeholder="auto or number">
                </div>
            </div>
            <div class="section">
                <h3>3. Start and Monitor Training</h3>
                <p>Start the training process and monitor the output in the logs below. You can also use TensorBoard for detailed metrics.</p>
                <div>
                    <button class="btn btn-success" id="start-training-btn" onclick="startTraining()">Start Training</button>
                    <button class="btn btn-danger" id="stop-training-btn" onclick="stopTraining()" disabled>Stop Training</button>
                    <button class="btn btn-primary" onclick="openTensorboard()">View Progress in TensorBoard</button>
                </div>
                <div id="training-status" style="margin-top: 15px; font-weight: bold;">Status: Not running</div>
            </div>
            <div class="section">
                <h3>Training Logs</h3>
                <div id="training-logs" class="logs">Waiting for training to start...</div>
            </div>
        </div>

        <!-- Evaluation Tab -->
        <div id="evaluation" class="tab-content">
            <div class="section">
                <h3>1. Start the Simulation Server</h3>
                <p>Evaluation requires the simulation server to be running. You can start it from the <strong>Simulation</strong> tab or by using the button below.</p>
                <button class="btn btn-primary" onclick="startSimulation()">Start Simulation Server</button>
                 <div id="eval-sim-status" style="margin-top: 10px;">Simulation Status: <span class="process-stopped">Stopped</span></div>
            </div>
            <div class="section">
                <h3>2. Select a Model to Evaluate</h3>
                <p>Choose a trained model from the list below. New models will appear here after training is complete.</p>
                <div class="form-group">
                    <label for="model-select">Model:</label>
                    <select id="model-select">
                        <option value="">Loading models...</option>
                    </select>
                </div>
            </div>
            <div class="section">
                <h3>3. Run Evaluation</h3>
                <p>Start the evaluation to see how the model performs. The AI will play against itself in the simulation.</p>
                <div>
                    <button class="btn btn-success" id="start-eval-btn" onclick="startEvaluation()">Start Evaluation</button>
                    <button class="btn btn-danger" id="stop-eval-btn" onclick="stopEvaluation()" disabled>Stop Evaluation</button>
                </div>
                <div id="evaluation-status" style="margin-top: 15px; font-weight: bold;">Status: Not running</div>
            </div>
            <div class="section">
                <h3>Evaluation Logs</h3>
                <div id="evaluation-logs" class="logs">Waiting for evaluation to start...</div>
            </div>
        </div>

        <!-- Monitoring Tab -->
        <div id="monitoring" class="tab-content">
            <div class="section">
                <h3>Tensorboard</h3>
                <div>
                    <button class="btn btn-success" id="start-tb-btn" onclick="startTensorboard()">Start Tensorboard</button>
                    <button class="btn btn-danger" id="stop-tb-btn" onclick="stopTensorboard()" disabled>Stop Tensorboard</button>
                    <button class="btn btn-primary" onclick="openTensorboard()">Open in Browser</button>
                </div>
                <div id="tensorboard-status" style="margin-top: 15px; font-weight: bold;"></div>
            </div>
            <div class="section">
                <h3>System Metrics</h3>
                <div id="system-metrics" class="metrics">Loading metrics...</div>
            </div>
        </div>

        <!-- API Tab -->
        <div id="api" class="tab-content">
            <div class="section">
                <h3>Serve Models via API</h3>
                <p>This tab allows you to expose a trained model through a TCP socket API. This is for advanced use cases where an external application needs to get actions from the model in real-time.</p>
                <div class="form-group">
                    <label for="api-host">Host:</label>
                    <input type="text" id="api-host" value="127.0.0.1">
                </div>
                <div class="form-group">
                    <label for="api-port">Port:</label>
                    <input type="text" id="api-port" value="9999">
                </div>
                <div>
                    <button class="btn btn-success" id="start-api-btn" onclick="startApiServer()">Start API Server</button>
                    <button class="btn btn-danger" id="stop-api-btn" onclick="stopApiServer()" disabled>Stop API Server</button>
                </div>
                <div id="api-status" style="margin-top: 15px; font-weight: bold;">Status: Not running</div>
            </div>
             <div class="section">
                <h3>API Logs</h3>
                <div id="api-logs" class="logs">Waiting for API server to start...</div>
            </div>
        </div>

        <!-- Simulation Tab -->
        <div id="simulation" class="tab-content">
            <div class="section">
                <h3>1. Start the Simulation Server</h3>
                <p>The simulation server is a modified Old School RuneScape private server that the AI interacts with. It's required for both training and evaluation.</p>
                <div>
                    <button class="btn btn-success" id="start-sim-btn" onclick="startSimulation()">Start Simulation</button>
                    <button class="btn btn-danger" id="stop-sim-btn" onclick="stopSimulation()" disabled>Stop Simulation</button>
                </div>
                <div id="sim-status" style="margin-top: 15px; font-weight: bold;">Status: Not running</div>
            </div>
            <div class="section">
                <h3>2. (Optional) Connect a Game Client to Watch the AI</h3>
                <p>You can watch the AI play by connecting a standard OSRS client to the simulation server.</p>
                <ol>
                    <li><strong>Clone the client:</strong> <pre><code>git clone https://github.com/RSPSApp/elvarg-rsps.git /tmp/elvarg-client</code></pre></li>
                    <li><strong>Run the client:</strong> <pre><code>cd /tmp/elvarg-client/ElvargClient && ./gradlew run</code></pre></li>
                    <li><strong>Connect:</strong> In the client, connect to server address <strong>127.0.0.1</strong> on port <strong>43595</strong>.</li>
                </ol>
                 <div style="margin-top: 15px; padding: 15px; background: #e9ecef; border-radius: 5px;">
                    <strong>Connection Info:</strong><br>
                    - Game Server Port: <strong>43595</strong> (for game clients)<br>
                    - RL Communication Port: <strong>43594</strong> (for the training script)
                </div>
            </div>
            <div class="section">
                <h3>Simulation Logs</h3>
                <div id="simulation-logs" class="logs">Waiting for simulation to start...</div>
            </div>
        </div>
    </div>

    <script>
        let statusUpdateInterval;

        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }

        async function apiCall(endpoint, method = 'GET', data = null) {
            const options = {
                method,
                headers: {'Content-Type': 'application/json'}
            };
            if (data) options.body = JSON.stringify(data);
            
            const response = await fetch(`/api/${endpoint}`, options);
            return await response.json();
        }

        async function updateStatus() {
            try {
                const status = await apiCall('status');
                
                // Update process statuses
                for (const [name, processStatus] of Object.entries(status.processes)) {
                    updateProcessStatus(name, processStatus);
                    if (processStatus.running) {
                        updateLogs(name);
                    }
                }
                
                // Update system metrics
                document.getElementById('system-metrics').textContent = status.system_metrics || 'Metrics unavailable';
                
            } catch (error) {
                console.error('Failed to update status:', error);
            }
        }

        async function updateLogs(processName) {
            try {
                const logData = await apiCall(`logs/${processName}`);
                const logElement = document.getElementById(`${processName}-logs`);
                if (logElement) {
                    logElement.textContent = logData.logs;
                    logElement.scrollTop = logElement.scrollHeight; // Auto-scroll
                }
            } catch (error) {
                console.error(`Failed to update logs for ${processName}:`, error);
            }
        }

        function updateProcessStatus(processName, status) {
            const statusElement = document.getElementById(`${processName}-status`);
            const startBtn = document.getElementById(`start-${processName === 'tensorboard' ? 'tb' : processName === 'evaluation' ? 'eval' : processName === 'simulation' ? 'sim' : processName}-btn`);
            const stopBtn = document.getElementById(`stop-${processName === 'tensorboard' ? 'tb' : processName === 'evaluation' ? 'eval' : processName === 'simulation' ? 'sim' : processName}-btn`);
            
            if (statusElement) statusElement.textContent = status.status;
            
            if (startBtn && stopBtn) {
                if (status.running) {
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                } else {
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                }
            }
        }

        async function loadPresets() {
            const presets = await apiCall('presets');
            const select = document.getElementById('preset-select');
            select.innerHTML = presets.map(preset => 
                `<option value="${preset}">${preset}</option>`
            ).join('');
        }

        async function loadModels() {
            const models = await apiCall('models');
            const select = document.getElementById('model-select');
            select.innerHTML = models.map(model => 
                `<option value="${model}">${model}</option>`
            ).join('');
        }

        async function checkEnvironment() {
            const statusGrid = document.getElementById('status-grid');
            const statuses = ['conda', 'python', 'java', 'simulation'];

            statuses.forEach(id => {
                const item = document.getElementById(`${id}-status`);
                const text = document.getElementById(`${id}-status-text`);
                item.classList.remove('error', 'warning');
                text.textContent = 'Checking...';
            });

            try {
                const result = await apiCall('check_environment');

                for (const [key, value] of Object.entries(result)) {
                    const item = document.getElementById(`${key}-status`);
                    const text = document.getElementById(`${key}-status-text`);

                    text.textContent = value.message;
                    if (value.status === 'Error') {
                        item.classList.add('error');
                    } else if (value.status === 'Warning') {
                        item.classList.add('warning');
                    }
                }
            } catch (error) {
                console.error("Failed to check environment:", error);
                statuses.forEach(id => {
                    const text = document.getElementById(`${id}-status-text`);
                    text.textContent = 'Failed to check.';
                });
            }
        }

        function openSetupGuide() {
            // This is handled by the backend, but we can provide a fallback
            window.open('SETUP_GUIDE.md', '_blank');
        }

        async function startTraining() {
            const preset = document.getElementById('preset-select').value;
            const distributed = document.getElementById('distributed-training').checked;
            const workers = document.getElementById('workers-input').value;
            
            if (!preset) {
                alert('Please select a training preset');
                return;
            }
            
            const result = await apiCall('start_training', 'POST', {
                preset, distributed, workers
            });
            
            if (result.success) {
                document.getElementById('training-status').textContent = `Training started: ${preset}`;
            } else {
                alert(`Failed to start training: ${result.error}`);
            }
        }

        async function stopTraining() {
            const result = await apiCall('stop_training', 'POST');
            if (result.success) {
                document.getElementById('training-status').textContent = 'Training stopped';
            }
        }

        async function startEvaluation() {
            const model = document.getElementById('model-select').value;
            if (!model) {
                alert('Please select a model');
                return;
            }
            
            const result = await apiCall('start_evaluation', 'POST', { model });
            if (result.success) {
                document.getElementById('evaluation-status').textContent = `Evaluation started: ${model}`;
            } else {
                alert(`Failed to start evaluation: ${result.error}`);
            }
        }

        async function stopEvaluation() {
            const result = await apiCall('stop_evaluation', 'POST');
            if (result.success) {
                document.getElementById('evaluation-status').textContent = 'Evaluation stopped';
            }
        }

        async function startApiServer() {
            const host = document.getElementById('api-host').value;
            const port = document.getElementById('api-port').value;
            
            const result = await apiCall('start_api', 'POST', { host, port });
            if (result.success) {
                document.getElementById('api-status').textContent = `API server started on ${host}:${port}`;
            } else {
                alert(`Failed to start API server: ${result.error}`);
            }
        }

        async function stopApiServer() {
            const result = await apiCall('stop_api', 'POST');
            if (result.success) {
                document.getElementById('api-status').textContent = 'API server stopped';
            }
        }

        async function startSimulation() {
            const result = await apiCall('start_simulation', 'POST');
            if (result.success) {
                document.getElementById('sim-status').textContent = 'Simulation server started';
            } else {
                alert(`Failed to start simulation: ${result.error}`);
            }
        }

        async function stopSimulation() {
            const result = await apiCall('stop_simulation', 'POST');
            if (result.success) {
                document.getElementById('sim-status').textContent = 'Simulation server stopped';
            }
        }

        async function startTensorboard() {
            const result = await apiCall('start_tensorboard', 'POST');
            if (result.success) {
                document.getElementById('tensorboard-status').textContent = 'Tensorboard started on http://localhost:6006';
                setTimeout(() => window.open('http://localhost:6006', '_blank'), 2000);
            } else {
                alert(`Failed to start Tensorboard: ${result.error}`);
            }
        }

        async function stopTensorboard() {
            const result = await apiCall('stop_tensorboard', 'POST');
            if (result.success) {
                document.getElementById('tensorboard-status').textContent = 'Tensorboard stopped';
            }
        }

        function openTensorboard() {
            window.open('http://localhost:6006', '_blank');
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadPresets();
            loadModels();
            updateStatus();
            checkEnvironment(); // Initial check
            statusUpdateInterval = setInterval(updateStatus, 3000); // More frequent updates
        });
    </script>
</body>
</html>
"""


class OSRSWebGUI:
    """Web-based GUI for OSRS PvP RL management."""
    
    def __init__(self, port=8080):
        self.port = port
        self.project_root = Path(__file__).parent
        self.pvp_ml_dir = self.project_root / "pvp-ml"
        self.simulation_dir = self.project_root / "simulation-rsps" / "ElvargServer"
        self.config_dir = self.pvp_ml_dir / "config"
        self.models_dir = self.pvp_ml_dir / "models"
        self.conda_env_path = self.pvp_ml_dir / "env"
        
        # Process tracking
        self.processes: Dict[str, subprocess.Popen] = {}
        self.log_queues: Dict[str, List[str]] = {}
        self.log_threads: Dict[str, threading.Thread] = {}
        
    def log_reader(self, process_name, stream):
        """Read process output and add to log queue."""
        if process_name not in self.log_queues:
            self.log_queues[process_name] = []

        for line in iter(stream.readline, ''):
            self.log_queues[process_name].append(line.strip())
            # Limit log size to prevent memory issues
            if len(self.log_queues[process_name]) > 500:
                self.log_queues[process_name].pop(0)
        stream.close()

    def run_command(self, command: List[str], cwd: Optional[Path] = None, env_vars: Optional[Dict] = None) -> subprocess.Popen:
        """Run a command in the conda environment."""
        # Use conda environment if available
        if self.conda_env_path.exists():
            conda_cmd = ["conda", "run", "-p", str(self.conda_env_path)] + command
        else:
            conda_cmd = command
            
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
            
        process = subprocess.Popen(
            conda_cmd,
            cwd=cwd or self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )

        # Start log reader threads
        process_name = command[0]

        stdout_thread = threading.Thread(target=self.log_reader, args=(process_name, process.stdout), daemon=True)
        stderr_thread = threading.Thread(target=self.log_reader, args=(process_name, process.stderr), daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        self.log_threads[process_name] = (stdout_thread, stderr_thread)

        return process
    
    def get_status(self):
        """Get current system status."""
        status = {
            'processes': {},
            'system_metrics': 'CPU: N/A | Memory: N/A | Processes: N/A'
        }
        
        # Check process statuses
        for name in ['training', 'evaluation', 'api', 'simulation', 'tensorboard']:
            if name in self.processes and self.processes[name].poll() is None:
                status['processes'][name] = {'running': True, 'status': 'Running'}
            else:
                status['processes'][name] = {'running': False, 'status': 'Stopped'}
                
        # Try to get system metrics
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            status['system_metrics'] = f"CPU: {cpu:.1f}% | Memory: {memory.percent:.1f}% | Active: {len([p for p in self.processes.values() if p.poll() is None])}"
        except ImportError:
            pass
            
        return status
    
    def get_presets(self):
        """Get available training presets."""
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
        return sorted(presets)
    
    def get_models(self):
        """Get available models."""
        models = []
        if self.models_dir.exists():
            for model_dir in self.models_dir.iterdir():
                if model_dir.is_dir():
                    models.append(f"models/{model_dir.name}")
        return sorted(models)
    
    def get_logs(self, log_type):
        """Get logs for a specific process."""
        # This is a simplified log retrieval. A better implementation would stream logs.
        logs = self.log_queues.get(log_type, [])
        return {"logs": "\n".join(logs)}
    
    def check_environment(self):
        """Check the status of the environment."""
        status = {}

        # Check conda environment
        try:
            result = subprocess.run(
                ["conda", "info", "--envs"],
                capture_output=True, text=True, timeout=10, check=True
            )
            if str(self.conda_env_path) in result.stdout:
                status['conda'] = {'status': 'OK', 'message': 'Conda environment found.'}
            else:
                status['conda'] = {'status': 'Error', 'message': 'Conda environment missing.'}
        except Exception as e:
            status['conda'] = {'status': 'Error', 'message': f"Conda check failed: {e}"}

        # Check Python packages
        try:
            result = subprocess.run(
                ["conda", "run", "-p", str(self.conda_env_path), "python", "-c", "import pvp_ml, torch, ray"],
                capture_output=True, text=True, timeout=30, check=True
            )
            status['python'] = {'status': 'OK', 'message': 'Core Python packages are installed.'}
        except Exception as e:
            status['python'] = {'status': 'Error', 'message': 'Python package check failed.'}

        # Check Java
        try:
            result = subprocess.run(
                ["conda", "run", "-p", str(self.conda_env_path), "java", "--version"],
                capture_output=True, text=True, timeout=10, check=True
            )
            if "17" in result.stdout:
                status['java'] = {'status': 'OK', 'message': f"Java 17 found: {result.stdout.splitlines()[0]}"}
            else:
                status['java'] = {'status': 'Warning', 'message': 'Java version is not 17.'}
        except Exception as e:
            status['java'] = {'status': 'Error', 'message': f"Java check failed: {e}"}

        # Check simulation server
        if (self.simulation_dir / "gradlew").exists():
            status['simulation'] = {'status': 'OK', 'message': 'Gradle wrapper found.'}
        else:
            status['simulation'] = {'status': 'Error', 'message': 'Simulation server (gradlew) not found.'}

        return status

    def start_training(self, config):
        """Start a training job."""
        try:
            if 'training' in self.processes and self.processes['training'].poll() is None:
                return {'success': False, 'error': 'Training already running'}
            
            command = ["train", "--preset", config['preset']]
            if config.get('distributed'):
                command.append("--distribute")
                if config.get('workers', '').strip() and config['workers'] != 'auto':
                    command.append(config['workers'])
                    
            process = self.run_command(command)
            self.processes['training'] = process
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_training(self):
        """Stop training."""
        return self.stop_process('training')
    
    def start_evaluation(self, config):
        """Start model evaluation."""
        try:
            if 'evaluation' in self.processes and self.processes['evaluation'].poll() is None:
                return {'success': False, 'error': 'Evaluation already running'}
            
            command = ["eval", "--model-path", config['model']]
            process = self.run_command(command)
            self.processes['evaluation'] = process
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_evaluation(self):
        """Stop evaluation."""
        return self.stop_process('evaluation')
    
    def start_api_server(self, config):
        """Start API server."""
        try:
            if 'api' in self.processes and self.processes['api'].poll() is None:
                return {'success': False, 'error': 'API server already running'}
            
            command = ["serve-api", "--host", config['host'], "--port", config['port']]
            process = self.run_command(command)
            self.processes['api'] = process
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_api_server(self):
        """Stop API server."""
        return self.stop_process('api')
    
    def start_simulation(self):
        """Start simulation server."""
        try:
            if 'simulation' in self.processes and self.processes['simulation'].poll() is None:
                return {'success': False, 'error': 'Simulation already running'}
            
            gradlew = self.simulation_dir / "gradlew"
            if not gradlew.exists():
                return {'success': False, 'error': 'Gradle wrapper not found'}
                
            os.chmod(gradlew, 0o755)
            process = subprocess.Popen(
                ["./gradlew", "run"],
                cwd=self.simulation_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes['simulation'] = process
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_simulation(self):
        """Stop simulation."""
        return self.stop_process('simulation')
    
    def start_tensorboard(self):
        """Start Tensorboard."""
        try:
            if 'tensorboard' in self.processes and self.processes['tensorboard'].poll() is None:
                return {'success': False, 'error': 'Tensorboard already running'}
            
            command = ["train", "tensorboard"]
            process = self.run_command(command)
            self.processes['tensorboard'] = process
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_tensorboard(self):
        """Stop Tensorboard."""
        return self.stop_process('tensorboard')
    
    def stop_process(self, name):
        """Stop a process by name."""
        try:
            if name in self.processes:
                process = self.processes[name]
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                del self.processes[name]
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cleanup(self):
        """Clean up all processes."""
        for name in list(self.processes.keys()):
            self.stop_process(name)
    
    def run(self):
        """Run the web GUI."""
        print(f"🌐 Starting OSRS PvP RL Web GUI on http://localhost:{self.port}")
        
        # Create custom handler class with GUI app reference
        def handler_factory(*args, **kwargs):
            return WebGUIHandler(*args, gui_app=self, **kwargs)
        
        try:
            with HTTPServer(("", self.port), handler_factory) as httpd:
                print(f"✅ Server running at http://localhost:{self.port}")
                print("🎯 Open your browser to the URL above to use the GUI")
                print("📖 Press Ctrl+C to stop the server")
                
                # Try to open browser automatically
                try:
                    webbrowser.open(f"http://localhost:{self.port}")
                except Exception:
                    pass  # Browser might not be available
                
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.cleanup()
        except Exception as e:
            print(f"❌ Server error: {e}")


def main():
    """Main entry point for the web GUI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OSRS PvP RL Web GUI")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the web server on")
    args = parser.parse_args()
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "pvp-ml").exists() or not (current_dir / "simulation-rsps").exists():
        print("❌ Please run this script from the project root directory")
        print("   Expected to find 'pvp-ml' and 'simulation-rsps' directories")
        sys.exit(1)
    
    # Create and run web GUI
    app = OSRSWebGUI(port=args.port)
    app.run()


if __name__ == "__main__":
    main()