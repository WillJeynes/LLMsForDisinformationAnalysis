import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

ENV_PATH = Path("../../agent/.env")
load_dotenv(dotenv_path=ENV_PATH)

client = OpenAI()

INPUT_FILE = "../../data/reranked/0_original.jsonl"
OUTPUT_FILE = "output.txt"
MODEL = "gpt-5-nano"

MAX_WORKERS = 60  # tune this

write_lock = Lock()


def make_request(line):
    try:
        data = json.loads(line)
        prompt = (
            "Provide a story item for the spread of a disinformation claim"
            "that is related to the topic: "
            + data.get("text", "")
            + " Include just the event no other text."
            + " A good example would be 'No immediate U.S. government confirmation and near‑simultaneous fact‑checks/debunks appeared (fact‑checks published June 26, 2024).' and 'Recycled/old footage of aircraft being shot down previously viral and repeatedly misattributed to the Russia–Ukraine war (e.g., 2011 Libya footage reused in 2022)'"
            + " If you cannot answer just return an empty string"
            + " Be concise, make no mistakes"
        )

        if not prompt:
            return ""

        response = client.responses.create(
            model=MODEL,
            input=prompt
        )

        text = response.output_text.strip() if response.output_text else ""

        if text and "\n" not in text and "sorry" not in text.lower() and "you" not in text.lower():
            return text

        return ""

    except Exception as e:
        return ""


def process_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as infile:
        lines = list(infile)

    with open(output_path, "w", encoding="utf-8") as outfile:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(make_request, line) for line in lines]

            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
                result = future.result()
                if result:
                    # 🔒 ensure thread-safe writes
                    with write_lock:
                        outfile.write(result + ",NSPECIFIC\n")


if __name__ == "__main__":
    process_file(INPUT_FILE, OUTPUT_FILE)