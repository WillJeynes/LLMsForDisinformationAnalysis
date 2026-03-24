import { GraphNode } from "@langchain/langgraph";
import { MessagesState } from "../state";
import { AIMessage } from "@langchain/core/messages";
import { evaluateWithRoberta } from "../tools/robertaCall";

export const robertaMetrics: GraphNode<typeof MessagesState> = async (state) => {
  const answer = state.proposedTriggerEvent[state.proposedTriggerEventIndex].Event
  
  const lrresult = await evaluateWithRoberta({answer, method:"logreg"})
  const lrscore = lrresult.validProb - lrresult.invalidProb;
  
  const roresult = await evaluateWithRoberta({answer, method:"roberta"})
  const roscore = roresult.validProb - roresult.invalidProb;
  
  const flresult = await evaluateWithRoberta({answer, method:"flan"})
  const flscore = flresult.validProb - flresult.invalidProb;
  
  //Option 1: combining scores
  // const score = lrscore * 0.3 + roscore * 0.5 + flscore * 0.3

  //Option 2: majority voting
  const rovote = roscore > 0.6
  const flvote = flscore > 0.94
  const lrvote = lrscore > 0.75

  let counter = 0
  if (rovote) counter++
  if (flvote) counter++
  if (lrvote) counter++

  let score = 0
  if (counter >= 2) {
    score = 0.7 + lrscore + flscore + lrscore
  }
  
  return {
    messages: [ new AIMessage("ROBERTA:" + score)]
  };
};