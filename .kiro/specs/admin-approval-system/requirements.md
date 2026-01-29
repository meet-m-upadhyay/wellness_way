# Requirements Document

## Introduction

This document specifies the requirements for an admin approval system that controls new user access to a wellness application. The system will replace the current immediate access model with a gated approval process where new users must be approved by an administrator before gaining application access.

## Glossary

- **Admin_User**: The designated administrator (meetupadhyaykgp@gmail.com) with privileges to approve or decline user registrations
- **Pending_User**: A user who has completed OAuth authentication but awaits admin approval
- **Approved_User**: A user who has been granted access by the admin
- **Declined_User**: A user whose access request has been rejected by the admin
- **Registration_Request**: A pending approval record containing user details and status
- **OAuth_System**: Google OAuth authentication service
- **Admin_Dashboard**: The administrative interface for managing users and approvals
- **Email_Service**: The system component responsible for sending notification emails
- **User_Status**: The approval state of a user (pending, approved, declined)

## Requirements

### Requirement 1: New User Registration Flow

**User Story:** As a new user, I want to understand my registration status after OAuth authentication, so that I know whether I can access the application or need to wait for approval.

#### Acceptance Criteria

1. WHEN a new user completes Google OAuth authentication, THE System SHALL create a Registration_Request with pending status
2. WHEN a new user's Registration_Request is pending, THE System SHALL display a "pending approval" message instead of granting application access
3. WHEN a user with pending status attempts to access protected routes, THE System SHALL redirect them to the pending approval page
4. WHEN a Registration_Request is created, THE System SHALL store the user's name, email, and registration timestamp

### Requirement 2: Admin Notification System

**User Story:** As an admin, I want to be notified immediately when new users register, so that I can review and process their requests promptly.

#### Acceptance Criteria

1. WHEN a new Registration_Request is created, THE Email_Service SHALL send a notification email to the Admin_User
2. WHEN sending admin notifications, THE Email_Service SHALL include the pending user's name, email, and registration date
3. WHEN a Registration_Request is created, THE Admin_Dashboard SHALL display the new request in the pending approvals section
4. WHEN the Admin_User accesses the dashboard, THE System SHALL show a count of pending Registration_Requests

### Requirement 3: Admin Approval Interface

**User Story:** As an admin, I want to review and manage pending user requests through the dashboard, so that I can control who gains access to the application.

#### Acceptance Criteria

1. WHEN the Admin_User views pending requests, THE Admin_Dashboard SHALL display user name, email, and registration date for each Registration_Request
2. WHEN the Admin_User clicks approve on a Registration_Request, THE System SHALL update the User_Status to approved
3. WHEN the Admin_User clicks decline on a Registration_Request, THE System SHALL update the User_Status to declined
4. WHEN a Registration_Request status changes, THE Admin_Dashboard SHALL update the display immediately

### Requirement 4: User Notification System

**User Story:** As a user, I want to be notified of my approval status, so that I know when I can access the application or if my request was declined.

#### Acceptance Criteria

1. WHEN an Admin_User approves a Registration_Request, THE Email_Service SHALL send an approval notification to the Pending_User
2. WHEN an Admin_User declines a Registration_Request, THE Email_Service SHALL send a decline notification to the Pending_User
3. WHEN sending approval emails, THE Email_Service SHALL include instructions for accessing the application
4. WHEN sending decline emails, THE Email_Service SHALL include information about the decision and next steps

### Requirement 5: Authentication Flow Management

**User Story:** As a user, I want the authentication system to respect my approval status, so that I can access the application only when approved.

#### Acceptance Criteria

1. WHEN an Approved_User attempts to sign in, THE OAuth_System SHALL grant normal application access
2. WHEN a Pending_User attempts to sign in, THE OAuth_System SHALL redirect to the pending approval page
3. WHEN a Declined_User attempts to sign in, THE System SHALL allow them to create a new Registration_Request
4. THE System SHALL validate User_Status on every authentication attempt
5. WHEN checking User_Status, THE System SHALL query the most current approval state from the database

### Requirement 6: Email Service Integration

**User Story:** As a system administrator, I want basic email delivery for notifications, so that stakeholders receive updates about registration status changes.

#### Acceptance Criteria

1. WHEN sending emails, THE Email_Service SHALL use simple templates for admin and user notifications
2. WHEN composing emails, THE Email_Service SHALL include user information and clear next steps
3. THE Email_Service SHALL send emails in HTML format

### Requirement 7: Data Persistence and Management

**User Story:** As a system, I want to maintain records of registration requests and approval decisions, so that the approval process works reliably.

#### Acceptance Criteria

1. WHEN storing Registration_Requests, THE System SHALL persist user email, name, registration timestamp, and current status
2. WHEN User_Status changes, THE System SHALL update the database immediately
3. THE System SHALL prevent duplicate Registration_Requests for the same email address while one is pending

### Requirement 8: Admin Dashboard Enhancement

**User Story:** As an admin, I want a simple dashboard interface for managing user approvals, so that I can efficiently process registration requests.

#### Acceptance Criteria

1. WHEN displaying pending requests, THE Admin_Dashboard SHALL show requests with user details
2. WHEN the dashboard loads, THE System SHALL display a count of pending Registration_Requests
3. THE Admin_Dashboard SHALL provide basic approve/decline buttons for each request