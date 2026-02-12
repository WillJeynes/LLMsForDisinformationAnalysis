import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { ChatOpenAI } from "@langchain/openai"
import { hydratePrompt } from "../prompts/hydratePrompt";

export function createModelNode(tools: any, promptPath: string): GraphNode<typeof MessagesState> {
    return async (state) => {
        const sysPrompt = await hydratePrompt(promptPath, state);

        const model = new ChatOpenAI({
            model: "gpt-5-mini"
        });
        const modelWithTools = model.bindTools(Object.values(tools));

        const response = await modelWithTools.invoke([
            new SystemMessage(
                sysPrompt
            ),
            ...state.messages,
        ]);

        return {
            messages: [response]
        };
    };
}