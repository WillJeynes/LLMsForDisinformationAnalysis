import axios from "axios";
import { checkDisinfo } from "./checkDisinfo";
import { writeToJSONL } from "../utils/writeToJSONL";
import { backOff } from "exponential-backoff";
import { logger } from "../utils/logger";

export async function queryScraper(query: string): Promise<string[]> {
    try {
        const response = await backOff(async () => {
            return await queryScraperWorker(query);
        },  {
            numOfAttempts: 10,
            startingDelay: 500,
            timeMultiple: 2,
            jitter: "full",
            maxDelay: 50000,
        })

        return response;
    }
    catch (err: any) {
        logger.error("Failed out of retry loop, returning placeholder to pipeline")
        return ["API EXCEPTION"]
    }
}

async function queryScraperWorker(query: string): Promise<string[]> {
    const instance = process.env.SCRAPER_INSTANCE;
    if (!instance) {
        throw new Error("SCRAPER_INSTANCE environment variable is not set");
    }

    const cleanQuery = query.replace(/[^A-Za-z0-9 ]+/g, "");

    const url = `${instance}/api/v1/web`;

    const params: Record<string, string> = Object.entries(process.env)
        .filter(([key, value]) => key.startsWith("SCRAPER_PARAM_") && value !== undefined)
        .reduce((acc: Record<string, string>, [key, value]) => {
            const paramName = key.replace(/^SCRAPER_PARAM_/, "").toLowerCase();
            acc[paramName] = value!;
            return acc;
        }, {});


    params.s = cleanQuery;

    let response;
    try {
        response = await axios.get(url, { params });
    } catch (err: any) {
        if (err.response) {
            const desc = `HTTP error ${err.response.status}: ${JSON.stringify(err.response.data)}`
            logger.error(desc)
            throw new Error(desc);
        }
        throw err;
    }

    const data = response.data;

    if (data?.status !== "ok") {
        const desc = `API returned status: ${data?.status}`;
        logger.error(desc)
        throw new Error(desc);
    }

    // TEMP?: Convert API results to array of formatted strings.

    const context = data.web ?? [];

    const lines: string[] = context.map((item: any) => {
        if (checkDisinfo(item.url)) {
            writeToJSONL("blocked.jsonl", { url: item.url, query: query })
            return "";
        }

        const title = (item.title ?? "").trim();
        const desc = (item.description ?? "").trim();
        const link = (item.url ?? "").trim();

        return `^^^ ${title}\n  ${desc}\n  ${link}`;
    });

    return lines;
}


// import dotenv from "dotenv";

// dotenv.config();
// console.log(await queryScraper("sir kier starmer"))