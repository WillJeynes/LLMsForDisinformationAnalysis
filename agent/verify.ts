import { END, START, StateGraph } from "@langchain/langgraph";
import { MessagesState } from "./state";
import { verificationSetup } from "./nodes/verificationSetup";
import { produceRanking } from "./nodes/produceRanking";
import { loopEndConditional } from "./conditionals/loop_end";
import { sort } from "./nodes/sort";
import { createEnsembleNode } from "./nodes/ensembleNode";

const roNode = createEnsembleNode("ROBERTA", "roberta");
const flNode = createEnsembleNode("FLAN", "flan");
const lrNode = createEnsembleNode("REGRESSION", "logreg");

const agent = new StateGraph(MessagesState)
  
  //NODES
  .addNode(verificationSetup.name, verificationSetup)
  .addNode("roNode", roNode)
  .addNode("flNode", flNode)
  .addNode("lrNode", lrNode)
  
  .addNode(produceRanking.name, produceRanking)
  .addNode(sort.name, sort)
  
  .addEdge(START, verificationSetup.name)
  
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