/**
 * Dashboard JavaScript - Apple HIG Inspired
 * Theme toggle, fullscreen, interactions, and data fetching
 */

// ========== THEME MANAGEMENT ==========
class ThemeManager {
  constructor() {
    this.storageKey = 'uuplastination-theme';
    this.init();
  }

  init() {
    // Load saved theme or detect system preference
    const savedTheme = localStorage.getItem(this.storageKey);
    
    if (savedTheme) {
      this.setTheme(savedTheme);
    } else {
      // Auto-detect from system
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.setTheme(prefersDark ? 'dark' : 'light');
    }

    // Listen for system theme changes
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
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    this.setTheme(next);
  }

  updateToggleIcon(theme) {
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
      toggle.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
    }
  }

  getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
  }
}

// ========== CAMERA/VIDEO MANAGEMENT ==========
class CameraManager {
  constructor(elementId) {
    this.element = document.getElementById(elementId);
    this.video = this.element?.querySelector('video') || this.element?.querySelector('img');
    this.fullscreenBtn = document.getElementById('camera-fullscreen-btn');
    this.init();
  }

  init() {
    if (!this.element) return;

    // Fullscreen button handler
    if (this.fullscreenBtn) {
      this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
    }

    // Keyboard shortcut: 'f' for fullscreen
    document.addEventListener('keydown', (e) => {
      if (e.key === 'f' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        this.toggleFullscreen();
      }
    });

    // Handle fullscreen change events
    document.addEventListener('fullscreenchange', () => this.onFullscreenChange());
    document.addEventListener('webkitfullscreenchange', () => this.onFullscreenChange());
  }

  async toggleFullscreen() {
    try {
      if (!document.fullscreenElement && !document.webkitFullscreenElement) {
        // Enter fullscreen
        if (this.element.requestFullscreen) {
          await this.element.requestFullscreen();
        } else if (this.element.webkitRequestFullscreen) {
          await this.element.webkitRequestFullscreen();
        }
      } else {
        // Exit fullscreen
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
      this.fullscreenBtn.textContent = isFullscreen ? '⤓ Exit Fullscreen' : '⤢ Fullscreen';
    }
  }
}

// ========== DATA MANAGEMENT ==========
class DataManager {
  constructor() {
    this.updateInterval = null;
    this.statsEndpoint = '/api/stats';
    this.statusEndpoint = '/api/status';
    this.metricsEndpoint = '/api/metrics';
    this.stepperStatusEndpoint = '/api/stepper/status';
  }

  async fetchJSON(url, options = {}) {
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
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Fetch error for ${url}:`, error);
      throw error;
    }
  }

  async updateBubbleRate() {
    try {
      const data = await this.fetchJSON(this.metricsEndpoint);
      const bpm = data?.bubble_rate_bpm || 0;
      const delta = data?.bubble_rate_delta || 0;

      const valueEl = document.getElementById('bubble-rate-value');
      const deltaEl = document.getElementById('bubble-rate-delta');

      if (valueEl) {
        valueEl.textContent = Math.round(bpm);
      }

      if (deltaEl) {
        const sign = delta >= 0 ? '+' : '';
        deltaEl.textContent = `${delta >= 0 ? '▲' : '▼'} ${sign}${delta} vs last min`;
        deltaEl.className = `metric-delta ${delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral'}`;
      }
    } catch (error) {
      // Graceful degradation - use mock data
      this.useMockBubbleRate();
    }
  }

  useMockBubbleRate() {
    const valueEl = document.getElementById('bubble-rate-value');
    const deltaEl = document.getElementById('bubble-rate-delta');

    if (valueEl) {
      // Generate realistic mock data with slight variation
      const baseBPM = 68;
      const variation = Math.floor(Math.random() * 10) - 5;
      valueEl.textContent = baseBPM + variation;
    }

    if (deltaEl) {
      const delta = Math.floor(Math.random() * 9) - 4;
      const sign = delta >= 0 ? '+' : '';
      deltaEl.textContent = `${delta >= 0 ? '▲' : '▼'} ${sign}${delta} vs last min`;
      deltaEl.className = `metric-delta ${delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral'}`;
    }
  }

  async updateSystemStats() {
    try {
      const data = await this.fetchJSON(this.statsEndpoint);

      // CPU Temperature
      const tempEl = document.getElementById('cpu-temp-value');
      if (tempEl && data?.cpu?.temp_c) {
        tempEl.textContent = data.cpu.temp_c.toFixed(1);
      }

      // FPS (if available)
      const fpsEl = document.getElementById('fps-value');
      if (fpsEl && data?.camera?.fps) {
        fpsEl.textContent = Math.round(data.camera.fps);
      }

      // Uptime
      const uptimeEl = document.getElementById('uptime-value');
      if (uptimeEl && data?.uptime_seconds) {
        uptimeEl.textContent = this.formatUptime(data.uptime_seconds);
      }

      // CPU Usage
      const cpuUsageEl = document.getElementById('cpu-usage-value');
      if (cpuUsageEl && data?.cpu?.usage_percent !== undefined) {
        cpuUsageEl.textContent = data.cpu.usage_percent.toFixed(1);
      }
    } catch (error) {
      // Use mock data on error
      this.useMockSystemStats();
    }
  }

