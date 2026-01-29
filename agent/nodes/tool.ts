import { AIMessage, ToolMessage } from "@langchain/core/messages";
import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";

export function createToolNode(tools: any): GraphNode<typeof MessagesState> {
  return async (state) => {
    const lastMessage = state.messages.at(-1);

    //STARTTEMP
    return {messages: [new AIMessage("yeman")]}
    //ENDTEMP

    if (lastMessage == null || !AIMessage.isInstance(lastMessage)) {
      return { messages: [] };
    }

    const result: ToolMessage[] = [];
    for (const toolCall of (lastMessage as AIMessage).tool_calls ?? []) {
      const tool = tools[toolCall.name];
      const observation = await tool.invoke(toolCall);
      result.push(observation);
    }

    return { messages: result };
  };
}