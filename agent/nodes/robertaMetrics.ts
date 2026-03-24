import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";
import { evaluateWithRoberta } from "../tools/robertaCall";

export const robertaMetrics: GraphNode<typeof MessagesState> = async (state) => {
  const answer = state.proposedTriggerEvent[state.proposedTriggerEventIndex].Event
  
  //Option 1:
  const lrresult = await evaluateWithRoberta({answer, method:"logreg"})
  const lrscore = lrresult.validProb - lrresult.invalidProb;
  
  const roresult = await evaluateWithRoberta({answer, method:"roberta"})
  const roscore = roresult.validProb - roresult.invalidProb;
  
  const flresult = await evaluateWithRoberta({answer, method:"flan"})
  const flscore = flresult.validProb - flresult.invalidProb;
  
  const score = lrscore * 0.3 + roscore * 0.5 + flscore * 0.3
  
  return {
    messages: [ new AIMessage("ROBERTA:" + score)]
  };
};