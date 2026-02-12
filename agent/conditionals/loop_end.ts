import { ConditionalEdgeRouter, END } from "@langchain/langgraph";
import { MessagesState } from "../state";


export const loopEndConditional: ConditionalEdgeRouter<typeof MessagesState, String> = (state) => {
    const triggerEvents = state.proposedTriggerEvent;
    const triggerEventsIndex = state.proposedTriggerEventIndex;

    if (triggerEventsIndex == triggerEvents.length-1) {
      return END
    }
    else {
      return "verificationSetup"
    }
  };

