🧠 نظرة عامة سريعة عن التطبيق
هذا المشروع هو API بلغة Python (FastAPI) لـ تصنيف تذاكر الدعم الفني باللغة العربية (Support Ticket Classification)، مع إضافة أولوية و تحديد ما إذا كان يحتاج مراجعة بشرية.

🔌 الواجهات (Endpoints)
✅ 1) /classify (POST)
يستقبل جسم JSON يحتوي على:
text (النص/التذكرة)
يرجع JSON فيه:
request_id (معرّف فريد للطلب)
category (التصنيف المتوقع)
category_confidence (ثقة النموذج)
priority (أولوية: High/Medium/Low بناءً على كلمات مفتاحية)
latency_ms (زمن الاستجابة)
needs_human_review (مؤشر إن كانت النتيجة تحتاج مراجعة بشرية)
✅ 2) /health (GET)
يفعل فحص الصحة البسيط ويرجع:
{"status": "ok"}
✅ 3) /metrics (GET)
يعرّض مقاييس Prometheus التي تُسجل داخل التطبيق (مثل عدد الطلبات، وقت الاستجابة، عدد الفشل، عدد الـ cache miss…).
🧠 كيف يعمل التصنيف؟

1. النموذج
   يستخدم مكتبة Hugging Face Transformers
   نموذج افتراضي: MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli
   يقوم بتصنيف النص ضمن مجموعة تصنيفات عربية ثابتة في الإعدادات
2. الكاش
   يستخدم @lru_cache لحفظ نتائج التصنيف بناءً على النص المطبّع (normalized)
   يقلل استخدام النموذج على الطلبات المتكررة
3. أولوية الرسالة (Priority)
   يتم تحديد أولوية الرسالة (High/Medium/Low) باستخدام قائمة كلمات مفتاحية (keywords) موجودة في الإعدادات.
4. مراجعة بشرية
   إذا كانت ثقة النموذج (category_confidence) أقل من العتبة (CONFIDENCE_THRESHOLD)، يُعلَن أن الرسالة “تحتاج مراجعة بشرية”.
   🧩 ملفات ومكونات أساسية
   main.py → تهيئة FastAPI وربط المسارات
   routes.py → تعريف المسارات (endpoints)
   inference_service.py → منطق التنفيذ (تصنيف، تسجيل مقاييس، سجل أحداث)
   loader.py → تحميل نموذج Transformers مرة واحدة
   settings.py → الإعدادات (نموذج، تصنيفات، كلمات أولوية، ثوابت)
   requirements.txt → الاعتمادات (FastAPI، Transformers، Torch، Prometheus، ...)
   🔍 بإيجاز
   التطبيق هو API خفيف يقوم بـ:

استقبال نص تذكرة دعم
تصنيفها لـ فئات عربية محددة
حساب أولوية بناءً على كلمات مفتاحية
تقدير الحاجة لمراجعة بشرية
تسجيل مقاييس الأداء (Prometheus)
إذا تحب، أقدر أشرح لك خطوة بخطوة كيفية تجربة الـ API محلياً أو إضافة فئات جديدة / تحسين

https://chatgpt.com/c/69b4a606-57f0-832b-ad85-79e7bcd16b48
