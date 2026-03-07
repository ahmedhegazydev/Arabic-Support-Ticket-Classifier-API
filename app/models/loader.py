import time
from transformers import pipeline
from app.core.config import MODEL_NAME
from app.core.logging_config import logger


class ModelLoader:

    def __init__(self):
        self.classifier = None

    def load_classifier(self):
        if self.classifier is None:

            logger.info(
                "event=model_loading model=%s",
                MODEL_NAME
            )

            start = time.time()

            self.classifier = pipeline(
                "zero-shot-classification",
                model=MODEL_NAME
            )

            load_time = int((time.time() - start) * 1000)

            logger.info(
                "event=model_loaded model=%s load_time_ms=%s",
                MODEL_NAME,
                load_time
            )

        return self.classifier


model_loader = ModelLoader()