import { parse } from "csv-parse";
import fs from "fs";
import { pipeline, cos_sim } from "@huggingface/transformers";
import bm25Factory from "wink-bm25-text-search";
import nlp from "wink-nlp-utils";
import { logger } from "../utils/logger";
import readline from "readline";

const CSV_PATHS = [
  "../data/dev-eng.csv",
  "../data/train-eng.csv",
];

const CACHE_PATH = "../data/csv.cache.json";

const JSONL_PATH = "../data/input.jsonl"

type EmbeddingCache = {
  rawtexts: string[];
  cleantexts: string[];
  embeddings: number[][];
};

export type RetrievalItem = {
  id: string | number;
  rawtext: string;
  cleantext?: string;
};

export type RankedResult = RetrievalItem & {
  denseScore: number;
  sparseScore: number;
  fusedScore: number;
};

let csvRawtexts: string[] = [];
let csvCleantexts: string[] = [];
let csvEmbeddings: number[][] = [];
let csvBM25: any = null;
let csvLoaded = false;

let jsonlRawtexts: string[] = [];
let jsonlCleantexts: string[] = [];
let jsonlEmbeddings: number[][] = [];
let jsonlBM25: any = null;
let jsonlLoaded = false;


logger.info("Loading embedding model...");
const featureExtractor = await pipeline(
  "feature-extraction",
  "Xenova/all-MiniLM-L6-v2"
);
logger.info("Embedding model loaded");

//Cached entrypoints
export async function rankNormalizedClaims(
  query: string,
  topK = 5
): Promise<RankedResult[]> {
  await ensureNormalizedClaimCSVLoaded();

  logger.info("Ranking from CSV cache...");

  const queryEmbedding = await embedText(query);

  const denseScores = csvEmbeddings.map((docEmbedding) =>
    cos_sim(docEmbedding, queryEmbedding)
  );

  const sparseScores = computeSparseScores(query, csvBM25, csvRawtexts);

  const fusedScores = reciprocalRankFusion([denseScores, sparseScores]);

  const ranked = csvRawtexts
    .map((text, i) => ({
      id: i,
      rawtext: text,
      cleantext: csvCleantexts[i],
      denseScore: denseScores[i],
      sparseScore: sparseScores[i],
      fusedScore: fusedScores[i],
    }))
    .sort((a, b) => b.fusedScore - a.fusedScore);

  logger.info("Ranking complete (CSV mode)");

  return ranked.slice(0, topK);
}

export async function rankExampleTriggerEvents(
  query: string,
  topK = 5
): Promise<RankedResult[]> {
  await ensureExampleClaimJsonlLoaded();

  logger.info("Ranking from JSONL cache...");

  const queryEmbedding = await embedText(query);

  const denseScores = jsonlEmbeddings.map((docEmbedding) =>
    cos_sim(docEmbedding, queryEmbedding)
  );

  const sparseScores = computeSparseScores(query, jsonlBM25, jsonlRawtexts);

  const fusedScores = reciprocalRankFusion([denseScores, sparseScores]);

  const ranked = jsonlRawtexts
    .map((text, i) => ({
      id: i,
      rawtext: text,
      cleantext: jsonlCleantexts[i],
      denseScore: denseScores[i],
      sparseScore: sparseScores[i],
      fusedScore: fusedScores[i],
    }))
    .sort((a, b) => b.fusedScore - a.fusedScore);

  logger.info("Ranking complete (JSONL mode)");

  return ranked.slice(0, topK);
}

//Dynamic Entrypoint
export async function rankDynamically(
  query: string,
  items: RetrievalItem[],
  topK = 5
): Promise<RankedResult[]> {
  logger.info("Ranking dynamically (no cache)...");

  if (!items.length) return [];

  const texts = items.map((i) => i.rawtext);

  const queryEmbedding = await embedText(query);

  const docEmbeddings = await Promise.all(
    texts.map((text) => embedText(text))
  );

  const denseScores = docEmbeddings.map((embedding) =>
    cos_sim(embedding, queryEmbedding)
  );

  const localBM25 = buildBM25(texts);

  const sparseScores = computeSparseScores(query, localBM25, texts);

  const fusedScores = reciprocalRankFusion([denseScores, sparseScores]);

  const ranked = items
    .map((item, i) => ({
      ...item,
      denseScore: denseScores[i],
      sparseScore: sparseScores[i],
      fusedScore: fusedScores[i],
    }))
    .sort((a, b) => b.fusedScore - a.fusedScore);

  logger.info("Ranking complete (dynamic mode)");

  return ranked.slice(0, topK);
}

