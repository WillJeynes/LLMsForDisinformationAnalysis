#!/usr/bin/env bash

set -e

run_agent () {
    echo "Starting LangGraph agent..."
    cd agent
    npx @langchain/langgraph-cli dev --host 127.0.0.1
}

run_ensemble_service () {
    echo "Starting Ensemble service..."
    cd "supporting/RAGAS_Service"
    .venv/bin/uvicorn ensemble_service:app --timeout-keep-alive 300
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

case "$1" in
    agent) run_agent ;;
    ensemble_service) run_ensemble_service ;;
    frontend) run_frontend ;;
    fetch) run_fetch ;;
    wrapper) run_wrapper ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: ./runproject [agent|ensemble_service|frontend|fetch|wrapper]"
        exit 1
        ;;
esac
