# Dashboard Assets — Apple-Inspired Dark Mode

Modern, minimal control dashboard for the UU Plastination lab monitoring system.

## Design System

### Colors
- **Background**: `#0B0B0F` (ultra-dark)
- **Surface**: `#111216` (card background)
- **Surface-2**: `#15171D` (elevated elements)
- **Border**: `rgba(255,255,255,0.08)` (subtle borders)
- **Accent**: `#0A84FF` (iOS blue)
- **Positive**: `#30D158` (success states)
- **Warning**: `#FFD60A` (warnings)
- **Danger**: `#FF453A` (errors, recording)

### Typography
- **Font Stack**: SF Pro Text, SF Pro Display, -apple-system, BlinkMacSystemFont, Inter, Segoe UI
- **Sizes**: Base 16px, headings use optical sizing (H1: 28px, H2: 22px, H3: 18px)
- **Mono**: SF Mono for code/data display

### Layout
- **12-column grid** on desktop (xl: ≥1280px)
- **6-column grid** on tablet (md: 768–1279px)
- **Full-width stack** on mobile (<768px)
- **Grid gaps**: 16px (mobile), 20px (desktop)

### Cards
- Border radius: `24px` (--radius-2xl)
- Padding: `20px` (mobile), `24px` (desktop)
- Shadow: Subtle elevation with top highlight
- Border: 1px solid rgba(255,255,255,0.08)

## Files

```
assets/
├── styles/
│   ├── design-tokens.css  # Color palette, spacing, typography
│   └── dashboard.css      # Layout, components, utilities
└── js/
    └── dashboard.js       # Logic, data fetching, interactions
```

## JavaScript Architecture

### Mock Data Mode

Set `MOCK_DATA = true` at the top of `dashboard.js` to use simulated data. Great for development and testing without a live backend.

```javascript
const MOCK_DATA = true; // Change to false for production
```

When `MOCK_DATA` is enabled:
- Bubble rate, system stats, and stepper status are generated locally
- Commands are logged to console but don't hit the API
- Chart renders with realistic animated data

### Key Classes

#### `Dashboard`
Main orchestrator. Initializes all subsystems.

#### `ThemeManager`
Handles light/dark mode toggle. Persists preference to localStorage. Auto-detects system preference.

#### `RecordingControl`
Manages the recording button in the header. Updates UI state (hollow dot → solid red dot with animation).

**TODO**: Wire `toggle()` method to backend recording endpoint.

#### `CameraManager`
- Fullscreen toggle (button or `f` key)
- Handles both `<video>` and `<img>` streams

**Stream URL**: `/stream.mjpg` (configure in HTML `<img src>` if different)

#### `BubbleChart`
Simple canvas-based line chart with area fill. Supports time range filters (15m, 1h, 6h, 24h).

**TODO**: Replace with a proper charting library (e.g., Chart.js, recharts) if more features are needed.

#### `DataManager`
Polls APIs every 5 seconds (configurable via `UPDATE_INTERVAL`).

**API Endpoints** (configure in `dashboard.js`):
- `GET /api/metrics` → Bubble rate + delta
- `GET /api/stats` → CPU, memory, uptime, services
- `GET /api/stepper/status` → Position, enabled state, errors

#### `ValveController`
Sends valve commands. Button actions:
- Enable / Disable
- Open / Close (preset moves)
- `+` / `−` (step adjustments)
- Abort (emergency stop)

**API Endpoints**:
- `POST /api/stepper/enable`
- `POST /api/stepper/disable`
- `POST /api/stepper/open`
- `POST /api/stepper/close`
- `POST /api/stepper/abort`
- `POST /api/stepper/step?steps=N`

## Integration Checklist

### 1. Disable Mock Mode
```javascript
// In dashboard.js, line ~8
const MOCK_DATA = false;
```

### 2. Verify API Endpoints
Ensure FastAPI routes match the paths in `DataManager` and `ValveController`.

### 3. Camera Stream URL
Update `<img src="/stream.mjpg">` in `index.html` if your stream is at a different path.

### 4. Wire Recording Control
In `RecordingControl.toggle()`, add fetch call to start/stop recording:
```javascript
async toggle() {
  this.recording = !this.recording;
  this.updateUI();
  
  // Add this:
  await fetch('/api/recording/toggle', { 
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recording: this.recording })
  });
}
```

### 5. Test Responsiveness
Open dashboard on:
- Desktop (1920×1080, 1280×720)
- Tablet (768px)
- Mobile (375px)

Grid should reflow correctly at each breakpoint.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `t` | Toggle light/dark theme |
| `f` | Fullscreen camera |
| `Ctrl+r` | Toggle recording |
| `?` | Show help |

## Accessibility

- All interactive elements have min 44×44px hit areas
- Keyboard navigation supported (Tab, Enter, Space)
- Focus rings use accent color (2px outline)
- `aria-label` and `role` attributes on key widgets
- Reduced motion support (`prefers-reduced-motion`)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

Uses modern CSS (custom properties, grid, backdrop-filter) and ES2020 JavaScript (optional chaining, nullish coalescing).

## Performance

- No heavy dependencies (vanilla JS + canvas)
- Auto-update intervals: 5s (stats), 2s (chart)
- Canvas chart renders ~60fps
- Lazy-loads images with `onerror` fallback

## Future Enhancements

- WebSocket for real-time bubble rate stream
- Replace canvas chart with Chart.js or recharts
- Add alerts/events feed with timestamps
- Export chart data as CSV
- Multi-camera support with tabs/carousel
- User authentication UI (currently assumes auth is upstream)

## License

Internal use only. Part of the UU Plastination project.
