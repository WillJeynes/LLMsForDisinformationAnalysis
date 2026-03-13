from pydantic import BaseModel
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
from fastapi import FastAPI

app = FastAPI()

MODEL_PATH = "./roberta_classifier"

tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)

class EvalRequest(BaseModel):
    answer: str

@app.post("/evaluate")
def evaluate_rob(req: EvalRequest):
    inputs = tokenizer(
        req.answer,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    model.eval()

    with torch.no_grad():
        logits = model(**inputs).logits

    probs = torch.softmax(logits, dim=1)
    return {
        "probabilities": probs.cpu().numpy().tolist()
    }