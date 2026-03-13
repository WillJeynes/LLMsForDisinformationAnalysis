import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";
import { removeDuplicates } from "../tools/removeDuplicates";
export const sort: GraphNode<typeof MessagesState> = async (state) => {
  let current = state.proposedTriggerEvent;

  // remove duplicates
  await removeDuplicates(current)

  // not sure which will be better from API, just do both
  current.sort((a, b) => ((b.score as number) ?? 0) - ((a.score as number) ?? 0));


  const displayVersion = current.map((item) => ({
    event: item.Event,
    reasoningWhyRelevant: item.ReasoningWhyRelevant,
    score: item.score ?? 0,
  }));

  let message = new AIMessage(JSON.stringify(displayVersion))

  return { proposedTriggerEvent: current, messages: [message] };
};
