"""Command-line interface for Kimi Usage Monitor."""

import os
import sys
import json
import logging
from typing import Optional
from pathlib import Path

import click

from .models import Config
from .monitor import KimiMonitor
from .kimicli_auth import KimiCLIAuth


# Default config file location
CONFIG_DIR = Path.home() / ".kimi-monitor"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> Optional[dict]:
    """Load saved configuration."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def save_config(config_dict: dict) -> None:
    """Save configuration."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Don't save API key
    save_dict = {k: v for k, v in config_dict.items() if k != "api_key"}
    with open(CONFIG_FILE, "w") as f:
        json.dump(save_dict, f, indent=2)


def clear_config() -> None:
    """Clear saved configuration."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


@click.command()
@click.option(
    "--plan",
    type=click.Choice(["free", "pro", "max5", "max20", "custom"]),
    default="pro",
    help="Plan type",
)
@click.option(
    "--custom-limit",
    type=int,
    default=None,
    help="Custom token limit",
)
@click.option(
    "--view",
    type=click.Choice(["realtime", "daily", "monthly"]),
    default="realtime",
    help="View type",
)
@click.option(
    "--timezone",
    default="auto",
    help="Timezone (auto-detected by default)",
)
@click.option(
    "--time-format",
    type=click.Choice(["12h", "24h", "auto"]),
    default="auto",
    help="Time format",
)
@click.option(
    "--theme",
    type=click.Choice(["auto", "light", "dark", "classic"]),
    default="auto",
    help="Display theme",
)
@click.option(
    "--refresh-rate",
    type=int,
    default=10,
    help="Data refresh rate in seconds (1-60)",
)
@click.option(
    "--refresh-per-second",
    type=float,
    default=0.75,
    help="Display refresh rate in Hz (0.1-20.0)",
)
@click.option(
    "--provider",
    type=click.Choice(["moonshot", "moonshot-global", "kimicode"]),
    default="moonshot",
    help="API provider",
)
@click.option(
    "--base-url",
    default=None,
    help="Custom API base URL",
)
@click.option(
    "--no-cost",
    is_flag=True,
    help="Hide cost estimates",
)
@click.option(
    "--no-predictions",
    is_flag=True,
    help="Hide usage predictions",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Logging level",
)
@click.option(
    "--log-file",
    default=None,
    help="Log file path",
)
@click.option(
    "--once",
    is_flag=True,
    help="Run once and exit (no live monitoring)",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear saved configuration",
)
@click.option(
    "--version",
    "-v",
    is_flag=True,
    help="Show version information",
)
@click.option(
    "--check-kimicli",
    is_flag=True,
    help="Check kimi-cli status / 檢查 kimi-cli 狀態",
)
def main(
    plan: str,
    custom_limit: Optional[int],
    view: str,
    timezone: str,
    time_format: str,
    theme: str,
    refresh_rate: int,
    refresh_per_second: float,
    provider: str,
    base_url: Optional[str],
    no_cost: bool,
    no_predictions: bool,
    log_level: str,
    log_file: Optional[str],
    once: bool,
    clear: bool,
    version: bool,
    check_kimicli: bool,
):
    """Kimi Usage Monitor - Real-time terminal monitoring for Kimi AI usage.
    
    Examples:
    
        # Start with default settings
        kimi-monitor
        
        # Use specific plan
        kimi-monitor --plan max5
        
        # Custom refresh rate
        kimi-monitor --refresh-rate 5
        
        # Dark theme
        kimi-monitor --theme dark
        
        # Run once and exit
        kimi-monitor --once
        
        # Use Kimi Code API
        kimi-monitor --provider kimicode
    """
    if version:
        from . import __version__
        click.echo(f"kimi-monitor version {__version__}")
        sys.exit(0)
    
    if check_kimicli:
        KimiCLIAuth.print_status()
        sys.exit(0)
    
    if clear:
        clear_config()
        click.echo("✅ Configuration cleared")
        sys.exit(0)
    
    # Load saved config
    saved_config = load_config() or {}
    
    # Override with command line args
    config_dict = {
        "api_key": os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY"),
        "base_url": base_url or saved_config.get("base_url"),
        "refresh_rate": refresh_rate,
        "refresh_per_second": refresh_per_second,
        "theme": theme if theme != "auto" else saved_config.get("theme", "auto"),
        "timezone": timezone if timezone != "auto" else saved_config.get("timezone", "auto"),
        "time_format": time_format if time_format != "auto" else saved_config.get("time_format", "auto"),
        "plan": plan,
        "custom_limit": custom_limit or saved_config.get("custom_limit"),
        "show_cost": not no_cost,
        "show_predictions": not no_predictions,
        "log_level": log_level,
        "log_file": log_file or saved_config.get("log_file"),
    }
    
    # Set base URL based on provider
    if not config_dict["base_url"]:
        if provider == "moonshot-global":
            config_dict["base_url"] = "https://api.moonshot.ai/v1"
        elif provider == "kimicode":
            config_dict["base_url"] = "https://api.kimi.com/coding/v1"
        else:
            config_dict["base_url"] = "https://api.moonshot.cn/v1"
    
    # Save config (without API key)
    save_config(config_dict)
    
    # Setup logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        filename=log_file,
    )
    
    # Create config
    try:
        config = Config(**config_dict)
    except Exception as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)
    
    # Create monitor
    monitor = KimiMonitor(config)
    
    # Run
    try:
        if once:
            usage = monitor.run_once()
            if usage:
                # Check if usage is empty (Kimi Code API limitation)
                if usage.total_quota == 0 and monitor.api.provider == "kimicode":
                    click.echo("⚠️  Kimi Code API does not support usage queries / Kimi Code API 不支援使用查詢")
                    click.echo("ℹ️  You can still use kimi-cli normally / 你仍可以正常使用 kimi-cli")
                    sys.exit(0)
                monitor.print_summary(usage)
            else:
                sys.exit(1)
        else:
            monitor.run(once=once)
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye! / 再見！")
        sys.exit(0)
    except Exception as e:
        logging.exception("Monitor failed")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
