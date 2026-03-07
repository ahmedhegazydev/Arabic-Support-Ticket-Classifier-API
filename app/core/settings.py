from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):

    MODEL_NAME: str = "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"

    CONFIDENCE_THRESHOLD: float = 0.45

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

    CACHE_SIZE: int = 256

    class Config:
        env_file = ".env"


settings = Settings()