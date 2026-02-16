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
import { sort } from "./nodes/sort";
import { triggerEventSetup } from "./nodes/triggerEventSetup";

const triggerEventToolNode = createToolNode(triggerEventToolsByName);

const normalisationModel = createModelNode([], "normalization.txt");
const triggerEventModel = createModelNode(triggerEventToolsByName, "trigger.txt");
const verificationModel = createModelNode([], "verify.txt");
const relationModel = createModelNode([], "relation.txt");

const triggerEventToolConditional = createToolConditional("triggerEventToolNode", verificationSetup.name);

const agent = new StateGraph(MessagesState)
  
  //NODES
  .addNode(normalizationSetup.name, normalizationSetup)
  .addNode("normalisationModel", normalisationModel)
  
  .addNode(triggerEventSetup.name, triggerEventSetup)
  .addNode("triggerEventToolNode", triggerEventToolNode)
  .addNode("triggerEventModel", triggerEventModel)

  .addNode(verificationSetup.name, verificationSetup)
  .addNode("verificationModel", verificationModel)
  .addNode(ragasMetrics.name, ragasMetrics)
  .addNode("relationModel", relationModel)
  
  .addNode(produceRanking.name, produceRanking)
  .addNode(sort.name, sort)
  
  .addEdge(START, normalizationSetup.name)
  .addEdge(normalizationSetup.name, "normalisationModel")
  .addEdge("normalisationModel", triggerEventSetup.name)

  .addEdge(triggerEventSetup.name, "triggerEventModel")
  
  // @ts-expect-error
  .addConditionalEdges("triggerEventModel", triggerEventToolConditional, ["triggerEventToolNode", verificationSetup.name])
  .addEdge("triggerEventToolNode", "triggerEventModel")
  
  .addEdge(verificationSetup.name, "verificationModel")
  .addEdge(verificationSetup.name, ragasMetrics.name)
  .addEdge(verificationSetup.name, "relationModel")

  .addEdge(ragasMetrics.name, produceRanking.name)
  .addEdge("verificationModel", produceRanking.name)
  .addEdge("relationModel", produceRanking.name)

  // @ts-expect-error
  .addConditionalEdges(produceRanking.name, loopEndConditional, [verificationSetup.name, sort.name])
  
  .addEdge(sort.name, END)

  .compile();

  export {agent}