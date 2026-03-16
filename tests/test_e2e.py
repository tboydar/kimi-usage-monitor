"""End-to-end tests for kimi-monitor.

These tests simulate real user workflows.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import json

from kimi_monitor.cli import main
from kimi_monitor import __version__


class TestCLIHelp:
    """Test CLI help commands."""
    
    def test_help_command(self):
        """Test help command displays correctly."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'kimi-monitor' in result.output
    
    def test_version_command(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(main, ['--version'])
        
        assert result.exit_code == 0
        assert __version__ in result.output


class TestCLICheckKimicli:
    """Test --check-kimicli command."""
    
    @patch('kimi_monitor.cli.KimiCLIAuth')
    def test_check_kimicli_installed(self, mock_auth_class):
        """Test check when kimi-cli is installed."""
        mock_auth = MagicMock()
        mock_auth.is_installed.return_value = True
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth
        
        runner = CliRunner()
        result = runner.invoke(main, ['--check-kimicli'])
        
        assert result.exit_code == 0
        mock_auth.print_status.assert_called_once()
    
    @patch('kimi_monitor.cli.KimiCLIAuth')
    def test_check_kimicli_not_installed(self, mock_auth_class):
        """Test check when kimi-cli is not installed."""
        mock_auth = MagicMock()
        mock_auth.is_installed.return_value = False
        mock_auth_class.return_value = mock_auth
        
        runner = CliRunner()
        result = runner.invoke(main, ['--check-kimicli'])
        
        assert result.exit_code == 0


class TestCLIOptions:
    """Test CLI option parsing."""
    
    @patch('kimi_monitor.cli.KimiMonitor')
    @patch.dict('os.environ', {'KIMI_API_KEY': 'sk-test'})
    def test_plan_option(self, mock_monitor_class):
        """Test --plan option."""
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(main, ['--once', '--plan', 'max5'])
        
        assert result.exit_code == 0
        # Config should have plan=max5
        call_args = mock_monitor_class.call_args
        assert call_args[0][0].plan == "max5"
    
    @patch('kimi_monitor.cli.KimiMonitor')
    @patch.dict('os.environ', {'KIMI_API_KEY': 'sk-test'})
    def test_theme_option(self, mock_monitor_class):
        """Test --theme option."""
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(main, ['--once', '--theme', 'dark'])
        
        assert result.exit_code == 0
        call_args = mock_monitor_class.call_args
        assert call_args[0][0].theme == "dark"
    
    @patch('kimi_monitor.cli.KimiMonitor')
    @patch.dict('os.environ', {'KIMI_API_KEY': 'sk-test'})
    def test_refresh_rate_option(self, mock_monitor_class):
        """Test --refresh-rate option."""
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(main, ['--once', '--refresh-rate', '5'])
        
        assert result.exit_code == 0
        call_args = mock_monitor_class.call_args
        assert call_args[0][0].refresh_rate == 5
    
    @patch('kimi_monitor.cli.KimiMonitor')
    @patch.dict('os.environ', {'KIMI_API_KEY': 'sk-test'})
    def test_provider_option(self, mock_monitor_class):
        """Test --provider option."""
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(main, ['--once', '--provider', 'kimicode'])
        
        assert result.exit_code == 0


class TestCLIClearConfig:
    """Test --clear command."""
    
    @patch('kimi_monitor.cli.clear_config')
    def test_clear_config(self, mock_clear):
        """Test clearing configuration."""
        runner = CliRunner()
        result = runner.invoke(main, ['--clear'])
        
        assert result.exit_code == 0
        assert 'Configuration cleared' in result.output or '已清除' in result.output
        mock_clear.assert_called_once()


class TestCLIRunOnce:
    """Test --once command."""
    
    @patch('kimi_monitor.cli.KimiMonitor')
    @patch.dict('os.environ', {'KIMI_API_KEY': 'sk-test'})
    def test_run_once_success(self, mock_monitor_class):
        """Test successful run once."""
        mock_usage = MagicMock()
        mock_usage.total_quota = 5_000_000
        mock_usage.used_quota = 1_000_000
        
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = mock_usage
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(main, ['--once'])
        
        assert result.exit_code == 0
        mock_monitor.run_once.assert_called_once()
        mock_monitor.print_summary.assert_called_once()
    
    @patch('kimi_monitor.cli.KimiMonitor')
    def test_run_once_no_api_key(self, mock_monitor_class):
        """Test run once without API key."""
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = None
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['--once'])
        
        # Should fail with exit code 1
        assert result.exit_code == 1