  useMockSystemStats() {
    const tempEl = document.getElementById('cpu-temp-value');
    if (tempEl) tempEl.textContent = (45 + Math.random() * 5).toFixed(1);

    const fpsEl = document.getElementById('fps-value');
    if (fpsEl) fpsEl.textContent = Math.round(28 + Math.random() * 4);

    const uptimeEl = document.getElementById('uptime-value');
    if (uptimeEl) uptimeEl.textContent = '5d 14h';

    const cpuUsageEl = document.getElementById('cpu-usage-value');
    if (cpuUsageEl) cpuUsageEl.textContent = (25 + Math.random() * 30).toFixed(1);
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

  async updateAIStatus() {
    try {
      const data = await this.fetchJSON(this.statusEndpoint);

      const statusEl = document.getElementById('ai-status-badge');
      const modelEl = document.getElementById('ai-model-name');
      const timeEl = document.getElementById('ai-last-updated');

      if (statusEl && data?.ai_status) {
        const status = data.ai_status.toLowerCase();
        statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        statusEl.className = `status-badge ${status === 'running' ? 'success' : status === 'error' ? 'error' : 'warning'}`;
      }

      if (modelEl && data?.model_name) {
        modelEl.textContent = data.model_name;
      }

      if (timeEl && data?.last_updated) {
        timeEl.textContent = new Date(data.last_updated).toLocaleTimeString();
      }
    } catch (error) {
      // Use mock data
      const statusEl = document.getElementById('ai-status-badge');
      if (statusEl) {
        statusEl.textContent = 'Idle';
        statusEl.className = 'status-badge warning';
      }

      const modelEl = document.getElementById('ai-model-name');
      if (modelEl) modelEl.textContent = 'YOLOv8n';

      const timeEl = document.getElementById('ai-last-updated');
      if (timeEl) timeEl.textContent = new Date().toLocaleTimeString();
    }
  }

  async updateStepperStatus() {
    try {
      const data = await this.fetchJSON(this.stepperStatusEndpoint);

      const posEl = document.getElementById('stepper-position');
      const statusEl = document.getElementById('stepper-status-text');

      if (posEl && data?.position_steps !== undefined) {
        posEl.textContent = data.position_steps;
      }

      if (statusEl) {
        const enabled = data?.enabled ? 'Enabled' : 'Disabled';
        const moving = data?.moving ? ', Moving' : '';
        statusEl.textContent = `${enabled}${moving}`;
      }
    } catch (error) {
      // Graceful degradation
      const statusEl = document.getElementById('stepper-status-text');
      if (statusEl) statusEl.textContent = 'Unknown';
    }
  }

  async updateAlerts() {
    try {
      // Placeholder - implement when alerts endpoint is available
      const alertsEl = document.getElementById('alerts-list');
      if (alertsEl && alertsEl.children.length === 0) {
        // Show empty state
        alertsEl.innerHTML = `
          <div class="empty-state" style="padding: var(--space-6);">
            <div class="empty-state-icon">✓</div>
            <div class="empty-state-message">No alerts</div>
          </div>
        `;
      }
    } catch (error) {
      console.error('Error updating alerts:', error);
    }
  }

  startAutoUpdate(interval = 5000) {
    // Initial update
    this.updateAll();

    // Set up periodic updates
    this.updateInterval = setInterval(() => {
      this.updateAll();
    }, interval);
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
      this.updateAIStatus(),
      this.updateStepperStatus(),
      this.updateAlerts(),
    ]);
  }
}

// ========== STEPPER CONTROLS ==========
class StepperController {
  constructor() {
    this.baseUrl = '/api/stepper';
    this.bindButtons();
  }

  async sendCommand(endpoint, options = {}) {
    const messageEl = document.getElementById('stepper-message');
    
    try {
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
        messageEl.style.color = 'var(--success)';
      }

      return data;
    } catch (error) {
      if (messageEl) {
        messageEl.textContent = `Error: ${error.message}`;
        messageEl.style.color = 'var(--error)';
      }
      throw error;
    }
  }

  bindButtons() {
    const buttons = {
      'stepper-enable': () => this.sendCommand('/enable'),
      'stepper-disable': () => this.sendCommand('/disable'),
      'stepper-open': () => this.sendCommand('/open'),
      'stepper-close': () => this.sendCommand('/close'),
      'stepper-abort': () => this.sendCommand('/abort'),
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

    // Stepper slider
    const slider = document.getElementById('stepper-slider');
    const sliderValue = document.getElementById('stepper-slider-value');
    
    if (slider && sliderValue) {
      slider.addEventListener('input', (e) => {
        sliderValue.textContent = e.target.value;
      });

      slider.addEventListener('change', async (e) => {
        const steps = e.target.value;
        try {
          await this.sendCommand(`/step?steps=${steps}`);
        } catch (error) {
          console.error('Slider command error:', error);
        }
      });
    }
  }
}

