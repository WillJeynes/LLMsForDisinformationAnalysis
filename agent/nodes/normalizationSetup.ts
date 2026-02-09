import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage, BaseMessage, HumanMessage } from "@langchain/core/messages";
import { calculateSimilarity } from "../tools/clan/retreiveExamples";

export const normalizationSetup: GraphNode<typeof MessagesState> = async (state) => {
  let similarityResults = await calculateSimilarity(state.disinformationTitle)

  console.log(similarityResults)

  let messages : BaseMessage[] = similarityResults.map((item) => {
    return new AIMessage(`Original Claim: ${item.rawtext}. \n\n Normalised Claim: ${item.cleantext}`)
  })
  
  return { messages: messages, disinformationTitle: state.disinformationTitle };
};