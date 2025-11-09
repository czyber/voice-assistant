import json
import os
from pathlib import Path

from core.logging_utils import get_logger

logger = get_logger(__name__)


def _find_project_root() -> Path:
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "config.local.json").exists() or (current / "config.json").exists():
            logger.debug("Resolved project root path=%s", current)
            return current
        current = current.parent
    return Path(__file__).parent.parent


class Config:
    def __init__(self, config_file: str | None = None) -> None:
        self.config_data = {}
        if config_file is None:
            project_root = _find_project_root()
            config_file = project_root / "config.local.json"
        else:
            config_file = Path(config_file)

        if config_file.exists():
            with open(config_file, "r") as f:
                self.config_data = json.load(f)
            logger.info(
                "Loaded config file path=%s has_openai=%s has_elevenlabs=%s",
                config_file,
                bool(self.openai_api_key),
                bool(self.elevenlabs_api_key),
            )
        else:
            logger.warning(
                "Config file missing; using empty defaults path=%s",
                config_file,
            )

    @property
    def openai_api_key(self) -> str:
        return self.config_data.get("openai", {}).get("api_key", "")

    @property
    def elevenlabs_api_key(self) -> str:
        return self.config_data.get("elevenlabs", {}).get("api_key", "")

    @property
    def openai_organization(self) -> str:
        return self.config_data.get("openai", {}).get("organization", "")


def get_config() -> Config:
    logger.debug("Creating Config instance")
    return Config()
