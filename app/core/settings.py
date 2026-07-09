from functools import lru_cache

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'SIG Microbuses API'
    app_version: str = '0.1.0'
    api_prefix: str = '/api/v1'
    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/sig_microbuses'
    jwt_secret_key: str = 'change-me'
    jwt_algorithm: str = 'HS256'
    jwt_access_token_minutes: int = 60
    cors_allow_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    cors_allow_origin_regex: str = r'https?://(localhost|127\.0\.0\.1)(:\d+)?'

    super_admin_email: str = 'admin@sig.local'
    super_admin_password: str = 'ChangeMe123!'
    super_admin_full_name: str = 'Super Admin SIG'
    walking_graph_path: str = 'data/walking/santa_cruz_walk.graphml'
    walking_default_speed_kmh: float = 4.5

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    @field_validator('database_url')
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith('postgresql://'):
            return value.replace('postgresql://', 'postgresql+psycopg://', 1)
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
