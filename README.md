#AI ChatBot

## Description
The ChatBot,is an AI-powered assistant equipped to provide comprehensive information, answer queries, and engage in meaningful conversations about retail industry. It ensures accuracy in responses through its extensive knowledge base, making it a reliable resource for users seeking information about the industry.

## ✨ Features

- 🤖 **AI-Powered Responses** using Google Gemini 2.0 Flash
- 🌍 **Multi-language Support** with automatic translation
- 📚 **RAG (Retrieval-Augmented Generation)** with FAISS vector database
- 👥 **Role-Based Access Control** (Admin & User roles)
- 📄 **PDF Document Training** (Admin only)
- 💬 **Chat History** and conversation context
- 👍👎 **Feedback System** for continuous improvement
- 🚀 **Flask API** for external integrations

## 🔐 Authentication Methods

### Option 1: Username & Password
Traditional login for existing users with credentials stored in `config.yaml`.

### Option 2: Google SSO (NEW!)
- Login with your @gmail.com Google account
- One-click authentication
- No password management needed
- Automatic user provisioning

**See [GOOGLE_SSO_SETUP.md](GOOGLE_SSO_SETUP.md) for setup instructions**

## Installation

### Prerequisites
- Python 3.12+
- Google API Key (for Gemini LLM)
- Google OAuth Credentials (for SSO - optional)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd ai-chatbot
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file with the following:
```env
# Google Gemini API
GOOGLE_API_KEY="your-gemini-api-key"

# Flask Configuration
SECURE_API_KEY="_unify_ai_chatbot_878899"
FLASK_RUN_HOST="0.0.0.0"
FLASK_RUN_PORT="17191"

# Google OAuth (Optional - for SSO)
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
OAUTH_REDIRECT_URI="http://localhost:8501"
```

### Step 4: Run the Application
```bash
streamlit run main.py
```

Access the application at: `http://localhost:8501`

## 📦 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Web UI framework |
| **Backend API** | Flask | REST API endpoints |
| **LLM** | Google Gemini 2.0 Flash | AI language model |
| **Embeddings** | Google GenAI | Text embeddings |
| **Vector DB** | FAISS | Document similarity search |
| **PDF Processing** | PyPDF2 | Extract text from PDFs |
| **Translation** | deep-translator | Multi-language support |
| **Authentication** | Custom + Google OAuth | Dual auth system |
| **Deployment** | Docker | Containerization |

## 📖 Documentation

- **[GOOGLE_SSO_SETUP.md](GOOGLE_SSO_SETUP.md)** - Complete Google SSO setup guide
- **[QUICK_START_SSO.md](QUICK_START_SSO.md)** - Quick reference for SSO
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation details

## 🚀 Usage

### For End Users:
1. Navigate to the chatbot URL
2. Choose login method:
   - Enter username/password, OR
   - Click "🔐 Login with Google"
3. Start asking questions about Unify!
4. Use starter questions in the sidebar
5. Provide feedback using 👍/👎 buttons

### For Administrators:
1. Login with admin credentials
2. Switch to "Admin" role in sidebar
3. **Document Upload**: Train the chatbot with new PDFs
4. **User Management**: Add new users
5. Review user feedback for improvements

## 🔧 Configuration

### config.yaml Structure:
```yaml
admin_users:
  - username1
  - username2

credentials:
  usernames:
    username1:
      name: "Display Name"
      email: "user@gmail.com"
      password: "password123"

google_oauth:
  enabled: true
  allowed_domain: "gmail.com"
  admin_google_users:
    - admin@gmail.com
```

## 🐳 Docker Deployment

### Build Image:
```bash
docker build -t u-chatbot .
```

### Run Container:
```bash
docker run -p 8501:8501 -p 17191:17191 u-chatbot
```

### Using Docker Compose:
```bash
docker-compose up -d
```

## 🔌 API Integration

The Flask API endpoint is available for external integrations:

```bash
POST http://localhost:17191/chatbot
Headers: x-api-key: your-api-key
Body: {
  "question": "What is Unify?",
  "chat_history": []
}
```

## 🛠️ Development

### Project Structure:
```
ai-chatbot/
├── main.py                 # Streamlit UI application
├── trainapp.py            # Core AI logic and RAG
├── flaskapp.py            # Flask API endpoints
├── config.yaml            # User configuration
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .env                  # Environment variables
├── faiss_index/          # Vector database storage
└── docs/
    ├── GOOGLE_SSO_SETUP.md
    ├── QUICK_START_SSO.md
    └── IMPLEMENTATION_SUMMARY.md
```

## 📊 Features Breakdown

### Core AI Features:
- ✅ Document chunking and embedding
- ✅ Similarity-based retrieval
- ✅ Conversational context management
- ✅ Multi-turn conversations
- ✅ Language detection and translation

### Security Features:
- ✅ User authentication (dual method)
- ✅ Role-based access control
- ✅ Domain restriction for SSO
- ✅ API key validation (Flask)
- ✅ Session management

## Support
For help and support:
- **Email**: .LLM@gmail.com
- **Documentation**: See docs/ folder
- **Issues**: Contact your administrator

## 🗺️ Roadmap
- [x] Basic chatbot functionality
- [x] Multi-language support
- [x] Google SSO integration
- [ ] Enhanced analytics dashboard
- [ ] Chat history export
- [ ] Advanced admin reporting
- [ ] Rate limiting implementation
- [ ] Password hashing (bcrypt)
- [ ] Database integration (PostgreSQL)

## Project Status
🟢 **Active Development** - Version 2.0 with Google SSO integration complete
