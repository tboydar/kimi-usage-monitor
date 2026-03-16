"""Tests for monitor module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
import signal

from kimi_monitor.monitor import KimiMonitor
from kimi_monitor.models import Config, UsageData
from kimi_monitor.api import KimiAPIError


class TestKimiMonitorInit:
    """Test KimiMonitor initialization."""
    
    def test_init(self, mock_config):
        """Test monitor initialization."""
        monitor = KimiMonitor(mock_config)
        
        assert monitor.config == mock_config
        assert monitor.api is not None
        assert monitor.ui is not None
        assert monitor._running is False
    
    def test_signal_handlers(self, mock_config):
        """Test signal handlers are set up."""
        monitor = KimiMonitor(mock_config)
        
        # Signal handlers should be set
        # (We can't easily test this without actually sending signals)


class TestKimiMonitorSignalHandling:
    """Test signal handling."""
    
    def test_signal_handler(self, mock_config):
        """Test signal handler sets running to False."""
        monitor = KimiMonitor(mock_config)
        monitor._running = True
        
        # Simulate signal
        monitor._signal_handler(signal.SIGINT, None)
        
        assert monitor._running is False


class TestKimiMonitorFetchData:
    """Test data fetching."""
    
    @patch('kimi_monitor.monitor.KimiAPI')
    def test_fetch_data_success(self, mock_api_class, mock_config, mock_usage_data):
        """Test successful data fetch."""
        mock_api = MagicMock()
        mock_api.get_usage.return_value = mock_usage_data
        mock_api_class.return_value = mock_api
        
        monitor = KimiMonitor(mock_config)
        result = monitor._fetch_data()
        
        assert result == mock_usage_data
        assert monitor._daily_data == []  # Empty because we mocked get_daily_usage to fail
    
    @patch('kimi_monitor.monitor.KimiAPI')
    def test_fetch_data_api_error(self, mock_api_class, mock_config):
        """Test data fetch with API error."""
        mock_api = MagicMock()
        mock_api.get_usage.side_effect = KimiAPIError("API Error")
        mock_api_class.return_value = mock_api
        
        monitor = KimiMonitor(mock_config)
        result = monitor._fetch_data()
        
        assert result is None
    
    @patch('kimi_monitor.monitor.KimiAPI')
    def test_fetch_data_daily_cache(self, mock_api_class, mock_config, mock_usage_data, mock_daily_usage):
        """Test daily data caching."""
        mock_api = MagicMock()
        mock_api.get_usage.return_value = mock_usage_data
        mock_api.get_daily_usage.return_value = mock_daily_usage
        mock_api_class.return_value = mock_api
        
        monitor = KimiMonitor(mock_config)
        
        # First fetch
        monitor._fetch_data()
        assert len(monitor._daily_data) == 2
        
        # Second fetch (should use cache)
        monitor._fetch_data()
        # get_daily_usage should only be called once due to caching
        assert mock_api.get_daily_usage.call_count == 1
    
    def test_should_fetch_daily_initial(self, mock_config):
        """Test should fetch daily when no previous fetch."""
        monitor = KimiMonitor(mock_config)
        
        assert monitor._should_fetch_daily() is True
    
    def test_should_fetch_daily_recent(self, mock_config):
        """Test should not fetch daily when recently fetched."""
        monitor = KimiMonitor(mock_config)
        monitor._last_daily_fetch = datetime.now(timezone.utc)
        
        assert monitor._should_fetch_daily() is False


class TestKimiMonitorRunOnce:
    """Test run_once method."""
    
    @patch('kimi_monitor.monitor.KimiAPI')
    def test_run_once_success(self, mock_api_class, mock_config, mock_usage_data):
        """Test successful run_once."""
        mock_api = MagicMock()
        mock_api.api_key = "sk-test"
        mock_api.get_usage.return_value = mock_usage_data
        mock_api_class.return_value = mock_api
        
        monitor = KimiMonitor(mock_config)
        result = monitor.run_once()
        
        assert result == mock_usage_data
    
    @patch('kimi_monitor.monitor.KimiAPI')
    def test_run_once_no_api_key(self, mock_api_class, mock_config):
        """Test run_once without API key."""
        mock_api = MagicMock()
        mock_api.api_key = None
        mock_api_class.return_value = mock_api
        
        monitor = KimiMonitor(mock_config)
        result = monitor.run_once()
        
        assert result is None


class TestKimiMonitorPrintSummary:
    """Test print_summary method."""
    
    def test_print_summary(self, mock_config, mock_usage_data, mock_daily_usage, capsys):
        """Test summary printing."""
        monitor = KimiMonitor(mock_config)
        monitor._daily_data = mock_daily_usage
        
        monitor.print_summary(mock_usage_data)
        
        captured = capsys.readouterr()
        assert "Kimi Usage Summary" in captured.out


class TestKimiMonitorUpdateDisplay:
    """Test display update."""
    
    def test_update_display(self, mock_config, mock_usage_data):
        """Test display update."""
        monitor = KimiMonitor(mock_config)
        
        # Create mock live display
        monitor.ui._live = MagicMock()
        
        monitor._update_display(mock_usage_data)
        
        # Should call update on live display
        monitor.ui._live.update.assert_called_once()


class TestKimiMonitorFullRun:
    """Test full run method with mocking."""
    
    @patch('kimi_monitor.monitor.KimiAPI')
    @patch('kimi_monitor.monitor.KimiCLIAuth')
    def test_run_no_api_key(self, mock_auth_class, mock_api_class, mock_config):
        """Test run without API key exits."""
        mock_api = MagicMock()
        mock_api.api_key = None
        mock_api_class.return_value = mock_api
        
        mock_auth = MagicMock()
        mock_auth.is_installed.return_value = False
        mock_auth_class.return_value = mock_auth
        
        monitor = KimiMonitor(mock_config)
        
        with pytest.raises(SystemExit) as exc_info:
            monitor.run()
        
        assert exc_info.value.code == 1
    
    @patch('kimi_monitor.monitor.KimiAPI')
    @patch('kimi_monitor.monitor.KimiCLIAuth')
    def test_run_connection_failed(self, mock_auth_class, mock_api_class, mock_config):
        """Test run when connection test fails."""
        mock_api = MagicMock()
        mock_api.api_key = "sk-test"
        mock_api.test_connection.return_value = False
        mock_api_class.return_value = mock_api
        
        mock_auth = MagicMock()
        mock_auth.is_installed.return_value = False
        mock_auth_class.return_value = mock_auth
        
        monitor = KimiMonitor(mock_config)
        
        with pytest.raises(SystemExit) as exc_info:
            monitor.run()
        
        assert exc_info.value.code == 1
    
    @patch('kimi_monitor.monitor.KimiAPI')
    @patch('kimi_monitor.monitor.KimiCLIAuth')
    @patch('kimi_monitor.monitor.time.sleep')
    def test_run_successful_iteration(self, mock_sleep, mock_auth_class, mock_api_class, mock_config, mock_usage_data):
        """Test successful run iteration."""
        mock_api = MagicMock()
        mock_api.api_key = "sk-test"
        mock_api.test_connection.return_value = True
        mock_api.get_usage.return_value = mock_usage_data
        mock_api_class.return_value = mock_api
        
        mock_auth = MagicMock()
        mock_auth.is_installed.return_value = True
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth
        
        monitor = KimiMonitor(mock_config)
        monitor._running = True
        
        # Stop after first iteration
        def stop_after_first(*args, **kwargs):
            monitor._running = False
        
        mock_sleep.side_effect = stop_after_first
        
        # Mock UI live display
        monitor.ui.start_live = MagicMock()
        monitor.ui.stop_live = MagicMock()
        monitor.ui.update_live = MagicMock()
        
        # Should not raise
        monitor.run()
        
        assert monitor.ui.start_live.called
        assert monitor.ui.stop_live.called
