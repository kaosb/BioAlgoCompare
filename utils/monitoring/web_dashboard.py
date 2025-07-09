"""
Web-based real-time dashboard for algorithm monitoring.

This module provides an HTTP server with a web interface for displaying
real-time algorithm performance and system metrics.
"""

import json
import time
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
import webbrowser

from .metrics_collector import MetricsCollector, AlgorithmMetrics, SystemMetrics

logger = logging.getLogger(__name__)


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the web dashboard."""
    
    def __init__(self, *args, dashboard=None, **kwargs):
        self.dashboard = dashboard
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/' or path == '/index.html':
                self._serve_index()
            elif path == '/api/metrics':
                self._serve_metrics()
            elif path == '/api/history':
                self._serve_history(parsed_path.query)
            elif path.startswith('/static/'):
                self._serve_static(path)
            else:
                self._send_404()
        except Exception as e:
            logger.error(f"Error handling request {path}: {e}")
            self._send_500()
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            if path == '/api/control':
                self._handle_control()
            else:
                self._send_404()
        except Exception as e:
            logger.error(f"Error handling POST {path}: {e}")
            self._send_500()
    
    def _serve_index(self):
        """Serve the main dashboard HTML page."""
        html_content = self._get_dashboard_html()
        self._send_response(200, html_content, 'text/html')
    
    def _serve_metrics(self):
        """Serve current metrics as JSON."""
        if not self.dashboard:
            self._send_500()
            return
        
        metrics = {
            'timestamp': time.time(),
            'algorithm': self.dashboard.metrics_collector.algorithm_metrics.to_dict(),
            'system': self.dashboard.metrics_collector.system_metrics.to_dict()
        }
        
        self._send_response(200, json.dumps(metrics), 'application/json')
    
    def _serve_history(self, query_string):
        """Serve historical metrics data."""
        if not self.dashboard:
            self._send_500()
            return
        
        params = parse_qs(query_string)
        metric_name = params.get('metric', ['fitness'])[0]
        limit = int(params.get('limit', [100])[0])
        
        # Get time series data
        data = self.dashboard.metrics_collector.get_time_series_data(metric_name)
        
        # Limit data points
        if len(data) > limit:
            data = data[-limit:]
        
        response = {
            'metric': metric_name,
            'data': data,
            'length': len(data)
        }
        
        self._send_response(200, json.dumps(response), 'application/json')
    
    def _serve_static(self, path):
        """Serve static files (CSS, JS)."""
        # For simplicity, we'll inline CSS and JS in the HTML
        self._send_404()
    
    def _handle_control(self):
        """Handle control commands (pause, resume, reset)."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            command_data = json.loads(post_data.decode('utf-8'))
            command = command_data.get('command')
            
            if command == 'pause':
                self.dashboard._paused = True
                response = {'status': 'paused'}
            elif command == 'resume':
                self.dashboard._paused = False
                response = {'status': 'resumed'}
            elif command == 'reset':
                self.dashboard.metrics_collector.reset()
                response = {'status': 'reset'}
            else:
                response = {'error': 'Unknown command'}
            
            self._send_response(200, json.dumps(response), 'application/json')
        except Exception as e:
            logger.error(f"Error handling control command: {e}")
            self._send_500()
    
    def _send_response(self, status_code, content, content_type):
        """Send HTTP response."""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        self.wfile.write(content)
    
    def _send_404(self):
        """Send 404 Not Found response."""
        self._send_response(404, '404 Not Found', 'text/plain')
    
    def _send_500(self):
        """Send 500 Internal Server Error response."""
        self._send_response(500, '500 Internal Server Error', 'text/plain')
    
    def _get_dashboard_html(self):
        """Generate the dashboard HTML page."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BioAlgoCompare - Real-Time Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1rem;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            color: white;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .header .status {
            color: #f0f0f0;
            font-size: 1rem;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: auto auto;
            gap: 1rem;
            padding: 1rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        
        .panel h2 {
            color: #2c3e50;
            margin-bottom: 1rem;
            font-size: 1.5rem;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .metric {
            padding: 0.5rem;
            border-left: 4px solid #3498db;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .metric-label {
            font-weight: bold;
            color: #2c3e50;
            font-size: 0.9rem;
        }
        
        .metric-value {
            font-size: 1.2rem;
            color: #27ae60;
            margin-top: 0.25rem;
        }
        
        .chart-container {
            height: 300px;
            margin-top: 1rem;
        }
        
        .controls {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .btn-primary { background: #3498db; color: white; }
        .btn-warning { background: #f39c12; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        
        .status-running { background: #27ae60; }
        .status-paused { background: #f39c12; }
        .status-stopped { background: #e74c3c; }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 0.5rem;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.3s ease;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="header">
        <h1>🧬 BioAlgoCompare Monitor</h1>
        <div class="status">
            <span class="status-indicator status-running" id="statusIndicator"></span>
            <span id="statusText">Initializing...</span>
            <span style="margin-left: 2rem;">Uptime: <span id="uptime">00:00:00</span></span>
        </div>
    </div>
    
    <div class="dashboard">
        <!-- Algorithm Metrics Panel -->
        <div class="panel">
            <h2>🎯 Algorithm Metrics</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Iteration</div>
                    <div class="metric-value" id="iteration">0</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Best Fitness</div>
                    <div class="metric-value" id="bestFitness">N/A</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Current Fitness</div>
                    <div class="metric-value" id="currentFitness">N/A</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Diversity</div>
                    <div class="metric-value" id="diversity">0.000</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Convergence Rate</div>
                    <div class="metric-value" id="convergenceRate">0.000</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Stagnation</div>
                    <div class="metric-value" id="stagnation">0</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-warning" onclick="pauseResume()">⏸️ Pause</button>
                <button class="btn btn-danger" onclick="reset()">🔄 Reset</button>
            </div>
        </div>
        
        <!-- System Resources Panel -->
        <div class="panel">
            <h2>💻 System Resources</h2>
            <div class="metric">
                <div class="metric-label">CPU Usage</div>
                <div class="metric-value" id="cpuUsage">0.0%</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpuProgress" style="width: 0%"></div>
                </div>
            </div>
            
            <div class="metric" style="margin-top: 1rem;">
                <div class="metric-label">Memory Usage</div>
                <div class="metric-value" id="memoryUsage">0.0%</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memoryProgress" style="width: 0%"></div>
                </div>
            </div>
            
            <div class="metrics-grid" style="margin-top: 1rem;">
                <div class="metric">
                    <div class="metric-label">Memory Used</div>
                    <div class="metric-value" id="memoryUsed">0 MB</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Processes</div>
                    <div class="metric-value" id="processCount">0</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Temperature</div>
                    <div class="metric-value" id="temperature">N/A</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Load Average</div>
                    <div class="metric-value" id="loadAverage">N/A</div>
                </div>
            </div>
        </div>
        
        <!-- Fitness Chart Panel -->
        <div class="panel">
            <h2>📈 Fitness Progression</h2>
            <div class="chart-container">
                <canvas id="fitnessChart"></canvas>
            </div>
        </div>
        
        <!-- Performance Chart Panel -->
        <div class="panel">
            <h2>⚡ Performance Metrics</h2>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Global variables
        let isPaused = false;
        let startTime = Date.now();
        let fitnessChart, performanceChart;
        
        // Initialize charts
        function initCharts() {
            // Fitness chart
            const fitnessCtx = document.getElementById('fitnessChart').getContext('2d');
            fitnessChart = new Chart(fitnessCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Best Fitness',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Current Fitness',
                        data: [],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });
            
            // Performance chart
            const perfCtx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(perfCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU %',
                        data: [],
                        borderColor: '#9b59b6',
                        backgroundColor: 'rgba(155, 89, 182, 0.1)',
                        yAxisID: 'y'
                    }, {
                        label: 'Memory %',
                        data: [],
                        borderColor: '#f39c12',
                        backgroundColor: 'rgba(243, 156, 18, 0.1)',
                        yAxisID: 'y'
                    }, {
                        label: 'Diversity',
                        data: [],
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            max: 100
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            max: 1,
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });
        }
        
        // Update metrics display
        function updateMetrics(data) {
            const algo = data.algorithm;
            const sys = data.system;
            
            // Algorithm metrics
            document.getElementById('iteration').textContent = algo.iteration;
            document.getElementById('bestFitness').textContent = 
                algo.best_fitness === null || algo.best_fitness === Infinity ? 'N/A' : algo.best_fitness.toFixed(6);
            document.getElementById('currentFitness').textContent = 
                algo.current_fitness === null || algo.current_fitness === Infinity ? 'N/A' : algo.current_fitness.toFixed(6);
            document.getElementById('diversity').textContent = algo.population_diversity.toFixed(4);
            document.getElementById('convergenceRate').textContent = algo.convergence_rate.toFixed(6);
            document.getElementById('stagnation').textContent = algo.stagnation_counter;
            
            // System metrics
            document.getElementById('cpuUsage').textContent = sys.cpu_percent.toFixed(1) + '%';
            document.getElementById('memoryUsage').textContent = sys.memory_percent.toFixed(1) + '%';
            document.getElementById('memoryUsed').textContent = Math.round(sys.memory_used_mb) + ' MB';
            document.getElementById('processCount').textContent = sys.process_count;
            
            // Progress bars
            document.getElementById('cpuProgress').style.width = sys.cpu_percent + '%';
            document.getElementById('memoryProgress').style.width = sys.memory_percent + '%';
            
            // Optional metrics
            if (sys.temperature !== null) {
                document.getElementById('temperature').textContent = sys.temperature.toFixed(1) + '°C';
            }
            
            if (sys.load_average && sys.load_average.length > 0) {
                document.getElementById('loadAverage').textContent = 
                    sys.load_average.slice(0, 3).map(x => x.toFixed(2)).join(' | ');
            }
            
            // Update charts
            updateCharts(data);
        }
        
        // Update charts with new data
        function updateCharts(data) {
            const now = new Date().toLocaleTimeString();
            const algo = data.algorithm;
            const sys = data.system;
            
            // Fitness chart
            if (fitnessChart.data.labels.length > 50) {
                fitnessChart.data.labels.shift();
                fitnessChart.data.datasets[0].data.shift();
                fitnessChart.data.datasets[1].data.shift();
            }
            
            fitnessChart.data.labels.push(now);
            fitnessChart.data.datasets[0].data.push(algo.best_fitness === Infinity ? null : algo.best_fitness);
            fitnessChart.data.datasets[1].data.push(algo.current_fitness === Infinity ? null : algo.current_fitness);
            fitnessChart.update('none');
            
            // Performance chart
            if (performanceChart.data.labels.length > 50) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
                performanceChart.data.datasets[1].data.shift();
                performanceChart.data.datasets[2].data.shift();
            }
            
            performanceChart.data.labels.push(now);
            performanceChart.data.datasets[0].data.push(sys.cpu_percent);
            performanceChart.data.datasets[1].data.push(sys.memory_percent);
            performanceChart.data.datasets[2].data.push(algo.population_diversity);
            performanceChart.update('none');
        }
        
        // Update uptime display
        function updateUptime() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            
            document.getElementById('uptime').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        // Fetch metrics from server
        async function fetchMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                updateMetrics(data);
                
                // Update status
                document.getElementById('statusText').textContent = 'Running';
                document.getElementById('statusIndicator').className = 'status-indicator status-running';
            } catch (error) {
                console.error('Error fetching metrics:', error);
                document.getElementById('statusText').textContent = 'Connection Error';
                document.getElementById('statusIndicator').className = 'status-indicator status-stopped';
            }
        }
        
        // Control functions
        async function pauseResume() {
            const command = isPaused ? 'resume' : 'pause';
            try {
                const response = await fetch('/api/control', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: command})
                });
                const result = await response.json();
                
                isPaused = !isPaused;
                const btn = event.target;
                btn.textContent = isPaused ? '▶️ Resume' : '⏸️ Pause';
                
                document.getElementById('statusText').textContent = isPaused ? 'Paused' : 'Running';
                document.getElementById('statusIndicator').className = 
                    `status-indicator ${isPaused ? 'status-paused' : 'status-running'}`;
            } catch (error) {
                console.error('Error controlling dashboard:', error);
            }
        }
        
        async function reset() {
            if (confirm('Are you sure you want to reset all metrics?')) {
                try {
                    const response = await fetch('/api/control', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({command: 'reset'})
                    });
                    
                    // Clear charts
                    fitnessChart.data.labels = [];
                    fitnessChart.data.datasets.forEach(dataset => dataset.data = []);
                    fitnessChart.update();
                    
                    performanceChart.data.labels = [];
                    performanceChart.data.datasets.forEach(dataset => dataset.data = []);
                    performanceChart.update();
                    
                    startTime = Date.now();
                } catch (error) {
                    console.error('Error resetting:', error);
                }
            }
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            
            // Start periodic updates
            setInterval(fetchMetrics, 1000);  // Update every second
            setInterval(updateUptime, 1000);  // Update uptime every second
            
            // Initial fetch
            fetchMetrics();
        });
    </script>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        pass


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server."""
    daemon_threads = True
    allow_reuse_address = True


