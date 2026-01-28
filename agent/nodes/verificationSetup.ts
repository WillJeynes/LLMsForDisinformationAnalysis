import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { HumanMessage } from "@langchain/core/messages";

export const verificationSetup: GraphNode<typeof MessagesState> = async (state) => {
  //TODO: this might not be needed, looks nice on the graph tho
  
  return { messages: [ new HumanMessage(state.messages.at(-1)?.content ?? "undefined")] };
};