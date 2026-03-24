import { END, START, StateGraph } from "@langchain/langgraph";
import { MessagesState } from "./state";
import { createToolNode } from "./nodes/tool";
import { createToolConditional } from "./conditionals/tool_end";
import { normalizationSetup } from "./nodes/normalizationSetup";
import { triggerEventToolsByName } from "./tools/triggerEventTools"
import { verificationSetup } from "./nodes/verificationSetup";
import { produceRanking } from "./nodes/produceRanking";
import { createModelNode } from "./nodes/model";
import { loopEndConditional } from "./conditionals/loop_end";
import { sort } from "./nodes/sort";
import { triggerEventSetup } from "./nodes/triggerEventSetup";
import { createEnsembleNode } from "./nodes/ensembleNode";

const triggerEventToolNode = createToolNode(triggerEventToolsByName);

const normalisationModel = createModelNode([], "normalization.txt");
const triggerEventModel = createModelNode(triggerEventToolsByName, "trigger.txt");

const triggerEventToolConditional = createToolConditional("triggerEventToolNode", verificationSetup.name);

const roNode = createEnsembleNode("ROBERTA", "roberta");
const flNode = createEnsembleNode("FLAN", "flan");
const lrNode = createEnsembleNode("REGRESSION", "logreg");

const agent = new StateGraph(MessagesState)
  
  //NODES
  .addNode(normalizationSetup.name, normalizationSetup)
  .addNode("normalisationModel", normalisationModel)
  
  .addNode(triggerEventSetup.name, triggerEventSetup)
  .addNode("triggerEventToolNode", triggerEventToolNode)
  .addNode("triggerEventModel", triggerEventModel)

  .addNode(verificationSetup.name, verificationSetup)

  .addNode("roNode", roNode)
  .addNode("flNode", flNode)
  .addNode("lrNode", lrNode)
  
  .addNode(produceRanking.name, produceRanking)
  .addNode(sort.name, sort)
  
  .addEdge(START, normalizationSetup.name)
  .addEdge(normalizationSetup.name, "normalisationModel")
  .addEdge("normalisationModel", triggerEventSetup.name)

  .addEdge(triggerEventSetup.name, "triggerEventModel")
  
  // @ts-expect-error
  .addConditionalEdges("triggerEventModel", triggerEventToolConditional, ["triggerEventToolNode", verificationSetup.name])
  .addEdge("triggerEventToolNode", "triggerEventModel")
  
  .addEdge(verificationSetup.name, "roNode")
  .addEdge(verificationSetup.name, "flNode")
  .addEdge(verificationSetup.name, "lrNode")
  
  .addEdge("roNode", produceRanking.name)
  .addEdge("flNode", produceRanking.name)
  .addEdge("lrNode", produceRanking.name)

  // @ts-expect-error
  .addConditionalEdges(produceRanking.name, loopEndConditional, [verificationSetup.name, sort.name])
  
  .addEdge(sort.name, END)

  .compile();

  export {agent}