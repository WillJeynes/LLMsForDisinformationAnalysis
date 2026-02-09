import { parse } from "csv-parse";
import fs from "fs";
import { pipeline, cos_sim } from "@huggingface/transformers";
import { logger } from "../../utils/logger";

//TODO, am getting duplicates, is it from the multi files?
const CSV_PATHS = [
  "./tools/clan/dev-eng.csv",
  // "./tools/clan/test-eng.csv",
  "./tools/clan/train-eng.csv",
];

const CACHE_PATH = "./tools/clan/dev.embeddings.json";

type EmbeddingCache = {
  rawtexts: string[];
  cleantexts: string[];
  embeddings: number[][];
};

export type NormalisedMatch = {
  index: number;
  score: number;
  rawtext: string;
  cleantext: string;
};

let rawtexts: string[] = [];
let cleantexts: string[] = [];
let embeddings: number[][] = [];

const featureExtractor = await pipeline(
  "feature-extraction",
  "Xenova/all-MiniLM-L6-v2"
);


async function loadOrBuildCache(): Promise<void> {
  if (fs.existsSync(CACHE_PATH)) {
    logger.info("Loading embeddings from cache");

    const raw = fs.readFileSync(CACHE_PATH, "utf-8");
    const cache: EmbeddingCache = JSON.parse(raw);

    rawtexts = cache.rawtexts;
    cleantexts = cache.cleantexts;
    embeddings = cache.embeddings.map(e => Array.from(e));

    logger.info("Loaded %s embeddings", embeddings.length);
    return;
  }

  logger.warn("Cache not found. Generating embeddings");

  for (const csvPath of CSV_PATHS) {
    await buildCacheFromCSV(csvPath);
  }

  const cache: EmbeddingCache = {
    rawtexts,
    cleantexts,
    embeddings,
  };

  fs.writeFileSync(CACHE_PATH, JSON.stringify(cache));

  logger.info("Cached %s embeddings", embeddings.length);
}

async function buildCacheFromCSV(csvPath: string): Promise<void> {
  let count = 0;

  logger.info("Processing CSV: %s", csvPath);

  const stream = fs.createReadStream(csvPath).pipe(parse());

  for await (const row of stream) {
    const text = row[0];
    if (!text) continue;

    const output = await featureExtractor(text, {
      pooling: "mean",
      normalize: true,
    });

    rawtexts.push(text);
    cleantexts.push(row[1]);
    const vector = Array.from(output.data as Float32Array);
    embeddings.push(vector);


    count++;
    if (count % 100 === 0) {
      logger.info("[%s] Processed %s rows", csvPath, count);
    }
  }

  logger.info("[%s] Finished (%s rows)", csvPath, count);
}

export async function calculateSimilarity(
  query: string,
  topK = 5
): Promise<NormalisedMatch[]> {
  await loadOrBuildCache()

  const queryEmbedding = await featureExtractor(query, {
    pooling: "mean",
    normalize: true,
  });

  return embeddings
    .map((embedding, index) => ({
      index,
      score: cos_sim(embedding, queryEmbedding.data as number[]),
      rawtext: rawtexts[index],
      cleantext: cleantexts[index]
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}