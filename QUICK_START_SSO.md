# Quick Start: Google SSO for Unify AI ChatBot

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google+ API** and **Google Identity Toolkit API**
4. Create **OAuth 2.0 Client ID** (Web application)
5. Add authorized redirect URIs:
   - Local: `http://localhost:8501`
   - Production: `https://your-domain.com`

### Step 3: Configure .env File

Update your `.env` file with the credentials:

```env
# Add these lines to your existing .env file
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
OAUTH_REDIRECT_URI="http://localhost:8501"
```

### Step 4: Run the Application

```bash
streamlit run main.py
```

### Step 5: Test Login

1. Navigate to `http://localhost:8501`
2. Click **"🔐 Login with Google"** button
3. Sign in with your @group.com account
4. You're in! 🎉

## 📋 What Changed?

### Files Modified:
- ✅ `requirements.txt` - Added Google OAuth libraries
- ✅ `main.py` - Added Google SSO functionality
- ✅ `config.yaml` - Added OAuth settings
- ✅ `.env` - Added OAuth credentials

### New Features:
- ✅ **Login with Google** button on login page
- ✅ Side-by-side login options (Password OR Google)
- ✅ Domain restriction (@group.com only)
- ✅ Admin support for Google SSO users
- ✅ Existing login system unchanged

## 🔐 Making Google Users Admin

Edit `config.yaml`:

```yaml
google_oauth:
  enabled: true
  allowed_domain: "  admin_google_users:
    - your.email@gmail.com
```

## 🎯 Key Points

- ✅ Existing username/password login still works
- ✅ Both login methods work simultaneously
- ✅ Only @group.com emails can login via Google
- ✅ Google SSO users are regular users by default
- ✅ Can make specific Google users admins via config

## 📖 Full Documentation

See `GOOGLE_SSO_SETUP.md` for complete setup guide.

## 🆘 Common Issues

**Issue**: "OAuth not configured" warning
**Fix**: Set `GOOGLE_CLIENT_ID` in `.env` file

**Issue**: Can't login with Google
**Fix**: Verify redirect URI matches in Google Console and `.env`

**Issue**: Wrong email domain
**Fix**: Only @group.com emails are allowed (by design)
