/**
 * Dashboard JavaScript - Apple Dark Mode Inspired
 * Enhanced with recording control, mock data, and simple chart rendering
 */

// ========== CONFIGURATION ==========
const MOCK_DATA = true; // Set to false when real endpoints are available
const UPDATE_INTERVAL = 5000; // 5 seconds
const CHART_UPDATE_INTERVAL = 2000; // 2 seconds for chart animation

// ========== THEME MANAGEMENT ==========
class ThemeManager {
  constructor() {
    this.storageKey = 'uuplastination-theme';
    this.init();
  }

  init() {
    const savedTheme = localStorage.getItem(this.storageKey);
    
    if (savedTheme) {
      this.setTheme(savedTheme);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.setTheme(prefersDark ? 'dark' : 'light');
    }

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem(this.storageKey)) {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.storageKey, theme);
    this.updateToggleIcon(theme);
  }

  toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'light' ? 'dark' : 'light';
    this.setTheme(next);
  }

  updateToggleIcon(theme) {
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.querySelector('span').textContent = theme === 'dark' ? '☀️' : '🌙';
      toggle.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
    }
  }
}

// ========== RECORDING CONTROL ==========
class RecordingControl {
  constructor() {
    this.recording = false;
    this.button = document.getElementById('recording-control');
    this.dot = document.getElementById('recording-dot');
    this.text = document.getElementById('recording-text');
    this.init();
  }

  init() {
    if (!this.button) return;

    this.button.addEventListener('click', () => this.toggle());
  }

  toggle() {
    this.recording = !this.recording;
    this.updateUI();
    
    // TODO: Wire to backend recording endpoint
    console.log(`Recording ${this.recording ? 'started' : 'stopped'}`);
  }

  updateUI() {
    if (this.recording) {
      this.button.classList.add('recording');
      this.dot.className = 'recording-dot';
      this.text.textContent = 'Recording…';
    } else {
      this.button.classList.remove('recording');
      this.dot.className = 'recording-dot-hollow';
      this.text.textContent = 'Record';
    }
  }

  start() {
    if (!this.recording) {
      this.recording = true;
      this.updateUI();
    }
  }

  stop() {
    if (this.recording) {
      this.recording = false;
      this.updateUI();
    }
  }
}

// ========== CAMERA MANAGEMENT ==========
class CameraManager {
  constructor(elementId) {
    this.element = document.getElementById(elementId);
    this.video = this.element?.querySelector('video') || this.element?.querySelector('img');
    this.fullscreenBtn = document.getElementById('camera-fullscreen-btn');
    this.init();
  }

  init() {
    if (!this.element) return;

    if (this.fullscreenBtn) {
      this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'f' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        this.toggleFullscreen();
      }
    });

    document.addEventListener('fullscreenchange', () => this.onFullscreenChange());
    document.addEventListener('webkitfullscreenchange', () => this.onFullscreenChange());
  }

  async toggleFullscreen() {
    try {
      if (!document.fullscreenElement && !document.webkitFullscreenElement) {
        if (this.element.requestFullscreen) {
          await this.element.requestFullscreen();
        } else if (this.element.webkitRequestFullscreen) {
          await this.element.webkitRequestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          await document.webkitExitFullscreen();
        }
      }
    } catch (err) {
      console.error('Fullscreen error:', err);
    }
  }

  onFullscreenChange() {
    const isFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement);
    if (this.fullscreenBtn) {
      const span = this.fullscreenBtn.querySelector('span');
      if (span) span.textContent = isFullscreen ? '⤓' : '⤢';
      this.fullscreenBtn.childNodes[1].textContent = isFullscreen ? ' Exit Fullscreen' : ' Fullscreen';
    }
  }
}

// ========== MOCK DATA GENERATORS ==========
class MockDataGenerator {
  constructor() {
    this.bubbleRate = 70;
    this.bubbleRateHistory = [];
    this.initHistory();
  }

  initHistory() {
    // Initialize with 100 data points
    const now = Date.now();
    for (let i = 100; i >= 0; i--) {
      this.bubbleRateHistory.push({
        time: now - i * 10000, // 10 second intervals
        value: 65 + Math.random() * 10
      });
    }
  }

  getBubbleRate() {
    // Simulate realistic BPM variation
    this.bubbleRate += (Math.random() - 0.5) * 3;
    this.bubbleRate = Math.max(60, Math.min(85, this.bubbleRate));
    
    const delta = (Math.random() - 0.5) * 3;
    
    // Add to history
    this.bubbleRateHistory.push({
      time: Date.now(),
      value: this.bubbleRate
    });
    
    // Keep only last 1000 points
    if (this.bubbleRateHistory.length > 1000) {
      this.bubbleRateHistory.shift();
    }
    
    return {
      bpm: Math.round(this.bubbleRate * 10) / 10,
      delta: Math.round(delta * 10) / 10
    };
  }

