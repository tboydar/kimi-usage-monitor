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
        # 立即退出 / Exit immediately
        import sys
        sys.exit(0)
    
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
    
    def run(self, once: bool = False) -> None:
        """Run the monitor.
        
        Args:
            once: Run once and exit / 執行一次後退出
        """
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
        
        # 檢查是否支援使用量查詢 / Check if usage query is supported
        usage = self.api.get_usage()
        if usage.total_quota == 0 and self.api.provider == "kimicode":
            self.ui.print_warning("Kimi Code API does not support usage queries / Kimi Code API 不支援使用查詢")
            self.ui.print_info("OAuth tokens cannot access usage endpoints / OAuth token 無法存取使用量端點")
            self.ui.print_info("\nTo see your usage:")
            self.ui.print_info("  1. Visit https://platform.moonshot.cn/console/account")
            self.ui.print_info("  2. Or use Moonshot API Key instead of kimi-cli OAuth")
            self.ui.print_info("\n你仍可以正常使用 kimi-cli / You can still use kimi-cli normally")
            
            # 顯示可用資訊 / Show available info
            self.ui.print_info("\n📊 Connection Info / 連線資訊:")
            self.ui.print_info(f"  Provider: {self.api.provider}")
            self.ui.print_info(f"  Base URL: {self.api.base_url}")
            if self.api.api_key:
                self.ui.print_info(f"  Auth: OAuth (kimi-cli)")
            
            # 顯示模型資訊 / Show model info
            try:
                models = self.api.get_models()
                if models:
                    self.ui.print_info(f"\n  Available Models / 可用模型:")
                    for model in models:
                        self.ui.print_info(f"    - {model.get('display_name', model.get('id', 'Unknown'))}")
            except:
                pass
            
            if once:
                sys.exit(0)
            else:
                self.ui.print_info("\nPress Ctrl+C to exit / 按 Ctrl+C 退出")
                self._running = True
                try:
                    while self._running:
                        import time
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    self._running = False
                self.ui.print_info("\nExiting... / 退出中...")
                sys.exit(0)
        
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
