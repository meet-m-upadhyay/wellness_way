# Google OAuth Setup Guide

This guide explains how to set up Google OAuth authentication for the WellnessWay Diet Planner application.

## Prerequisites

- Google Cloud Console account
- WellnessWay application running locally or deployed

## Step 1: Create Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note down your project ID

## Step 2: Enable Google+ API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Google+ API" and enable it
3. Also enable "Google Identity" if available

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" user type
   - Fill in the required fields:
     - App name: "WellnessWay Diet Planner"
     - User support email: Your email
     - Developer contact information: Your email
   - Add scopes: `email`, `profile`, `openid`
   - Add test users if needed

4. Create OAuth client ID:
   - Application type: "Web application"
   - Name: "WellnessWay Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:3000` (for development)
     - Your production domain (e.g., `https://wellnessway.example.com`)
   - Authorized redirect URIs:
     - `http://localhost:3000` (for development)
     - Your production domain (e.g., `https://wellnessway.example.com`)

5. Copy the Client ID and Client Secret

## Step 4: Configure Backend Environment

Update your backend `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
JWT_SECRET_KEY=your-jwt-secret-key-here-at-least-32-characters
```

## Step 5: Configure Frontend Environment

Update your frontend `.env` file:

```env
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id-here.apps.googleusercontent.com
```

## Step 6: Install Dependencies

### Backend Dependencies (already included)
```bash
cd backend
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

### Frontend Dependencies
```bash
cd frontend
npm install google-auth-library jwt-decode
```

## Step 7: Test the Setup

1. Start the backend server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. Start the frontend server:
   ```bash
   cd frontend
   npm start
   ```

3. Navigate to `http://localhost:3000/login`
4. Click the "Sign in with Google" button
5. Complete the OAuth flow
6. Verify you're redirected to the profile setup page

## Security Considerations

### Production Setup

1. **HTTPS Only**: Ensure your production application uses HTTPS
2. **Secure Cookies**: Configure secure cookie settings
3. **CORS**: Restrict CORS origins to your actual domains
4. **Environment Variables**: Never commit real credentials to version control

### JWT Security

1. **Secret Key**: Use a strong, randomly generated JWT secret key (at least 32 characters)
2. **Token Expiration**: Access tokens expire in 30 minutes, refresh tokens in 7 days
3. **Token Storage**: Tokens are stored in localStorage (consider httpOnly cookies for production)

## Troubleshooting

### Common Issues

1. **"Invalid client" error**:
   - Check that your Client ID is correct
   - Verify the authorized origins match your current URL

2. **"Redirect URI mismatch"**:
   - Ensure your redirect URIs in Google Console match your application URLs
   - Check for trailing slashes and protocol (http vs https)

3. **"Access blocked" error**:
   - Add your email as a test user in the OAuth consent screen
   - Verify the OAuth consent screen is properly configured

4. **Token verification fails**:
   - Check that your backend Google Client ID matches the frontend
   - Ensure the JWT secret key is properly configured

### Debug Mode

Enable debug logging in the backend by setting:
```env
LOG_LEVEL=DEBUG
```

This will show detailed authentication logs to help troubleshoot issues.

## API Endpoints

The authentication system provides these endpoints:

- `POST /api/v1/auth/google` - Authenticate with Google OAuth token
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/status` - Check auth service status

## Frontend Integration

The authentication is integrated into the React app with:

- `AuthContext` - Global authentication state management
- `GoogleLogin` - Google OAuth login component
- `ProtectedRoute` - Route protection wrapper
- `LoginPage` - Complete login page with Google OAuth

## Database Migration

Run the database migration to add authentication fields:

```bash
cd backend
python -m alembic upgrade head
```

This adds the following fields to the users table:
- `email` (unique, required)
- `google_id` (unique, optional)
- `is_active` (boolean, default true)
- `profile_completed` (boolean, default false)

## Next Steps

After setting up authentication:

1. Users can sign in with their Google account
2. New users are automatically created with basic info from Google
3. Users are redirected to profile setup to complete their health information
4. All API requests are authenticated with JWT tokens
5. The application maintains backward compatibility with the X-User-Id header for existing functionality

The authentication system is now fully integrated and ready for production use!