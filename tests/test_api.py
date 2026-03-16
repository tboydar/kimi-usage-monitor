"""Tests for API module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import requests

from kimi_monitor.api import KimiAPI, KimiAPIError
from kimi_monitor.models import UsageData


class TestKimiAPI:
    """Test KimiAPI class."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        api = KimiAPI(api_key="sk-test-key")
        assert api.api_key == "sk-test-key"
        assert api.base_url == "https://api.moonshot.cn/v1"
        assert api.provider == "moonshot"
    
    def test_init_with_env_var(self, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("KIMI_API_KEY", "sk-env-key")
        api = KimiAPI()
        assert api.api_key == "sk-env-key"
    
    def test_init_with_moonshot_global_provider(self):
        """Test initialization with moonshot-global provider."""
        api = KimiAPI(api_key="sk-test", provider="moonshot-global")
        assert api.base_url == "https://api.moonshot.ai/v1"
    
    def test_init_with_kimicode_provider(self):
        """Test initialization with kimicode provider."""
        api = KimiAPI(api_key="sk-test", provider="kimicode")
        assert api.base_url == "https://api.kimi.com/coding/v1"
    
    def test_get_headers(self):
        """Test header generation."""
        api = KimiAPI(api_key="sk-test")
        headers = api._get_headers()
        assert headers["Authorization"] == "Bearer sk-test"
        assert headers["Content-Type"] == "application/json"


class TestKimiAPIRequests:
    """Test KimiAPI HTTP requests."""
    
    @patch('kimi_monitor.api.requests.Session')
    def test_test_connection_success(self, mock_session_class):
        """Test successful connection test."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        result = api.test_connection()
        
        assert result is True
        mock_session.request.assert_called_once()
    
    @patch('kimi_monitor.api.requests.Session')
    def test_test_connection_failure(self, mock_session_class):
        """Test failed connection test."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.raise_for_status.side_effect = requests.HTTPError("401")
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-invalid")
        result = api.test_connection()
        
        assert result is False
    
    @patch('kimi_monitor.api.requests.Session')
    def test_get_usage_success(self, mock_session_class, mock_api_response):
        """Test successful usage fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        usage = api.get_usage()
        
        assert isinstance(usage, UsageData)
        assert usage.total_quota == 5_000_000
        assert usage.used_quota == 1_200_000
    
    @patch('kimi_monitor.api.requests.Session')
    def test_get_usage_caching(self, mock_session_class, mock_api_response):
        """Test usage data caching."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        
        # First call
        usage1 = api.get_usage()
        # Second call (should use cache)
        usage2 = api.get_usage()
        
        # Should only make one request
        assert mock_session.request.call_count == 1
        assert usage1.total_quota == usage2.total_quota
    
    @patch('kimi_monitor.api.requests.Session')
    def test_get_usage_force_refresh(self, mock_session_class, mock_api_response):
        """Test force refresh bypasses cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        
        # First call
        api.get_usage()
        # Force refresh
        api.get_usage(force_refresh=True)
        
        # Should make two requests
        assert mock_session.request.call_count == 2
    
    @patch('kimi_monitor.api.requests.Session')
    def test_rate_limit_error(self, mock_session_class):
        """Test rate limit handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {}
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        
        with pytest.raises(KimiAPIError, match="Rate limited"):
            api._make_request("GET", "/test")
    
    @patch('kimi_monitor.api.requests.Session')
    def test_auth_error(self, mock_session_class):
        """Test authentication error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {}
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-invalid")
        
        with pytest.raises(KimiAPIError, match="Invalid API key"):
            api._make_request("GET", "/test")
    
    @patch('kimi_monitor.api.requests.Session')
    def test_timeout_error(self, mock_session_class):
        """Test timeout error handling."""
        mock_session = MagicMock()
        mock_session.request.side_effect = requests.exceptions.Timeout()
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        
        with pytest.raises(KimiAPIError, match="timeout"):
            api._make_request("GET", "/test")
    
    @patch('kimi_monitor.api.requests.Session')
    def test_connection_error(self, mock_session_class):
        """Test connection error handling."""
        mock_session = MagicMock()
        mock_session.request.side_effect = requests.exceptions.ConnectionError()
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        
        with pytest.raises(KimiAPIError, match="Connection error"):
            api._make_request("GET", "/test")


class TestKimiAPIModels:
    """Test API models endpoint."""
    
    @patch('kimi_monitor.api.requests.Session')
    def test_get_models_success(self, mock_session_class):
        """Test successful models fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "kimi-k2.5", "name": "Kimi K2.5"},
                {"id": "kimi-for-coding", "name": "Kimi For Coding"},
            ]
        }
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        models = api.get_models()
        
        assert len(models) == 2
        assert models[0]["id"] == "kimi-k2.5"
    
    @patch('kimi_monitor.api.requests.Session')
    def test_get_models_empty(self, mock_session_class):
        """Test empty models response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        models = api.get_models()
        
        assert models == []
    
    @patch('kimi_monitor.api.requests.Session')
    def test_get_models_error(self, mock_session_class):
        """Test models fetch error."""
        mock_session = MagicMock()
        mock_session.request.side_effect = KimiAPIError("API Error")
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        models = api.get_models()
        
        assert models == []


class TestKimiAPIBalance:
    """Test API balance endpoint."""
    
    @patch('kimi_monitor.api.requests.Session')
    def test_get_balance_success(self, mock_session_class):
        """Test successful balance fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": 100.0, "currency": "USD"}
        
        mock_session = MagicMock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        balance = api.get_balance()
        
        assert balance["balance"] == 100.0
    
    @patch('kimi_monitor.api.requests.Session')
    def test_get_balance_error(self, mock_session_class):
        """Test balance fetch error."""
        mock_session = MagicMock()
        mock_session.request.side_effect = KimiAPIError("API Error")
        mock_session_class.return_value = mock_session
        
        api = KimiAPI(api_key="sk-test")
        balance = api.get_balance()
        
        assert balance == {}
