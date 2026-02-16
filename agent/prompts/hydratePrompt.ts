import fs from "fs";
import { queryScraper } from "../tools/webSearch";
import { rankAndDisplayData } from "../tools/triggerEventTools";

export async function hydratePrompt(path: string, state: any) : Promise<string> {
    // TODO: expand into full context-based replacement engine

    let raw = fs.readFileSync("prompts/" + path, "utf-8");

    raw = raw.replace("###TITLE###", state.disinformationTitle);
    raw = raw.replace("###LM###", state.messages.at(-1).content);
    raw = raw.replace("###NTITLE###", state.normalizedClaim);

    if (raw.indexOf("###TECLAIM###") != -1) {
        const title = state.proposedTriggerEvent[state.proposedTriggerEventIndex].Event
        raw = raw.replace("###TECLAIM###", title)
    }

    if (raw.indexOf("###TESEARCH###") != -1) {
        const output = state.proposedTriggerEvent[state.proposedTriggerEventIndex].context
        raw = raw.replace("###TESEARCH###", output)
    }

    return raw;
}
