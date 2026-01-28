import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage, HumanMessage } from "@langchain/core/messages";

export const dummyTriggerEventModel: GraphNode<typeof MessagesState> = async (state) => {
  //TODO: call AI model with collected data
  
  return {
    messages: [ new AIMessage("Trigger events of: " + state.messages.at(-1)?.content)]
  };
};