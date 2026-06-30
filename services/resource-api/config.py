'''
This file is our configuration file that sets up all variables that will be used by the API
'''

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

    jwt_secret: str
    database_url: str
    verification_svc_url: str
    oidc_url: str
    cors_origins: str = "http://localhost:5173"


    '''
    This function just makes sure that the postgres url is set up to be async. In production instead of updating the url, I might add a validation instead since variables should be set through deployments.

    The reason it's a property is so then it makes the function callable as an attribute instead of a method. This makes it so that anything called from settings doesn't need parantheses, and also this adds lazy evaluation so then this conversion only happens when it's accessed and not when the Settings object is created
    '''
    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


settings = Settings()