//CSV stuff
async function ensureNormalizedClaimCSVLoaded(): Promise<void> {
  if (csvLoaded) return;

  logger.info("Initializing CSV ranking mode...");

  if (fs.existsSync(CACHE_PATH)) {
    logger.info("Loading CSV cache from disk...");

    const raw = fs.readFileSync(CACHE_PATH, "utf-8");
    const cache: EmbeddingCache = JSON.parse(raw);

    csvRawtexts = cache.rawtexts;
    csvCleantexts = cache.cleantexts;
    csvEmbeddings = cache.embeddings;

    logger.info("Loaded %s cached embeddings", csvEmbeddings.length);
  } else {
    logger.warn("CSV cache not found. Building embeddings...");

    const seen = new Set<string>();

    for (const path of CSV_PATHS) {
      await processNormalizationCSV(path, seen);
    }

    const cache: EmbeddingCache = {
      rawtexts: csvRawtexts,
      cleantexts: csvCleantexts,
      embeddings: csvEmbeddings,
    };

    fs.writeFileSync(CACHE_PATH, JSON.stringify(cache));
    logger.info("Cache written (%s embeddings)", csvEmbeddings.length);
  }

  csvBM25 = buildBM25(csvRawtexts);

  csvLoaded = true;
  logger.info("CSV mode ready");
}

async function processNormalizationCSV(
  path: string,
  seen: Set<string>
): Promise<void> {
  logger.info("Processing CSV: %s", path);

  const stream = fs.createReadStream(path).pipe(parse());

  for await (const row of stream) {
    const text = row[0];
    if (!text || seen.has(text)) continue;

    seen.add(text);

    const embedding = await embedText(text);

    csvRawtexts.push(text);
    csvCleantexts.push(row[1]);
    csvEmbeddings.push(embedding);

    if (csvRawtexts.length % 100 === 0) {
      logger.info("Embedded %s documents...", csvRawtexts.length);
    }
  }

  logger.info("Finished CSV: %s", path);
}

async function ensureExampleClaimJsonlLoaded(): Promise<void> {
  if (jsonlLoaded) return;

  logger.info("Initializing JSONL ranking...");
  const stream = fs.createReadStream(JSONL_PATH);

  const rl = readline.createInterface({
    input: stream,
    crlfDelay: Infinity,
  });

  for await (const line of rl) {
    if (!line.trim()) continue; // skip empty lines

    const row = JSON.parse(line);

    const text = row.text;

    const embedding = await embedText(text);

    jsonlRawtexts.push(text);

    const parsed_content = row.events;

    const filtered_content = parsed_content.filter(itm => itm.human_score > 0.5 && itm.score > 0.5)

    jsonlCleantexts.push(JSON.stringify(filtered_content));
    jsonlEmbeddings.push(embedding);
  }


  jsonlBM25 = buildBM25(jsonlRawtexts);

  jsonlLoaded = true;
  logger.info("JSONL ranking done");
}


async function embedText(text: string): Promise<number[]> {
  const output = await featureExtractor(text, {
    pooling: "mean",
    normalize: true,
  });

  return Array.from(output.data as Float32Array);
}

function buildBM25(texts: string[]) {
  logger.info("Building BM25 index (%s docs)...", texts.length);

  const bm25 = bm25Factory();

  bm25.defineConfig({
    fldWeights: { text: 1 },
    bm25Params: { k1: 1.2, b: 0.75 },
  });

  bm25.definePrepTasks([
    nlp.string.lowerCase,
    nlp.string.tokenize0,
    nlp.tokens.removeWords,
  ]);

  texts.forEach((text, i) => {
    bm25.addDoc({ text }, i);
  });

  bm25.consolidate();

  logger.info("BM25 ready");

  return bm25;
}

function computeSparseScores(
  query: string,
  bm25: any,
  texts: string[]
): number[] {
  const results = bm25.search(query);

  const scores = new Array(texts.length).fill(0);

  results.forEach((r: any) => {
    scores[r[0]] = r[1];
  });

  return scores;
}

function reciprocalRankFusion(
  scoreLists: number[][],
  k = 60
): number[] {
  const length = scoreLists[0].length;
  const fused = new Array(length).fill(0);

  for (const scores of scoreLists) {
    const ranked = scores
      .map((score, i) => ({ score, i }))
      .sort((a, b) => b.score - a.score)
      .map((x) => x.i);

    ranked.forEach((docIndex, rank) => {
      fused[docIndex] += 1 / (k + rank);
    });
  }

  return fused;
}

// console.log(await rankFromCSV("barrack obama"))
// console.log(
//   await rankDynamically(
//     "i fell over",
//     [
//       { id: 1, rawtext: "I slipped and fell on the floor." },
//       { id: 2, rawtext: "Barack Obama was the 44th president." },
//       { id: 3, rawtext: "He tripped and hurt his knee badly." },
//       { id: 4, rawtext: "The weather is sunny today." },
//       { id: 5, rawtext: "She lost her balance and fell down the stairs." },
//     ]
//   )
// );

// await ensureExampleClaimJsonlLoaded()
// console.log(await rankExampleTriggerEvents("Niger"))