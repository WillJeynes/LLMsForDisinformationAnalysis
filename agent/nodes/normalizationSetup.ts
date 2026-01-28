import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { HumanMessage } from "@langchain/core/messages";

export const normalizationSetup: GraphNode<typeof MessagesState> = async (state) => {
  //TODO: Implement claim normalisation, using few shot prompting and CLAN Dataset
  
  return { messages: [ new HumanMessage(state.disinformationTitle)] };
};