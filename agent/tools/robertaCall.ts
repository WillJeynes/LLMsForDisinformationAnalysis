import axios from "axios";

export async function evaluateWithRoberta({
  answer
}: {
  answer: string;
}) {
  const res = await axios.post("http://localhost:8000/evaluate", {
    answer
  });
  // console.log(res.data)
  const validProb = res.data["probabilities"][0][0]
  const invalidProv = res.data["probabilities"][0][1]

  return validProb > invalidProv ? 1 : 0;
}

// let res = await evaluateWithRoberta({answer: "High-profile political downplaying of COVID-19 (examples: President Trump saying 'it will go away' in March–August 2020)"});
// console.log(res)

// res = await evaluateWithRoberta({answer: "Multiple mirrored reuploads (2020–2023) put the clip on other channels with titles implying it was a genuine 1970s public information film."});
// console.log(res)