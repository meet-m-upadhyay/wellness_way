"""
Email notification service for WellnessWay.

Subscribes to EventBus events and sends transactional emails via SMTP (Gmail).
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import get_settings
from app.core.events import event_bus, USER_REGISTERED, ADMIN_ACTION_COMPLETED

logger = logging.getLogger(__name__)


# ── Low-level SMTP helper ────────────────────────────────────────────

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP. Returns True on success."""
    settings = get_settings()
    email_cfg = settings.email

    if not email_cfg.enable_notifications:
        logger.info(f"[EMAIL] Notifications disabled – skipping email to {to_email}")
        return False

    if not email_cfg.smtp_user or not email_cfg.smtp_password:
        logger.warning("[EMAIL] SMTP credentials not configured – skipping")
        return False

    from_addr = email_cfg.from_email or email_cfg.smtp_user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"WellnessWay <{from_addr}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(email_cfg.smtp_host, email_cfg.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email_cfg.smtp_user, email_cfg.smtp_password.get_secret_value())
            server.sendmail(from_addr, to_email, msg.as_string())
        logger.info(f"[EMAIL] Sent '{subject}' to {to_email}")
        return True
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send to {to_email}: {e}", exc_info=True)
        return False


# ── HTML email templates ─────────────────────────────────────────────

def _admin_new_user_html(user_email: str, user_name: str) -> str:
    """HTML body for the admin notification when a new user registers."""
    settings = get_settings()
    dashboard_url = f"{settings.email.app_base_url}/admin"
    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8faf9; border-radius: 12px; padding: 32px;">
        <h2 style="color: #059669; margin-top: 0;">🆕 New Registration Request</h2>
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">
            A new user has requested access to <strong>WellnessWay</strong>:
        </p>
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
            <tr>
                <td style="padding: 8px 12px; background: #ecfdf5; border-radius: 6px; font-weight: 600; color: #065f46; width: 100px;">Name</td>
                <td style="padding: 8px 12px; color: #374151;">{user_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px 12px; background: #ecfdf5; border-radius: 6px; font-weight: 600; color: #065f46;">Email</td>
                <td style="padding: 8px 12px; color: #374151;">{user_email}</td>
            </tr>
        </table>
        <p style="margin-top: 24px;">
            <a href="{dashboard_url}" style="display: inline-block; background: #059669; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                Open Admin Dashboard
            </a>
        </p>
        <p style="color: #9ca3af; font-size: 12px; margin-top: 24px;">
            This is an automated notification from WellnessWay.
        </p>
    </div>
    """


def _user_decision_html(user_name: str, status: str, note: Optional[str] = None) -> str:
    """HTML body for the user notification about their approval/rejection."""
    settings = get_settings()
    is_approved = status == "approved"
    heading = "✅ Access Approved!" if is_approved else "❌ Access Declined"
    colour = "#059669" if is_approved else "#dc2626"
    message = (
        "Your registration has been approved. You can now sign in and start using WellnessWay!"
        if is_approved
        else "Unfortunately, your registration request has been declined."
    )
    login_url = f"{settings.email.app_base_url}/login"

    note_block = ""
    if note:
        note_block = f"""
        <div style="background: #f3f4f6; border-left: 4px solid {colour}; padding: 12px 16px; border-radius: 6px; margin: 16px 0;">
            <p style="margin: 0; font-size: 13px; color: #6b7280; font-weight: 600;">Note from admin:</p>
            <p style="margin: 4px 0 0; font-size: 14px; color: #374151;">{note}</p>
        </div>
        """

    cta = ""
    if is_approved:
        cta = f"""
        <p style="margin-top: 24px;">
            <a href="{login_url}" style="display: inline-block; background: #059669; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                Sign In Now
            </a>
        </p>
        """

    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8faf9; border-radius: 12px; padding: 32px;">
        <h2 style="color: {colour}; margin-top: 0;">{heading}</h2>
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">
            Hi <strong>{user_name}</strong>,
        </p>
        <p style="color: #374151; font-size: 15px; line-height: 1.6;">{message}</p>
        {note_block}
        {cta}
        <p style="color: #9ca3af; font-size: 12px; margin-top: 24px;">
            This is an automated notification from WellnessWay.
        </p>
    </div>
    """


# ── Event handlers ───────────────────────────────────────────────────

async def on_user_registered(user_email: str, user_name: str, **_):
    """Handler: notify admin when a new user registers."""
    settings = get_settings()
    admin_email = settings.email.admin_email
    if not admin_email:
        logger.warning("[EMAIL] No ADMIN_EMAIL configured – skipping admin notification")
        return

    subject = f"[WellnessWay] New Registration: {user_name}"
    html = _admin_new_user_html(user_email, user_name)
    send_email(admin_email, subject, html)


async def on_admin_action(user_email: str, user_name: str, status: str, note: Optional[str] = None, **_):
    """Handler: notify user about admin decision (approved / declined)."""
    action_word = "Approved" if status == "approved" else "Declined"
    subject = f"[WellnessWay] Your Registration Has Been {action_word}"
    html = _user_decision_html(user_name, status, note)
    send_email(user_email, subject, html)


# ── Bootstrap ────────────────────────────────────────────────────────

def init_email_listeners() -> None:
    """Subscribe email handlers to the event bus. Call once at app startup."""
    event_bus.subscribe(USER_REGISTERED, on_user_registered)
    event_bus.subscribe(ADMIN_ACTION_COMPLETED, on_admin_action)
    logger.info("[EMAIL] Email notification listeners registered")
