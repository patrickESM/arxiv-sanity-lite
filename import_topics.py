"""Import historical arXiv papers for selected topic areas."""

import logging
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

import feedparser

from aslite.arxiv import parse_response
from aslite.db import get_metas_db, get_papers_db


TOPICS = {
    "human-shape": (
        'all:"human mesh recovery" OR all:"human pose and shape" OR '
        'all:"human body reconstruction" OR all:"human shape estimation" OR '
        'all:SMPL OR all:SMPL-X OR all:BEDLAM OR all:Anny-One OR all:Anny-Fit'
    ),
    "6dof-pose": (
        'all:"6DoF pose estimation" OR all:"6-DoF pose estimation" OR '
        'all:"6D object pose" OR all:"six degree of freedom pose" OR '
        'all:"object pose estimation"'
    ),
    "scatter-radiation": (
        '(all:"scatter radiation" OR all:"scattered radiation" OR '
        'all:"scatter estimation" OR all:"scatter prediction" OR '
        'all:"scatter correction") AND '
        '(all:X-ray OR all:radiography OR all:tomography OR all:CT OR '
        'all:fluoroscopy OR all:"medical imaging")'
    ),
}

BATCH_SIZE = 100
MAX_PER_TOPIC = int(os.environ.get("ARXIV_TOPIC_MAX", "2000"))


def fetch(query, start):
    params = urllib.parse.urlencode({
        "search_query": query,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
        "start": start,
        "max_results": BATCH_SIZE,
    })
    url = "https://export.arxiv.org/api/query?" + params
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    pdb = get_papers_db(flag="c")
    mdb = get_metas_db(flag="c")
    total_added = 0
    total_updated = 0

    try:
        initial_count = len(pdb)

        for topic, query in TOPICS.items():
            seen = 0
            added = 0
            updated = 0

            for start in range(0, MAX_PER_TOPIC, BATCH_SIZE):
                logging.info("%s: fetching results %d-%d", topic, start, start + BATCH_SIZE)
                raw = fetch(query, start)
                feed = feedparser.parse(raw)
                papers = parse_response(raw)

                if start == 0:
                    available = int(feed.feed.get("opensearch_totalresults", len(papers)))
                    logging.info("%s: arXiv reports %d matching papers", topic, available)

                if not papers:
                    break

                for paper in papers:
                    pid = paper["_id"]
                    if pid not in pdb:
                        pdb[pid] = paper
                        mdb[pid] = {"_time": paper["_time"]}
                        added += 1
                    elif paper["_time"] > pdb[pid]["_time"]:
                        pdb[pid] = paper
                        mdb[pid] = {"_time": paper["_time"]}
                        updated += 1

                seen += len(papers)
                if len(papers) < BATCH_SIZE:
                    break
                time.sleep(3)

            total_added += added
            total_updated += updated
            logging.info(
                "%s complete: seen=%d added=%d updated=%d",
                topic,
                seen,
                added,
                updated,
            )

        logging.info(
            "all topics complete: before=%d after=%d added=%d updated=%d",
            initial_count,
            len(pdb),
            total_added,
            total_updated,
        )
    finally:
        pdb.close()
        mdb.close()

    if total_added or total_updated:
        logging.info("paper database changed; recomputing TF-IDF features")
        subprocess.run([sys.executable, "compute.py"], check=True)
    else:
        logging.info("no paper changes; keeping existing TF-IDF features")


if __name__ == "__main__":
    main()
