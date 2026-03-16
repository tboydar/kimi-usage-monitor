"""Tests for UI module."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from rich.table import Table
from rich.progress import Progress
from rich.panel import Panel

from kimi_monitor.ui import KimiUI, KimiTheme
from kimi_monitor.models import UsageData, Config


class TestKimiTheme:
    """Test KimiTheme class."""
    
    def test_get_dark_theme(self):
        """Test dark theme generation."""
        theme = KimiTheme.get_theme("dark")
        assert theme is not None
    
    def test_get_light_theme(self):
        """Test light theme generation."""
        theme = KimiTheme.get_theme("light")
        assert theme is not None
    
    def test_get_classic_theme(self):
        """Test classic theme generation."""
        theme = KimiTheme.get_theme("classic")
        assert theme is not None
    
    def test_get_auto_theme(self):
        """Test auto theme generation."""
        theme = KimiTheme.get_theme("auto")
        assert theme is not None


class TestKimiUI:
    """Test KimiUI class."""
    
    def test_init(self, mock_config):
        """Test UI initialization."""
        ui = KimiUI(mock_config)
        assert ui.config == mock_config
        assert ui.console is not None
    
    def test_format_number_small(self, mock_config):
        """Test formatting small numbers."""
        ui = KimiUI(mock_config)
        assert ui._format_number(999) == "999"
    
    def test_format_number_thousands(self, mock_config):
        """Test formatting thousands."""
        ui = KimiUI(mock_config)
        assert ui._format_number(1500) == "1.5K"
        assert ui._format_number(10000) == "10.0K"
    
    def test_format_number_millions(self, mock_config):
        """Test formatting millions."""
        ui = KimiUI(mock_config)
        assert ui._format_number(1500000) == "1.50M"
        assert ui._format_number(5000000) == "5.00M"
    
    def test_format_cost_small(self, mock_config):
        """Test formatting small costs."""
        ui = KimiUI(mock_config)
        assert ui._format_cost(0.5) == "$0.5000"
    
    def test_format_cost_medium(self, mock_config):
        """Test formatting medium costs."""
        ui = KimiUI(mock_config)
        assert ui._format_cost(5.5) == "$5.500"
    
    def test_format_cost_large(self, mock_config):
        """Test formatting large costs."""
        ui = KimiUI(mock_config)
        assert ui._format_cost(150.0) == "$150.00"
    
    def test_get_status_color_healthy(self, mock_config):
        """Test healthy status color."""
        ui = KimiUI(mock_config)
        usage = UsageData(total_quota=1000, used_quota=100)  # 10% used
        assert ui._get_status_color(usage) == "success"
    
    def test_get_status_color_warning(self, mock_config):
        """Test warning status color."""
        ui = KimiUI(mock_config)
        usage = UsageData(total_quota=1000, used_quota=800)  # 80% used
        assert ui._get_status_color(usage) == "warning"
    
    def test_get_status_color_critical(self, mock_config):
        """Test critical status color."""
        ui = KimiUI(mock_config)
        usage = UsageData(total_quota=1000, used_quota=950)  # 95% used
        assert ui._get_status_color(usage) == "danger"


class TestKimiUIComponents:
    """Test UI component generation."""
    
    def test_create_progress_bar(self, mock_config, mock_usage_data):
        """Test progress bar creation."""
        ui = KimiUI(mock_config)
        progress = ui.create_progress_bar(mock_usage_data)
        
        assert isinstance(progress, Progress)
    
    def test_create_progress_bar_empty_data(self, mock_config):
        """Test progress bar with empty data."""
        ui = KimiUI(mock_config)
        usage = UsageData(total_quota=0, used_quota=0)
        progress = ui.create_progress_bar(usage)
        
        assert isinstance(progress, Progress)
    
    def test_create_usage_table(self, mock_config, mock_usage_data):
        """Test usage table creation."""
        ui = KimiUI(mock_config)
        table = ui.create_usage_table(mock_usage_data)
        
        assert isinstance(table, Table)
    
    def test_create_usage_table_empty(self, mock_config):
        """Test usage table with empty data."""
        ui = KimiUI(mock_config)
        usage = UsageData(total_quota=0, used_quota=0)
        table = ui.create_usage_table(usage)
        
        assert isinstance(table, Table)
    
    def test_create_usage_table_no_cost(self, mock_config, mock_usage_data):
        """Test usage table when cost is hidden."""
        config = Config(**{**mock_config.model_dump(), "show_cost": False})
        ui = KimiUI(config)
        table = ui.create_usage_table(mock_usage_data)
        
        assert isinstance(table, Table)
    
    def test_create_plan_info(self, mock_config, mock_usage_data):
        """Test plan info panel creation."""
        ui = KimiUI(mock_config)
        panel = ui.create_plan_info(mock_usage_data)
        
        assert isinstance(panel, Panel)
    
    def test_create_plan_info_no_expiry(self, mock_config):
        """Test plan info without expiry date."""
        ui = KimiUI(mock_config)
        usage = UsageData(plan="free", expires_at=None)
        panel = ui.create_plan_info(usage)
        
        assert isinstance(panel, Panel)
    
    def test_create_daily_table(self, mock_config, mock_daily_usage):
        """Test daily usage table creation."""
        ui = KimiUI(mock_config)
        table = ui.create_daily_table(mock_daily_usage)
        
        assert isinstance(table, Table)
    
    def test_create_daily_table_empty(self, mock_config):
        """Test daily usage table with empty data."""
        ui = KimiUI(mock_config)
        table = ui.create_daily_table([])
        
        assert isinstance(table, Table)


class TestKimiUIMessages:
    """Test UI message methods."""
    
    def test_print_error(self, mock_config, capsys):
        """Test error message printing."""
        ui = KimiUI(mock_config)
        ui.print_error("Test error message")
        
        captured = capsys.readouterr()
        assert "Error" in captured.out or "error" in captured.out.lower()
    
    def test_print_warning(self, mock_config, capsys):
        """Test warning message printing."""
        ui = KimiUI(mock_config)
        ui.print_warning("Test warning message")
        
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "warning" in captured.out.lower()
    
    def test_print_success(self, mock_config, capsys):
        """Test success message printing."""
        ui = KimiUI(mock_config)
        ui.print_success("Test success message")
        
        captured = capsys.readouterr()
        assert "✅" in captured.out or "success" in captured.out.lower()
    
    def test_print_info(self, mock_config, capsys):
        """Test info message printing."""
        ui = KimiUI(mock_config)
        ui.print_info("Test info message")
        
        captured = capsys.readouterr()
        assert "ℹ️" in captured.out or "info" in captured.out.lower()


class TestKimiUILive:
    """Test UI live display."""
    
    def test_start_live(self, mock_config, mock_usage_data):
        """Test starting live display."""
        ui = KimiUI(mock_config)
        layout = ui.create_main_layout(mock_usage_data)
        
        # Should not raise
        ui.start_live(layout)
        ui.stop_live()
    
    def test_stop_live_without_start(self, mock_config):
        """Test stopping live without starting."""
        ui = KimiUI(mock_config)
        # Should not raise
        ui.stop_live()
    
    def test_update_live(self, mock_config, mock_usage_data):
        """Test updating live display."""
        ui = KimiUI(mock_config)
        layout1 = ui.create_main_layout(mock_usage_data)
        
        ui.start_live(layout1)
        layout2 = ui.create_main_layout(mock_usage_data)
        ui.update_live(layout2)
        ui.stop_live()
    
    def test_update_live_without_start(self, mock_config, mock_usage_data):
        """Test update without starting live."""
        ui = KimiUI(mock_config)
        layout = ui.create_main_layout(mock_usage_data)
        
        # Should not raise
        ui.update_live(layout)


class TestKimiUIMainLayout:
    """Test main layout creation."""
    
    def test_create_main_layout(self, mock_config, mock_usage_data, mock_daily_usage):
        """Test main layout creation."""
        ui = KimiUI(mock_config)
        layout = ui.create_main_layout(mock_usage_data, mock_daily_usage)
        
        assert layout is not None
        assert "header" in layout
        assert "main" in layout
        assert "footer" in layout
    
    def test_create_main_layout_no_daily(self, mock_config, mock_usage_data):
        """Test main layout without daily data."""
        ui = KimiUI(mock_config)
        layout = ui.create_main_layout(mock_usage_data, None)
        
        assert layout is not None