  getSystemStats() {
    return {
      cpu: {
        temp_c: 45 + Math.random() * 5,
        usage_percent: 30 + Math.random() * 25
      },
      memory: {
        used: 2.1 + Math.random() * 0.3,
        total: 4,
        percent: 52 + Math.random() * 8
      },
      uptime_seconds: 478932 + Math.floor(Math.random() * 100),
      services: {
        camera: Math.random() > 0.1 ? 'active' : 'inactive',
        stepper: Math.random() > 0.05 ? 'active' : 'inactive',
        nginx: 'active',
        api: 'active'
      }
    };
  }

  getStepperStatus() {
    return {
      enabled: true,
      moving: false,
      position_steps: Math.floor(Math.random() * 200),
        worker_alive: true,
      last_error: null
    };
  }
}

// ========== SIMPLE CHART RENDERER ==========
class BubbleChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas?.getContext('2d');
    this.dataPoints = [];
    this.timeRange = '15m'; // Default
    this.init();
  }

  init() {
    if (!this.canvas) return;

    // Set canvas size
    this.resize();
    window.addEventListener('resize', () => this.resize());

    // Bind time range controls
    const chips = document.querySelectorAll('.chart-chip');
    chips.forEach(chip => {
      chip.addEventListener('click', (e) => {
        chips.forEach(c => c.classList.remove('active'));
        e.target.classList.add('active');
        this.timeRange = e.target.dataset.range;
        this.render();
      });
    });
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width * window.devicePixelRatio;
    this.canvas.height = rect.height * window.devicePixelRatio;
    this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    this.render();
  }

  updateData(dataPoints) {
    this.dataPoints = dataPoints;
    this.render();
  }

  render() {
    if (!this.ctx || this.dataPoints.length === 0) return;

    const width = this.canvas.width / window.devicePixelRatio;
    const height = this.canvas.height / window.devicePixelRatio;
    const padding = 40;

    // Clear canvas
    this.ctx.clearRect(0, 0, width, height);

    // Filter data by time range
    const now = Date.now();
    const ranges = { '15m': 15 * 60 * 1000, '1h': 60 * 60 * 1000, '6h': 6 * 60 * 60 * 1000, '24h': 24 * 60 * 60 * 1000 };
    const cutoff = now - ranges[this.timeRange];
    const filtered = this.dataPoints.filter(p => p.time >= cutoff);

    if (filtered.length < 2) return;

    // Find min/max values
    const values = filtered.map(p => p.value);
    const minVal = Math.min(...values) - 5;
    const maxVal = Math.max(...values) + 5;

    // Draw grid lines
    this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    this.ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (height - 2 * padding) * i / 5;
      this.ctx.beginPath();
      this.ctx.moveTo(padding, y);
      this.ctx.lineTo(width - padding, y);
      this.ctx.stroke();
    }

    // Draw area fill
    this.ctx.beginPath();
    filtered.forEach((point, i) => {
      const x = padding + (width - 2 * padding) * i / (filtered.length - 1);
      const y = height - padding - ((point.value - minVal) / (maxVal - minVal)) * (height - 2 * padding);
      
      if (i === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    });

    // Close the area
    const lastX = padding + (width - 2 * padding);
    const lastY = height - padding - ((filtered[filtered.length - 1].value - minVal) / (maxVal - minVal)) * (height - 2 * padding);
    this.ctx.lineTo(lastX, height - padding);
    this.ctx.lineTo(padding, height - padding);
    this.ctx.closePath();

    // Fill area with gradient
    const gradient = this.ctx.createLinearGradient(0, padding, 0, height - padding);
    gradient.addColorStop(0, 'rgba(10, 132, 255, 0.3)');
    gradient.addColorStop(1, 'rgba(10, 132, 255, 0.05)');
    this.ctx.fillStyle = gradient;
    this.ctx.fill();

    // Draw line
    this.ctx.beginPath();
    filtered.forEach((point, i) => {
      const x = padding + (width - 2 * padding) * i / (filtered.length - 1);
      const y = height - padding - ((point.value - minVal) / (maxVal - minVal)) * (height - 2 * padding);
      
      if (i === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    });
    this.ctx.strokeStyle = '#0A84FF';
    this.ctx.lineWidth = 2;
    this.ctx.stroke();

    // Draw axes labels
    this.ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    this.ctx.font = '12px SF Mono, monospace';
    this.ctx.textAlign = 'right';
    
    // Y-axis labels
    for (let i = 0; i <= 5; i++) {
      const val = minVal + (maxVal - minVal) * (5 - i) / 5;
      const y = padding + (height - 2 * padding) * i / 5;
      this.ctx.fillText(Math.round(val), padding - 10, y + 4);
    }
  }
}

