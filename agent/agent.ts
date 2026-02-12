import { END, START, StateGraph } from "@langchain/langgraph";
import { MessagesState } from "./state";
import { createToolNode } from "./nodes/tool";
import { createToolConditional } from "./conditionals/tool_end";
import { normalizationSetup } from "./nodes/normalizationSetup";
import { triggerEventToolsByName } from "./tools/triggerEventTools"
import { verificationSetup } from "./nodes/verificationSetup";
import { ragasMetrics } from "./nodes/ragasMetrics";
import { produceRanking } from "./nodes/produceRanking";
import { createModelNode } from "./nodes/model";
import { loopEndConditional } from "./conditionals/loop_end";

const triggerEventToolNode = createToolNode(triggerEventToolsByName);

const normalisationModel = createModelNode([], "normalization.txt");
const triggerEventModel = createModelNode(triggerEventToolsByName, "trigger.txt");
const verificationModel = createModelNode([], "verify.txt");

const triggerEventToolConditional = createToolConditional("triggerEventToolNode", verificationSetup.name);

const agent = new StateGraph(MessagesState)
  
  //NODES
  
  .addNode(normalizationSetup.name, normalizationSetup)
  .addNode("normalisationModel", normalisationModel)
  
  .addNode("triggerEventToolNode", triggerEventToolNode)
  .addNode("triggerEventModel", triggerEventModel)

  .addNode(verificationSetup.name, verificationSetup)
  .addNode("verificationModel", verificationModel)
  .addNode(ragasMetrics.name, ragasMetrics)
  .addNode(produceRanking.name, produceRanking)
  
  .addEdge(START, normalizationSetup.name)
  .addEdge(normalizationSetup.name, "normalisationModel")
  .addEdge("normalisationModel", "triggerEventModel")
  
  // @ts-expect-error
  .addConditionalEdges("triggerEventModel", triggerEventToolConditional, ["triggerEventToolNode", verificationSetup.name])
  .addEdge("triggerEventToolNode", "triggerEventModel")
  
  .addEdge(verificationSetup.name, "verificationModel")
  .addEdge(verificationSetup.name, ragasMetrics.name)

  .addEdge(ragasMetrics.name, produceRanking.name)
  .addEdge("verificationModel", produceRanking.name)

  // @ts-expect-error
  .addConditionalEdges(produceRanking.name, loopEndConditional, [verificationSetup.name, END])
  
  .compile();

  export {agent}