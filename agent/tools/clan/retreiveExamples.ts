import { parse } from "csv-parse";
import fs from "fs";
import { pipeline, cos_sim } from "@huggingface/transformers";
import { logger } from "../../utils/logger";

const CSV_PATH = "./tools/clan/dev-eng.csv";
const CACHE_PATH = "./tools/clan/dev-eng.embeddings.json";

type EmbeddingCache = {
  texts: string[];
  embeddings: number[][];
};

export type NormalisedMatch = {
  index: number; 
  score: number; 
  text: string
};

let texts: string[] = [];
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

    texts = cache.texts;

    embeddings = cache.embeddings.map(e => Array.from(e));

    logger.info("Loaded %s embeddings", embeddings.length);
    return;
  }

  logger.warn("Cache not found. Generating embeddings", embeddings.length);

  await buildCacheFromCSV();

  const cache: EmbeddingCache = {
    texts,
    embeddings,
  };

  fs.writeFileSync(CACHE_PATH, JSON.stringify(cache));

  logger.info("Cached %s embeddings", embeddings.length);
}

async function buildCacheFromCSV(): Promise<void> {
  let count = 0;

  const stream = fs.createReadStream(CSV_PATH).pipe(parse());

  for await (const row of stream) {
    const text = row[0];
    if (!text) continue;

    const output = await featureExtractor(text, {
      pooling: "mean",
      normalize: true,
    });

    texts.push(text);
    const vector = Array.from(output.data as Float32Array);
    embeddings.push(vector);


    count++;
    if (count % 100 === 0) {
      logger.info("Processed %s", count);
    }
  }
}

export async function calculateSimilarity(query: string,topK = 5): Promise<NormalisedMatch[]> {
  const queryEmbedding = await featureExtractor(query, {
    pooling: "mean",
    normalize: true,
  });

  return embeddings
    .map((embedding, index) => ({
      index,
      score: cos_sim(embedding, queryEmbedding.data as number[]),
      text: texts[index],
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

//TEMP: testing code
await loadOrBuildCache();

const results = await calculateSimilarity(
  "Wonderful to see London has taken a stand to defend freedom and the right to choose."
);

console.log(results);
