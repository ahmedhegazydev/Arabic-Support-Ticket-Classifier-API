from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import pipeline
import time
import uuid

app = FastAPI(title="Arabic Ticket Classifier API", version="0.1.0")

classifier = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")