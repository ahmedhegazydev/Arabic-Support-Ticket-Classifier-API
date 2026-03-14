from typing import List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/tickets_db"
    MODEL_VERSION: str = "v1.0.0"

    MODEL_NAME: str = "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"
    CONFIDENCE_THRESHOLD: float = 0.45
    CACHE_SIZE: int = 256

    CATEGORIES: List[str] = [
        "مشكلة تسجيل دخول",
        "مشكلة دفع أو فاتورة",
        "مشكلة في الحساب",
        "مشكلة تقنية بالنظام",
        "طلب دعم",
        "استفسار عام",
        "شكوى",
        "اقتراح",
    ]

    HIGH_PRIORITY_KEYWORDS: List[str] = [
        "عاجل",
        "متوقف",
        "مش شغال",
        "لا استطيع الدخول",
        "لا أستطيع الدخول",
        "down",
        "urgent",
        "cannot login",
    ]

    MEDIUM_PRIORITY_KEYWORDS: List[str] = [
        "بطئ",
        "بطيء",
        "مشكلة",
        "error",
        "خطأ",
        "تأخير",
    ]

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()