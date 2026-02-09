import axios from "axios";

export async function evaluateWithRagas({
  question,
  answer,
  contexts,
}: {
  question: string;
  answer: string;
  contexts: string[];
}) {
  const res = await axios.post("http://localhost:8001/evaluate", {
    question,
    answer,
    contexts,
  });

  return res.data;
}

// let res = await evaluateWithRagas({question: "Who was Bill Nye", answer: "Bill Nye was a Scientist", contexts: ["Bill nye was a Scientist"]});
// console.log(res)