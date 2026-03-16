"""Tests for models module."""

import pytest
from datetime import datetime, timezone

from kimi_monitor.models import UsageData, Config, DailyUsage


class TestUsageData:
    """Test UsageData model."""
    
    def test_usage_percentage(self):
        """Test usage percentage calculation."""
        usage = UsageData(total_quota=1000, used_quota=250)
        assert usage.usage_percentage == 25.0
        assert usage.remaining_percentage == 75.0
    
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
        usage = UsageData(total_quota=1000, used_quota=800)  # 80% used
        assert usage.status == "warning"
    
    def test_status_critical(self):
        """Test critical status."""
        usage = UsageData(total_quota=1000, used_quota=950)  # 95% used
        assert usage.status == "critical"
    
    def test_days_until_expiry(self):
        """Test days until expiry calculation."""
        future = datetime.now(timezone.utc) + timedelta(days=30)
        usage = UsageData(expires_at=future)
        assert usage.days_until_expiry == 30


class TestConfig:
    """Test Config model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.refresh_rate == 10
        assert config.theme == "auto"
        assert config.plan == "pro"
    
    def test_api_key_validation(self):
        """Test API key validation."""
        with pytest.raises(ValueError):
            Config(api_key="invalid-key")
        
        config = Config(api_key="sk-valid-key")
        assert config.api_key == "sk-valid-key"


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
        assert daily.cost == 0.5
