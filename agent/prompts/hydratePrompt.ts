import fs from "fs";

export function hydratePrompt(path: string, state: any) {
    // TODO: expand into full context-based replacement engine

    let raw = fs.readFileSync("prompts/" + path, "utf-8");

    raw = raw.replace("###TITLE###", state.disinformationTitle);
    raw = raw.replace("###LM###", state.messages.at(-1).content);

    return raw;
}
