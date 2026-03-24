import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";
import { evaluateWithEnsemble } from "../tools/ensembleCall";

export function createEnsembleNode(title: string, method: string): GraphNode<typeof MessagesState> {
  return async (state) => {
    const answer = state.proposedTriggerEvent[state.proposedTriggerEventIndex].Event

    const result = await evaluateWithEnsemble({ answer, method })
    const score = result.validProb - result.invalidProb;

    return {
      messages: [new AIMessage(title + ":" + score)]
    };
  };
};