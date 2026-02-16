import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage, BaseMessage, HumanMessage } from "@langchain/core/messages";
import { rankExampleTriggerEvents, rankNormalizedClaims } from "../tools/retreiveExamples";

export const triggerEventSetup: GraphNode<typeof MessagesState> = async (state) => {
  let nc = state?.messages?.at(-1)?.content ?? "" //keep a copy of normalized trigger event. Again two things, womp womp
  
  //Now give in-context examples. hopwfully we can self-teach?
  let similarityResults = await rankExampleTriggerEvents(state.disinformationTitle)

  let messages : BaseMessage[] = similarityResults.map((item) => {
    return new AIMessage(`Event: ${item.rawtext}, Claims and given scores: ${item.cleantext}`)
  })
  
  return { messages: messages, disinformationTitle: state.disinformationTitle, normalizedClaim: nc };
};