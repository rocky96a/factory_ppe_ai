import os
import smtplib

from datetime import datetime
from email.message import EmailMessage

from database.db import update_email_status


def send_violation_email(
    violation_id,
    camera_id,
    location,
    tracking_id,
    confidence,
    evidence_path
):
    """
    Send NO HELMET violation email with evidence photo.
    """

    enabled = os.getenv(
        "EMAIL_ENABLED",
        "false"
    ).lower() == "true"

    if not enabled:
        print("EMAIL DISABLED")
        return False

    smtp_host = os.getenv(
        "SMTP_HOST",
        "smtp.gmail.com"
    )

    smtp_port = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    smtp_use_tls = os.getenv(
        "SMTP_USE_TLS",
        "true"
    ).lower() == "true"

    username = os.getenv("EMAIL_USERNAME", "")
    password = os.getenv("EMAIL_PASSWORD", "")
    email_from = os.getenv("EMAIL_FROM", username)
    email_to = os.getenv("EMAIL_TO", "")

    # --------------------------------------------------------
    # CHECK EMAIL CONFIGURATION
    # --------------------------------------------------------

    if not username or not password or not email_to:

        print(
            "EMAIL ERROR: "
            "SMTP credentials are not configured"
        )

        update_email_status(
            violation_id,
            "FAILED"
        )

        return False

    # --------------------------------------------------------
    # CHECK EVIDENCE
    # --------------------------------------------------------

    if not evidence_path:

        print(
            "EMAIL ERROR: "
            "Evidence photo path is empty"
        )

        update_email_status(
            violation_id,
            "FAILED"
        )

        return False

    if not os.path.exists(evidence_path):

        print(
            f"EMAIL ERROR: "
            f"Evidence photo not found: "
            f"{evidence_path}"
        )

        update_email_status(
            violation_id,
            "FAILED"
        )

        return False

    # --------------------------------------------------------
    # EMAIL CONTENT
    # --------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    confidence_percent = round(
        float(confidence) * 100,
        2
    )

    subject = (
        f"NO HELMET ALERT | "
        f"{camera_id} | "
        f"Tracking ID {tracking_id}"
    )

    body = f"""
FACTORY PPE SAFETY VIOLATION

Detection:
NO HELMET

Camera ID:
{camera_id}

Location:
{location}

Tracking ID:
{tracking_id}

Confidence:
{confidence_percent}%

Time:
{timestamp}

The evidence photograph is attached
to this email.

Please check the factory floor.
"""

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to

    message.set_content(body)

    # --------------------------------------------------------
    # ATTACH EVIDENCE PHOTO
    # --------------------------------------------------------

    try:

        with open(
            evidence_path,
            "rb"
        ) as file:

            photo_data = file.read()

        message.add_attachment(
            photo_data,
            maintype="image",
            subtype="jpeg",
            filename=os.path.basename(
                evidence_path
            )
        )

    except Exception as exc:

        print(
            f"EMAIL ERROR: "
            f"Could not attach evidence: {exc}"
        )

        update_email_status(
            violation_id,
            "FAILED"
        )

        return False

    # --------------------------------------------------------
    # SEND EMAIL
    # --------------------------------------------------------

    try:

        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=20
        ) as server:

            if smtp_use_tls:
                server.starttls()

            server.login(
                username,
                password
            )

            server.send_message(
                message
            )

        sent_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        update_email_status(
            violation_id,
            "SENT",
            sent_at
        )

        print(
            f"EMAIL SENT | "
            f"{camera_id} | "
            f"{location} | "
            f"ID {tracking_id}"
        )

        return True

    except Exception as exc:

        print(
            f"EMAIL ERROR: {exc}"
        )

        update_email_status(
            violation_id,
            "FAILED"
        )

        return False