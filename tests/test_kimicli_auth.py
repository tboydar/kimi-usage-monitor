"""Tests for kimicli_auth module."""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from kimi_monitor.kimicli_auth import KimiCLIAuth


class TestKimiCLIAuthDetection:
    """Test kimi-cli detection."""
    
    def test_is_installed_true(self, tmp_path, monkeypatch):
        """Test detection when kimi-cli is installed."""
        kimi_dir = tmp_path / ".kimi"
        kimi_dir.mkdir()
        
        with patch.object(KimiCLIAuth, 'KIMI_CONFIG_DIR', kimi_dir):
            assert KimiCLIAuth.is_installed() is True
    
    def test_is_installed_false(self, tmp_path, monkeypatch):
        """Test detection when kimi-cli is not installed."""
        non_existent = tmp_path / ".nonexistent"
        
        with patch.object(KimiCLIAuth, 'KIMI_CONFIG_DIR', non_existent):
            assert KimiCLIAuth.is_installed() is False


class TestKimiCLIAuthToken:
    """Test OAuth token retrieval."""
    
    def test_get_oauth_token_success(self, tmp_path):
        """Test successful token retrieval."""
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        cred_file = cred_dir / "kimi-code.json"
        cred_file.write_text(json.dumps({
            "access_token": "eyJtest_access_token",
            "refresh_token": "test_refresh_token"
        }))
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            token = KimiCLIAuth._get_oauth_token()
            assert token == "eyJtest_access_token"
    
    def test_get_oauth_token_not_found(self, tmp_path):
        """Test token retrieval when file doesn't exist."""
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            token = KimiCLIAuth._get_oauth_token()
            assert token is None
    
    def test_get_oauth_token_invalid_json(self, tmp_path):
        """Test token retrieval with invalid JSON."""
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        cred_file = cred_dir / "kimi-code.json"
        cred_file.write_text("invalid json")
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            token = KimiCLIAuth._get_oauth_token()
            assert token is None
    
    def test_get_oauth_token_other_files(self, tmp_path):
        """Test token retrieval from other credential files."""
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        # Create a different credential file
        cred_file = cred_dir / "other-provider.json"
        cred_file.write_text(json.dumps({
            "access_token": "other_token",
        }))
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            token = KimiCLIAuth._get_oauth_token()
            assert token == "other_token"


class TestKimiCLIAuthGetAPIKey:
    """Test API key retrieval."""
    
    def test_get_api_key_from_env(self, monkeypatch):
        """Test getting API key from environment."""
        monkeypatch.setenv("KIMI_API_KEY", "sk-env-api-key")
        
        api_key = KimiCLIAuth.get_api_key()
        assert api_key == "sk-env-api-key"
    
    def test_get_api_key_from_moonshot_env(self, monkeypatch):
        """Test getting API key from MOONSHOT_API_KEY."""
        monkeypatch.setenv("MOONSHOT_API_KEY", "sk-moonshot-key")
        
        api_key = KimiCLIAuth.get_api_key()
        assert api_key == "sk-moonshot-key"
    
    def test_get_api_key_from_kimicli(self, tmp_path, monkeypatch):
        """Test getting API key from kimi-cli."""
        # Clear environment
        monkeypatch.delenv("KIMI_API_KEY", raising=False)
        monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
        
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        cred_file = cred_dir / "kimi-code.json"
        cred_file.write_text(json.dumps({
            "access_token": "eyJkimicli_token",
        }))
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            api_key = KimiCLIAuth.get_api_key()
            assert api_key == "eyJkimicli_token"
    
    def test_get_api_key_priority_env_over_kimicli(self, tmp_path, monkeypatch):
        """Test that env var takes priority over kimi-cli."""
        monkeypatch.setenv("KIMI_API_KEY", "sk-env-priority")
        
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        cred_file = cred_dir / "kimi-code.json"
        cred_file.write_text(json.dumps({
            "access_token": "kimicli_token",
        }))
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            api_key = KimiCLIAuth.get_api_key()
            assert api_key == "sk-env-priority"
    
    def test_get_api_key_no_auth(self, tmp_path, monkeypatch):
        """Test when no authentication is available."""
        monkeypatch.delenv("KIMI_API_KEY", raising=False)
        monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
        
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            api_key = KimiCLIAuth.get_api_key()
            assert api_key is None


