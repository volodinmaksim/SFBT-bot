from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


def _parse_int_list(raw_value: str | None) -> list[int]:
    if not raw_value:
        return []

    values: list[int] = []
    for chunk in raw_value.split(','):
        item = chunk.strip()
        if not item:
            continue
        values.append(int(item))
    return values


class Settings(BaseSettings):
    DB_URL: str
    BOT_TOKEN: SecretStr
    TEST_BOT_TOKEN: SecretStr | None = None
    TEST_MODE: bool = False
    TEST_DELAY_SECONDS: int = 5
    TEST_DAY_DELAY_SECONDS: int = 20
    REDIS_URL: str | None = None
    RABBITMQ_URL: str | None = None
    BASE_URL: str

    CHAT_ID_TO_CHECK_1: int
    CHAT_URL_1: str
    CHAT_ID_TO_CHECK_2: int
    CHAT_URL_2: str
    SECRET_TG_KEY: str
    RESOURCE_LINK: str
    START_MESSAGE_ID: int | None = None
    TEMPLATE_CHAT_ID: int | None = None
    AFTER_LINK_NO_MESSAGE_IDS: str = ''
    AFTER_LINK_YES_INITIAL_MESSAGE_IDS: str = ''
    AFTER_LINK_YES_DELAY_1_MESSAGE_ID: int | None = None
    AFTER_LINK_YES_DELAY_2_MESSAGE_ID: int | None = None
    AFTER_LINK_YES_DAY_1_MESSAGE_IDS: str = ''
    AFTER_LINK_YES_DAY_2_MESSAGE_IDS: str = ''
    AFTER_LINK_YES_DAY_3_MESSAGE_ID: int | None = None
    AFTER_LINK_YES_DAY_4_MESSAGE_ID: int | None = None
    AFTER_LINK_YES_FOLLOWUP_MESSAGE_ID: int | None = None
    AFTER_LINK_YES_DAY_5_MESSAGE_ID: int | None = None

    HOST: str
    PORT: int
    RABBITMQ_PREFETCH: int = 1
    RABBITMQ_MAX_RETRIES: int = 5
    RABBITMQ_RETRY_DELAY_MS: int = 30000

    # PROXY
    PROXY_IP_OR_DOMAIN: str
    PROXY_PORT: int
    PROXY_LOGIN: str
    PROXY_PASSWORD: SecretStr

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / 'sfbt.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @field_validator(
        'TEST_BOT_TOKEN',
        'START_MESSAGE_ID',
        'TEMPLATE_CHAT_ID',
        'AFTER_LINK_YES_DELAY_1_MESSAGE_ID',
        'AFTER_LINK_YES_DELAY_2_MESSAGE_ID',
        'AFTER_LINK_YES_DAY_3_MESSAGE_ID',
        'AFTER_LINK_YES_DAY_4_MESSAGE_ID',
        'AFTER_LINK_YES_FOLLOWUP_MESSAGE_ID',
        'AFTER_LINK_YES_DAY_5_MESSAGE_ID',
        mode='before',
    )
    @classmethod
    def empty_strings_to_none(cls, value):
        if value == '':
            return None
        return value

    @property
    def after_link_no_message_ids(self) -> list[int]:
        return _parse_int_list(self.AFTER_LINK_NO_MESSAGE_IDS)

    @property
    def after_link_yes_initial_message_ids(self) -> list[int]:
        return _parse_int_list(self.AFTER_LINK_YES_INITIAL_MESSAGE_IDS)

    @property
    def after_link_yes_day_1_message_ids(self) -> list[int]:
        return _parse_int_list(self.AFTER_LINK_YES_DAY_1_MESSAGE_IDS)

    @property
    def after_link_yes_day_2_message_ids(self) -> list[int]:
        return _parse_int_list(self.AFTER_LINK_YES_DAY_2_MESSAGE_IDS)

    @property
    def active_bot_token(self) -> SecretStr:
        if (
            self.TEST_MODE
            and self.TEST_BOT_TOKEN is not None
            and self.TEST_BOT_TOKEN.get_secret_value().strip()
        ):
            return self.TEST_BOT_TOKEN
        return self.BOT_TOKEN

    @property
    def after_link_delay_seconds(self) -> int:
        if self.TEST_MODE:
            return self.TEST_DELAY_SECONDS
        return 30

    @property
    def after_link_day_delay_seconds(self) -> int:
        if self.TEST_MODE:
            return self.TEST_DAY_DELAY_SECONDS
        return 24 * 60 * 60

    @property
    def after_link_follow_up_delay_seconds(self) -> int:
        if self.TEST_MODE:
            return self.TEST_DELAY_SECONDS
        return 10 * 60

    @property
    def checked_channels(self) -> list[tuple[int, str]]:
        return [
            (self.CHAT_ID_TO_CHECK_1, self.CHAT_URL_1),
            (self.CHAT_ID_TO_CHECK_2, self.CHAT_URL_2),
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
