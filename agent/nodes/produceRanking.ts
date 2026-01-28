import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage, HumanMessage } from "@langchain/core/messages";

export const produceRanking: GraphNode<typeof MessagesState> = async (state) => {
  //TODO: produce ranking here
  
  return { messages: [ new AIMessage(state.messages?.length.toString() ?? "0")] };
};