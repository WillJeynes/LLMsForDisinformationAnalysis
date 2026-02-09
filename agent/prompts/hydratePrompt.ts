import fs from "fs";

export function hydratePrompt(path: string, replacement: string) {
    // TODO: expand into full context-based replacement engine

    let raw = fs.readFileSync("prompts/" + path, "utf-8");

    return raw.replace("###", replacement)
}