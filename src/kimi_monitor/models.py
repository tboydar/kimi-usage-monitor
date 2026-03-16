"""Data models for Kimi Usage Monitor."""

from datetime import datetime, timedelta
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class UsageData(BaseModel):
    """Kimi API usage data model."""
    
    total_quota: int = Field(default=0, description="Total token quota")
    used_quota: int = Field(default=0, description="Used tokens")
    remaining_quota: int = Field(default=0, description="Remaining tokens")
    
    # Time-based usage
    daily_usage: int = Field(default=0, description="Today's token usage")
    weekly_usage: int = Field(default=0, description="This week's token usage")
    monthly_usage: int = Field(default=0, description="This month's token usage")
    
    # Session info
    session_count: int = Field(default=0, description="Number of active sessions")
    last_session_time: Optional[datetime] = Field(default=None, description="Last session timestamp")
    
    # Plan info
    plan: str = Field(default="unknown", description="Current plan name")
    expires_at: Optional[datetime] = Field(default=None, description="Plan expiration date")
    reset_period: str = Field(default="daily", description="Quota reset period")
    
    # Cost info
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    
    @property
    def usage_percentage(self) -> float:
        """Calculate usage percentage."""
        if self.total_quota <= 0:
            return 0.0
        return (self.used_quota / self.total_quota) * 100
    
    @property
    def remaining_percentage(self) -> float:
        """Calculate remaining percentage."""
        return 100.0 - self.usage_percentage
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until plan expiry."""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.now(self.expires_at.tzinfo)
        return max(0, delta.days)
    
    @property
    def status(self) -> Literal["healthy", "warning", "critical"]:
        """Determine usage status."""
        remaining = self.remaining_percentage
        if remaining < 10:
            return "critical"
        elif remaining < 30:
            return "warning"
        return "healthy"


class Config(BaseModel):
    """Monitor configuration."""
    
    # API settings
    api_key: Optional[str] = Field(default=None, description="Kimi API key")
    base_url: str = Field(default="https://api.moonshot.cn/v1", description="API base URL")
    
    # Display settings
    refresh_rate: int = Field(default=10, ge=1, le=60, description="Data refresh rate in seconds")
    refresh_per_second: float = Field(default=0.75, ge=0.1, le=20.0, description="Display refresh rate in Hz")
    theme: Literal["auto", "light", "dark", "classic"] = Field(default="auto", description="UI theme")
    timezone: str = Field(default="auto", description="Timezone for display")
    time_format: Literal["12h", "24h", "auto"] = Field(default="auto", description="Time format")
    
    # Plan settings
    plan: Literal["free", "pro", "max5", "max20", "custom"] = Field(default="pro", description="Plan type")
    custom_limit: Optional[int] = Field(default=None, description="Custom token limit")
    
    # Feature settings
    show_cost: bool = Field(default=True, description="Show cost estimates")
    show_predictions: bool = Field(default=True, description="Show usage predictions")
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_file: Optional[str] = Field(default=None)
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key format."""
        if v and not v.startswith("sk-"):
            raise ValueError("API key must start with 'sk-'")
        return v


class SessionData(BaseModel):
    """Session data model."""
    
    session_id: str
    start_time: datetime
    token_usage: int = 0
    message_count: int = 0
    model: str = "kimi-k2.5"
    
    @property
    def duration(self) -> timedelta:
        """Calculate session duration."""
        return datetime.now(self.start_time.tzinfo) - self.start_time
    
    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes."""
        return self.duration.total_seconds() / 60


class DailyUsage(BaseModel):
    """Daily usage aggregation."""
    
    date: datetime
    total_tokens: int
    input_tokens: int
    output_tokens: int
    request_count: int
    cost: float
    
    
class MonthlyUsage(BaseModel):
    """Monthly usage aggregation."""
    
    month: datetime
    total_tokens: int
    request_count: int
    cost: float
    daily_average: float
