import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage, HumanMessage } from "@langchain/core/messages";

export const dummyRagasMetrics: GraphNode<typeof MessagesState> = async (state) => {
  //TODO: get ragas metrics
  
  return {
    messages: [ new AIMessage("RAGASSED : " + state.messages.at(-1)?.content)]
  };
};