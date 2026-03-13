import { pipeline, cos_sim } from "@huggingface/transformers";

let featureExtractor = await pipeline(
    "feature-extraction",
    "Xenova/all-MiniLM-L6-v2"
);

export async function removeDuplicates(state: any) {
    const embeddings: number[][] = [];

    const outputs = await featureExtractor(
        state.map(s => s.Event),
        { pooling: "mean", normalize: true }
    );

    for (const o of outputs) {
      embeddings.push(Array.from(o.data));
    }

    const len = state.length;
    for (let i = 0; i < len; i++) {
        for (let j = i + 1; j < len; j++) {
            if (state[i].score === -1 || state[j].score === -1) continue;

            const sim = cos_sim(embeddings[i], embeddings[j]);
            console.log(sim)
            if (sim > 0.55) {
                const scoreI = state[i].score ?? 0;
                const scoreJ = state[j].score ?? 0;

                if (scoreI > scoreJ) {
                    state[j].score = -1;
                } else if (scoreJ > scoreI) {
                    state[i].score = -1;
                } else {
                    // if equal, keep earlier
                    state[j].score = -1;
                }
            }
        }
    }

    return state;
}