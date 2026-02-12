import { END, START, StateGraph } from "@langchain/langgraph";
import { MessagesState } from "./state";
import { createToolNode } from "./nodes/tool";
import { createToolConditional } from "./conditionals/tool_end";
import { normalizationSetup } from "./nodes/normalizationSetup";
import { triggerEventToolsByName } from "./tools/triggerEventTools"
import { createDummyModelNode } from "./nodes/dummyModel";
import { verificationSetup } from "./nodes/verificationSetup";
import { dummyRagasMetrics } from "./nodes/dummyRagasMetrics";
import { produceRanking } from "./nodes/produceRanking";
import { createModelNode } from "./nodes/model";
import { loopEndConditional } from "./conditionals/loop_end";

const triggerEventToolNode = createToolNode(triggerEventToolsByName);

const dummyVerificationModel = createDummyModelNode("verification of");

const normalisationModel = createModelNode([], "normalization.txt");
const triggerEventModel = createModelNode(triggerEventToolsByName, "trigger.txt");


const triggerEventToolConditional = createToolConditional("triggerEventToolNode", verificationSetup.name);

const agent = new StateGraph(MessagesState)
  
  //NODES
  
  .addNode(normalizationSetup.name, normalizationSetup)
  .addNode("normalisationModel", normalisationModel)
  
  .addNode("triggerEventToolNode", triggerEventToolNode)
  .addNode("triggerEventModel", triggerEventModel)

  .addNode(verificationSetup.name, verificationSetup)
  .addNode("dummyVerificationModel", dummyVerificationModel)
  .addNode(dummyRagasMetrics.name, dummyRagasMetrics)
  .addNode(produceRanking.name, produceRanking)
  
  .addEdge(START, normalizationSetup.name)
  .addEdge(normalizationSetup.name, "normalisationModel")
  .addEdge("normalisationModel", "triggerEventModel")
  
  // @ts-expect-error
  .addConditionalEdges("triggerEventModel", triggerEventToolConditional, ["triggerEventToolNode", verificationSetup.name])
  .addEdge("triggerEventToolNode", "triggerEventModel")
  
  .addEdge(verificationSetup.name, "dummyVerificationModel")
  .addEdge(verificationSetup.name, dummyRagasMetrics.name)

  .addEdge(dummyRagasMetrics.name, produceRanking.name)
  .addEdge("dummyVerificationModel", produceRanking.name)

  
  .addConditionalEdges(produceRanking.name, loopEndConditional, [verificationSetup.name, END])
  
  .compile();

  export {agent}