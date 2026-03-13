import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";
import { evaluateWithRoberta } from "../tools/robertaCall";

export const robertaMetrics: GraphNode<typeof MessagesState> = async (state) => {
  const answer = state.proposedTriggerEvent[state.proposedTriggerEventIndex].Event
  
  const result = await evaluateWithRoberta({answer})
  
  return {
    messages: [ new AIMessage("ROBERTA:" + result)]
  };
};