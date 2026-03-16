"""Kimi Usage Monitor main module."""

import time
import signal
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

from .api import KimiAPI, KimiAPIError
from .models import UsageData, Config, DailyUsage
from .ui import KimiUI
from .kimicli_auth import KimiCLIAuth

logger = logging.getLogger(__name__)


class KimiMonitor:
    """Kimi Usage Monitor."""
    
    def __init__(self, config: Config):
        """Initialize monitor.
        
        Args:
            config: Monitor configuration
        """
        self.config = config
        self.api = KimiAPI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self.ui = KimiUI(config)
        self._running = False
        self._daily_data: List[DailyUsage] = []
        self._last_daily_fetch: Optional[datetime] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal")
        self._running = False
    
    def _should_fetch_daily(self) -> bool:
        """Check if daily data should be fetched."""
        if not self._last_daily_fetch:
            return True
        return datetime.now() - self._last_daily_fetch > timedelta(minutes=5)
    
    def _fetch_data(self) -> Optional[UsageData]:
        """Fetch usage data.
        
        Returns:
            Usage data or None if failed
        """
        try:
            usage = self.api.get_usage()
            
            # Fetch daily data if needed
            if self._should_fetch_daily():
                self._daily_data = self.api.get_daily_usage(days=7)
                self._last_daily_fetch = datetime.now()
            
            return usage
            
        except KimiAPIError as e:
            self.ui.print_error(str(e))
            return None
    
    def _update_display(self, usage: UsageData) -> None:
        """Update display.
        
        Args:
            usage: Usage data
        """
        layout = self.ui.create_main_layout(usage, self._daily_data)
        self.ui.update_live(layout)
    
    def run(self) -> None:
        """Run the monitor."""
        # 顯示 kimi-cli 狀態 / Show kimi-cli status
        if KimiCLIAuth.is_installed():
            self.ui.print_info("Detected kimi-cli installation / 檢測到 kimi-cli 安裝")
            if KimiCLIAuth.is_authenticated():
                self.ui.print_success("Using kimi-cli authentication / 使用 kimi-cli 認證")
            else:
                self.ui.print_warning("kimi-cli not authenticated / kimi-cli 未認證")
        
        # Check API key
        if not self.api.api_key:
            self.ui.print_error("No API key found. Please set KIMI_API_KEY environment variable.")
            self.ui.print_info("Or login with: kimi login / 或使用 kimi login 登入")
            self.ui.print_info("Get your API key from: https://platform.moonshot.cn")
            sys.exit(1)
        
        # Test connection
        self.ui.print_info("Testing connection to Kimi API...")
        if not self.api.test_connection():
            self.ui.print_error("Failed to connect to Kimi API. Please check your API key.")
            sys.exit(1)
        
        self.ui.print_success("Connected to Kimi API!")
        
        # Initial data fetch
        usage = self._fetch_data()
        if not usage:
            self.ui.print_error("Failed to fetch usage data.")
            sys.exit(1)
        
        # Start live display
        layout = self.ui.create_main_layout(usage, self._daily_data)
        self.ui.start_live(layout)
        self._running = True
        
        logger.info("Monitor started")
        
        try:
            while self._running:
                # Fetch updated data
                usage = self._fetch_data()
                
                if usage:
                    self._update_display(usage)
                
                # Wait for next refresh
                time.sleep(self.config.refresh_rate)
                
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
        finally:
            self.ui.stop_live()
            self.ui.print_info("Monitor stopped. Goodbye!")
    
    def run_once(self) -> Optional[UsageData]:
        """Run monitor once and return data.
        
        Returns:
            Usage data or None
        """
        if not self.api.api_key:
            self.ui.print_error("No API key found. Please set KIMI_API_KEY environment variable.")
            return None
        
        return self._fetch_data()
    
    def print_summary(self, usage: UsageData) -> None:
        """Print usage summary.
        
        Args:
            usage: Usage data
        """
        self.ui.console.print()
        self.ui.console.print("=" * 50)
        self.ui.console.print("🌙 Kimi Usage Summary")
        self.ui.console.print("=" * 50)
        
        # Progress bar
        progress = self.ui.create_progress_bar(usage)
        self.ui.console.print(progress)
        
        # Usage table
        self.ui.console.print()
        self.ui.console.print(self.ui.create_usage_table(usage))
        
        # Plan info
        self.ui.console.print()
        self.ui.console.print(self.ui.create_plan_info(usage))
        
        # Daily data
        if self._daily_data:
            self.ui.console.print()
            self.ui.console.print(self.ui.create_daily_table(self._daily_data))
        
        self.ui.console.print()
        self.ui.console.print("=" * 50)
