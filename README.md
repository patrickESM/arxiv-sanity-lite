
# arxiv-sanity-lite

> **Changes in this fork:** Added a ready-to-use Docker Compose setup with a
> persistent data volume, automatic first-run database initialization, a
> Gunicorn web service on `http://localhost:5000`, and a separate updater
> container that checks arXiv every 24 hours and recomputes TF-IDF features
> whenever papers change. Both containers use `restart: unless-stopped`. This
> fork also adds an optional historical topic importer for human shape and mesh
> recovery (Anny-One, BEDLAM, SMPL/SMPL-X), 6DoF object pose estimation, and
> scatter-radiation estimation in medical imaging.

A much lighter-weight arxiv-sanity from-scratch re-write. Periodically polls arxiv API for new papers. Then allows users to tag papers of interest, and recommends new papers for each tag based on SVMs over tfidf features of paper abstracts. Allows one to search, rank, sort, slice and dice these results in a pretty web UI. Lastly, arxiv-sanity-lite can send you daily emails with recommendations of new papers based on your tags. Curate your tags, track recent papers in your area, and don't miss out!

I am running a live version of this code on [arxiv-sanity-lite.com](https://arxiv-sanity-lite.com).

![Screenshot](screenshot.jpg)

#### To run

##### Docker Compose (easiest)

Build and start the application with:

```bash
docker compose up --build
```

Then open <http://localhost:5000>. On the first start the container downloads
the latest 100 matching arXiv papers and computes their TF-IDF features. The
initial startup can therefore take a few minutes. The database is kept in the
named Docker volume `arxiv-sanity-data` and is reused on subsequent starts.

The Compose stack also starts an `updater` service. It checks arXiv once after
the initial feature database is ready and then every 24 hours. If papers have
changed, it recomputes the TF-IDF features. Both services use `restart:
unless-stopped`, so they start again automatically with Docker unless they were
explicitly stopped.

The initial number of papers and the host port can be changed if desired:

```bash
ARXIV_FETCH_NUM=1000 ARXIV_SANITY_PORT=8080 docker compose up --build
```

The updater fetches up to 2000 entries per check. Its batch size and interval
(in seconds) can be changed if desired:

```bash
ARXIV_UPDATE_FETCH_NUM=1000 ARXIV_UPDATE_INTERVAL=43200 docker compose up -d
```

Updater activity can be followed with:

```bash
docker compose logs -f updater
```

This fork also includes an optional historical topic import for human shape
and mesh recovery (including Anny-One and BEDLAM), 6DoF object pose
estimation, and scatter-radiation estimation in medical imaging. It imports
matching arXiv metadata and recomputes the TF-IDF features when needed:

```bash
docker compose --profile tools run --rm topic-importer
```

By default, up to 2000 results are considered per topic. This can be changed
with `ARXIV_TOPIC_MAX`.

##### Without Docker

To run this locally I usually run the following script to update the database with any new papers. I typically schedule this via a periodic cron job:

```bash
#!/bin/bash

python3 arxiv_daemon.py --num 2000

if [ $? -eq 0 ]; then
    echo "New papers detected! Running compute.py"
    python3 compute.py
else
    echo "No new papers were added, skipping feature computation"
fi
```

You can see that updating the database is a matter of first downloading the new papers via the arxiv api using `arxiv_daemon.py`, and then running `compute.py` to compute the tfidf features of the papers. Finally to serve the flask server locally we'd run something like:

```bash
export FLASK_APP=serve.py; flask run
```

All of the database will be stored inside the `data` directory. Finally, if you'd like to run your own instance on the interwebs I recommend simply running the above on a [Linode](https://www.linode.com), e.g. I am running this code currently on the smallest "Nanode 1 GB" instance indexing about 30K papers, which costs $5/month.

(Optional) Finally, if you'd like to send periodic emails to users about new papers, see the `send_emails.py` script. You'll also have to `pip install sendgrid`. I run this script in a daily cron job.

#### Requirements

 Install via requirements:

 ```bash
 pip install -r requirements.txt
 ```

#### Todos

- Make website mobile friendly with media queries in css etc
- The metas table should not be a sqlitedict but a proper sqlite table, for efficiency
- Build a reverse index to support faster search, right now we iterate through the entire database

#### License

MIT
