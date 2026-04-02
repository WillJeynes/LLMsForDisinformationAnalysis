import axios from "axios";

export async function evaluateWithEnsemble({
  answer,
  method
}: {
  answer: string;
  method: string
}): Promise<{ validProb: number; invalidProb: number; }> {
    const res = await axios.post(process.env.RANKING_URL ?? "http://localhost:8000/evaluate", {
    answer,
    method
  }, {timeout: 0});
  // console.log(res.data)
  const validProb = res.data["probabilities"][0][0]
  const invalidProb = res.data["probabilities"][0][1] + res.data["probabilities"][0][2]

  return {validProb, invalidProb};
}

// import dotenv from "dotenv";

// dotenv.config();

// let res = await evaluateWithEnsemble({method:"flan" ,answer: "High-profile political downplaying of COVID-19 (examples: President Trump saying 'it will go away' in March–August 2020)"});
// console.log(res)

// res = await evaluateWithEnsemble({method:"roberta" ,answer: "Multiple mirrored reuploads (2020–2023) put the clip on other channels with titles implying it was a genuine 1970s public information film."});
// console.log(res)

// res = await evaluateWithEnsemble({method:"logreg" ,answer: "The COVID-19 Pandemic"});
// console.log(res)