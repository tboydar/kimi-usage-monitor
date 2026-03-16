"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from kimi_monitor.models import UsageData, Config, DailyUsage


@pytest.fixture
def mock_usage_data():
    """Create mock usage data."""
    return UsageData(
        total_quota=5_000_000,
        used_quota=1_200_000,
        remaining_quota=3_800_000,
        daily_usage=125_000,
        weekly_usage=890_000,
        monthly_usage=3_500_000,
        plan="pro",
        expires_at=datetime(2026, 4, 15, 23, 59, 59, tzinfo=timezone.utc),
        reset_period="daily",
        total_cost=12.50,
    )


@pytest.fixture
def mock_config():
    """Create mock config."""
    return Config(
        api_key="sk-test-api-key",
        base_url="https://api.moonshot.cn/v1",
        refresh_rate=10,
        theme="dark",
        plan="pro",
        show_cost=True,
    )


@pytest.fixture
def mock_daily_usage():
    """Create mock daily usage data."""
    return [
        DailyUsage(
            date=datetime(2026, 3, 10),
            total_tokens=100_000,
            input_tokens=40_000,
            output_tokens=60_000,
            request_count=50,
            cost=0.25,
        ),
        DailyUsage(
            date=datetime(2026, 3, 11),
            total_tokens=150_000,
            input_tokens=60_000,
            output_tokens=90_000,
            request_count=75,
            cost=0.375,
        ),
    ]


@pytest.fixture
def mock_api_response():
    """Create mock API response."""
    return {
        "data": {
            "total_quota": 5_000_000,
            "used_quota": 1_200_000,
            "remaining_quota": 3_800_000,
            "plan": "pro",
            "expires_at": "2026-04-15T23:59:59Z",
            "daily_usage": 125_000,
            "weekly_usage": 890_000,
            "monthly_usage": 3_500_000,
            "total_cost": 12.50,
        }
    }


@pytest.fixture
def mock_kimicli_credentials(tmp_path):
    """Create mock kimi-cli credentials directory."""
    kimi_dir = tmp_path / ".kimi"
    cred_dir = kimi_dir / "credentials"
    cred_dir.mkdir(parents=True)
    
    # Create mock credential file
    cred_file = cred_dir / "kimi-code.json"
    cred_file.write_text('{"access_token": "eyJtest_token", "refresh_token": "refresh"}')
    
    return kimi_dir


@pytest.fixture
def mock_requests_session():
    """Create mock requests session."""
    session = MagicMock()
    
    # Mock successful response
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": {
            "total_quota": 5_000_000,
            "used_quota": 1_200_000,
            "remaining_quota": 3_800_000,
            "plan": "pro",
        }
    }
    response.text = '{"data": {}}'
    response.headers = {}
    
    session.request.return_value = response
    return session
