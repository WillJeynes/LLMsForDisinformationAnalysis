import { Client } from "@langchain/langgraph-sdk";

// only set the apiUrl if you changed the default port when calling langgraph dev
const client = new Client({ apiUrl: "http://localhost:2024"});
const thread = await client.threads.create();

const streamResponse = client.runs.stream(
  thread["thread_id"],
  "agent", 
  {
    input: {
      "messages": ["3+5" ]
    },
    streamMode: "messages-tuple",
  }
);

for await (const chunk of streamResponse) {
  console.log(`Receiving new event of type: ${chunk.event}...`);
  console.log(JSON.stringify(chunk.data));
  console.log("\n\n");
}