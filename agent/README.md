## Refining the agent output

Experiments modifying pipeline

| Model            | % Correct | % Change |
|------------------|----------:|---------:|
| BASELINE         | 33        | 0        |
| Improv Prompt    | 39.96     | 0.21     |
| Add Examples     | 44.67     | 0.35     |
| Date             | 45.51     | 0.38     |
| Chain of Thought | 43.38     | 0.31     |
| Self-Critique    | 44.36     | 0.34     |

Experiments with different model types:
| Model                         | % Correct | % Change |
|-------------------------------|----------:|---------:|
| gpt-5-mini                    | 33        | 0        |
| gpt-5.4-mini                  | 32.4      | -0.02    |
| llama3.1:8b-instruct-q4_K_M   | ?         | ?        |
| qwen3.5:9b                    | 0         | -100     |

%age valid URLS
| Model                         | Number    | % Age    |
|-------------------------------|----------:|---------:|
| gpt-5-mini                    | 22/405    | 5.43     |
| gpt-5.4-mini                  | 29/278    | 10.43    |
| llama3.1:8b-instruct-q4_K_M   | ?         | ?        |
| qwen3.5:9b                    | 0         | 0        |