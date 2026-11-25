# Campus Notes Board

> This README is yours to write. Replace every line in italics with your own content, then delete this note.
> The sections match Section 14 of the project brief. Describe **your** implementation, not the brief's.

## 1. Overview and architecture diagram

_What you built, in a short paragraph. Then embed your architecture diagram, for example `![Architecture](screenshots/architecture.png)`._

## 2. Prerequisites

_What someone needs before they can repeat your deployment: AWS account setup, Region, the IAM user you work as, tools._

## 3. Deployment steps

_The steps you followed to get from an empty VPC to a running app: EC2, service user, systemd service, nginx. Include the commands._

## 4. Configuration variables

Names only. Never put real values in this file.

| Variable | Meaning |
|---|---|
| `DB_HOST` | RDS endpoint |
| `DB_PORT` | Database port |
| `DB_NAME` | Database name |
| `DB_USER` | Application database user |
| `DB_PASSWORD` | Password for that user (kept in an env file outside Git) |
| `S3_BUCKET` | Bucket for the PDFs |
| `AWS_REGION` | Region of the bucket |
| `MAX_UPLOAD_MB` | Largest PDF accepted (optional) |

_Add where your env file lives, its owner and its permissions._

## 5. Database and S3 setup

_How you created the database, the application user and its privileges, the `notes` table, and the bucket settings (Block Public Access, ownership, encryption)._

## 6. Security

_Your security groups (app-sg, db-sg), why RDS is private, your IAM role and its policy explained line by line, and how the app gets AWS credentials without access keys._

## 7. Evidence

_Link your screenshots: alarm triggered, CloudTrail event, end-to-end test, direct S3 URL returning 403._

## 8. Known limitations, cost and cleanup

_Limitations (the starter's own list is in `app/README.md`; keep the ones that apply and add yours). Your monthly cost estimate and what it actually cost. How you cleaned up._
