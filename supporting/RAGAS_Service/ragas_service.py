from fastapi import FastAPI
from pydantic import BaseModel
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset
from pathlib import Path
from dotenv import load_dotenv
import os
import math

app = FastAPI()

ENV_PATH = Path("../../agent/.env")

load_dotenv(dotenv_path=ENV_PATH)

def sanitize(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not found")

class EvalRequest(BaseModel):
    question: str
    answer: str
    contexts: list[str]

@app.post("/evaluate")
def evaluate_rag(req: EvalRequest):
    dataset = Dataset.from_dict({
        "question": [req.question],
        "answer": [req.answer],
        "contexts": [req.contexts],
        # "ground_truth": []
    })

    result = evaluate(
        dataset,
        metrics=[
            faithfulness, 
          #  answer_relevancy, 
          #  context_precision
        ],
    )

    raw = result.to_pandas().to_dict(orient="records")[0]
    return sanitize(raw)