class TestE2EWorkflow:
    """Test complete user workflows."""
    
    @patch('kimi_monitor.cli.KimiMonitor')
    @patch('kimi_monitor.cli.KimiCLIAuth')
    def test_full_workflow_with_kimicli(self, mock_auth_class, mock_monitor_class):
        """Test full workflow using kimi-cli authentication."""
        # Setup mocks
        mock_auth = MagicMock()
        mock_auth.is_installed.return_value = True
        mock_auth.is_authenticated.return_value = True
        mock_auth.get_api_key.return_value = "oauth_token_from_kimicli"
        mock_auth_class.return_value = mock_auth
        
        mock_usage = MagicMock()
        mock_usage.total_quota = 5_000_000
        mock_usage.used_quota = 1_200_000
        mock_usage.remaining_quota = 3_800_000
        mock_usage.plan = "pro"
        mock_usage.status = "healthy"
        
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = mock_usage
        mock_monitor_class.return_value = mock_monitor
        
        # Run without KIMI_API_KEY (should use kimi-cli)
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['--once', '--theme', 'dark'])
        
        assert result.exit_code == 0
        # Verify that KimiMonitor was created with correct config
        assert mock_monitor_class.called
        call_args = mock_monitor_class.call_args[0][0]
        assert call_args.theme == "dark"
    
    @patch('kimi_monitor.cli.KimiMonitor')
    @patch('kimi_monitor.cli.KimiCLIAuth')
    @patch('kimi_monitor.cli.save_config')
    def test_config_persistence(self, mock_save, mock_auth_class, mock_monitor_class):
        """Test that configuration is saved correctly."""
        mock_auth = MagicMock()
        mock_auth.is_installed.return_value = False
        mock_auth_class.return_value = mock_auth
        
        mock_usage = MagicMock()
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = mock_usage
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            with patch.dict('os.environ', {'KIMI_API_KEY': 'sk-test'}):
                result = runner.invoke(main, [
                    '--once',
                    '--theme', 'dark',
                    '--refresh-rate', '5',
                    '--timezone', 'Asia/Taipei'
                ])
        
        assert result.exit_code == 0
        # Verify config was saved (without API key)
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        assert saved_config['theme'] == 'dark'
        assert saved_config['refresh_rate'] == 5
        assert saved_config['timezone'] == 'Asia/Taipei'
        assert 'api_key' not in saved_config


class TestE2EErrorHandling:
    """Test error handling in E2E scenarios."""
    
    @patch('kimi_monitor.cli.KimiMonitor')
    @patch.dict('os.environ', {'KIMI_API_KEY': 'sk-invalid'})
    def test_api_connection_failure(self, mock_monitor_class):
        """Test handling of API connection failure."""
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = None  # Simulate failure
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        result = runner.invoke(main, ['--once'])
        
        assert result.exit_code == 1
    
    @patch('kimi_monitor.cli.KimiMonitor')
    def test_keyboard_interrupt(self, mock_monitor_class):
        """Test handling of keyboard interrupt."""
        mock_monitor = MagicMock()
        mock_monitor.run.side_effect = KeyboardInterrupt()
        mock_monitor_class.return_value = mock_monitor
        
        runner = CliRunner()
        with patch.dict('os.environ', {'KIMI_API_KEY': 'sk-test'}):
            result = runner.invoke(main, [])
        
        # KeyboardInterrupt should be handled gracefully
        assert result.exit_code == 0 or result.exit_code == 130


class TestE2EIntegration:
    """Integration tests that test multiple components together."""
    
    def test_import_all_modules(self):
        """Test that all modules can be imported."""
        from kimi_monitor import KimiMonitor, KimiAPI, UsageData, Config, KimiCLIAuth
        
        # Just verify imports work
        assert KimiMonitor is not None
        assert KimiAPI is not None
        assert UsageData is not None
        assert Config is not None
        assert KimiCLIAuth is not None
    
    def test_model_creation(self):
        """Test creating model instances."""
        from kimi_monitor.models import UsageData, Config
        
        usage = UsageData(
            total_quota=1000,
            used_quota=500,
            plan="pro"
        )
        
        assert usage.total_quota == 1000
        assert usage.usage_percentage == 50.0
        
        config = Config(
            api_key="sk-test-key",
            theme="dark"
        )
        
        assert config.theme == "dark"
