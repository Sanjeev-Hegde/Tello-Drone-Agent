"""
Configuration settings for Tello Drone Agent.
"""

import os
import logging
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings with Azure integration."""
    
    # Azure AI Vision Configuration
    azure_ai_vision_endpoint: str = Field(..., env="AZURE_AI_VISION_ENDPOINT")
    azure_ai_vision_key: Optional[str] = Field(None, env="AZURE_AI_VISION_KEY")
    
    # Azure AI Projects Configuration
    azure_ai_project_endpoint: str = Field(..., env="AZURE_AI_PROJECT_ENDPOINT")
    azure_ai_project_api_key: Optional[str] = Field(None, env="AZURE_AI_PROJECT_API_KEY")
    drone_agent_id: Optional[str] = Field(None, env="DRONE_AGENT_ID")
    
    # Azure Key Vault Configuration (Optional but recommended)
    azure_key_vault_url: Optional[str] = Field(None, env="AZURE_KEY_VAULT_URL")
    
    # Application Settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    camera_source: str = Field("webcam", env="CAMERA_SOURCE")  # webcam or tello
    enable_audio_input: bool = Field(True, env="ENABLE_AUDIO_INPUT")
    vision_confidence_threshold: float = Field(0.5, env="VISION_CONFIDENCE_THRESHOLD")
    
    # Tello Drone Settings
    tello_ip: str = Field("192.168.10.1", env="TELLO_IP")
    tello_port: int = Field(8889, env="TELLO_PORT")
    tello_video_port: int = Field(11111, env="TELLO_VIDEO_PORT")
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        case_sensitive = False


class SecureConfigManager:
    """
    Secure configuration manager using Azure Key Vault.
    Follows Azure security best practices.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._key_vault_client = None
        self._credential = None
        
        # Only setup Key Vault if URL is provided and not a placeholder
        if (settings.azure_key_vault_url and 
            settings.azure_key_vault_url != "your_keyvault_url_here" and
            settings.azure_key_vault_url.startswith("https://")):
            self._setup_key_vault()
    
    def _setup_key_vault(self):
        """Setup Azure Key Vault client with proper authentication."""
        try:
            # Use DefaultAzureCredential for automatic credential detection
            # This supports Managed Identity, Azure CLI, and other auth methods
            self._credential = DefaultAzureCredential()
            self._key_vault_client = SecretClient(
                vault_url=self.settings.azure_key_vault_url,
                credential=self._credential
            )
            self.logger.info("Azure Key Vault client initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Key Vault: {e}")
            self.logger.info("Falling back to environment variables")
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Get secret from Key Vault with fallback to environment variable.
        
        Args:
            secret_name: Name of the secret in Key Vault
            fallback_env_var: Environment variable to use as fallback
            
        Returns:
            Secret value or None if not found
        """
        # Try Key Vault first
        if self._key_vault_client:
            try:
                secret = self._key_vault_client.get_secret(secret_name)
                self.logger.debug(f"Retrieved secret '{secret_name}' from Key Vault")
                return secret.value
            except Exception as e:
                self.logger.warning(f"Failed to retrieve secret '{secret_name}' from Key Vault: {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            value = os.getenv(fallback_env_var)
            if value:
                self.logger.debug(f"Retrieved secret '{secret_name}' from environment variable")
                return value
        
        self.logger.error(f"Secret '{secret_name}' not found in Key Vault or environment")
        return None
    
    def get_azure_openai_key(self) -> Optional[str]:
        """Get Azure OpenAI API key securely."""
        return self.get_secret("azure-openai-api-key", "AZURE_OPENAI_API_KEY")
    
    def get_ai_vision_key(self) -> Optional[str]:
        """Get Azure AI Vision key securely."""
        return self.get_secret("azure-ai-vision-key", "AZURE_AI_VISION_KEY")


def setup_logging(log_level: str = "INFO"):
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# Global settings instance
settings = Settings()
config_manager = SecureConfigManager(settings)

# Setup logging
setup_logging(settings.log_level)
