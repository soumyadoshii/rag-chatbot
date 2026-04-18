# Authentication Flow Diagrams

## 1. Google SSO Authentication Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     User Visits Chatbot                              │
│                  http://localhost:8501                               │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       Login Page                                     │
│  ┌─────────────────────┐    ┌──────────────────────┐                │
│  │ Username/Password   │    │  Google Sign-In      │                │
│  │                     │    │                      │                │
│  │ [Username]          │    │ Sign in with your    │                │
│  │ [Password]          │    │ @group.com        │                │
│  │ [Login Button]      │    │                      │                │
│  │                     │    │ [🔐 Login with      │                │
│  └─────────────────────┘    │     Google]          │                │
│                             └──────────────────────┘                │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Username/Password      │   │  Google SSO Selected    │
│  Login Selected         │   │                         │
└──────────┬──────────────┘   └──────────┬──────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Validate Credentials   │   │ Generate OAuth URL      │
│  from config.yaml       │   │ with state parameter    │
└──────────┬──────────────┘   └──────────┬──────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Authentication         │   │  Redirect to Google     │
│  Success/Failure        │   │  Login Page             │
└──────────┬──────────────┘   └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  User Enters Google     │
           │                  │  Credentials            │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Google Verifies        │
           │                  │  Credentials            │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  User Grants            │
           │                  │  Permissions            │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Google Redirects Back  │
           │                  │  with Authorization     │
           │                  │  Code                   │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Exchange Code for      │
           │                  │  ID Token               │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Verify ID Token        │
           │                  │  & Extract Email        │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Check if Email         │
           │                  │  ends with              │
           │                  │  @group.com          │
           │                  └──────────┬──────────────┘
           │                              │
           │                    ┌─────────┴──────────┐
           │                    │                    │
           │                    ▼                    ▼
           │         ┌──────────────────┐  ┌──────────────────┐
           │         │  Email Valid     │  │  Email Invalid   │
           │         │  (group.com)  │  │  Reject & Show   │
           │         └────────┬─────────┘  │  Error Message   │
           │                  │            └──────────────────┘
           │                  ▼
           │         ┌──────────────────┐
           │         │  Check if Admin  │
           │         │  (config.yaml)   │
           │         └────────┬─────────┘
           │                  │
           └──────────────────┴──────────────────┐
                                                  │
                                                  ▼
                                    ┌───────────────────────┐
                                    │  Set Session State:   │
                                    │  - authenticated: True│
                                    │  - user_info          │
                                    │  - auth_method        │
                                    │  - is_admin           │
                                    └──────────┬────────────┘
                                               │
                                               ▼
                                    ┌───────────────────────┐
                                    │  Redirect to Main     │
                                    │  Chatbot Interface    │
                                    └───────────────────────┘
```

## 2. Session Management

```
┌─────────────────────────────────────────────┐
│          Session State Variables            │
├─────────────────────────────────────────────┤
│  st.session_state.authenticated  = True/False│
│  st.session_state.user_info      = {        │
│      'name': 'User Name',                   │
│      'email': 'user@group.com'           │
│  }                                          │
│  st.session_state.auth_method    = 'google' │
│                                  or 'password'│
│  st.session_state.is_admin       = True/False│
│  st.session_state.chat_history   = [...]    │
│  st.session_state.messages       = [...]    │
└─────────────────────────────────────────────┘
```

## 3. Admin Role Assignment

```
                    ┌─────────────────┐
                    │  User Logged In │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Password Login   │      │  Google SSO      │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Check username   │      │ Check email in   │
    │ in admin_users   │      │ admin_google_    │
    │ list             │      │ users list       │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             └────────────┬────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  Set is_admin    │
                │  flag            │
                └────────┬─────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │ is_admin =   │          │ is_admin =   │
    │ True         │          │ False        │
    └──────┬───────┘          └──────┬───────┘
           │                         │
           ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │ Show Admin   │          │ Show User    │
    │ Role Toggle  │          │ Interface    │
    │ in Sidebar   │          │ Only         │
    └──────────────┘          └──────────────┘
```

## 4. Data Flow in Application

```
┌───────────────────────────────────────────────────────┐
│                    User Question                      │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────┐
│              Language Detection                       │
│       (enhanced_language_detection)                   │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────┐
│         Translate to English (if needed)              │
│              (translate_text)                         │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────┐
│         Load FAISS Vector Database                    │
│         (FAISS.load_local)                            │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────┐
│      Create Conversational Chain                     │
│         (conv_chain with Gemini)                      │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────┐
│    Retrieve Relevant Documents (RAG)                  │
│    k=8, score_threshold=0.25                          │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────┐
│    Generate Response with Gemini 2.0 Flash           │
│    (with chat history context)                        │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────┐
│    Translate Response Back (if needed)                │
│         to original language                          │
└────────────────────────┬──────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────┐
│         Display Response to User                      │
│    + Save to chat_history & messages                  │
└───────────────────────────────────────────────────────┘
```

## 5. File Organization

```
ai-chatbot/
│
├── main.py                      # Main Streamlit UI
│   ├── Authentication Logic
│   │   ├── Username/Password
│   │   └── Google SSO
│   ├── User Interface
│   ├── Admin Dashboard
│   └── Session Management
│
├── trainapp.py                  # Core AI Engine
│   ├── PDF Processing
│   ├── Text Chunking
│   ├── Vector Store
│   ├── Language Detection
│   ├── Translation
│   ├── Conversational Chain
│   └── User Input Processing
│
├── flaskapp.py                  # REST API
│   └── /chatbot endpoint
│
├── config.yaml                  # Configuration
│   ├── credentials
│   ├── admin_users
│   └── google_oauth settings
│
├── .env                         # Environment Variables
│   ├── GOOGLE_API_KEY
│   ├── GOOGLE_CLIENT_ID
│   ├── GOOGLE_CLIENT_SECRET
│   └── OAUTH_REDIRECT_URI
│
├── requirements.txt             # Dependencies
│
└── docs/                        # Documentation
    ├── GOOGLE_SSO_SETUP.md
    ├── QUICK_START_SSO.md
    ├── IMPLEMENTATION_SUMMARY.md
    ├── DEPLOYMENT_CHECKLIST.md
    └── AUTHENTICATION_FLOW.md  (this file)
```

## 6. Security Layers

```
┌─────────────────────────────────────────────────────┐
│              Layer 1: Network Level                 │
│  - HTTPS (Production)                               │
│  - Firewall Rules                                   │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Layer 2: Application Level                  │
│  - Session Management (Streamlit)                   │
│  - CORS Configuration (Flask)                       │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Layer 3: Authentication                     │
│  - Password Validation                              │
│  - Google OAuth Token Verification                  │
│  - Domain Restriction (@group.com)               │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Layer 4: Authorization                      │
│  - Role-Based Access Control                        │
│  - Admin vs User Permissions                        │
│  - Feature-Level Access Control                     │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Layer 5: Data Protection                    │
│  - Environment Variables (.env)                     │
│  - API Key Management                               │
│  - No Credentials in Code                           │
└─────────────────────────────────────────────────────┘
```

## 7. Error Handling Flow

```
              ┌─────────────────┐
              │  User Action    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Try/Except     │
              │  Block          │
              └────────┬────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
   ┌──────────┐              ┌──────────┐
   │ Success  │              │  Error   │
   └────┬─────┘              └────┬─────┘
        │                         │
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│ Return Result │         │ Log Error     │
└───────────────┘         └───────┬───────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │ User-Friendly │
                          │ Error Message │
                          └───────┬───────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │ Fallback      │
                          │ Behavior      │
                          └───────────────┘
```
