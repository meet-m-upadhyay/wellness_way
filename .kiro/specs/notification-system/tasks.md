# Event-Driven Notification System - Implementation Tasks

## Overview
Implementation tasks for Phase 1 of the event-driven notification system. All tasks integrate with existing WellnessWay codebase without breaking changes.

## Tasks

### 1. Core Event System Infrastructure
- [ ] 1.1 Create notification event classes
  - Create `app/services/notification/events.py`
  - Define `NotificationEvent` dataclass with all required fields
  - Add event type constants for user_registered, user_approved, user_declined
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 1.2 Create notification service with pub/sub pattern
  - Create `app/services/notification/service.py`
  - Implement `NotificationService` class with subscribe/publish methods
  - Add handler registration and event distribution logic
  - Create global service instance in `__init__.py`
  - _Requirements: 4.1, 4.2, 7.1_

### 2. Email Notification Handler
- [ ] 2.1 Create email notification handler
  - Create `app/services/notification/handlers/email.py`
  - Implement `EmailNotificationHandler` class with SMTP integration
  - Add email sending logic with error handling
  - Support HTML email templates
  - _Requirements: 2.1, 2.2, 2.3, 4.3, 5.2_

- [ ] 2.2 Create HTML email templates
  - Create `app/services/notification/templates/email/base.html`
  - Create `admin_new_request.html` template for admin notifications
  - Create `user_approved.html` template for approval notifications
  - Create `user_declined.html` template for decline notifications
  - Include WellnessWay branding and professional styling
  - _Requirements: 2.4, 6.3_

### 3. Configuration System
- [ ] 3.1 Create notification configuration system
  - Create `app/services/notification/config.py`
  - Add SMTP configuration class with environment variable loading
  - Add notification rules configuration
  - Add enable/disable flags for notification types
  - _Requirements: 3.4, 4.3, 6.1, 7.3_

- [ ] 3.2 Add environment variables to configuration
  - Update `app/core/config.py` to include notification settings
  - Add SMTP configuration fields (host, port, username, password, TLS)
  - Add notification enable/disable flags
  - Add admin email and support email configuration
  - _Requirements: 3.4, 6.1_

### 4. Integration with Existing Code
- [ ] 4.1 Integrate with auth service for user registration events
  - Modify `app/services/auth_service.py`
  - Add event publishing in `get_or_create_user_from_google` method
  - Publish "user_registered" event when new registration request is created
  - Ensure integration doesn't break existing functionality
  - _Requirements: 1.1, 3.1_

- [ ] 4.2 Integrate with admin endpoints for approval events
  - Modify `app/api/endpoints/admin.py`
  - Add event publishing in `approve_user_request` endpoint
  - Add event publishing in `decline_user_request` endpoint
  - Publish appropriate events after successful database operations
  - _Requirements: 1.2, 1.3, 3.2_

### 5. Service Initialization and Registration
- [ ] 5.1 Initialize notification service on application startup
  - Update `app/services/notification/__init__.py`
  - Create global notification service instance
  - Register email handler with service if email notifications enabled
  - Add proper error handling for initialization failures
  - _Requirements: 4.1, 4.2, 4.3_

### 6. Error Handling and Logging
- [ ] 6.1 Add comprehensive error handling
  - Add try/catch blocks around notification sending
  - Ensure notification failures don't affect core application flow
  - Add proper logging for notification events and failures
  - Add graceful degradation when SMTP is unavailable
  - _Requirements: 3.3, 4.4, 5.1, 6.2_

### 7. Testing and Validation
- [ ] 7.1 Create notification system tests
  - Create `tests/test_notification_service.py`
  - Test event publishing and handler registration
  - Test email handler with mock SMTP
  - Test integration with auth service and admin endpoints
  - _Requirements: All requirements_

- [ ] 7.2 End-to-end notification flow testing
  - Test complete user registration → admin email flow
  - Test complete admin approval → user email flow
  - Test complete admin decline → user email flow
  - Verify email templates render correctly with real data
  - _Requirements: All requirements_

## File Structure
```
backend/app/services/notification/
├── __init__.py                 # Service initialization and registration
├── events.py                   # Event classes and constants
├── service.py                  # Core NotificationService class
├── config.py                   # Configuration and settings
├── handlers/
│   ├── __init__.py
│   └── email.py               # EmailNotificationHandler
└── templates/
    └── email/
        ├── base.html          # Base template with branding
        ├── admin_new_request.html
        ├── user_approved.html
        └── user_declined.html

backend/tests/
└── test_notification_service.py  # Comprehensive tests
```

## Environment Variables to Add
```bash
# Add to .env files
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@wellnessway.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
NOTIFICATIONS_ENABLED=true
EMAIL_NOTIFICATIONS_ENABLED=true
ADMIN_EMAIL=meetupadhyaykgp@gmail.com
SUPPORT_EMAIL=support@wellnessway.com
APP_URL=http://localhost:3000
```

## Integration Points (Existing Files to Modify)
- `app/services/auth_service.py` - Add event publishing for user registration
- `app/api/endpoints/admin.py` - Add event publishing for approval/decline
- `app/core/config.py` - Add notification configuration fields
- `.env` files - Add SMTP and notification configuration

## Success Criteria
- [ ] Admin receives email when new user registers
- [ ] User receives email when approved by admin
- [ ] User receives email when declined by admin
- [ ] All emails use professional HTML templates
- [ ] System handles SMTP failures gracefully
- [ ] No breaking changes to existing functionality
- [ ] Architecture supports future notification channels
- [ ] All tests pass

## Notes
- All tasks maintain backward compatibility with existing code
- Notification failures do not affect core application functionality
- System is designed for easy extension with additional notification channels
- Email templates include WellnessWay branding and professional styling