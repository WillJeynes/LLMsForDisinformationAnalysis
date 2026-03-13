import { END, START, StateGraph } from "@langchain/langgraph";
import { MessagesState } from "./state";
import { verificationSetup } from "./nodes/verificationSetup";
import { ragasMetrics } from "./nodes/ragasMetrics";
import { produceRanking } from "./nodes/produceRanking";
import { createModelNode } from "./nodes/model";
import { loopEndConditional } from "./conditionals/loop_end";
import { sort } from "./nodes/sort";
import { robertaMetrics } from "./nodes/robertaMetrics";

const verificationModel = createModelNode([], "verify.txt");
const relationModel = createModelNode([], "relation.txt");

const agent = new StateGraph(MessagesState)
  
  //NODES
  .addNode(verificationSetup.name, verificationSetup)
  // .addNode("verificationModel", verificationModel)
  // .addNode(ragasMetrics.name, ragasMetrics)
  .addNode(robertaMetrics.name, robertaMetrics)
  // .addNode("relationModel", relationModel)
  
  .addNode(produceRanking.name, produceRanking)
  .addNode(sort.name, sort)
  
  .addEdge(START, verificationSetup.name)
  // .addEdge(verificationSetup.name, "verificationModel")
  // .addEdge(verificationSetup.name, ragasMetrics.name)
  .addEdge(verificationSetup.name, robertaMetrics.name)
  // .addEdge(verificationSetup.name, "relationModel")

  // .addEdge(ragasMetrics.name, produceRanking.name)
  .addEdge(robertaMetrics.name, produceRanking.name)
  // .addEdge("verificationModel", produceRanking.name)
  // .addEdge("relationModel", produceRanking.name)

  // @ts-expect-error
  .addConditionalEdges(produceRanking.name, loopEndConditional, [verificationSetup.name, sort.name])
  
  .addEdge(sort.name, END)

  .compile();

  export {agent}