import path from "path";
import { logger } from "../utils/logger"
import fs from "fs";
import { parse } from "tldts";

type RawSiteRecord = {
    Domain: string;
    Score: string;
};

type SiteScore = {
    domain: string;
    score: number;
};

const FILE_PATH = "../data/Iffy.json"

function parseSiteScores(): SiteScore[] {
    const raw = fs.readFileSync(path.resolve(FILE_PATH), "utf-8");
    const data: unknown = JSON.parse(raw);

    if (!Array.isArray(data)) {
        throw new Error("Invalid JSON: expected array");
    }

  return data.map((item) => {
    const record = item as RawSiteRecord;

    return {
      domain: record.Domain,
      score: Number(record.Score),
    };
  });
}

let scores: SiteScore[] | null = null

export function checkDisinfo(url: string): boolean {
    if (scores == null) {
        scores = parseSiteScores();
    }

    const domain = parse(url).domain;

    const match = scores.find(itm => itm.domain == domain)
    if (match != null) {
        logger.warn("Bad source %s detected with score %s", url, match.score)
        return true;
    }

    return false;
}


// console.log(checkDisinfo("http://www.zerohedge.com"))