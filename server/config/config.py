"""
Configuration for Vertex AI Gemini Multimodal Live Proxy Server
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv, find_dotenv
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(find_dotenv())

PROJECT_ID = os.environ.get('PROJECT_ID', 'next-2025-ces')
LOCATION = os.environ.get('VERTEX_LOCATION', 'us-central1')
DEMO_TYPE = os.environ.get('DEMO_TYPE', 'retail')

USE_VERTEX = int(os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 0))
logger.info(f"Initialized API configuration with Vertex AI: {USE_VERTEX}")

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

def get_secret(secret_id: str) -> str:
    """Get secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    project_id = PROJECT_ID
    
    if not project_id:
        raise ConfigurationError("PROJECT_ID environment variable is not set")
    
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        raise


class ApiConfig:
    """API configuration handler."""
    
    def __init__(self):
        self.api_key: Optional[str] = None

    async def initialize(self):
        """Initialize API credentials."""
        if not USE_VERTEX:
            try:
                self.api_key = get_secret('GOOGLE_API_KEY')
            except Exception as e:
                logger.warning(f"Failed to get API key from Secret Manager: {e}")
                self.api_key = os.getenv('GOOGLE_API_KEY')
                if not self.api_key:
                    raise ConfigurationError("No API key available from Secret Manager or environment")

# Initialize API configuration
api_config = ApiConfig()

# Model configuration
if USE_VERTEX == 1:
    MODEL = os.getenv('MODEL_VERTEX_API', 'gemini-live-2.5-flash-native-audio')
    AGENT_MODEL = os.getenv('AGENT_MODEL_VERTEX_API', MODEL)
    VOICE = os.getenv('VOICE_VERTEX_API', 'Aoede')
    print(f"Use Vertex API with live model: {MODEL}, agent model: {AGENT_MODEL}, and voice {VOICE}")
else:
    MODEL = os.getenv('MODEL_DEV_API', 'gemini-3.1-flash-live-preview')
    AGENT_MODEL = os.getenv('AGENT_MODEL_DEV_API', MODEL)
    VOICE = os.getenv('VOICE_DEV_API', 'Puck')
    print(f"Use Dev API (AI Studio) with live model: {MODEL}, agent model: {AGENT_MODEL}, and voice {VOICE}")

# ADK Feature Flags
USE_INTERACTIONS_API = os.getenv('USE_INTERACTIONS_API', 'false').lower() == 'true'
ENABLE_CONTEXT_CACHING = os.getenv('ENABLE_CONTEXT_CACHING', 'true').lower() == 'true'
logger.info(f"ADK Features - Interactions API: {USE_INTERACTIONS_API}, Context Caching: {ENABLE_CONTEXT_CACHING}")

# Load system instructions
try:
    with open('config/system-instructions.txt', 'r') as f:
        SYSTEM_INSTRUCTIONS = f.read()
except Exception as e:
    logger.error(f"Failed to load system instructions: {e}")
    SYSTEM_INSTRUCTIONS = ""

logger.info(f"System instructions: {SYSTEM_INSTRUCTIONS}")
available_languages = {"de-DE":"German (Germany)",
    "en-AU": "English (Australia)",	
    "en-GB": "English (United Kingdom)",
    "en-IN": "English (India)",
    "es-US": "Spanish (United States)",
    "fr-FR": "French (France)",	
    "hi-IN": "Hindi (India)",
    "pt-BR": "Portuguese (Brazil)",
    "ar-XA": "Arabic (Generic)",	
    "es-ES": "Spanish (Spain)",	
    "fr-CA": "French (Canada)",
    "id-ID": "Indonesian (Indonesia)",	
    "it-IT": "Italian (Italy)",
    "ja-JP": "Japanese (Japan)",
    "tr-TR": "Turkish (Turkey)",
    "vi-VN": "Vietnamese (Vietnam)",
    "bn-IN": "Bengali (India)",
    "gu-IN": "Gujarati (India)",	
    "kn-IN": "Kannada (India)",
    "ml-IN": "Malayalam (India)",
    "mr-IN": "Marathi (India)",
    "ta-IN": "Tamil (India)",
    "te-IN": "Telugu (India)",
    "nl-NL": "Dutch (Netherlands)",
    "ko-KR": "Korean (South Korea)",
    "cmn-CN": "Mandarin Chinese (China)",	
    "pl-PL": "Polish (Poland)",
    "ru-RU": "Russian (Russia)",
    "th-TH": "Thai (Thailand)"	
    }

LANGUAGE_CODE = os.getenv('LANGUAGE', 'en-GB')

try:
    LANGUAGE = available_languages[LANGUAGE_CODE]
except:
    LANGUAGE_CODE = 'en-GB'
    LANGUAGE = available_languages[LANGUAGE_CODE]

# Gemini Configuration
CONFIG = {
    "generation_config": {
        "response_modalities": ["AUDIO"],#, "TEXT"],
        "speech_config": VOICE,
        "language":LANGUAGE,
        "language_code":LANGUAGE_CODE,
        'input_audio_transcription': {},
        'output_audio_transcription': {}
    },
    "system_instruction": SYSTEM_INSTRUCTIONS
} 

logger.info(f"Configuration: {CONFIG}")
print(f"Configuration: {CONFIG['generation_config']['response_modalities']}")
print(f"Language code: {LANGUAGE_CODE}, Language: {LANGUAGE}")
