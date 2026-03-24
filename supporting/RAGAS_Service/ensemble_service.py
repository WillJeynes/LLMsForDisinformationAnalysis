from pydantic import BaseModel
from fastapi import FastAPI
import torch
import torch.nn as nn
import os
from sentence_transformers import SentenceTransformer
from huggingface_hub import hf_hub_download
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

app = FastAPI()

############################################
# SCHEMA
############################################

class EvalRequest(BaseModel):
    answer: str
    method: str  # "logreg", "roberta", "flan"


############################################
# REGRESSION MODEL
############################################

HF_REPO_ID = "WillJeynes/LLMsForDisinformationAnalysis-Regression"
MODEL_FILENAME = "logreg_classifier.pt"
CACHE_DIR = "./model_cache"


def load_checkpoint(repo_id: str, filename: str, cache_dir: str) -> dict:
    local_path = os.path.join(cache_dir, filename)
    if not os.path.exists(local_path):
        os.makedirs(cache_dir, exist_ok=True)
        hf_hub_download(repo_id=repo_id, filename=filename, local_dir=cache_dir)
    return torch.load(local_path, map_location="cpu")


class LogisticNet(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_classes, dropout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x):
        return self.net(x)


checkpoint = load_checkpoint(HF_REPO_ID, MODEL_FILENAME, CACHE_DIR)

encoder = SentenceTransformer(checkpoint["embedding_model"])

logreg_model = LogisticNet(
    checkpoint["input_dim"],
    checkpoint["hidden_dim"],
    checkpoint["num_classes"],
    checkpoint["dropout"],
)
logreg_model.load_state_dict(checkpoint["model_state"])
logreg_model.eval()


############################################
# ROBERTA
############################################

ROBERTA_PATH = "WillJeynes/LLMsForDisinformationAnalysis"

roberta_tokenizer = RobertaTokenizer.from_pretrained(ROBERTA_PATH)
roberta_model = RobertaForSequenceClassification.from_pretrained(ROBERTA_PATH)
roberta_model.eval()


############################################
# FLAN
############################################

FLAN_PATH = "WillJeynes/LLMsForDisinformationAnalysis-Flan"

INT_TO_LABEL = {
    0: "perfect",
    1: "story",
    2: "not specific",
}
LABEL_TO_INT = {v: k for k, v in INT_TO_LABEL.items()}

flan_tokenizer = AutoTokenizer.from_pretrained(FLAN_PATH)
flan_model = AutoModelForSeq2SeqLM.from_pretrained(FLAN_PATH)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
flan_model.to(device)
flan_model.eval()

label_token_ids = {
    label: flan_tokenizer(label, add_special_tokens=False).input_ids[0]
    for label in LABEL_TO_INT.keys()
}


def format_prompt(text: str) -> str:
    return (
        "Classify the following event into one of these categories: "
        "perfect, story, not specific.\n\n"
        f"Event: {text}\n\n"
        "Category:"
    )


def parse_generated_label(generated: str):
    generated = generated.strip().lower()
    for label_text, label_int in LABEL_TO_INT.items():
        if label_text in generated:
            return label_int
    return None


############################################
# ENDPOINT
############################################

@app.post("/evaluate")
def evaluate(req: EvalRequest):
    method = req.method.lower()

    ########################################
    # LOGREG
    ########################################
    if method == "logreg":
        embedding = encoder.encode(
            [req.answer],
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        x = torch.tensor(embedding, dtype=torch.float32)

        with torch.no_grad():
            logits = logreg_model(x)

        probs = torch.softmax(logits, dim=1)

        return {
            "method": "logreg",
            "probabilities": probs.cpu().numpy().tolist()
        }

    ########################################
    # ROBERTA
    ########################################
    elif method == "roberta":
        inputs = roberta_tokenizer(
            req.answer,
            return_tensors="pt",
            truncation=True,
            padding=True
        )

        with torch.no_grad():
            logits = roberta_model(**inputs).logits

        probs = torch.softmax(logits, dim=1)

        return {
            "method": "roberta",
            "probabilities": probs.cpu().numpy().tolist()
        }

    ########################################
    # FLAN
    ########################################
    elif method == "flan":
        prompt = format_prompt(req.answer)

        inputs = flan_tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256,
        ).to(device)

        with torch.no_grad():
            outputs = flan_model.generate(**inputs, max_new_tokens=8)

            decoder_input_ids = torch.tensor(
                [[flan_model.config.decoder_start_token_id]]
            ).to(device)

            logits_output = flan_model(
                **inputs,
                decoder_input_ids=decoder_input_ids
            )

            logits = logits_output.logits[:, 0, :]

        generated_text = flan_tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        label_logits = torch.tensor(
            [logits[0, tid].item() for tid in label_token_ids.values()]
        )

        label_probs = torch.softmax(label_logits, dim=0).tolist()

        return {
            "method": "flan",
            "generated": generated_text,
            "probabilities": [label_probs],
        }

    ########################################
    # INVALID METHOD
    ########################################
    else:
        return {
            "error": "Invalid method. Use 'logreg', 'roberta', or 'flan'."
        }