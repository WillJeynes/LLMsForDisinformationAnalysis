import { GraphNode } from "@langchain/langgraph";
import { MessagesState, ProposedTriggerEventArray } from "../state";
import { logger } from "../utils/logger";
import { queryScraper } from "../tools/webSearch";
import { rankAndDisplayData } from "../tools/triggerEventTools";

export const selfEvalSetup: GraphNode<typeof MessagesState> = async (state) => {
  let genResponse = state.messages.at(-1)?.content.toString() ?? "";
  const parsed = ProposedTriggerEventArray.parse(JSON.parse(genResponse));

  for (let i = 0; i < parsed.length; i++) {
    const search = parsed[i].SearchQuery
    const data = await queryScraper(search);
    const output = await rankAndDisplayData(data, search);

    parsed[i].context = output;
  }

  return { evalTriggerEvent: parsed };

};