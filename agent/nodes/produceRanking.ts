import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { BaseMessage } from "@langchain/core/messages";

type Priority = keyof typeof mapping;

const mapping = {
  VERYHIGH: 1.0,
  HIGH: 0.75,
  MEDIUM: 0.5,
  LOW: 0.25,
  VERYLOW: 0.0
} as const;

function mapResponse(value: string): number {
  const upper = value.toUpperCase() as Priority;

  if (upper in mapping) {
    return mapping[upper];
  }

  return 0;
}

function getLastMessageContaining(
  messages: BaseMessage[],
  searchString: string
): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const content = messages[i].content;
    if (typeof content === "string" && content.includes(searchString)) {
      return content;
    }
  }
  return "";
}

export const produceRanking: GraphNode<typeof MessagesState> = async (state) => {
  //TODO: what should these weights be
  let conf = getLastMessageContaining(state.messages, "CONFIDENCE")?.split(":")[1] //TODO: we can better error handle here
  let ragas = getLastMessageContaining(state.messages, "RAGAS")?.split(":")[1] //TODO: we can genericify this too surely
  let rel = getLastMessageContaining(state.messages, "RELATION")?.split(":")[1]

  let result = mapResponse(conf) * Number.parseFloat(ragas) * mapResponse(rel)
  
  let current = state.proposedTriggerEvent;
  current[state.proposedTriggerEventIndex].score = result;

  return  { proposedTriggerEvent: current };
};