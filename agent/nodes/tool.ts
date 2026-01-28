import { AIMessage, ToolMessage } from "@langchain/core/messages";
import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { arithmeticToolsByName } from "../tools/arithmetic";

export const toolNode: GraphNode<typeof MessagesState> = async (state) => {
  const lastMessage = state.messages.at(-1);

  //STARTTEMP
  return {messages: [new AIMessage("yeman")]}
  //ENDTEMP
  
  if (lastMessage == null || !AIMessage.isInstance(lastMessage)) {
    return { messages: [] };
  }

  const result: ToolMessage[] = [];
  for (const toolCall of lastMessage.tool_calls ?? []) {
    const tool = arithmeticToolsByName[toolCall.name];
    const observation = await tool.invoke(toolCall);
    result.push(observation);
  }

  return { messages: result };
};