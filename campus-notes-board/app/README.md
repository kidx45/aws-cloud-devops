# Campus Notes Board: the starter app

A small Flask application that lets users upload PDF notes, list them and download them.
PDFs are stored in a private S3 bucket and the note details in MySQL (RDS).

You do not need to change any code to complete the project. The work is on the AWS side.
If you want to change the app or replace it with your own code, you may, as long as it still meets the requirements in the brief.

## What is in this folder

| File | Purpose |
|---|---|
| `app.py` | The whole application (routes, database, S3) |
| `templates/`, `static/` | The web pages and stylesheet |
| `requirements.txt` | Python dependencies |
| `schema.sql` | The `notes` table. You create it yourself from EC2 |
| `.env.example` | The settings the app needs (names only) |

## Settings

The app reads everything from environment variables and refuses to start if a required one is missing.

| Variable | Required | Meaning |
|---|---|---|
| `DB_HOST` | yes | RDS endpoint |
| `DB_PORT` | no (3306) | Database port |
| `DB_NAME` | yes | Database name |
| `DB_USER` | yes | Application database user |
| `DB_PASSWORD` | yes | That user's password |
| `S3_BUCKET` | yes | Bucket for the PDFs |
| `AWS_REGION` | yes | Region of the bucket |
| `MAX_UPLOAD_MB` | no (10) | Largest PDF accepted |
| `DB_SSL_CA` | no | Path to a CA bundle, only if you choose to use TLS for MySQL |

There are no AWS access keys anywhere. `boto3` finds the temporary credentials of the IAM role attached to the instance.

## Running it on your EC2 instance

Install the tools and the dependencies (Ubuntu):

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Load your settings into the shell, then start the app in the foreground to check that it works:

```bash
set -a; . /path/to/your/notes.env; set +a
venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 --access-logfile - app:app
```

The app listens on port 8000 on the local machine only. A non-root process cannot use port 80, and the brief asks you to put nginx in front. Turning this command into a service that survives a reboot is your task (project brief, Section 7).

## Pages

| Path | What it does |
|---|---|
| `/` | Upload form and the list of notes |
| `/upload` | Receives the form (POST) |
| `/download/<id>` | Streams the PDF from S3 through the app |
| `/health` | Plain-text status of the app, the database and S3 |

`/health` returns HTTP 503 when the database or S3 is unhealthy. The S3 line uses `HeadBucket`, which needs `s3:ListBucket`. If your role does not have that permission, the line says so, and uploads and downloads can still work.

## Good to know

- **Logs:** everything is written to standard output, including the full error behind any failure. On a systemd service, read it with `journalctl -u <your-service-name>`.
- **Timeouts:** database connections give up after 5 seconds and S3 calls after about 5 seconds to connect. A blocked network path shows up quickly rather than hanging.
- **S3 keys:** the app generates them (`notes/<random>.pdf`). The user's file name is never used. Every key starts with `notes/`.
- **S3 operations the app calls:** `PutObject` when uploading, `GetObject` when downloading, and `HeadBucket` on `/health` only. Decide what your IAM policy needs from that.
- **Upload checks:** PDF only (extension and file signature), size limit, required fields, parameterised SQL.
- **Order of an upload:** the app checks the database connection first, then writes to S3, then inserts the row.

## Limitations of the starter (list the relevant ones in your README)

- No login. Anyone who can reach the app can upload and download.
- No delete or edit.
- No protection against repeated uploads (no rate limit, no CSRF token).
- If the database insert fails after the file reached S3, the object is left behind. The role in the brief has no delete permission, so the app does not try to clean up.
- Plain HTTP only.
