# For user authentication

import os
import streamlit as st
import base64
from trainapp import user_input, get_pdf_text, get_text_chunks, vector_store
import yaml
from yaml.loader import SafeLoader
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501")

def get_google_oauth_url():
    """Generate Google OAuth URL for authentication"""
    try:
        # OAuth 2.0 client configuration
        client_config = {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [OAUTH_REDIRECT_URI],
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ],
            redirect_uri=OAUTH_REDIRECT_URI
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url, state
    except Exception as e:
        st.error(f"Error generating OAuth URL: {e}")
        return None, None

def verify_google_token(token):
    """Verify Google OAuth token and extract user info"""
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        # Extract user information
        email = idinfo.get('email', '')
        name = idinfo.get('name', '')
        
        return {
            'email': email,
            'name': name,
            'authenticated': True
        }
    except Exception as e:
        st.error(f"Token verification failed: {e}")
        return None

def handle_google_oauth_callback():
    """Handle the OAuth callback from Google"""
    try:
        # Get the authorization code from URL parameters
        query_params = st.query_params
        
        if 'code' in query_params:
            code = query_params['code']
            
            # Exchange authorization code for tokens
            client_config = {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [OAUTH_REDIRECT_URI],
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile"
                ],
                redirect_uri=OAUTH_REDIRECT_URI
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Verify the ID token
            user_info = verify_google_token(credentials.id_token)
            
            if user_info and user_info['email'].endswith('@gmail.com'):
                # Clear the query parameters
                st.query_params.clear()
                return user_info
            else:
                st.error("Only @group.com email addresses are allowed.")
                st.query_params.clear()
                return None
                
    except Exception as e:
        st.error(f"OAuth callback error: {e}")
        st.query_params.clear()
        return None
    
    return None

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None
    
