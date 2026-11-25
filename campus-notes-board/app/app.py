"""Campus Notes Board: starter application for AWS Student Builder Group, Project 01.

A deliberately small Flask app. Users upload a PDF note with a title, course and
description. The PDF goes to a private S3 bucket and the metadata goes to MySQL.

All settings come from environment variables (see .env.example). The app never
holds AWS access keys: boto3 finds the EC2 instance role's temporary credentials
on its own.

Everything the app does is logged to stdout, so on a systemd service you read it
with journalctl.
"""
import logging
import os
import sys
import uuid
from contextlib import contextmanager

import boto3
import pymysql
import pymysql.cursors
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, Response, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

# --------------------------------------------------------------------- logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("notes")

# --------------------------------------------------------------------- settings
REQUIRED_SETTINGS = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "S3_BUCKET", "AWS_REGION"]

_missing = [name for name in REQUIRED_SETTINGS if not os.environ.get(name)]
if _missing:
    _message = "Missing required environment variables: " + ", ".join(_missing)
    log.error(_message)
    raise RuntimeError(_message)


def int_setting(name, default):
    raw = os.environ.get(name, str(default))
    try:
        return int(raw)
    except ValueError:
        message = f"Environment variable {name} must be a whole number (got {raw!r})"
        log.error(message)
        raise RuntimeError(message) from None


DB_HOST = os.environ["DB_HOST"]
DB_PORT = int_setting("DB_PORT", 3306)
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_SSL_CA = os.environ.get("DB_SSL_CA")  # optional: path to a CA bundle to enable TLS
S3_BUCKET = os.environ["S3_BUCKET"]
AWS_REGION = os.environ["AWS_REGION"]
MAX_UPLOAD_MB = int_setting("MAX_UPLOAD_MB", 10)

# Every object key starts with this prefix, so an IAM policy can be scoped to it.
S3_PREFIX = "notes/"

MAX_BYTES = MAX_UPLOAD_MB * 1024 * 1024
TITLE_MAX = 255
COURSE_MAX = 150
DESCRIPTION_MAX = 2000
LIST_LIMIT = 200
DOWNLOAD_CHUNK = 64 * 1024

# --------------------------------------------------------------------- clients
# Short timeouts so a blocked network path fails in seconds, not minutes.
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    config=Config(connect_timeout=5, read_timeout=20, retries={"max_attempts": 2, "mode": "standard"}),
)

DB_ERRORS = (pymysql.MySQLError, OSError)
S3_ERRORS = (ClientError, BotoCoreError)


def connect_db():
    options = dict(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
    )
    if DB_SSL_CA:
        options["ssl"] = {"ca": DB_SSL_CA}
    return pymysql.connect(**options)


@contextmanager
def db_connection():
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()


def describe_db_error(exc):
    """Short, safe description (no host names) for the health page."""
    code = exc.args[0] if exc.args and isinstance(exc.args[0], int) else None
    return f"{type(exc).__name__} {code}" if code is not None else type(exc).__name__


def s3_error_code(exc):
    if isinstance(exc, ClientError):
        return str(exc.response.get("Error", {}).get("Code", "Unknown"))
    return type(exc).__name__


# --------------------------------------------------------------------- the app
app = Flask(__name__)
# Reject oversized requests early (with room for the other form fields).
app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES + 100 * 1024


@app.after_request
def add_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def render_index(message=None, kind="info", form=None, status=200):
    """Render the main page. If the database cannot be used, say so and return 503."""
    notes = []
    db_ok = True
    try:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, course_name, description, created_at "
                "FROM notes ORDER BY created_at DESC, id DESC LIMIT %s",
                (LIST_LIMIT,),
            )
            notes = cur.fetchall()
    except DB_ERRORS as exc:
        db_ok = False
        log.error("Could not list notes (database %s:%s, user %s): %s", DB_HOST, DB_PORT, DB_USER, exc)
        message = "The notes list is unavailable because the database could not be used. Details are in the application log."
        kind, status = "error", 503
    page = render_template(
        "index.html",
        notes=notes,
        db_ok=db_ok,
        message=message,
        kind=kind,
        form=form or {},
        max_mb=MAX_UPLOAD_MB,
    )
    return page, status


def render_error(title, message, status):
    return render_template("error.html", title=title, message=message), status


@app.get("/")
def index():
    if request.args.get("uploaded") == "1":
        return render_index("Note uploaded.", "success")
    return render_index()


# --------------------------------------------------------------------- upload
class UploadError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def read_form():
    return {
        "title": request.form.get("title", "").strip(),
        "course_name": request.form.get("course_name", "").strip(),
        "description": request.form.get("description", "").strip(),
    }


def check_upload(form, file):
    """Validate the form fields and the PDF. Returns the file bytes."""
    if not form["title"]:
        raise UploadError("Enter a title for the note.", 400)
    if len(form["title"]) > TITLE_MAX:
        raise UploadError(f"The title must be {TITLE_MAX} characters or fewer.", 400)
    if not form["course_name"]:
        raise UploadError("Enter the course name.", 400)
    if len(form["course_name"]) > COURSE_MAX:
        raise UploadError(f"The course name must be {COURSE_MAX} characters or fewer.", 400)
    if len(form["description"]) > DESCRIPTION_MAX:
        raise UploadError(f"The description must be {DESCRIPTION_MAX} characters or fewer.", 400)
    if file is None or not file.filename:
        raise UploadError("Choose a PDF file to upload.", 400)
    if not file.filename.lower().endswith(".pdf"):
        raise UploadError("Only PDF files are allowed. The file name must end in .pdf.", 400)

    data = file.read()
    if not data:
        raise UploadError("The file is empty.", 400)
    if len(data) > MAX_BYTES:
        raise UploadError(f"That file is too large. The limit is {MAX_UPLOAD_MB} MB.", 413)
    if not data.startswith(b"%PDF-"):
        raise UploadError("That file does not look like a valid PDF.", 400)
    return data


