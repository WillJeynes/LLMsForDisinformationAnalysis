import { tool } from "@langchain/core/tools";
import * as z from "zod";
import { queryScraper } from "./webSearch";
import { extractWebpageContent } from "./webpageFetch";
import { rankDynamically } from "./retreiveExamples";


export async function rankAndDisplayData(data: string[], context: string):Promise<string> {
  let index = 0;
  let ranked = await rankDynamically(context, data.map(irm => ({ id: index++, rawtext: irm })))
  return ranked.map(itm => itm.rawtext).join("\n")
}

// Define tools
const webSearch = tool(
  async ({ a }) => {
    const data = await queryScraper(a);
    return await rankAndDisplayData(data, a);
  },
  {
    name: "WebSearch",
    description: "Search DuckDuckGo for the provided query",
    schema: z.object({
      a: z.string().describe("Search term"),
    }),
  }
);

const openWebpage = tool(
  async ({ a }) => {
    const data = await extractWebpageContent(a);
    return data;
  },
  {
    name: "WebRetreiveUrl",
    description: "Fetches and reads the FULL contents of a webpage. REQUIRED when detailed or accurate information is needed.",
    schema: z.object({
      a: z.url().describe("URL")
    }),
  }
);

// Augment the LLM with tools
export const triggerEventToolsByName = {
  [webSearch.name]: webSearch,
  [openWebpage.name]: openWebpage
};