class WebDashboard:
    """
    Web-based real-time dashboard for monitoring algorithm performance.
    
    Provides an HTTP server with a comprehensive web interface displaying
    algorithm metrics, system resources, and interactive charts.
    
    Features:
    - Real-time metrics display
    - Interactive charts with Chart.js
    - System resource monitoring
    - Responsive design
    - Control interface (pause/resume/reset)
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        host: str = 'localhost',
        port: int = 8080,
        auto_open: bool = True
    ):
        """
        Initialize web dashboard.
        
        Args:
            metrics_collector: MetricsCollector instance to monitor
            host: Server host address
            port: Server port number
            auto_open: Whether to automatically open browser
        """
        self.metrics_collector = metrics_collector
        self.host = host
        self.port = port
        self.auto_open = auto_open
        
        # Server components
        self.server: Optional[ThreadedHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = False
        
        logger.info(f"Web dashboard initialized on {host}:{port}")
    
    def start(self) -> None:
        """Start the web dashboard server."""
        if self._running:
            return
        
        try:
            # Create handler class with dashboard reference
            def handler_factory(*args, **kwargs):
                return DashboardHandler(*args, dashboard=self, **kwargs)
            
            # Create server
            self.server = ThreadedHTTPServer((self.host, self.port), handler_factory)
            
            # Start server in separate thread
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            self._running = True
            
            # Get actual port (in case 0 was specified)
            actual_port = self.server.server_address[1]
            url = f"http://{self.host}:{actual_port}"
            
            logger.info(f"Web dashboard started at {url}")
            
            # Auto-open browser
            if self.auto_open:
                try:
                    webbrowser.open(url)
                    logger.info("Opened dashboard in browser")
                except Exception as e:
                    logger.warning(f"Failed to open browser: {e}")
            
            print(f"\n🌐 Web Dashboard available at: {url}")
            print("Press Ctrl+C to stop the dashboard")
            
        except OSError as e:
            if e.errno == 48:  # Address already in use
                logger.error(f"Port {self.port} is already in use")
                # Try to find available port
                for try_port in range(self.port + 1, self.port + 100):
                    try:
                        self.port = try_port
                        self.start()
                        return
                    except OSError:
                        continue
                raise RuntimeError("Could not find available port")
            else:
                raise
    
    def stop(self) -> None:
        """Stop the web dashboard server."""
        if not self._running:
            return
        
        self._running = False
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.server_thread:
            self.server_thread.join(timeout=5.0)
        
        logger.info("Web dashboard stopped")
    
    def get_url(self) -> str:
        """Get the dashboard URL."""
        if self.server:
            actual_port = self.server.server_address[1]
            return f"http://{self.host}:{actual_port}"
        return f"http://{self.host}:{self.port}"
    
    def is_running(self) -> bool:
        """Check if the dashboard is running."""
        return self._running
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()