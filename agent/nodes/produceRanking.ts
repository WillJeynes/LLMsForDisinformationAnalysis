import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { BaseMessage } from "@langchain/core/messages";

//TODO: Each of these might need different weights
const keys = ["CONFIDENCE", "RAGAS", "RELATION"];

const mapping = {
  VERYHIGH: 1.0,
  HIGH: 0.75,
  MEDIUM: 0.5,
  LOW: 0.25,
  VERYLOW: 0.0,
} as const;

type Priority = keyof typeof mapping;

function mapResponse(value: string | undefined | null): number {
  if (!value) return 0;

  const trimmed = value.trim();
  const num = parseFloat(trimmed);

  // If number, return it
  if (!isNaN(num)) return num;

  // Otherwise, map to value
  const upper = trimmed.toUpperCase() as Priority;
  return mapping[upper] ?? 0;
}

function getLastMessageContaining(
  messages: BaseMessage[],
  searchString: string
): string | null {
  for (let i = messages.length - 1; i >= 0; i--) {
    const content = messages[i].content;
    if (typeof content === "string" && content.includes(searchString)) {
      return content;
    }
  }
  return null;
}

export const produceRanking: GraphNode<typeof MessagesState> = async (state) => {
  // Extract and map values
  const values = keys.map((key) => {
    const msg = getLastMessageContaining(state.messages, key);
    const part = msg?.split(":").at(1);
    return mapResponse(part);
  });

  // Multiply!
  const result = values.reduce((acc, val) => acc * val, 1);

  const current = state.proposedTriggerEvent;
  current[state.proposedTriggerEventIndex].score = result;

  return { proposedTriggerEvent: current };
};
