#!/usr/bin/env bash

set -e

run_agent () {
    echo "Starting LangGraph agent..."
    cd agent
    npx @langchain/langgraph-cli dev
}

run_ragas_service () {
    echo "Starting RAGAS service..."
    cd "supporting/RAGAS_Service"
    .venv/bin/uvicorn ragas_service:app --port 8001
}

run_frontend () {
    echo "Starting frontend (Streamlit)..."
    cd "supporting/scorer"
    .venv/bin/streamlit run display.py
}

run_fetch () {
    echo "Running fetch job..."
    cd "supporting/dbkf"
    python fetch.py
}

run_wrapper () {
    echo "Running wrapper..."
    cd "supporting/Wrapper"
    npm run dev
}

run_analysis () {
    cd supporting/scorer
    python analyse.py
}

case "$1" in
    agent) run_agent ;;
    ragas_service) run_ragas_service ;;
    frontend) run_frontend ;;
    fetch) run_fetch ;;
    wrapper) run_wrapper ;;
    analysis) run_analysis ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: ./runproject [agent|ragas_service|frontend|fetch|wrapper|analysis]"
        exit 1
        ;;
esac
