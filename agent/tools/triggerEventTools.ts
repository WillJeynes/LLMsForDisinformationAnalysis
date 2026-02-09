import { tool } from "@langchain/core/tools";
import * as z from "zod";
import { queryScraper } from "./webSearch";
import { extractWebpageContent } from "./webpageFetch";


function rankAndDisplayData(data: string[]):string {
  //TODO: hybrid re-ranking of the provided data
  return data.join("\n")
}

// Define tools
const webSearch = tool(
  async ({ a }) => {
    const data = await queryScraper(a);
    return rankAndDisplayData(data);
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
    return rankAndDisplayData(data);
  },
  {
    name: "OpenWebpage",
    description: "Opens webpage and returns most relevent snippets",
    schema: z.object({
      a: z.string().describe("URL"),
    }),
  }
);

// Augment the LLM with tools
export const triggerEventToolsByName = {
  [webSearch.name]: webSearch,
  [openWebpage.name]: openWebpage
};
