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
import { selfEvalSetup } from "./nodes/selfEvalSetup";

const triggerEventToolNode = createToolNode(triggerEventToolsByName);
const peToolNode = createToolNode(triggerEventToolsByName);

const normalisationModel = createModelNode([], "normalization.txt");
const triggerEventModel = createModelNode(triggerEventToolsByName, "trigger.txt");
const evaluationModel = createModelNode([], "eval.txt");
const peModel = createModelNode(triggerEventToolsByName, "posteval.txt");

const triggerEventToolConditional = createToolConditional("triggerEventToolNode", selfEvalSetup.name);
const peToolConditional = createToolConditional("peToolNode", verificationSetup.name);

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

  .addNode(selfEvalSetup.name, selfEvalSetup)
  .addNode("evaluationModel", evaluationModel)
  
  .addNode("peToolNode", peToolNode)
  .addNode("peModel", peModel)

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
  .addConditionalEdges("triggerEventModel", triggerEventToolConditional, ["triggerEventToolNode", selfEvalSetup.name])
  .addEdge("triggerEventToolNode", "triggerEventModel")
  
  .addEdge(selfEvalSetup.name, "evaluationModel")
  .addEdge("evaluationModel", "peModel")

  // @ts-expect-error
  .addConditionalEdges("peModel", peToolConditional, ["peToolNode", verificationSetup.name])
  .addEdge("peToolNode", "peModel")
  
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