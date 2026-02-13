import fs from "fs";
import path from "path";
import { Client } from "@langchain/langgraph-sdk";
import cliProgress from "cli-progress";
import pLimit from "p-limit";


const INPUT_FILE = "./claims.json";
const OUTPUT_FILE = "./results.jsonl";
const API_URL = "http://localhost:2024";
const AGENT_NAME = "agent";
const MAX_CONCURRENCY = 50;

const client = new Client({ apiUrl: API_URL });

type Claim = {
  documentUrl: string;
  text: string;
  [key: string]: any;
};

type ResultRecord = {
  documentUrl: string;
  text: string;
  status: "success" | "error";
  output?: any;
  error?: string;
};

function appendResult(record: ResultRecord) {
  fs.appendFileSync(OUTPUT_FILE, JSON.stringify(record) + "\n");
}

async function processClaim(claim: Claim): Promise<ResultRecord> {
  try {
    const thread = await client.threads.create();

    const stream = client.runs.stream(
      thread.thread_id,
      AGENT_NAME,
      {
        input: {
          disinformationTitle: claim.text,
        },
        streamMode: "messages-tuple",
        recursionLimit: 100,
      }
    );

    let lastMessage: any = null;

    for await (const chunk of stream) {
      // capture latest output
      if (chunk?.data) {
        lastMessage = chunk.data;
      }
    }

    return {
      documentUrl: claim.documentUrl,
      text: claim.text,
      status: "success",
      output: lastMessage,
    };
  } catch (err: any) {
    return {
      documentUrl: claim.documentUrl,
      text: claim.text,
      status: "error",
      error: err?.message ?? String(err),
    };
  }
}


async function main() {
  console.log("Reading input file...");

  const raw = fs.readFileSync(INPUT_FILE, "utf-8");
  const claims: Claim[] = JSON.parse(raw);

  console.log(`Loaded ${claims.length} records`);

  fs.writeFileSync(OUTPUT_FILE, "", { flag: "a" });

  const limit = pLimit(MAX_CONCURRENCY);

  const progressBar = new cliProgress.SingleBar(
    {
      format:
        "Progress |{bar}| {percentage}% | {value}/{total} | ETA: {eta}s",
    },
    cliProgress.Presets.shades_classic
  );

  progressBar.start(claims.length, 0);

  let completed = 0;

  const tasks = claims.map((claim) =>
    limit(async () => {
      const result = await processClaim(claim);

      appendResult(result);

      completed++;
      progressBar.update(completed);
    })
  );

  await Promise.all(tasks);

  progressBar.stop();
  console.log("Processing complete");
}

main().catch((err) => {
  console.error("Fatal error:", err);
});
