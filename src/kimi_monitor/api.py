"""Kimi API client for fetching usage data."""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

import requests

from .models import UsageData, SessionData, DailyUsage, MonthlyUsage
from .kimicli_auth import KimiCLIAuth

logger = logging.getLogger(__name__)


class KimiAPIError(Exception):
    """Kimi API error."""
    pass


class KimiAPI:
    """Kimi API client."""
    
    # API endpoints
    MOONSHOT_BASE = "https://api.moonshot.cn/v1"
    MOONSHOT_GLOBAL = "https://api.moonshot.ai/v1"
    KIMICODE_BASE = "https://api.kimi.com/coding/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: str = "moonshot"
    ):
        """Initialize API client.
        
        初始化 API 客戶端。會自動檢測本機 kimi-cli 認證資訊。
        
        Args:
            api_key: API key (defaults to KIMI_API_KEY env var or kimi-cli auth)
            base_url: API base URL
            provider: Provider type (moonshot, moonshot-global, kimicode)
        """
        # 優先順序 / Priority:
        # 1. 傳入的 api_key / Passed api_key
        # 2. 環境變數 / Environment variable
        # 3. kimi-cli 認證 / kimi-cli authentication
        
        # 檢查是否有環境變數 / Check environment variables first
        env_api_key = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
        
        # 檢查 kimi-cli 認證 / Check kimi-cli auth
        kimicli_api_key = KimiCLIAuth.get_api_key()
        
        self.api_key = api_key or env_api_key or kimicli_api_key
        
        # 如果從 kimi-cli 取得認證，使用其設定 / If auth from kimi-cli, use its config
        if not api_key and not env_api_key and kimicli_api_key:
            logger.info("Using kimicode provider for kimi-cli authentication")
            provider = "kimicode"  # kimi-cli 使用 kimicode provider
        
        self.provider = provider
        
        if base_url:
            self.base_url = base_url
        elif provider == "moonshot-global":
            self.base_url = self.MOONSHOT_GLOBAL
        elif provider == "kimicode":
            self.base_url = self.KIMICODE_BASE
        else:
            self.base_url = self.MOONSHOT_BASE
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        # Cache for usage data
        self._cache: Dict[str, Any] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=10)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            **kwargs: Additional request arguments
            
        Returns:
            JSON response data
            
        Raises:
            KimiAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method,
                url,
                headers=self._get_headers(),
                timeout=30,
                **kwargs
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise KimiAPIError(f"Rate limited. Retry after {retry_after} seconds")
            
            # Check for auth errors
            if response.status_code == 401:
                raise KimiAPIError("Invalid API key. Please check your KIMI_API_KEY")
            
            response.raise_for_status()
            return response.json() if response.text else {}
            
        except requests.exceptions.Timeout:
            raise KimiAPIError("Request timeout. Please check your network connection")
        except requests.exceptions.ConnectionError:
            raise KimiAPIError("Connection error. Please check your network connection")
        except requests.exceptions.RequestException as e:
            raise KimiAPIError(f"Request failed: {e}")
    
    def get_usage(self, force_refresh: bool = False) -> UsageData:
        """Get current usage data.
        
        Args:
            force_refresh: Bypass cache
            
        Returns:
            Usage data
        """
        # Check cache
        if not force_refresh and self._cache_time:
            if datetime.now() - self._cache_time < self._cache_ttl:
                logger.debug("Using cached usage data")
                return self._cache.get("usage", UsageData())
        
        try:
            # Try to get usage from API
            # Moonshot API has a /users/me endpoint for usage info
            data = self._make_request("GET", "/users/me")
            
            usage_info = data.get("data", {})
            
            usage = UsageData(
                total_quota=usage_info.get("total_quota", 0),
                used_quota=usage_info.get("used_quota", 0),
                remaining_quota=usage_info.get("remaining_quota", 0),
                plan=usage_info.get("plan", "unknown"),
                daily_usage=usage_info.get("daily_usage", 0),
                weekly_usage=usage_info.get("weekly_usage", 0),
                monthly_usage=usage_info.get("monthly_usage", 0),
                total_cost=usage_info.get("total_cost", 0.0),
            )
            
            # Parse expiration date
            if expires_at := usage_info.get("expires_at"):
                try:
                    usage.expires_at = datetime.fromisoformat(
                        expires_at.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse expiration date: {expires_at}")
            
            # Update cache
            self._cache["usage"] = usage
            self._cache_time = datetime.now()
            
            return usage
            
        except KimiAPIError:
            # If API fails, try to get from response headers in recent requests
            # or return empty data
            logger.warning("Failed to fetch usage from API, returning default")
            return UsageData()
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance.
        
        Returns:
            Balance information
        """
        try:
            return self._make_request("GET", "/users/me/balance")
        except KimiAPIError as e:
            logger.error(f"Failed to get balance: {e}")
            return {}
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models.
        
        Returns:
            List of available models
        """
        try:
            data = self._make_request("GET", "/models")
            return data.get("data", [])
        except KimiAPIError as e:
            logger.error(f"Failed to get models: {e}")
            return []
    
    def get_daily_usage(self, days: int = 7) -> List[DailyUsage]:
        """Get daily usage history.
        
        Args:
            days: Number of days to fetch
            
        Returns:
            List of daily usage data
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            data = self._make_request(
                "GET",
                "/usage/daily",
                params={
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }
            )
            
            daily_data = []
            for item in data.get("data", []):
                daily_data.append(DailyUsage(
                    date=datetime.fromisoformat(item["date"]),
                    total_tokens=item.get("total_tokens", 0),
                    input_tokens=item.get("input_tokens", 0),
                    output_tokens=item.get("output_tokens", 0),
                    request_count=item.get("request_count", 0),
                    cost=item.get("cost", 0.0)
                ))
            
            return daily_data
            
        except KimiAPIError as e:
            logger.error(f"Failed to get daily usage: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test API connection.
        
        Returns:
            True if connection successful
        """
        if not self.api_key:
            return False
        
        try:
            self._make_request("GET", "/models")
            return True
        except KimiAPIError:
            return False
