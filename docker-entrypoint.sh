#!/bin/sh
set -eu

mkdir -p data

fetch_papers() {
    num="${ARXIV_FETCH_NUM:-100}"
    echo "Fetching up to ${num} papers from arXiv..."
    python arxiv_daemon.py --num "${num}"
}

if [ ! -f data/features.p ]; then
    echo "No feature database found; initializing arxiv-sanity-lite."
    fetch_papers
    python compute.py
elif [ "${ARXIV_UPDATE_ON_START:-0}" = "1" ]; then
    if fetch_papers; then
        echo "Paper database changed; recomputing TF-IDF features."
        python compute.py
    else
        echo "No new papers found; keeping the existing features."
    fi
fi

exec "$@"
