import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { ChatOllama } from "@langchain/ollama";
import { hydratePrompt } from "../prompts/hydratePrompt";

export function createModelNode(tools: any, promptPath: string): GraphNode<typeof MessagesState> {
    return async (state) => {
        const sysPrompt = await hydratePrompt(promptPath, state);

        const model = new ChatOllama({
            model: "deepseek-r1:14b",
            temperature: 0.7,
        });

        const modelWithTools = model.bindTools(Object.values(tools));

        const response = await modelWithTools.invoke([
            new SystemMessage(sysPrompt),
            ...state.messages,
        ]);

        return {
            messages: [response]
        };
    };
}