def store_note(form, data):
    """Save the PDF to S3 and the metadata to MySQL."""
    # Connect to the database first, so a database problem is found before
    # anything is written to S3.
    try:
        conn = connect_db()
    except DB_ERRORS as exc:
        log.error("Upload failed: cannot connect to database %s:%s as %s: %s", DB_HOST, DB_PORT, DB_USER, exc)
        raise UploadError(
            "The database could not be reached, so nothing was saved. Details are in the application log.", 503
        ) from None

    try:
        # The key is generated here. The user's file name is never used.
        key = f"{S3_PREFIX}{uuid.uuid4()}.pdf"
        try:
            s3.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType="application/pdf")
        except S3_ERRORS as exc:
            log.error("Upload failed: S3 PutObject on s3://%s/%s: %s", S3_BUCKET, key, exc)
            raise UploadError(
                "The file could not be stored. Details are in the application log.", 502
            ) from None

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO notes (title, course_name, description, s3_object_key) VALUES (%s, %s, %s, %s)",
                    (form["title"], form["course_name"], form["description"] or None, key),
                )
                note_id = cur.lastrowid
            conn.commit()
        except DB_ERRORS as exc:
            log.error(
                "Upload failed: database insert failed after the file was stored. "
                "Orphaned object left at s3://%s/%s: %s",
                S3_BUCKET,
                key,
                exc,
            )
            raise UploadError(
                "The file was stored but the note could not be saved. Details are in the application log.", 503
            ) from None
    finally:
        conn.close()

    log.info("Stored note id=%s key=%s size=%d bytes", note_id, key, len(data))


@app.post("/upload")
def upload():
    form = read_form()
    try:
        data = check_upload(form, request.files.get("file"))
        store_note(form, data)
    except UploadError as err:
        return render_index(err.message, "error", form, err.status)
    # Redirect after POST so a browser refresh does not upload the note again.
    return redirect(url_for("index", uploaded=1), code=303)


@app.errorhandler(413)
def request_too_large(_exc):
    log.warning("Rejected an upload larger than the %d MB limit", MAX_UPLOAD_MB)
    return render_index(f"That file is too large. The limit is {MAX_UPLOAD_MB} MB.", "error", None, 413)


@app.errorhandler(500)
def server_error(_exc):
    # Flask has already logged the traceback.
    return render_error("Something went wrong", "The application hit an unexpected error. Details are in the application log.", 500)


# --------------------------------------------------------------------- download
@app.get("/download/<int:note_id>")
def download(note_id):
    try:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT title, s3_object_key FROM notes WHERE id = %s", (note_id,))
            row = cur.fetchone()
    except DB_ERRORS as exc:
        log.error("Download of note %s failed: database %s:%s: %s", note_id, DB_HOST, DB_PORT, exc)
        return render_error("Database unavailable", "The note could not be looked up. Details are in the application log.", 503)

    if row is None:
        return render_error("Note not found", "There is no note with that number.", 404)

    key = row["s3_object_key"]
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    except S3_ERRORS as exc:
        code = s3_error_code(exc)
        log.error("Download of note %s failed: S3 GetObject on s3://%s/%s: %s", note_id, S3_BUCKET, key, exc)
        if code in ("NoSuchKey", "404"):
            return render_error("File missing", "This note's PDF is not in storage.", 404)
        return render_error("Storage unavailable", "The PDF could not be retrieved. Details are in the application log.", 502)

    filename = (secure_filename(row["title"]) or "note") + ".pdf"
    body = obj["Body"]

    def stream():
        try:
            yield from body.iter_chunks(DOWNLOAD_CHUNK)
        finally:
            body.close()

    log.info("Download note id=%s key=%s", note_id, key)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if "ContentLength" in obj:
        headers["Content-Length"] = str(obj["ContentLength"])
    return Response(stream(), mimetype="application/pdf", headers=headers)


# --------------------------------------------------------------------- health
@app.get("/health")
def health():
    """Plain-text status of the app and each dependency. Returns 503 if one is down."""
    lines = ["app: ok"]
    healthy = True

    try:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM notes")
            count = cur.fetchone()["n"]
        lines.append(f"database: ok ({count} notes)")
    except DB_ERRORS as exc:
        healthy = False
        log.error("Health check: database %s:%s: %s", DB_HOST, DB_PORT, exc)
        lines.append(f"database: error ({describe_db_error(exc)})")

    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        lines.append("s3: ok")
    except S3_ERRORS as exc:
        code = s3_error_code(exc)
        log.error("Health check: S3 HeadBucket on %s: %s", S3_BUCKET, exc)
        if code in ("403", "AccessDenied"):
            # HeadBucket needs s3:ListBucket. A least-privilege role may not have it,
            # and uploads and downloads can still work. So this is not a failure.
            lines.append("s3: HeadBucket denied (expected without s3:ListBucket; uploads may still work)")
        else:
            healthy = False
            lines.append(f"s3: error ({code})")

    return Response("\n".join(lines) + "\n", status=200 if healthy else 503, mimetype="text/plain")
