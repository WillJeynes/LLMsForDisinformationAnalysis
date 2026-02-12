import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage, HumanMessage } from "@langchain/core/messages";
import { evaluateWithRagas } from "../tools/ragasCall";

export const ragasMetrics: GraphNode<typeof MessagesState> = async (state) => {
  const question = "A possible trigger event for: " + state.disinformationTitle //Should it be raw, or normalized?
  const answer = state.proposedTriggerEvent[state.proposedTriggerEventIndex].Event
  const contexts = state.proposedTriggerEvent[state.proposedTriggerEventIndex].context?.split("^^^") ?? []
  
  const results = await evaluateWithRagas({question, answer, contexts})
  
  return {
    messages: [ new AIMessage("RAGAS:" + results.faithfulness)]
  };
};