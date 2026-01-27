import type { ToolCall } from "@langchain/core/messages/tool";
import { task } from "@langchain/langgraph";
import { arithmeticToolsByName } from "../tools/arithmetic";

export const toolNode = task({ name: "callTool" }, async (toolCall: ToolCall) => {
  const tool = arithmeticToolsByName[toolCall.name];
  return tool.invoke(toolCall);
});