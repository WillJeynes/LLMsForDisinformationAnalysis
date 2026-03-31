import { GraphNode } from "@langchain/langgraph";
import { MessagesState, ProposedTriggerEventArray } from "../state";
import { logger } from "../utils/logger";
import { jsonrepair } from 'jsonrepair';

export const verificationSetup: GraphNode<typeof MessagesState> = async (state) => {
  if (state.proposedTriggerEvent == undefined) {
    logger.warn("No trigger events in memory, parsing");

    const genResponse = state.messages.at(-1)?.content.toString() ?? "";

    let repaired: string;
    try {
      repaired = jsonrepair(genResponse);
    } catch (repairErr: any) {
      logger.error("Failed to repair JSON from LLM response.");
      logger.error("Original LLM response:\n%s", genResponse);
      throw new Error(`JSON repair failed: ${repairErr.message}`);
    }

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
          logger.error("No array found in JSON after parsing.");
          logger.error("Repaired JSON:\n%s", repaired);
          logger.error("Original LLM response:\n%s", genResponse);
          throw new Error("No array found in JSON structure");
        }
      }
    } catch (parseErr: any) {
      logger.error("Failed to parse LLM response to JSON or validate array.");
      logger.error("Repaired JSON:\n%s", repaired);
      logger.error("Original LLM response:\n%s", genResponse);
      throw new Error(`Parsing failed: ${parseErr.message}`);
    }

    return { proposedTriggerEvent: parsed, proposedTriggerEventIndex: 0 };
  } else {
    logger.info("Trigger event index %s", state.proposedTriggerEventIndex + 1);

    return { proposedTriggerEvent: state.proposedTriggerEvent, proposedTriggerEventIndex: state.proposedTriggerEventIndex + 1 };
  }
};