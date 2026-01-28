// import { SystemMessage } from "@langchain/core/messages";
// import { GraphNode } from "@langchain/langgraph";
// import { MessagesState } from "../state";
// import { arithmeticTools } from "../tools/arithmetic";
// import { ChatOpenAI } from "@langchain/openai"

// const model = new ChatOpenAI({
//   model: "gpt-5-mini"
// });

// const modelWithTools = model.bindTools(arithmeticTools);

// export const llmCall: GraphNode<typeof MessagesState> = async (state) => {
//   const response = await modelWithTools.invoke([
//     new SystemMessage(
//       "You are a helpful assistant tasked with performing arithmetic on a set of inputs. Any calculation, no matter how trivial, should be done with tools.  Output the final answer with %%% on each side"
//     ),
//     ...state.messages,
//   ]);
//   return {
//     messages: [response],
//     llmCalls: 1,
//   };
// };