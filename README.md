# AI models for identifying trigger events in disinformation analysis
Final Dissertation Submission Repository

## Project Description
-- todo --

## Solution Diagram
-- todo --

## Repository Structure
```
├── run.sh                          # Bash script to run project elements from one place
├── data/                           # Holder from project data
|   ├── blocked.jsonl               # Web search results blocked by the Iffy list
|   ├── error.log                   # Log file containing critical exceptions
|   ├── claims.json                 # Retreived claims from dbkf fetcher
|   ├── dev-eng.csv
|   ├── train-eng.csv               # Normalized disinformation claims in CSV format from CLAN
|   ├── Iffy.json                   # Iffy dataset of disinformation domains
|   ├── input.jsonl                 # Response in cleaned format to give as context to agent
|   ├── ranked.jsonl                # Cleaned trigger event response from scorer frontend
|   └── results.jsonl               # Output from wrapper script, read and modified by scorer
├── literature/
|   └── report.pdf                  # Final submission report
├── agent/                          # Code for main project pipeline
|   ├── agent.ts                    # Graph definition file
|   ├── conditionals/               # Conditional translations
|   ├── prompts/                    # System promps, plus replacement code
|   ├── tools/                      # Internal and LLM facing tools
|   └── utils/                      # Logger
└── supporting/                     
    ├── dbkf/                       # Tool to download claims from DBKF for use in wrapper
    ├── RAGAS_Service               # Small python API to make RAGAS metrics available in the TS projects (required to run pipeline)
    ├── scorer                      # Frontend for labelling data, plus associated analysis
    └── Wrapper                     # Bulk run pipeline on pre-downloaded claims
```
