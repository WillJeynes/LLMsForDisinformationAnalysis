import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";
import { evaluateWithRoberta } from "../tools/robertaCall";

export const robertaMetrics: GraphNode<typeof MessagesState> = async (state) => {
  const answer = state.proposedTriggerEvent[state.proposedTriggerEventIndex].Event
  
  const result = await evaluateWithRoberta({answer})
  
  let score = 0;
  if (result.validProb > result.invalidProb) {
    score = 0.7 + ((result.validProb - result.invalidProb)*0.3);
  }
  
  return {
    messages: [ new AIMessage("ROBERTA:" + score)]
  };
};