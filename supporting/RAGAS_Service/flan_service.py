from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from fastapi import FastAPI

app = FastAPI()

MODEL_PATH = "WillJeynes/LLMsForDisinformationAnalysis-Flan"

INT_TO_LABEL = {
    0: "perfect",
    1: "story",
    2: "not specific",
}

LABEL_TO_INT = {v: k for k, v in INT_TO_LABEL.items()}

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


def format_prompt(text: str) -> str:
    return (
        "Classify the following event into one of these categories: "
        "perfect, story, not specific.\n\n"
        f"Event: {text}\n\n"
        "Category:"
    )


def parse_generated_label(generated: str) -> int | None:
    generated = generated.strip().lower()
    for label_text, label_int in LABEL_TO_INT.items():
        if label_text in generated:
            return label_int
    return None


class EvalRequest(BaseModel):
    answer: str


@app.post("/evaluate")
def evaluate(req: EvalRequest):
    prompt = format_prompt(req.answer)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256,
    ).to(device)

    with torch.no_grad():
        # Get the generated label
        outputs = model.generate(
            **inputs,
            max_new_tokens=8,
        )

        # Produce a confidence score
        decoder_input_ids = torch.tensor([[model.config.decoder_start_token_id]]).to(device)
        logits_output = model(**inputs, decoder_input_ids=decoder_input_ids)
        logits = logits_output.logits[:, 0, :]

    # Decode the generated text label
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    predicted_int = parse_generated_label(generated_text)

    # Extract probabilities
    label_token_ids = {
        label: tokenizer(label, add_special_tokens=False).input_ids[0]
        for label in LABEL_TO_INT.keys()
    }

    label_logits = torch.tensor(
        [logits[0, tid].item() for tid in label_token_ids.values()]
    )
    label_probs = torch.softmax(label_logits, dim=0).tolist()

    return {
        "generated": generated_text,
        "probabilities": [label_probs],
    }