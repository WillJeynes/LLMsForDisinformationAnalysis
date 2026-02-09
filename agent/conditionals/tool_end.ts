import { ConditionalEdgeRouter, END } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";

export function createToolConditional(a: String, b: String): ConditionalEdgeRouter<typeof MessagesState, String> {
  // @ts-expect-error
  var genericToolConditional: ConditionalEdgeRouter<typeof MessagesState, String> = (state) => {
    const lastMessage = state.messages.at(-1);

    // Check if it's an AIMessage before accessing tool_calls
    if (!lastMessage || !AIMessage.isInstance(lastMessage)) {
      return b;
    }

    // If the LLM makes a tool call, then perform an action
    if (lastMessage.tool_calls?.length) {
      return a;
    }

    // Otherwise, we stop (reply to the user)
    return b;
  };
  return genericToolConditional
}

