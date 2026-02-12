import {
  StateSchema,
  MessagesValue,
} from "@langchain/langgraph";
import { z } from "zod/v4";

export const ProposedTriggerEvent = z.object({
  Event: z.string(),
  ReasoningWhyRelevant: z.string(),
  SearchQuery: z.string(),
  Url: z.url(),
  IsItselfDisinformation: z.boolean(),
  context: z.string().optional(),
  score: z.number().optional()
})

export const ProposedTriggerEventArray = z.array(ProposedTriggerEvent);

export const MessagesState = new StateSchema({
  disinformationTitle: z.string(),
  messages: MessagesValue,
  proposedTriggerEvent: ProposedTriggerEventArray,
  proposedTriggerEventIndex: z.int(),
});

