import axios from "axios";

export async function queryScraper(query: string): Promise<string[]> {
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
            throw new Error(
                `HTTP error ${err.response.status}: ${JSON.stringify(err.response.data)}`
            );
        }
        throw err;
    }

    const data = response.data;

    if (data?.status !== "ok") {
        throw new Error(`API returned status: ${data?.status}`);
    }

    // TEMP?: Convert API results to array of formatted strings.

    const context = data.web ?? [];

    const lines: string[] = context.map((item: any) => {
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