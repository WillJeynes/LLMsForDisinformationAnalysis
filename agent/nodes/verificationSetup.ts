import { GraphNode } from "@langchain/langgraph";
import { MessagesState, ProposedTriggerEventArray } from "../state";
import { logger } from "../utils/logger";

export const verificationSetup: GraphNode<typeof MessagesState> = async (state) => {
  //this is kinda doing two things, but having two nodes for it seems overkill
  console.log(state.proposedTriggerEvent)
  console.log(state.proposedTriggerEventIndex)
  if (state.proposedTriggerEvent == undefined) {
    logger.warn("No trigger events in memory, parsing")

    let genResponse = state.messages.at(-1)?.content.toString() ?? "";
    const parsed = ProposedTriggerEventArray.parse(JSON.parse(genResponse));

    return { proposedTriggerEvent: parsed, proposedTriggerEventIndex: 0 };
  }
  else {
    logger.info("Trigger event index %s", state.proposedTriggerEventIndex+1)
    
    return { proposedTriggerEvent: state.proposedTriggerEvent, proposedTriggerEventIndex: state.proposedTriggerEventIndex+1 };
  }
};