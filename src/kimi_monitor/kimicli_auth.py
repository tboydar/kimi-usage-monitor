"""Kimi CLI authentication detector.

自動檢測本機 kimi-cli 的認證資訊
Automatically detect local kimi-cli authentication
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class KimiCLIAuth:
    """Detect and use kimi-cli authentication."""
    
    # kimi-cli 配置路徑 / kimi-cli config paths
    KIMI_CONFIG_DIR = Path.home() / ".kimi"
    CREDENTIALS_DIR = KIMI_CONFIG_DIR / "credentials"
    
    @classmethod
    def is_installed(cls) -> bool:
        """Check if kimi-cli is installed.
        
        檢查是否已安裝 kimi-cli
        
        Returns:
            True if kimi-cli config directory exists
        """
        return cls.KIMI_CONFIG_DIR.exists()
    
    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if kimi-cli is authenticated.
        
        檢查是否已通過 kimi-cli 認證
        
        Returns:
            True if valid OAuth token exists
        """
        return cls._get_oauth_token() is not None
    
    @classmethod
    def _get_oauth_token(cls) -> Optional[str]:
        """Get OAuth token from kimi-cli credentials.
        
        從 kimi-cli 憑證取得 OAuth token
        
        Returns:
            Access token or None
        """
        # 檢查 kimicode 憑證 / Check kimicode credentials
        kimicode_cred = cls.CREDENTIALS_DIR / "kimi-code.json"
        
        if kimicode_cred.exists():
            try:
                with open(kimicode_cred, "r") as f:
                    data = json.load(f)
                    token = data.get("access_token")
                    if token:
                        logger.debug("Found kimi-code OAuth token")
                        return token
            except (json.JSONDecodeError, IOError) as e:
                logger.debug(f"Failed to read kimicode credentials: {e}")
        
        # 檢查其他可能的憑證檔案 / Check other credential files
        if cls.CREDENTIALS_DIR.exists():
            for cred_file in cls.CREDENTIALS_DIR.glob("*.json"):
                try:
                    with open(cred_file, "r") as f:
                        data = json.load(f)
                        token = data.get("access_token")
                        if token:
                            logger.debug(f"Found OAuth token in {cred_file.name}")
                            return token
                except (json.JSONDecodeError, IOError):
                    continue
        
        return None
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Get API key from kimi-cli.
        
        從 kimi-cli 取得 API key
        
        Returns:
            API key or None
        """
        # 優先從環境變數 / Priority: environment variable
        api_key = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
        if api_key:
            logger.debug("Using API key from environment variable")
            return api_key
        
        # 嘗試從 kimi-cli 取得 / Try to get from kimi-cli
        if not cls.is_installed():
            logger.debug("kimi-cli not installed")
            return None
        
        # 取得 OAuth token / Get OAuth token
        oauth_token = cls._get_oauth_token()
        if oauth_token:
            logger.info("Using kimi-cli authentication")
            return oauth_token
        
        logger.debug("No valid authentication found in kimi-cli")
        return None
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get kimi-cli configuration.
        
        取得 kimi-cli 設定
        
        Returns:
            Configuration dictionary
        """
        config = {
            "installed": cls.is_installed(),
            "authenticated": cls.is_authenticated(),
            "config_dir": str(cls.KIMI_CONFIG_DIR),
        }
        
        # 讀取 kimi-cli 設定檔 / Read kimi-cli config
        config_file = cls.KIMI_CONFIG_DIR / "config.toml"
        if config_file.exists():
            try:
                import tomllib
                with open(config_file, "rb") as f:
                    toml_config = tomllib.load(f)
                    config["default_model"] = toml_config.get("default_model", "unknown")
                    
                    # 取得 provider 資訊 / Get provider info
                    providers = toml_config.get("providers", {})
                    for provider_name, provider_config in providers.items():
                        if isinstance(provider_config, dict):
                            config["base_url"] = provider_config.get("base_url", "")
                            break
            except ImportError:
                # Python < 3.11
                try:
                    import tomli as tomllib
                    with open(config_file, "rb") as f:
                        toml_config = tomllib.load(f)
                        config["default_model"] = toml_config.get("default_model", "unknown")
                except ImportError:
                    logger.debug("tomli not installed, skipping TOML parsing")
            except Exception as e:
                logger.debug(f"Failed to parse config.toml: {e}")
        
        return config
    
    @classmethod
    def print_status(cls) -> None:
        """Print kimi-cli authentication status.
        
        印出 kimi-cli 認證狀態
        """
        print("🖥️  Kimi CLI Status / Kimi CLI 狀態")
        print("=" * 50)
        
        if not cls.is_installed():
            print("❌ kimi-cli not installed / 未安裝 kimi-cli")
            print("   Install from: https://www.kimi.com/code")
            return
        
        print(f"✅ kimi-cli installed / 已安裝")
        print(f"   Config directory: {cls.KIMI_CONFIG_DIR}")
        
        config = cls.get_config()
        if "default_model" in config:
            print(f"   Default model: {config['default_model']}")
        
        if cls.is_authenticated():
            print("✅ Authenticated / 已認證")
            token_preview = cls._get_oauth_token()
            if token_preview:
                print(f"   Token: {token_preview[:20]}...{token_preview[-4:]}")
        else:
            print("❌ Not authenticated / 未認證")
            print("   Run: kimi login")
        
        print("=" * 50)
