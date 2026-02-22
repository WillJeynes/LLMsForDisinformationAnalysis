import fs from "fs";

export function writeToJSONL(path: string, line: any) {
    fs.appendFileSync(`../data/${path}`, JSON.stringify(line) + "\n", "utf-8");
}