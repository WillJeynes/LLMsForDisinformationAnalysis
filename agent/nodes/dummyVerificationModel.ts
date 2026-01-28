import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage, HumanMessage } from "@langchain/core/messages";

export const dummyVerificationModel: GraphNode<typeof MessagesState> = async (state) => {
  //TODO: call AI model with collected data
  
  return {
    messages: [ new AIMessage("Verified : " + state.messages.at(-1)?.content)]
  };
};