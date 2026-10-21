from datetime import datetime, timezone
import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email import Email
from app.models.thread import EmailThread
from app.models.sync_run import SyncRun
from app.services.gmail_service import list_recent_messages
from app.services.classification_service import ClassificationService

logger = logging.getLogger(__name__)

FALLBACK_SUMMARY = "Analyse automatique indisponible."


def _is_classified(email: Email) -> bool:
    return bool(
        email.category
        and email.summary
        and email.summary.strip()
        and email.summary.strip() != FALLBACK_SUMMARY
    )


def sync_gmail(db: Session, max_results: int = 10) -> dict:
    run = SyncRun(status="running", imported_count=0)
    db.add(run)
    db.commit()
    db.refresh(run)
    run_id = run.id

    imported = 0
    skipped = 0
    classified = 0
    already_classified = 0
    failed = 0

    try:
        messages = list_recent_messages(max_results=max_results)
    except Exception as exc:
        logger.exception("Impossible de récupérer les messages Gmail")
        run = db.get(SyncRun, run_id)
        if run:
            run.status = "failed"
            run.error = str(exc)[:4000]
            run.finished_at = datetime.utcnow()
            db.commit()
        raise

    for index, message in enumerate(messages):
        try:
            gmail_id = message["gmail_message_id"]

            email = db.scalar(
                select(Email).where(Email.gmail_message_id == gmail_id)
            )

            if email is not None:
                skipped += 1

                if _is_classified(email) and email.status != "à vérifier":
                    already_classified += 1
                    continue
            else:
                thread = db.scalar(
                    select(EmailThread).where(
                        EmailThread.gmail_thread_id
                        == message["gmail_thread_id"]
                    )
                )

                if thread is None:
                    thread = EmailThread(
                        gmail_thread_id=message["gmail_thread_id"],
                        subject=message.get("subject", ""),
                    )
                    db.add(thread)
                    db.flush()

                timestamp = message.get("internal_date")
                received_at = (
                    datetime.fromtimestamp(
                        int(timestamp) / 1000,
                        tz=timezone.utc,
                    ).replace(tzinfo=None)
                    if timestamp
                    else datetime.utcnow()
                )

                email = Email(
                    gmail_message_id=gmail_id,
                    thread_id=thread.id,
                    sender=message.get("sender", ""),
                    recipients=message.get("recipients", ""),
                    subject=message.get("subject", ""),
                    body=message.get("body", ""),
                    received_at=received_at,
                    category="autre",
                    priority=2,
                    status="à traiter",
                )
                db.add(email)
                db.commit()
                db.refresh(email)
                imported += 1

            try:
                ClassificationService(db).classify_email(email.id)
                db.commit()

                email = db.get(Email, email.id)
                if email and _is_classified(email):
                    classified += 1
                    if email.status == "à vérifier":
                        email.status = "à traiter"
                    db.commit()
                else:
                    failed += 1
                    if email:
                        email.status = "à vérifier"
                    db.commit()

            except Exception as exc:
                db.rollback()
                logger.exception(
                    "Échec de classification pour le message Gmail %s",
                    gmail_id,
                )
                failed += 1

                email = db.scalar(
                    select(Email).where(Email.gmail_message_id == gmail_id)
                )
                if email:
                    email.status = "à vérifier"
                    db.commit()

        except Exception:
            db.rollback()
            logger.exception("Échec du traitement d'un message Gmail")
            failed += 1

        if index < len(messages) - 1:
            time.sleep(0.5)

    run = db.get(SyncRun, run_id)
    if run:
        run.status = "partial" if failed else "success"
        run.imported_count = imported
        run.finished_at = datetime.utcnow()
        run.error = f"{failed} message(s) en échec" if failed else None
        db.commit()

    return {
        "status": "partial" if failed else "success",
        "fetched": len(messages),
        "imported": imported,
        "skipped_duplicates": skipped,
        "classified": classified,
        "already_classified": already_classified,
        "failed": failed,
        "sync_run_id": run_id,
    }

