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
            self.send_json_response({'logs': self.gui_app.get_logs(log_type)})
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
                <h3>Environment Status</h3>
                <div id="status-grid" class="status-grid">
                    <div class="status-item" id="conda-status">
                        <h4>Conda Environment</h4>
                        <div>Status: <span id="conda-status-text">Checking...</span></div>
                    </div>
                    <div class="status-item" id="python-status">
                        <h4>Python Packages</h4>
                        <div>Status: <span id="python-status-text">Checking...</span></div>
                    </div>
                    <div class="status-item" id="java-status">
                        <h4>Java Runtime</h4>
                        <div>Status: <span id="java-status-text">Checking...</span></div>
                    </div>
                    <div class="status-item" id="simulation-status">
                        <h4>Simulation Server</h4>
                        <div>Status: <span id="simulation-status-text">Checking...</span></div>
                    </div>
                </div>
                <button class="btn btn-primary" onclick="checkEnvironment()">Check Environment</button>
                <button class="btn btn-secondary" onclick="openSetupGuide()">Open Setup Guide</button>
            </div>
        </div>

        <!-- Training Tab -->
        <div id="training" class="tab-content">
            <div class="section">
                <h3>Training Configuration</h3>
                <div class="form-group">
                    <label for="preset-select">Training Preset:</label>
                    <select id="preset-select">
                        <option value="">Loading presets...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="distributed-training"> Distributed Training
                    </label>
                </div>
                <div class="form-group">
                    <label for="workers-input">Parallel Workers:</label>
                    <input type="text" id="workers-input" value="auto" placeholder="auto or number">
                </div>
                <div>
                    <button class="btn btn-success" id="start-training-btn" onclick="startTraining()">Start Training</button>
                    <button class="btn btn-danger" id="stop-training-btn" onclick="stopTraining()" disabled>Stop Training</button>
                    <button class="btn btn-primary" onclick="openTensorboard()">View Progress</button>
                </div>
                <div id="training-status" style="margin-top: 15px; font-weight: bold;"></div>
            </div>
            <div class="section">
                <h3>Training Logs</h3>
                <div id="training-logs" class="logs"></div>
            </div>
        </div>

        <!-- Evaluation Tab -->
        <div id="evaluation" class="tab-content">
            <div class="section">
                <h3>Model Selection</h3>
                <div class="form-group">
                    <label for="model-select">Model:</label>
                    <select id="model-select">
                        <option value="">Loading models...</option>
                    </select>
                </div>
                <div>
                    <button class="btn btn-success" id="start-eval-btn" onclick="startEvaluation()">Start Evaluation</button>
                    <button class="btn btn-danger" id="stop-eval-btn" onclick="stopEvaluation()" disabled>Stop Evaluation</button>
                    <button class="btn btn-secondary" onclick="startSimulation()">Start Simulation</button>
                </div>
                <div id="evaluation-status" style="margin-top: 15px; font-weight: bold;"></div>
            </div>
            <div class="section">
                <h3>Evaluation Logs</h3>
                <div id="evaluation-logs" class="logs"></div>
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
                <h3>API Server Configuration</h3>
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
                <div id="api-status" style="margin-top: 15px; font-weight: bold;"></div>
            </div>
        </div>

        <!-- Simulation Tab -->
        <div id="simulation" class="tab-content">
            <div class="section">
                <h3>Simulation Server</h3>
                <div>
                    <button class="btn btn-success" id="start-sim-btn" onclick="startSimulation()">Start Simulation</button>
                    <button class="btn btn-danger" id="stop-sim-btn" onclick="stopSimulation()" disabled>Stop Simulation</button>
                </div>
                <div id="sim-status" style="margin-top: 15px; font-weight: bold;"></div>
                <div style="margin-top: 15px; padding: 15px; background: #e9ecef; border-radius: 5px;">
                    <strong>Connection Info:</strong><br>
                    Game Server: localhost:43595 (for RSPS clients)<br>
                    RL API Server: localhost:43594 (for training/evaluation)
                </div>
            </div>
            <div class="section">
                <h3>Simulation Logs</h3>
                <div id="simulation-logs" class="logs"></div>
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
                updateProcessStatus('training', status.processes.training);
                updateProcessStatus('evaluation', status.processes.evaluation);
                updateProcessStatus('api', status.processes.api);
                updateProcessStatus('simulation', status.processes.simulation);
                updateProcessStatus('tensorboard', status.processes.tensorboard);
                
                // Update system metrics
                document.getElementById('system-metrics').textContent = status.system_metrics || 'Metrics unavailable';
                
            } catch (error) {
                console.error('Failed to update status:', error);
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
            // This would trigger environment check on the backend
            console.log('Checking environment...');
        }

        function openSetupGuide() {
            window.open('/SETUP_GUIDE.md', '_blank');
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
            statusUpdateInterval = setInterval(updateStatus, 5000);
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
            
        return subprocess.Popen(
            conda_cmd,
            cwd=cwd or self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
    
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
        if log_type in self.processes:
            process = self.processes[log_type]
            try:
                stdout, stderr = process.communicate(timeout=0.1)
                return f"{stdout}\n{stderr}".strip()
            except subprocess.TimeoutExpired:
                return "Process running..."
        return "No logs available"
    
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