# Implementation Plan: Admin Approval System

## Overview

This implementation plan converts the admin approval system design into discrete coding tasks. The approach focuses on building core functionality first, then adding email notifications, and finally integrating the admin dashboard. Each task builds incrementally to ensure the system works at every step.

## Tasks

- [x] 1. Set up database schema and core models
  - Create registration_requests table migration
  - Add approval_status column to users table
  - Create RegistrationRequest SQLAlchemy model with approval methods
  - Update User model with approval status functionality
  - _Requirements: 7.1, 7.2, 7.3_

- [ ]* 1.1 Write property test for registration request creation
  - **Property 1: Registration Request Creation**
  - **Validates: Requirements 1.1, 1.4, 7.1**

- [x] 2. Implement backend authentication and registration flow
  - [x] 2.1 Create registration API endpoint (/auth/register)
    - Handle new user OAuth data and create pending registration requests
    - Implement duplicate email prevention logic
    - Return appropriate status responses
    - _Requirements: 1.1, 1.4, 7.3_

  - [x] 2.2 Create user status check API endpoint (/auth/status)
    - Query current user approval status from database
    - Return status and appropriate messages
    - _Requirements: 5.4, 5.5_

  - [ ]* 2.3 Write property test for duplicate registration prevention
    - **Property 9: Duplicate Registration Prevention**
    - **Validates: Requirements 7.3**

- [x] 3. Implement admin management API endpoints
  - [x] 3.1 Create pending requests endpoint (/admin/pending-requests)
    - Query and return all pending registration requests
    - Include user details and request counts
    - _Requirements: 2.3, 2.4, 3.1_

  - [x] 3.2 Create approval endpoints (/admin/approve-user/{user_id}, /admin/decline-user/{user_id})
    - Update registration request status in database
    - Handle concurrent approval conflicts
    - Return success/error responses
    - _Requirements: 3.2, 3.3, 7.2_

  - [ ]* 3.3 Write property test for status update consistency
    - **Property 6: Status Update Consistency**
    - **Validates: Requirements 3.2, 3.3, 3.4, 7.2**

- [x] 4. Checkpoint - Test core backend functionality
  - Ensure all API endpoints work correctly, ask the user if questions arise.

- [ ] 5. Implement email service integration
  - [ ] 5.1 Create email service class with template support
    - Implement EmailService with send methods for admin/user notifications
    - Create HTML email templates for admin notifications, user approvals, and user declines
    - Add email configuration and error handling
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 5.2 Integrate email notifications with registration and approval flows
    - Add admin notification email when registration requests are created
    - Add user notification emails when requests are approved/declined
    - _Requirements: 2.1, 4.1, 4.2_

  - [ ]* 5.3 Write property test for email content completeness
    - **Property 4: Email Content Completeness**
    - **Validates: Requirements 2.2, 4.3, 4.4, 6.1, 6.2, 6.3**

- [x] 6. Implement frontend authentication flow modifications
  - [x] 6.1 Create PendingApprovalPage component
    - Display pending approval message for users awaiting approval
    - Include user-friendly messaging and next steps
    - _Requirements: 1.2_

  - [x] 6.2 Modify authentication guard and login handler
    - Check user approval status after OAuth completion
    - Redirect to appropriate pages based on status (approved, pending, declined)
    - Implement route protection for pending users
    - _Requirements: 1.3, 5.1, 5.2, 5.3_

  - [ ]* 6.3 Write property test for pending user access control
    - **Property 2: Pending User Access Control**
    - **Validates: Requirements 1.2, 1.3, 5.2**

- [x] 7. Implement admin dashboard components
  - [x] 7.1 Create PendingRequestsList component
    - Display list of pending registration requests with user details
    - Show registration dates and user information
    - Include pending request count display
    - _Requirements: 3.1, 8.1, 8.2_

  - [x] 7.2 Create ApprovalActions component
    - Implement approve/decline buttons for each request
    - Add confirmation dialogs for approval actions
    - Handle API calls and update UI immediately after status changes
    - _Requirements: 3.2, 3.3, 3.4, 8.3_

  - [ ]* 7.3 Write property test for dashboard display accuracy
    - **Property 5: Dashboard Display Accuracy**
    - **Validates: Requirements 2.4, 3.1, 8.1, 8.2, 8.3**

- [x] 8. Integrate admin dashboard with existing admin interface
  - [x] 8.1 Add pending approvals section to existing admin dashboard
    - Integrate PendingRequestsList and ApprovalActions components
    - Add navigation and styling consistent with existing admin interface
    - _Requirements: 2.3, 8.1_

  - [x] 8.2 Wire up admin notification system
    - Connect registration request creation to admin dashboard updates
    - Ensure real-time or near-real-time display of new requests
    - _Requirements: 2.3_

- [ ]* 8.3 Write property test for admin notification trigger
  - **Property 3: Admin Notification Trigger**
  - **Validates: Requirements 2.1, 2.3**

- [ ] 9. Implement comprehensive authentication status validation
  - [ ] 9.1 Add authentication middleware for status checking
    - Validate user approval status on every protected route access
    - Query current status from database for each authentication attempt
    - Handle status changes between sessions
    - _Requirements: 5.4, 5.5_

  - [ ]* 9.2 Write property test for authentication status validation
    - **Property 8: Authentication Status Validation**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [ ] 10. Add user notification system integration
  - [ ] 10.1 Connect approval actions to user email notifications
    - Trigger appropriate user emails when admin approves/declines requests
    - Ensure emails contain required information and next steps
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 10.2 Write property test for user notification on status change
    - **Property 7: User Notification on Status Change**
    - **Validates: Requirements 4.1, 4.2**

- [x] 11. Final integration and testing
  - [x] 11.1 Wire all components together for complete user journey
    - Test complete flow from new user registration through admin approval to user access
    - Ensure all email notifications work end-to-end
    - Verify error handling and edge cases work correctly
    - _Requirements: All requirements_

  - [ ]* 11.2 Write integration tests for complete approval workflow
    - Test end-to-end user journey from registration to approval
    - Verify email notifications and dashboard updates work together
    - _Requirements: All requirements_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design document
- Integration tests verify the complete user approval workflow
- Email functionality should use mock services during development to avoid external dependencies