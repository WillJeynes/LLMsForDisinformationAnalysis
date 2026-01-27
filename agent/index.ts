import { addMessages, entrypoint } from "@langchain/langgraph";
import { type BaseMessage } from "@langchain/core/messages";
import { HumanMessage } from "@langchain/core/messages";
import { modelNode } from "./nodes/model";
import { toolNode } from "./nodes/tool";
import 'dotenv/config';

const agent = entrypoint({ name: "agent" }, async (messages: BaseMessage[]) => {
  let modelResponse = await modelNode(messages);

  while (true) {
    if (!modelResponse.tool_calls?.length) {
      break;
    }

    // Execute tools
    const toolResults = await Promise.all(
      modelResponse.tool_calls.map((toolCall) => toolNode(toolCall))
    );
    messages = addMessages(messages, [modelResponse, ...toolResults]);
    modelResponse = await modelNode(messages);
  }

  return messages;
});

export {agent}

const result = await agent.invoke([new HumanMessage("Add 3 and 4.")]);

for (const message of result) {
  console.log(`[${message.getType()}]: ${message.text}`);
}