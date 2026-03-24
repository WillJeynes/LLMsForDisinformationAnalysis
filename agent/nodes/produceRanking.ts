import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { BaseMessage } from "@langchain/core/messages";

const models = {
  REGRESSION: 0.3,
  ROBERTA: 0.5,
  FLAN: 0.3,
} as const;

type ModelKey = keyof typeof models;

function mapResponse(value: string | undefined | null): number {
  if (!value) return 0;

  const trimmed = value.trim();
  const num = parseFloat(trimmed);

  if (!isNaN(num)) {
    return num;
  } else {
    return 0;
  }
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
  const values = (Object.keys(models) as ModelKey[]).map((key) => {
    const msg = getLastMessageContaining(state.messages, key);
    const part = msg?.split(":").at(1);
    const baseValue = mapResponse(part);

    return baseValue * models[key];
  });

  const result = values.reduce((acc, val) => acc + val, 0);

  const current = state.proposedTriggerEvent;
  current[state.proposedTriggerEventIndex].score = result;

  return { proposedTriggerEvent: current };
};