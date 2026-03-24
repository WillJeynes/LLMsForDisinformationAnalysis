import fs from "fs";
import readline from "readline";
import { Client } from "@langchain/langgraph-sdk";
import cliProgress from "cli-progress";
import pLimit from "p-limit";

const INPUT_FILE = process.env.INPUT_FILE ?? "../../data/claims.json";
const OUTPUT_FILE = process.env.OUTPUT_FILE ?? "../../data/results.jsonl";

const API_URL = "http://localhost:2024";
const AGENT_NAME = process.env.AGENT ?? "agent";

/**
 * Modes
 * claim     -> claims from DBKF
 * verifier  -> jsonl claims to test reranking with
 */
const MODE = process.env.MODE ?? "claim";

const MAX_CONCURRENCY = 5;

const client = new Client({ apiUrl: API_URL });


type Claim = {
  documentUrl: string;
  text: string;
  dateCreated: string;
  [key: string]: any;
};

type VerifierInput = {
  documentUrl?: string;
  text?: string;
  normalized?: string;
  events?: any;
  run_id: string;
  date?: string;
  [key: string]: any;
};

type ResultRecord = {
  documentUrl?: string;
  text?: string;
  status: "success" | "error" | "wrapper_crash";
  normalized?: string;
  events?: any;
  run_id: string;
  date?: string;
  // error handling
  error?: string;
  dump?: any;
};

function appendResult(record: ResultRecord) {
  fs.appendFileSync(OUTPUT_FILE, JSON.stringify(record) + "\n");
}

async function readJSONL(file: string): Promise<any[]> {
  const stream = fs.createReadStream(file);

  const rl = readline.createInterface({
    input: stream,
    crlfDelay: Infinity
  });

  const results: any[] = [];

  for await (const line of rl) {
    if (line.trim().length === 0) continue;
    results.push(JSON.parse(line));
  }

  return results;
}

async function loadInputs(): Promise<any[]> {
  if (INPUT_FILE.endsWith(".jsonl")) {
    return readJSONL(INPUT_FILE);
  }

  const raw = fs.readFileSync(INPUT_FILE, "utf-8");
  return JSON.parse(raw);
}


function buildAgentInput(record: Claim | VerifierInput) {
  if (MODE === "claim") {
    const claim = record as Claim;

    return {
      disinformationTitle: claim.text,
      date: claim.dateCreated
    };
  }

  if (MODE === "verifier") {
    const v = record as VerifierInput;

    return {
      disinformationTitle: v.text,
      date: v.date,
      proposedTriggerEvent: v.events,
      normalizedClaim: v.normalizedClaim,
      proposedTriggerEventIndex: -1
    };
  }

  throw new Error(`Unknown mode: ${MODE}`);
}


async function processRecord(record: any): Promise<ResultRecord> {
  try {
    const thread = await client.threads.create();

    const stream = client.runs.stream(thread.thread_id, AGENT_NAME, {
      input: buildAgentInput(record),
      streamMode: "values",
      config: {
        recursion_limit: 50
      }
    });

    let lastContent: any = null;

    for await (const chunk of stream) {
      lastContent = chunk;
    }

    if (lastContent?.event !== "error") {
      return {
        documentUrl: record.documentUrl,
        text: record.text,
        date: record.dateCreated,
        status: "success",
        events: lastContent.data.proposedTriggerEvent,
        normalized: lastContent.data.normalizedClaim,
        run_id: thread.thread_id
      };
    } else {
      return {
        documentUrl: record.documentUrl,
        text: record.text,
        date: record.date,
        status: "error",
        dump: lastContent,
        run_id: thread.thread_id
      };
    }
  } catch (err: any) {
    return {
      documentUrl: record.documentUrl,
      text: record.text,
      date: record.date,
      status: "wrapper_crash",
      error: err?.message ?? String(err),
      run_id: "NONE"
    };
  }
}


async function main() {
  console.log("Reading input file...");

  const records = await loadInputs();

  console.log(`Loaded ${records.length} records`);

  fs.writeFileSync(OUTPUT_FILE, "", { flag: "a" });

  const limit = pLimit(MAX_CONCURRENCY);

  const progressBar = new cliProgress.SingleBar(
    {
      format:
        "Progress |{bar}| {percentage}% | {value}/{total} | ETA: {eta}s"
    },
    cliProgress.Presets.shades_classic
  );

  progressBar.start(records.length, 0);

  let completed = 0;

  const tasks = records.map((record) =>
    limit(async () => {
      const result = await processRecord(record);

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