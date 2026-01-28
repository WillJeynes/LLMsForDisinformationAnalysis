import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";

export function createDummyModelNode(addition): GraphNode<typeof MessagesState> {
    return async (state) => {
        //TODO: call AI model with collected data

        return {
            messages: [new AIMessage(addition + " : " + state.messages.at(-1)?.content)]
        };
    };
}