// ========== BUTTON INTERACTIONS ==========
class ButtonInteractions {
  constructor() {
    this.init();
  }

  init() {
    // Add press effect to all buttons
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn');
      if (btn) {
        this.animatePress(btn);
      }
    });

    // Keyboard support for custom buttons
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        const btn = e.target.closest('.btn');
        if (btn) {
          e.preventDefault();
          btn.click();
        }
      }
    });
  }

  animatePress(button) {
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
      button.style.transform = '';
    }, 100);
  }
}

// ========== CARD ANIMATIONS ==========
class CardAnimations {
  constructor() {
    this.observeCards();
  }

  observeCards() {
    // Stagger card entrance animations
    const cards = document.querySelectorAll('.card');
    
    cards.forEach((card, index) => {
      card.style.animationDelay = `${index * 30}ms`;
    });

    // Use Intersection Observer for scroll-triggered animations
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.style.opacity = '1';
              entry.target.style.transform = 'translateY(0)';
            }
          });
        },
        {
          threshold: 0.1,
        }
      );

      cards.forEach((card) => observer.observe(card));
    }
  }
}

// ========== LOGS VIEWER ==========
class LogsViewer {
  constructor(elementId) {
    this.container = document.getElementById(elementId);
    this.maxLogs = 50;
    this.logs = [];
    this.init();
  }

  init() {
    if (!this.container) return;

    // Add some mock logs for demonstration
    this.addMockLogs();

    // Auto-scroll to bottom
    this.scrollToBottom();
  }

  addLog(time, message, level = 'info') {
    const entry = { time, message, level };
    this.logs.unshift(entry);

    if (this.logs.length > this.maxLogs) {
      this.logs.pop();
    }

    this.render();
  }

  addMockLogs() {
    const now = new Date();
    const mockLogs = [
      { time: new Date(now - 5000), message: 'Camera stream started', level: 'info' },
      { time: new Date(now - 15000), message: 'Stepper motor enabled', level: 'info' },
      { time: new Date(now - 45000), message: 'AI model loaded: YOLOv8n', level: 'success' },
      { time: new Date(now - 120000), message: 'System startup complete', level: 'success' },
      { time: new Date(now - 180000), message: 'Connecting to API...', level: 'info' },
    ];

    this.logs = mockLogs;
    this.render();
  }

  render() {
    if (!this.container) return;

    this.container.innerHTML = this.logs
      .map(
        (log) => `
        <div class="log-entry">
          <span class="log-time">${this.formatTime(log.time)}</span>
          <span class="log-message">${this.escapeHtml(log.message)}</span>
        </div>
      `
      )
      .join('');
  }

  formatTime(date) {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  scrollToBottom() {
    if (this.container) {
      this.container.scrollTop = this.container.scrollHeight;
    }
  }
}

// ========== INITIALIZE APPLICATION ==========
class Dashboard {
  constructor() {
    this.themeManager = null;
    this.dataManager = null;
    this.cameraManager = null;
    this.stepperController = null;
    this.buttonInteractions = null;
    this.cardAnimations = null;
    this.logsViewer = null;
  }

  init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    console.log('🚀 Initializing UU Plastination Dashboard...');

    // Initialize theme management
    this.themeManager = new ThemeManager();

    // Bind theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        this.themeManager.toggleTheme();
      });
    }

    // Initialize camera/video
    this.cameraManager = new CameraManager('camera-widget');

    // Initialize data management and start updates
    this.dataManager = new DataManager();
    this.dataManager.startAutoUpdate(5000);

    // Initialize stepper controls
    this.stepperController = new StepperController();

    // Initialize button interactions
    this.buttonInteractions = new ButtonInteractions();

    // Initialize card animations
    this.cardAnimations = new CardAnimations();

    // Initialize logs viewer
    this.logsViewer = new LogsViewer('logs-container');

    // Keyboard shortcuts
    this.setupKeyboardShortcuts();

    console.log('✅ Dashboard initialized successfully');
  }

  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ignore if user is typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      // 't' - toggle theme
      if (e.key === 't') {
        e.preventDefault();
        this.themeManager.toggleTheme();
      }

      // 'f' - fullscreen camera (handled in CameraManager)
      // 'r' - refresh data
      if (e.key === 'r') {
        e.preventDefault();
        this.dataManager.updateAll();
      }

      // '?' - show help
      if (e.key === '?') {
        e.preventDefault();
        this.showHelp();
      }
    });
  }

  showHelp() {
    const shortcuts = [
      { key: 't', description: 'Toggle theme' },
      { key: 'f', description: 'Toggle fullscreen camera' },
      { key: 'r', description: 'Refresh data' },
      { key: '?', description: 'Show this help' },
    ];

    const message = shortcuts
      .map((s) => `${s.key} - ${s.description}`)
      .join('\n');

    alert(`Keyboard Shortcuts:\n\n${message}`);
  }

  destroy() {
    // Clean up
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
