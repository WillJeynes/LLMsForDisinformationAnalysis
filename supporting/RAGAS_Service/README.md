# Classifier work for evaluating model quality

Made using a dataset of 1000 labeled claims from MVP pipeline.

Roberta model trained on an augmented dataset with LLM generated adversarial examples for low frequency labels.

Flan model trained using raw labelled claims, inherrent natural language ability allows for pattern recognition without the need for fake data.

Regression model trained using the roberta dataset.

Used ensemble model in the final version, with the component models available on Hugging Face. 

| Model                                                      | % Correct | % Valid taken forward|Used in ensemble|Link
|------------------------------------------------------------|-----------|----------------------|----------------|-
| Original                                                   | 53.22     | 61.72                |
| Original (RAGAS)                                           | 56.01     | 57.73                |
| Roberta (base)                                             | 75        | 70                   |
| Roberta (Generated Data)                                   | 76        | 71                   |
| Roberta (Generated Data + Back Translation)                | 74        | 71                   |
| Roberta (Generated Data + Back Translation + Thresholding) | 77        | 90                   |Y|[Here](https://huggingface.co/WillJeynes/LLMsForDisinformationAnalysis)
| Distilled Roberta                                          | 72.73     | 69.57                |
| Flan                                                       | 79.17     | 85.71                |Y|[Here](https://huggingface.co/WillJeynes/LLMsForDisinformationAnalysis-Flan)
| Simple Regression Model                                    | 74.77     | 85.71                |Y|[Here](https://huggingface.co/WillJeynes/LLMsForDisinformationAnalysis-Regression)
| Ensemble Model (weighted confidence score sum)             | 84.21     | 83.33                |
| Ensemble Model (majority voting)                           | 80.2      | 95.12                |