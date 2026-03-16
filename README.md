# 🌙 Kimi CLI Usage Monitor

A beautiful real-time terminal monitoring tool for Kimi AI usage with advanced analytics and Rich UI. Track your token consumption, monitor expiration dates, and get detailed usage insights.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

```
🌙 Kimi Usage Monitor
══════════════════════════════════════════════════
Last updated: 2024-03-16 15:30:00
══════════════════════════════════════════════════

Token Usage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  24.0%
                                            3.8M remaining

📊 Usage Statistics
Metric          Value         Percentage
─────────────────────────────────────────
Total Quota     5.0M          100%
Used            1.2M          24.0%
Remaining       3.8M          76.0%
Today's Usage   125K
This Week       890K
Total Cost      $0.50

📋 Plan Information
┌─────────────────────────────────────┐
│ Plan: PRO                           │
│ Expires: 2024-04-15 (30 days left)  │
│ Reset: Daily                        │
└─────────────────────────────────────┘

══════════════════════════════════════════════════
Press Ctrl+C to exit | Auto-refresh: 10s
══════════════════════════════════════════════════
```

## ✨ Features

### 🔄 Real-time Monitoring
- Live token usage tracking with beautiful progress bars
- Configurable refresh rates (1-60 seconds)
- Auto-updating display with smooth animations

### 📊 Rich UI Components
- **Progress Bars**: Visual representation of token usage
- **Data Tables**: Detailed usage statistics
- **Plan Information**: Current plan, expiration, and reset period
- **Daily History**: Last 7 days usage breakdown

### 🎨 Beautiful Themes
- **Auto**: Automatically detects terminal background
- **Light**: Clean light theme
- **Dark**: Eye-friendly dark theme
- **Classic**: Traditional terminal colors

### 🌍 Multi-Provider Support
- **Moonshot CN**: Chinese endpoint (api.moonshot.cn)
- **Moonshot Global**: International endpoint (api.moonshot.ai)
- **Kimi Code**: Coding-specific endpoint (api.kimi.com)

### 📈 Usage Analytics
- Total quota and remaining tokens
- Daily, weekly, and monthly usage
- Cost estimates
- Expiration date tracking

## 🚀 Installation

### Using pip (Recommended)

```bash
pip install kimi-monitor
```

### Using uv (Modern Python)

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install with uv
uv tool install kimi-monitor
```

### From Source

```bash
git clone https://github.com/eugene/kimi-usage-monitor.git
cd kimi-usage-monitor
pip install -e .
```

## 📖 Usage

### Quick Start

```bash
# Set your API key
export KIMI_API_KEY="sk-..."

# Start monitoring
kimi-monitor
```

### Command Aliases

```bash
kimi-monitor      # Full command
kimi-usage        # Alternative
km                # Shortest alias
```

### Configuration Options

```bash
# Use specific plan
kimi-monitor --plan max5

# Dark theme
kimi-monitor --theme dark

# Faster refresh
kimi-monitor --refresh-rate 5

# Run once (no live mode)
kimi-monitor --once

# Use Kimi Code API
kimi-monitor --provider kimicode
```

### Available Plans

| Plan | Description |
|------|-------------|
| `free` | Free tier |
| `pro` | Pro subscription |
| `max5` | Max5 subscription |
| `max20` | Max20 subscription |
| `custom` | Custom limits |

### Provider Options

| Provider | Endpoint |
|----------|----------|
| `moonshot` | https://api.moonshot.cn/v1 |
| `moonshot-global` | https://api.moonshot.ai/v1 |
| `kimicode` | https://api.kimi.com/coding/v1 |

## 🔧 Configuration

### Environment Variables

```bash
# Required
export KIMI_API_KEY="sk-..."

# Optional
export MOONSHOT_API_KEY="sk-..."  # Alternative
```

### Saved Configuration

Settings are automatically saved to `~/.kimi-monitor/config.json`:

```json
{
  "theme": "dark",
  "refresh_rate": 10,
  "timezone": "Asia/Shanghai",
  "time_format": "24h"
}
```

Clear saved settings:

```bash
kimi-monitor --clear
```

## 📊 Display Views

### Real-time View (Default)

```bash
kimi-monitor --view realtime
```

Shows:
- Live progress bar
- Current usage statistics
- Plan information
- Last 7 days history

### Daily View

```bash
kimi-monitor --view daily --once
```

Displays aggregated daily usage statistics.

### Monthly View

```bash
kimi-monitor --view monthly --once
```

Shows monthly usage trends and analytics.

## 🎨 Themes

```bash
# Auto-detect (default)
kimi-monitor --theme auto

# Light theme
kimi-monitor --theme light

# Dark theme
kimi-monitor --theme dark

# Classic terminal colors
kimi-monitor --theme classic
```

## 📝 Logging

```bash
# Debug logging
kimi-monitor --log-level DEBUG

# Log to file
kimi-monitor --log-file ~/.kimi-monitor/monitor.log
```

## 🛠️ Development

### Setup Development Environment

```bash
git clone https://github.com/eugene/kimi-usage-monitor.git
cd kimi-usage-monitor
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
ruff check src/
```

## 📁 Project Structure

```
kimi-usage-monitor/
├── src/
│   └── kimi_monitor/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py          # CLI entry point
│       ├── models.py       # Data models
│       ├── api.py          # API client
│       ├── ui.py           # Rich UI components
│       └── monitor.py      # Monitor engine
├── tests/
├── docs/
├── pyproject.toml
├── README.md
└── LICENSE
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal UI
- Uses [Click](https://github.com/pallets/click) for CLI interface

## 📞 Support

- GitHub Issues: [Report a bug](https://github.com/eugene/kimi-usage-monitor/issues)
- Discussions: [Ask a question](https://github.com/eugene/kimi-usage-monitor/discussions)

## 🔗 Links

- [Kimi Platform](https://platform.moonshot.cn)
- [Kimi Code](https://www.kimi.com/code)
- [API Documentation](https://platform.moonshot.cn/docs)

---

Made with ❤️ for the Kimi AI community
