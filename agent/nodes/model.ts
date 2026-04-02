import { SystemMessage } from "@langchain/core/messages";
import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { ChatOllama } from "@langchain/ollama";
import { hydratePrompt } from "../prompts/hydratePrompt";
import { logger } from "../utils/logger";

export function createModelNode(tools: any, promptPath: string): GraphNode<typeof MessagesState> {
    return async (state) => {
        const sysPrompt = await hydratePrompt(promptPath, state);

        const model = new ChatOllama({
            model: "llama3.1:8b-instruct-q4_K_M",
            temperature: 0.3
        });

        const modelWithTools = model.bindTools(Object.values(tools));

        const response = await modelWithTools.invoke([
            new SystemMessage(sysPrompt),
            ...state.messages,
        ]);

        logger.error(response);

        return {
            messages: [response]
        };
    };
}