// ========== DATA MANAGEMENT ==========
class DataManager {
  constructor() {
    this.updateInterval = null;
    this.mockData = MOCK_DATA ? new MockDataGenerator() : null;
    this.chart = new BubbleChart('bubble-chart-canvas');
  }

  async fetchJSON(url, options = {}) {
    if (MOCK_DATA) {
      throw new Error('Mock mode enabled');
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }

  async updateBubbleRate() {
    try {
      let data;
      
      if (MOCK_DATA) {
        data = this.mockData.getBubbleRate();
      } else {
        data = await this.fetchJSON('/api/metrics');
      }

      const valueEl = document.getElementById('bubble-rate-value');
      const deltaEl = document.getElementById('bubble-rate-delta');

      if (valueEl) {
        valueEl.textContent = data.bpm || 0;
      }

      if (deltaEl) {
        const delta = data.delta || 0;
        const sign = delta >= 0 ? '+' : '';
        deltaEl.textContent = `${delta >= 0 ? '▲' : '▼'} ${sign}${delta.toFixed(1)} vs 5min avg`;
        deltaEl.className = `metric-delta ${delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral'}`;
      }
    } catch (error) {
      console.error('Error updating bubble rate:', error);
    }
  }

  async updateSystemStats() {
    try {
      let data;
      
      if (MOCK_DATA) {
        data = this.mockData.getSystemStats();
      } else {
        data = await this.fetchJSON('/api/stats');
      }

      // CPU Temperature
      const tempEl = document.getElementById('cpu-temp');
      if (tempEl && data?.cpu?.temp_c !== undefined) {
        tempEl.textContent = data.cpu.temp_c.toFixed(1);
      }

      // CPU Usage
      const cpuUsageEl = document.getElementById('cpu-usage');
      if (cpuUsageEl && data?.cpu?.usage_percent !== undefined) {
        cpuUsageEl.textContent = data.cpu.usage_percent.toFixed(1);
      }

      // Memory
      const memoryEl = document.getElementById('memory-usage');
      if (memoryEl && data?.memory) {
        memoryEl.textContent = `${data.memory.used.toFixed(1)} / ${data.memory.total}`;
      }

      // Uptime
      const uptimeEl = document.getElementById('uptime');
      if (uptimeEl && data?.uptime_seconds) {
        uptimeEl.textContent = this.formatUptime(data.uptime_seconds);
      }

      // Services
      const cameraEl = document.getElementById('camera-service');
      if (cameraEl && data?.services?.camera) {
        cameraEl.textContent = this.capitalize(data.services.camera);
      }

      const stepperEl = document.getElementById('stepper-service');
      if (stepperEl && data?.services?.stepper) {
        stepperEl.textContent = this.capitalize(data.services.stepper);
      }

    } catch (error) {
      console.error('Error updating system stats:', error);
    }
  }

  async updateStepperStatus() {
    try {
      let data;
      
      if (MOCK_DATA) {
        data = this.mockData.getStepperStatus();
      } else {
        data = await this.fetchJSON('/api/stepper/status');
      }

      const statusEl = document.getElementById('valve-status-text');
      if (statusEl) {
        const enabled = data?.enabled ? 'Enabled' : 'Disabled';
        const moving = data?.moving ? ', Moving' : '';
        statusEl.textContent = `${enabled}${moving}`;
      }

      const posEl = document.getElementById('valve-position');
      const fillEl = document.getElementById('valve-position-fill');
      if (data?.position_steps !== undefined) {
        // Convert steps to percentage (assuming 200 steps = 100%)
        const percent = Math.round((data.position_steps / 200) * 100);
        if (posEl) posEl.textContent = percent;
        if (fillEl) fillEl.style.width = `${percent}%`;
      }

    } catch (error) {
      console.error('Error updating stepper status:', error);
    }
  }

  updateChart() {
    if (this.mockData && this.chart) {
      this.chart.updateData(this.mockData.bubbleRateHistory);
    }
  }

  formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  startAutoUpdate() {
    this.updateAll();
    this.updateInterval = setInterval(() => {
      this.updateAll();
    }, UPDATE_INTERVAL);

    // Update chart more frequently
    setInterval(() => {
      this.updateChart();
    }, CHART_UPDATE_INTERVAL);
  }

  stopAutoUpdate() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  async updateAll() {
    await Promise.allSettled([
      this.updateBubbleRate(),
      this.updateSystemStats(),
      this.updateStepperStatus(),
    ]);
  }
}

// ========== VALVE CONTROLS ==========
class ValveController {
  constructor() {
    this.baseUrl = '/api/stepper';
    this.bindButtons();
  }

