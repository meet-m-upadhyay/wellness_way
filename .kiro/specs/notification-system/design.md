# Event-Driven Notification System - Design

## Architecture Overview

The notification system uses an event-driven pub/sub pattern that integrates seamlessly with the existing WellnessWay codebase without breaking changes.

## Core Components

### 1. Event System
```python
# app/services/notification/events.py
@dataclass
class NotificationEvent:
    event_type: str  # "user_registered", "user_approved", "user_declined"
    user_email: str
    user_name: str
    admin_email: str
    metadata: Dict[str, Any]
    timestamp: datetime

# app/services/notification/service.py
class NotificationService:
    def __init__(self):
        self.handlers: Dict[str, List[NotificationHandler]] = {}
    
    def subscribe(self, event_type: str, handler: NotificationHandler):
        """Register handler for specific event type"""
    
    def publish(self, event: NotificationEvent):
        """Send event to all registered handlers"""
```

### 2. Email Handler
```python
# app/services/notification/handlers/email.py
class EmailNotificationHandler:
    def __init__(self, smtp_config: SMTPConfig):
        self.smtp_config = smtp_config
        self.template_loader = TemplateLoader()
    
    def handle(self, event: NotificationEvent):
        """Send email notification based on event type"""
```

### 3. Integration Points

**Auth Service Integration:**
```python
# app/services/auth_service.py (existing file)
# Add to get_or_create_user_from_google method:

if new_registration:
    # Existing code...
    
    # NEW: Publish notification event
    from app.services.notification.service import notification_service
    event = NotificationEvent(
        event_type="user_registered",
        user_email=google_user_info['email'],
        user_name=google_user_info['name'],
        admin_email="meetupadhyaykgp@gmail.com",
        metadata={"request_id": str(new_request.id)}
    )
    notification_service.publish(event)
```

**Admin Endpoints Integration:**
```python
# app/api/endpoints/admin.py (existing file)
# Add to approve_user_request and decline_user_request:

# After successful approval/decline:
event = NotificationEvent(
    event_type="user_approved",  # or "user_declined"
    user_email=registration_request.email,
    user_name=registration_request.name,
    admin_email=admin_user.email,
    metadata={"request_id": request_id}
)
notification_service.publish(event)
```

## Email Templates

### Template Structure
```
backend/app/services/notification/templates/email/
├── base.html                    # Base template with WellnessWay branding
├── admin_new_request.html       # Admin notification for new registration
├── user_approved.html           # User notification for approval
└── user_declined.html           # User notification for decline
```

### Template Variables
- `user_name`: User's display name
- `user_email`: User's email address
- `admin_name`: Admin's name (for user notifications)
- `app_url`: WellnessWay application URL
- `support_email`: Support contact email

## Configuration

### Environment Variables
```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@wellnessway.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true

# Notification Settings
NOTIFICATIONS_ENABLED=true
EMAIL_NOTIFICATIONS_ENABLED=true
ADMIN_EMAIL=meetupadhyaykgp@gmail.com
SUPPORT_EMAIL=support@wellnessway.com
APP_URL=https://wellnessway.com
```

### Notification Configuration
```python
# app/services/notification/config.py
NOTIFICATION_CONFIG = {
    "user_registered": {
        "admin": ["email"],
        "user": []
    },
    "user_approved": {
        "admin": [],
        "user": ["email"]
    },
    "user_declined": {
        "admin": [],
        "user": ["email"]
    }
}
```

## Error Handling

### Graceful Degradation
- Notification failures do not affect core application functionality
- Failed notifications are logged but do not raise exceptions
- SMTP connection errors are handled gracefully

### Logging
```python
# Log notification events and failures
logger.info(f"Notification sent: {event.event_type} to {event.user_email}")
logger.error(f"Notification failed: {event.event_type} - {error}")
```

## Service Initialization

### Global Service Instance
```python
# app/services/notification/__init__.py
from .service import NotificationService
from .handlers.email import EmailNotificationHandler
from .config import get_notification_config

# Initialize global notification service
notification_service = NotificationService()

# Register email handler if enabled
if get_notification_config().email_enabled:
    email_handler = EmailNotificationHandler(get_smtp_config())
    notification_service.subscribe("user_registered", email_handler)
    notification_service.subscribe("user_approved", email_handler)
    notification_service.subscribe("user_declined", email_handler)
```

## Future Extensibility

The architecture supports easy addition of new notification channels:

```python
# Future: Add SMS handler
sms_handler = SMSNotificationHandler(twilio_config)
notification_service.subscribe("user_approved", sms_handler)

# Future: Add WhatsApp handler
whatsapp_handler = WhatsAppNotificationHandler(whatsapp_config)
notification_service.subscribe("user_approved", whatsapp_handler)
```

## Database Impact

**No database changes required** - the system works with existing tables and data structures.

## API Impact

**No API changes required** - notifications are triggered internally by existing endpoints.