class TestKimiCLIAuthIsAuthenticated:
    """Test authentication status."""
    
    def test_is_authenticated_true(self, tmp_path):
        """Test when authenticated."""
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        cred_file = cred_dir / "kimi-code.json"
        cred_file.write_text(json.dumps({
            "access_token": "valid_token",
        }))
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            assert KimiCLIAuth.is_authenticated() is True
    
    def test_is_authenticated_false(self, tmp_path):
        """Test when not authenticated."""
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir()
        
        with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
            assert KimiCLIAuth.is_authenticated() is False


class TestKimiCLIAuthGetConfig:
    """Test configuration retrieval."""
    
    def test_get_config_basic(self, tmp_path):
        """Test basic config retrieval."""
        kimi_dir = tmp_path / ".kimi"
        kimi_dir.mkdir()
        
        config_file = kimi_dir / "config.toml"
        config_file.write_text('''
default_model = "kimi-code/kimi-for-coding"
default_thinking = true

[providers."managed:kimi-code"]
type = "kimi"
base_url = "https://api.kimi.com/coding/v1"
''')
        
        with patch.object(KimiCLIAuth, 'KIMI_CONFIG_DIR', kimi_dir):
            config = KimiCLIAuth.get_config()
            
            assert config["installed"] is True
            assert config["config_dir"] == str(kimi_dir)
            assert config["default_model"] == "kimi-code/kimi-for-coding"
            assert config["base_url"] == "https://api.kimi.com/coding/v1"
    
    def test_get_config_no_file(self, tmp_path):
        """Test config when file doesn't exist."""
        kimi_dir = tmp_path / ".kimi"
        kimi_dir.mkdir()
        
        with patch.object(KimiCLIAuth, 'KIMI_CONFIG_DIR', kimi_dir):
            config = KimiCLIAuth.get_config()
            
            assert config["installed"] is True
            assert "default_model" not in config


class TestKimiCLIAuthPrintStatus:
    """Test status printing."""
    
    def test_print_status_installed_authenticated(self, tmp_path, capsys):
        """Test printing status when installed and authenticated."""
        kimi_dir = tmp_path / ".kimi"
        kimi_dir.mkdir()
        cred_dir = kimi_dir / "credentials"
        cred_dir.mkdir()
        
        cred_file = cred_dir / "kimi-code.json"
        cred_file.write_text(json.dumps({
            "access_token": "eyJvalid_token",
        }))
        
        with patch.object(KimiCLIAuth, 'KIMI_CONFIG_DIR', kimi_dir):
            with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
                KimiCLIAuth.print_status()
        
        captured = capsys.readouterr()
        assert "installed" in captured.out or "已安裝" in captured.out
        assert "Authenticated" in captured.out or "已認證" in captured.out
    
    def test_print_status_not_installed(self, tmp_path, capsys):
        """Test printing status when not installed."""
        non_existent = tmp_path / ".nonexistent"
        
        with patch.object(KimiCLIAuth, 'KIMI_CONFIG_DIR', non_existent):
            KimiCLIAuth.print_status()
        
        captured = capsys.readouterr()
        assert "not installed" in captured.out or "未安裝" in captured.out
    
    def test_print_status_not_authenticated(self, tmp_path, capsys):
        """Test printing status when installed but not authenticated."""
        kimi_dir = tmp_path / ".kimi"
        kimi_dir.mkdir()
        cred_dir = kimi_dir / "credentials"
        cred_dir.mkdir()
        
        with patch.object(KimiCLIAuth, 'KIMI_CONFIG_DIR', kimi_dir):
            with patch.object(KimiCLIAuth, 'CREDENTIALS_DIR', cred_dir):
                KimiCLIAuth.print_status()
        
        captured = capsys.readouterr()
        assert "Not authenticated" in captured.out or "未認證" in captured.out