def load_custom_css():
    try:
        with open("style.css", "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def load_config():
    """Load user configuration from config file"""
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.load(file, SafeLoader)
            return config
    except FileNotFoundError:
        st.error("Config file not found. Please create a config.yaml file.")
        return None

def check_password(username, password, config):
    """Check if the password matches the password in config - using plaintext comparison"""
    if not config or username not in config['credentials']['usernames']:
        return False, None
    
    user_data = config['credentials']['usernames'][username]
    stored_password = user_data['password']
    
    # Direct comparison for plaintext passwords
    if stored_password == password:
        return True, user_data
    return False, None

def is_admin(username, config):
    """Check if the user is an admin"""
    if 'admin_users' in config and username in config['admin_users']:
        return True
    return False

def is_google_admin(email, config):
    """Check if the Google SSO user is an admin"""
    if 'google_oauth' in config and 'admin_google_users' in config['google_oauth']:
        if email in config['google_oauth']['admin_google_users']:
            return True
    return False

def main():
    st.set_page_config('Unify LLM Bot')
    
    # First check if the user is authenticated
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.is_admin = False
        st.session_state.auth_method = None  # Track authentication method
    
    # Load config file
    config = load_config()
    if not config:
        st.stop()
    
    # Check for Google OAuth callback
    if not st.session_state.authenticated:
        google_user = handle_google_oauth_callback()
        if google_user:
            st.session_state.authenticated = True
            st.session_state.user_info = google_user
            st.session_state.auth_method = 'google'
            # Check if Google SSO user is admin
            st.session_state.is_admin = is_google_admin(google_user['email'], config)
            st.rerun()
    
    # If not authenticated, show login form
    if not st.session_state.authenticated:
        st.title("Login to  Unify AI ChatBot")
        
        # Create two columns for login options
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.form("login_form"):
                # st.subheader("Username & Password Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Login")
                
                if submit_button:
                    authenticated, user_info = check_password(username, password, config)
                    if authenticated:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.user_info['username'] = username
                        st.session_state.auth_method = 'password'
                        st.session_state.is_admin = is_admin(username, config)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with col2:
            st.subheader("Google Sign-In")
            st.write("Sign in with your google account")
            
            # Check if Google OAuth is configured
            if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID != "your-client-id.apps.googleusercontent.com":
                if st.button("🔐 Login with Google", use_container_width=True, type="primary"):
                    auth_url, state = get_google_oauth_url()
                    if auth_url:
                        st.session_state.oauth_state = state
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                        st.info("Redirecting to Google Sign-In...")
            else:
                st.warning("⚠️ Google OAuth not configured. Please set up GOOGLE_CLIENT_ID in .env file.")
        
        # Sign-up information
        st.markdown("---")
        st.write("For Sign-Up - Please send an email to .LLM@group.com and we will revert to you soon.")
        return
    
    # Once authenticated, proceed with the main application
    st.title(" Unify AI ChatBot")
    load_custom_css()
    
    # adding logo to unify chatbot page.  
    logo_path = ".static/Group 4898.png"
    
    # Initialize session states if they are not present
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'user_feedback' not in st.session_state:
        st.session_state.user_feedback = []
    
    if "user_question" not in st.session_state:
        st.session_state.user_question = ""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sidebar Menu for User & Admin based on user role
    with st.sidebar:
        # Try to load the logo if it exists
        logo_b64 = get_image_base64(logo_path)
        if logo_b64:
            st.markdown(f"""
            <div style="background-color: white; padding: 10px; border-radius: 10px; display: inline-block;">
            <img src="data:image/png;base64,{logo_b64}" width="200" height="30">
            </div>""", unsafe_allow_html=True)
        else:
            st.write(" Unify AI ChatBot")
        
        # Show logged in user info with authentication method
        user_display_name = st.session_state.user_info.get('name', 'User')
        auth_method = st.session_state.get('auth_method', 'password')
        
        if auth_method == 'google':
            st.write(f"👤 {user_display_name}")
            # st.caption(f"🔐 Google SSO: {st.session_state.user_info.get('email', '')}")
        else:
            st.write(f"Logged in as: {user_display_name}")
        
        # Only show role selector for admin users
        if st.session_state.is_admin:
            role = st.radio("Select Role", ("User", "Admin"), horizontal=True)
        else:
            role = "User"  # Regular users can only access user functionality
            
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.is_admin = False
            st.rerun()
            
        if role == "User":
            # Sample Starter Questions in Sidebar
            sample_questions = [
                "Give a detailed summary of 's Unify application?",
                "How UNIFY help with inventory management and improve operational efficiency?",
                "What are AI capabilities of Unify?",
                "What are the key features of 's Unify?",
                "What kind of reports can I generate using Unify?",
            ]
            
            # Display starter questions as clickable options in the sidebar
            for question in sample_questions:
                if st.button(question, use_container_width=True):
                    st.session_state.messages.append({'role': 'User', 'content': question, 'avatar': '👨🏻‍💻'})
                    response = user_input(question, [])
                    st.session_state.messages.append({'role': 'Assistant', 'content': response, 'avatar': '🤖'})

    
    if role == "User":
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=message.get("avatar")):
                st.markdown(message["content"])

        # Use the stored user question or the user input
        user_question = st.session_state.user_question or st.chat_input("Ask a question on 's Unify product")
        
        # Handle the question if provided
        if user_question:
            st.session_state.user_question = ""  # Clear the stored question after usage
            with st.chat_message('User', avatar='👨🏻‍💻'):
                st.markdown(user_question)
                st.session_state.messages.append({'role': 'User', 'content': user_question, 'avatar': '👨🏻‍💻'})

            with st.chat_message('Assistant', avatar='🤖'):
                response = user_input(user_question, st.session_state.chat_history)
                st.write(response)
                st.session_state.messages.append({'role': 'Assistant', 'content': response, 'avatar': '🤖'})
                

        # Conditionally display feedback buttons if a response exists
        if st.session_state.messages and st.session_state.messages[-1]["role"] == 'Assistant':
            # Feedback Section
            user_col1, user_col2 = st.columns([2, 25])
            with user_col1:
                feedback_button_neg = st.button('👎🏻')
            with user_col2:
                feedback_button_pos = st.button('👍🏻')

            # Automatically submit feedback when either thumbs-up or thumbs-down is clicked
            if (feedback_button_neg or feedback_button_pos) and st.session_state.chat_history:
                generated_answer = st.session_state.chat_history[-1]
                user_question = st.session_state.chat_history[-2]
                question_number = len(st.session_state.chat_history)

                # Prepare feedback message
                st.session_state.user_feedback.append(f"{int(question_number / 2)}. Question: {user_question}")
                st.session_state.user_feedback.append(f" Answer: {generated_answer}")
                feedback_type = "Positive" if feedback_button_pos else "Negative"
                st.session_state.user_feedback.append(f" Feedback: {feedback_type}")

                # Submit feedback
                feedback_file = "feedback.txt"
                with open(feedback_file, "a" if os.path.exists(feedback_file) else "w", encoding="utf-8") as file:
                    for content in st.session_state.user_feedback:
                        file.write(content + "\n")
                st.session_state.user_feedback = []  # Clear feedback after submission
                st.success("Thank you for your feedback, we will add the data and retrain the model.")

    elif role == "Admin" and st.session_state.is_admin:
        # Admin Interface for uploading documents
        st.header("Admin Dashboard")
        
        tab1, tab2 = st.tabs(["Document Upload", "User Management"])
        
        with tab1:
            pdf_docs = st.file_uploader('Upload documents to train the chatbot', accept_multiple_files=True)
            if st.button('Submit Data') and pdf_docs:
                with st.spinner('Processing...'):
                    raw_text = get_pdf_text(pdf_docs)
                    chunks = get_text_chunks(raw_text)
                    vector_store(chunks)
                    st.success('Data has been successfully processed!')
        
        with tab2:
            # User management section for admins
            st.subheader("Current Users")
            
            # Display existing users in a more structured format
            users_data = []
            for username, user_data in config['credentials']['usernames'].items():
                users_data.append({
                    "Username": username,
                    "Name": user_data.get('name', ''),
                    "Email": user_data.get('email', ''),
                    "Role": "Admin" if is_admin(username, config) else "User"
                })
            
            st.table(users_data)
            
            # Add new user form
            st.subheader("Add New User")
            with st.form("add_user_form"):
                new_username = st.text_input("Username")
                new_name = st.text_input("Name")
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["User", "Admin"])
                
                submit_user = st.form_submit_button("Add User")
                
                if submit_user and new_username and new_password:
                    if new_username in config['credentials']['usernames']:
                        st.error(f"Username '{new_username}' already exists!")
                    else:
                        # Add user to credentials with plaintext password
                        config['credentials']['usernames'][new_username] = {
                            'name': new_name,
                            'email': new_email,
                            'password': new_password  # Store password as plaintext
                        }
                        
                        # Add to admin_users if role is Admin
                        if new_role == "Admin" and 'admin_users' in config:
                            config['admin_users'].append(new_username)
                        
                        # Save updated config
                        with open('config.yaml', 'w') as file:
                            yaml.dump(config, file)
                        
                        st.success(f"User '{new_username}' added successfully!")
                        st.info("Please refresh the page to see the updated user list.")

if __name__ == "__main__":
    main()