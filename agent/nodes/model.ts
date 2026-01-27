import { task, entrypoint } from "@langchain/langgraph";
import { BaseMessage, SystemMessage } from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai"
import { arithmeticTools } from "../tools/arithmetic";

const model = new ChatOpenAI({
  model: "gpt-5-mini"
});

const modelWithTools = model.bindTools(arithmeticTools);

export const modelNode = task({ name: "callLlm" }, async (messages: BaseMessage[]) => {
    

    return modelWithTools.invoke([
    new SystemMessage(
      "You are a helpful assistant tasked with performing arithmetic on a set of inputs."
    ),
    ...messages,
  ]);
});