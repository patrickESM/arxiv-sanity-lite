#!/bin/sh
set -u

interval="${ARXIV_UPDATE_INTERVAL:-86400}"
fetch_num="${ARXIV_FETCH_NUM:-2000}"

echo "Waiting for the web service to initialize the shared feature database..."
while [ ! -f data/features.p ]; do
    sleep 10
done

while true; do
    echo "Checking arXiv for up to ${fetch_num} new or updated papers..."

    if python arxiv_daemon.py --num "${fetch_num}"; then
        echo "Paper database changed; recomputing TF-IDF features."
        if python compute.py; then
            echo "Feature database updated successfully."
        else
            echo "Feature computation failed; it will be retried after the next paper update."
        fi
    else
        echo "No paper changes detected."
    fi

    echo "Next update check in ${interval} seconds."
    sleep "${interval}"
done
