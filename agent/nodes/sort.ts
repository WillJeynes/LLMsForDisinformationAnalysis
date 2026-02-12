import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";
export const sort: GraphNode<typeof MessagesState> = async (state) => {
  //not sure which will be better from API, just do both

  let current = state.proposedTriggerEvent;
  current.sort((a, b) => ((b.score as number) ?? 0) - ((a.score as number) ?? 0));


  const displayVersion = current.map((item) => ({
    event: item.Event,
    reasoningWhyRelevant: item.ReasoningWhyRelevant,
    score: item.score ?? 0,
  }));

  let message = new AIMessage(JSON.stringify(displayVersion))

  return { proposedTriggerEvent: current, messages: [message] };
};
