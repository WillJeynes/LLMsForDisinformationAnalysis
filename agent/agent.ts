import { END, START, StateGraph } from "@langchain/langgraph";
import { MessagesState } from "./state";
import { toolNode } from "./nodes/tool";
import { createToolConditional } from "./conditionals/tool_end";
import { normalizationSetup } from "./nodes/normalizationSetup";
import { dummyNormalisationModel } from "./nodes/dummyNormalisationModel";
import { dummyTriggerEventModel } from "./nodes/dummyTriggerEventModel";

const triggerEventToolConditional = createToolConditional(toolNode.name, END)
const agent = new StateGraph(MessagesState)
  
  //NODES
  .addNode("toolNode", toolNode)
  .addNode(normalizationSetup.name, normalizationSetup)
  .addNode(dummyNormalisationModel.name, dummyNormalisationModel)
  .addNode(dummyTriggerEventModel.name, dummyTriggerEventModel)
  
  .addEdge(START, normalizationSetup.name)
  .addEdge(normalizationSetup.name, dummyNormalisationModel.name)
  .addEdge(dummyNormalisationModel.name, dummyTriggerEventModel.name)
  
  // @ts-expect-error
  .addConditionalEdges(dummyTriggerEventModel.name, triggerEventToolConditional, [toolNode.name, END])
  
  .addEdge(toolNode.name, dummyTriggerEventModel.name)
  
  .addEdge(dummyTriggerEventModel.name, END)
  .compile();

  export {agent}