  async sendCommand(endpoint, options = {}) {
    const messageEl = document.getElementById('valve-message');
    
    try {
      if (MOCK_DATA) {
        console.log(`[MOCK] Command: ${endpoint}`);
        if (messageEl) {
          messageEl.textContent = `[MOCK] Command sent: ${endpoint}`;
          messageEl.style.color = 'var(--positive)';
        }
        return { success: true };
      }

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      if (messageEl) {
        messageEl.textContent = 'Command sent successfully';
        messageEl.style.color = 'var(--positive)';
      }

      return data;
    } catch (error) {
      if (messageEl) {
        messageEl.textContent = `Error: ${error.message}`;
        messageEl.style.color = 'var(--danger)';
      }
      throw error;
    }
  }

  bindButtons() {
    const buttons = {
      'valve-enable': () => this.sendCommand('/enable'),
      'valve-disable': () => this.sendCommand('/disable'),
      'valve-open': () => this.sendCommand('/open'),
      'valve-close': () => this.sendCommand('/close'),
      'valve-abort': () => this.sendCommand('/abort'),
      'valve-plus': () => this.sendCommand('/step?steps=10'),
      'valve-minus': () => this.sendCommand('/step?steps=-10'),
    };

    Object.entries(buttons).forEach(([id, handler]) => {
      const button = document.getElementById(id);
      if (button) {
        button.addEventListener('click', async (e) => {
          const btn = e.currentTarget;
          btn.disabled = true;
          
          try {
            await handler();
          } finally {
            setTimeout(() => {
              btn.disabled = false;
            }, 500);
          }
        });
      }
    });
  }
}

// ========== KEYBOARD SHORTCUTS ==========
function setupKeyboardShortcuts(themeManager, recordingControl) {
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
      return;
    }

    if (e.key === 't') {
      e.preventDefault();
      themeManager.toggleTheme();
    }

    if (e.key === 'r' && e.ctrlKey) {
      e.preventDefault();
      recordingControl.toggle();
    }

    if (e.key === '?') {
      e.preventDefault();
      showHelp();
    }
  });
}

function showHelp() {
  const shortcuts = [
    { key: 't', description: 'Toggle theme' },
    { key: 'f', description: 'Toggle fullscreen camera' },
    { key: 'Ctrl+r', description: 'Toggle recording' },
    { key: '?', description: 'Show this help' },
  ];

  const message = shortcuts
    .map((s) => `${s.key} - ${s.description}`)
    .join('\n');

  alert(`Keyboard Shortcuts:\n\n${message}`);
}

// ========== INITIALIZE APPLICATION ==========
class Dashboard {
  constructor() {
    this.themeManager = null;
    this.recordingControl = null;
    this.dataManager = null;
    this.cameraManager = null;
    this.valveController = null;
  }

  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    console.log('🚀 Initializing Plastination Control Dashboard...');
    console.log(`📊 Mock Data Mode: ${MOCK_DATA ? 'ENABLED' : 'DISABLED'}`);

    // Initialize theme
    this.themeManager = new ThemeManager();

    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        this.themeManager.toggleTheme();
      });
    }

    // Initialize recording control
    this.recordingControl = new RecordingControl();

    // Initialize camera
    this.cameraManager = new CameraManager('camera-widget');

    // Initialize data management
    this.dataManager = new DataManager();
    this.dataManager.startAutoUpdate();

    // Initialize valve controls
    this.valveController = new ValveController();

    // Setup keyboard shortcuts
    setupKeyboardShortcuts(this.themeManager, this.recordingControl);

    console.log('✅ Dashboard initialized successfully');
  }

  destroy() {
    if (this.dataManager) {
      this.dataManager.stopAutoUpdate();
    }
  }
}

// Initialize the dashboard
const dashboard = new Dashboard();
dashboard.init();

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  dashboard.destroy();
});

// Export for debugging
window.dashboard = dashboard;
window.MOCK_DATA = MOCK_DATA;
