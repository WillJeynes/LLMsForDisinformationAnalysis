import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage, BaseMessage } from "@langchain/core/messages";
import { rankExampleTriggerEvents } from "../tools/retreiveExamples";

function extractTE(text: string) {
  const match = text.match(/<norm>([\s\S]*?)<\/norm>/);
  if (!match) throw new Error("Nothing found between <norm> tags");
  return match[1].trim();
}


export const triggerEventSetup: GraphNode<typeof MessagesState> = async (state) => {
  let raw = state?.messages?.at(-1)?.content ?? "" //keep a copy of normalized trigger event. Again two things, womp womp
  let nc = extractTE(raw.toString())

  //Now give in-context examples. hopwfully we can self-teach?
  let similarityResults = await rankExampleTriggerEvents(state.disinformationTitle)

  let messages : BaseMessage[] = similarityResults.map((item) => {
    return new AIMessage(`- Event: ${item.rawtext} \n\n - Claims and given scores: ${item.cleantext}`)
  })
  
  return { messages: messages, disinformationTitle: state.disinformationTitle, normalizedClaim: nc };
};