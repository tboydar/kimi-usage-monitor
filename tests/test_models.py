"""Tests for models module."""

import pytest
from datetime import datetime, timezone, timedelta

from kimi_monitor.models import UsageData, Config, DailyUsage, SessionData, MonthlyUsage


class TestUsageData:
    """Test UsageData model."""
    
    def test_usage_percentage(self, mock_usage_data):
        """Test usage percentage calculation."""
        assert mock_usage_data.usage_percentage == 24.0
        assert mock_usage_data.remaining_percentage == 76.0
    
    def test_usage_percentage_zero_quota(self):
        """Test usage percentage with zero quota."""
        usage = UsageData(total_quota=0, used_quota=0)
        assert usage.usage_percentage == 0.0
        assert usage.remaining_percentage == 100.0
    
    def test_status_healthy(self):
        """Test healthy status."""
        usage = UsageData(total_quota=1000, used_quota=100)  # 10% used
        assert usage.status == "healthy"
    
    def test_status_warning(self):
        """Test warning status."""
        usage = UsageData(total_quota=1000, used_quota=800)  # 80% used, 20% remaining
        assert usage.status == "warning"
    
    def test_status_critical(self):
        """Test critical status."""
        usage = UsageData(total_quota=1000, used_quota=950)  # 95% used, 5% remaining
        assert usage.status == "critical"
    
    def test_days_until_expiry(self):
        """Test days until expiry calculation."""
        future = datetime.now(timezone.utc) + timedelta(days=30)
        usage = UsageData(expires_at=future)
        assert usage.days_until_expiry == 30
    
    def test_days_until_expiry_none(self):
        """Test days until expiry when expires_at is None."""
        usage = UsageData(expires_at=None)
        assert usage.days_until_expiry is None


class TestConfig:
    """Test Config model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.refresh_rate == 10
        assert config.theme == "auto"
        assert config.plan == "pro"
        assert config.show_cost is True
    
    def test_api_key_validation_valid(self):
        """Test valid API key."""
        config = Config(api_key="sk-valid-key")
        assert config.api_key == "sk-valid-key"
    
    def test_api_key_validation_invalid(self):
        """Test invalid API key."""
        with pytest.raises(ValueError, match="API key must start with 'sk-'"):
            Config(api_key="invalid-key")
    
    def test_refresh_rate_validation(self):
        """Test refresh rate validation."""
        with pytest.raises(ValueError):
            Config(refresh_rate=0)  # Should be >= 1
        
        with pytest.raises(ValueError):
            Config(refresh_rate=100)  # Should be <= 60
    
    def test_custom_limit_optional(self):
        """Test custom limit is optional."""
        config = Config()
        assert config.custom_limit is None
        
        config_with_limit = Config(custom_limit=100000)
        assert config_with_limit.custom_limit == 100000


class TestDailyUsage:
    """Test DailyUsage model."""
    
    def test_daily_usage_creation(self):
        """Test creating daily usage."""
        now = datetime.now()
        daily = DailyUsage(
            date=now,
            total_tokens=1000,
            input_tokens=400,
            output_tokens=600,
            request_count=10,
            cost=0.5,
        )
        assert daily.total_tokens == 1000
        assert daily.input_tokens == 400
        assert daily.output_tokens == 600
        assert daily.request_count == 10
        assert daily.cost == 0.5


class TestSessionData:
    """Test SessionData model."""
    
    def test_session_duration(self):
        """Test session duration calculation."""
        start = datetime.now(timezone.utc) - timedelta(minutes=30)
        session = SessionData(
            session_id="test-session",
            start_time=start,
            token_usage=1000,
            message_count=10,
        )
        
        assert session.duration.total_seconds() >= 30 * 60
        assert session.duration_minutes >= 30


class TestMonthlyUsage:
    """Test MonthlyUsage model."""
    
    def test_monthly_usage(self):
        """Test monthly usage creation."""
        month = datetime(2026, 3, 1)
        monthly = MonthlyUsage(
            month=month,
            total_tokens=1_000_000,
            request_count=500,
            cost=5.0,
            daily_average=32_258,
        )
        assert monthly.total_tokens == 1_000_000
        assert monthly.daily_average == 32_258
