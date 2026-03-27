import { GraphNode } from "@langchain/langgraph";
import { MessagesState, ProposedTriggerEventArray } from "../state";
import { logger } from "../utils/logger";
import { jsonrepair } from 'jsonrepair'

export const verificationSetup: GraphNode<typeof MessagesState> = async (state) => {
  //this is kinda doing two things, but having two nodes for it seems overkill

  if (state.proposedTriggerEvent == undefined) {
    logger.warn("No trigger events in memory, parsing")

    let genResponse = state.messages.at(-1)?.content.toString() ?? "";

    const repaired = jsonrepair(genResponse);

    let parsed;

    try {
      const json = JSON.parse(repaired);

      if (Array.isArray(json)) {
        parsed = ProposedTriggerEventArray.parse(json);
      } else {
        // try grab first value
        const firstValue = Object.values(json)[0];

        if (Array.isArray(firstValue)) {
          parsed = ProposedTriggerEventArray.parse(firstValue);
        } else {
          throw new Error("No array found in JSON");
        }
      }
    } catch (err: any) {
      logger.error(`Failed to parse LLM response: ${err.message}`);
      throw new Error(`Failed to parse LLM response: ${err}`);
    }
    
    return { proposedTriggerEvent: parsed, proposedTriggerEventIndex: 0 };
  }
  else {
    logger.info("Trigger event index %s", state.proposedTriggerEventIndex+1)
    
    return { proposedTriggerEvent: state.proposedTriggerEvent, proposedTriggerEventIndex: state.proposedTriggerEventIndex+1 };
  }
};