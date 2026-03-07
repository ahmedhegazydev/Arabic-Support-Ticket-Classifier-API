import os

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"
)

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))

CATEGORIES = [
    "مشكلة تسجيل دخول",
    "مشكلة دفع أو فاتورة",
    "مشكلة في الحساب",
    "مشكلة تقنية بالنظام",
    "طلب دعم",
    "استفسار عام",
    "شكوى",
    "اقتراح",
]

HIGH_PRIORITY_KEYWORDS = [
    "عاجل",
    "متوقف",
    "مش شغال",
    "لا استطيع الدخول",
    "لا أستطيع الدخول",
    "down",
    "urgent",
    "cannot login",
    "ما اقدر ادخل",
    "ما أقدر أدخل",
]

MEDIUM_PRIORITY_KEYWORDS = [
    "بطئ",
    "بطيء",
    "مشكلة",
    "error",
    "خطأ",
    "تأخير",
    "لا يعمل بشكل جيد",
]