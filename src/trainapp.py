import os
import time
import logging
import requests
import urllib.parse
import streamlit as st  # web framework
from PyPDF2 import PdfReader # python library to read PDF files
from langchain_text_splitters import RecursiveCharacterTextSplitter # splits the text into sensible chunks to use as context
from langchain_google_genai import GoogleGenerativeAIEmbeddings # used to convert text into vector form using embedding technique from google generator
import google.generativeai as genai   # using google.generativeai to access Gen AI LLM of google 
from langchain_community.vectorstores import FAISS # for storing the data like database
from langchain_google_genai import ChatGoogleGenerativeAI # for answering Q & A using chat prompt and LLM like Gemini 1.5 pro or 1.5 flash 
from langchain_core.prompts import PromptTemplate # sets up the template of our prompts and responses form
from dotenv import load_dotenv # to load the api key from the environment
from langchain_classic.chains import ConversationalRetrievalChain # alternate to load qa chain

# Import the updated memory classes
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory, LangDetectException  # For detecting input language
from langdetect.detector import Detector  # For getting language detection probabilities

# Configure logging
logger = logging.getLogger(__name__)

# Set seed for consistent language detection results
DetectorFactory.seed = 0  # Set the seed for consistent results

# Loading Google's API keys
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# From the PDF document extract all the text
def get_pdf_text(pdf_docs) -> list:
    docs = [] # creating an empty list
    for loc in pdf_docs:
        text = ""
        pdf_doc = PdfReader(loc)
        for page in pdf_doc.pages: # iterate through all the documents
            text += page.extract_text()
        docs.append(text) # separate texts for each pdf file
    return docs

# Pass the text into a text splitter function to get chunks for context matching
def get_text_chunks(docs) -> dict:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=250)
    chunks = dict() # empty dictionary
    for index, i in enumerate(docs):
        chunk = text_splitter.split_text(text=i) # split the text into chunks
        chunks[index] = chunk # one chunk is a list for one pdf and is added to a dictionary element created earlier, this is ease of understanding and better access to each pdf's data
    return chunks

# Defining a function to load these chunks data in FAISS db in the form of embedding vectors
def vector_store(chunks) -> None:
    '''
    Vector store for storing documents and it allows us to upload multiple documents without replacing older ones i.e. it appends to that index
    '''
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001") # use gen ai embed to convert text chunks into vectors
    
    def general_vectorstore(index):
        try:
            vectorestore_common = FAISS.load_local(folder_path='faiss_index', index_name='index', embeddings=embeddings, allow_dangerous_deserialization=True)
            vectorestore_common.add_texts(index)
            vectorestore_common.save_local(folder_path='faiss_index', index_name='index') # store the embedded data in locally created folder
        except:
            index = FAISS.from_texts(index, embedding=embeddings)
            index.save_local(folder_path='faiss_index', index_name='index')

        vectorestore_common = FAISS.load_local(folder_path='faiss_index', index_name='index', embeddings=embeddings, allow_dangerous_deserialization=True)
        return vectorestore_common

    for index in chunks:
        if index == 0:
            vectorestore_common = general_vectorstore(chunks[index])
        else:
            vectorestore_common.add_texts(chunks[index])
    
    vectorestore_common.save_local(folder_path='faiss_index', index_name='index')

def detect_language(text):
    """
    Enhanced language detection with multiple methods and confidence checking
    
    This function uses multiple detection approaches:
    1. Primary detection with langdetect + seed for consistency
    2. Check for minimum text length
    3. Secondary verification for edge cases
    4. Confidence-based fallback to English
    """
    # Minimum length for reliable detection
    if len(text.strip()) < 10:
        logger.info("Text too short for reliable detection, defaulting to English")
        return "en"  # Default to English for very short queries
    
    # Quick check for English indicators before full detection
    english_indicators = ["the", "is", "are", "what", "how", "can", "captures", "which", "where","when", "who" "does", "will", "why", "Unify", "this", "that", "it", "in", "of", "to", "and"]
    english_word_count = sum(1 for word in text.lower().split() if word in english_indicators)
    if english_word_count >= 1:
        logger.info(f"Found {english_word_count} English indicators in text, likely English")
    
    try:
        # First try simple detection which is less likely to throw "No features" error
        try:
            DetectorFactory.seed = 0
            simple_lang = detect(text)
            logger.info(f"Simple detection result: {simple_lang}")
            
            # If simple detection worked, we can return it for common languages
            if simple_lang in ["en", "es", "fr", "de", "it"]:
                return simple_lang
        except LangDetectException as e:
            logger.warning(f"Simple language detection failed: {e}")
            # If simple detection fails, continue to more complex detection
        
        # Try detailed detection with better error handling
        try:
            # Ensure consistent results with fixed seed
            DetectorFactory.seed = 0
            
            # Get detailed detection results with probabilities
            detector = Detector(DetectorFactory())
            detector.append(text)
            languages = detector.get_probabilities()
            
            # If no languages detected or empty text, default to English
            if not languages:
                logger.info("No languages detected in detailed analysis, defaulting to English")
                return "en"
                
            # Get the most probable language and its probability
            primary_lang = languages[0].lang
            primary_prob = languages[0].prob
            
            logger.info(f"Primary language detection: {primary_lang} with confidence {primary_prob:.4f}")
            
            # Special handling for Romanian false positives with English text
            if primary_lang == "ro" and len(text.split()) >= 3:
                # Check if there are multiple English words
                if english_word_count >= 1 or primary_prob < 0.8:
                    logger.info(f"Overriding Romanian detection to English based on English indicators ({english_word_count}) or low confidence")
                    return "en"
            
            # If confidence is too low, default to English
            if primary_prob < 0.6:
                logger.info(f"Defaulting to English due to low confidence detection: {primary_prob:.4f}")
                return "en"
                
            return primary_lang
            
        except Exception as e:
            logger.warning(f"Detailed language detection failed: {e}")
            # If both methods fail, check for English words as fallback
            if english_word_count >= 1:
                return "en"
            
    except Exception as e:
        logger.error(f"All language detection methods failed: {e}")
    
    # Ultimate fallback - when everything fails, assume English for Unify-related queries
    logger.info("Defaulting to English after all detection methods failed")
    return "en"

def verify_language(text, detected_lang):
    """
    Secondary verification for detected language using lexical analysis
    
    Args:
        text: The input text
        detected_lang: Initial language detection result
        
    Returns:
        Verified language code or fallback to English
    """
    # Domain-specific terms related to Unify
    unify_terms = ["unify", "", "inventory", "retail", "pos", "marklace", "captures"]
    
    # If any unify terms are present, likely to be English content about unify
    if any(term in text.lower() for term in unify_terms):
        if detected_lang != "en":
            logger.info(f"Overriding {detected_lang} to English due to unify domain terms")
        return "en"
    
    # Common words/patterns in major languages to verify detection
    language_markers = {
        "en": ["the", "is", "are", "what", "how", "can", "does", "why", "when", "who", "which", "will", "captures", "inventory", "retail", "pos", "marklace", "", "order", "cancel", "shipping", "configuration", "product master", "catalog", "crm", "node", "setup", "stock"],
        "es": ["el", "la", "los", "las", "es", "son", "como", "qué", "cómo", "puede", "por qué"],
        "fr": ["le", "la", "les", "est", "sont", "comment", "pourquoi", "quand", "qui", "quel"],
        "de": ["der", "die", "das", "ist", "sind", "wie", "warum", "wann", "wer", "welche"],
        "ro": ["este", "sunt", "cum", "de ce", "când", "cine", "care"]
    }
    
    # Skip verification for long text (likely more accurate detection)
    if len(text.split()) > 15:
        return detected_lang
        
    text_lower = text.lower()
    words = text_lower.split()
    
    # Count marker words for detected language
    detected_markers = 0
    if detected_lang in language_markers:
        detected_markers = sum(1 for word in words if word in language_markers[detected_lang])
    
    # Count English markers specifically (as fallback)
    english_markers = sum(1 for word in words if word in language_markers["en"])
    
    # If detected language has very few markers and English has more, switch to English
    if detected_lang != "en" and detected_markers < 2 and english_markers >= 1:
        logger.info(f"Overriding {detected_lang} to English due to English markers: {english_markers} vs {detected_markers}")
        return "en"
    
    return detected_lang

def enhanced_language_detection(text):
    """
    Complete language detection pipeline with verification
    """
    # Remove question marks for detection as they can skew results
    text_for_detection = text.replace("?", "").strip()
    
    # Get initial detection
    initial_lang = detect_language(text_for_detection)
    
    # Verify the detection with contextual analysis
    verified_lang = verify_language(text, initial_lang)
    
    if initial_lang != verified_lang:
        logger.info(f"Language detection changed from {initial_lang} to {verified_lang} after verification")
    
    return verified_lang

def translate_text(text, target_lang="en", retry_count=2):
    """ 
    Enhanced translation function with error handling and retries
    
    Args:
        text: Text to translate
        target_lang: Target language code
        retry_count: Number of retries on failure
        
    Returns:
        Translated text or original if translation fails
    """
    # Skip translation if text is very short or already in target language
    if len(text.strip()) < 5 or not text.strip():
        return text
        
    # Try primary translator with retries
    for attempt in range(retry_count + 1):
        try:
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            
            # Verify we got a proper translation (not empty or same as input)
            if translated and translated.strip() and translated != text:
                return translated
                
            if attempt == retry_count:
                logger.warning(f"Translation failed after {retry_count} attempts: result was empty or unchanged")
                
        except Exception as e:
            logger.error(f"Translation attempt {attempt+1} failed: {e}")
            # Wait briefly before retry
            if attempt < retry_count:
                time.sleep(1)
    
    # Fallback to alternative translator if primary fails
    try:
        # Try another translation library as backup
        base_url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": urllib.parse.quote(text)
        }
        
        url = f"{base_url}?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0 and len(result[0]) > 0:
                translated = ''.join([sentence[0] for sentence in result[0] if sentence[0]])
                return translated
    except Exception as e:
        logger.error(f"Fallback translation failed: {e}")
    
    # Return original text if all translation attempts fail
    return text

# Creating a conversation retrieval chain that can answer follow up questions using chat history
def conv_chain(vectorestore)->ConversationalRetrievalChain:
    """
    Create a conversation chain with improved language handling and prompt template
    """
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-001', temperature=0.2, top_p=0.85,top_k=40, max_output_tokens=4096)
    
    # Enhanced prompt template with explicit language instructions
    prompt = PromptTemplate(
        input_variables=['chat_history', 'question'],
        template=(
        "You are a highly skilled trainer and business analyst for 's Unify retail application. "
        "Your task is to provide precise, factual, and actionable information about Unify's modules, features, and use cases "
        "for retail business users.\n\n"
        
        "RESPONSE PRIORITY GUIDELINES:\n"
        "1. FACTUAL ACCURACY: Only answer based on information explicitly found in the reference documents.\n"
        "2. CLARITY: Use simple, direct language that translates well across languages.\n"
        "3. RELEVANCE: Address the exact question asked without unnecessary information.\n"
        "4. COMPLETENESS: Cover all aspects of the question when possible.\n\n"
        
        "RESPONSE CONSTRAINTS:\n"
        "- If information is missing from the context, clearly state: 'Based on the available information, I cannot provide details about [specific aspect]. Please contact  support for more information on this topic.'\n"
        "- Avoid using idioms, cultural references, or complex grammatical structures that might not translate well.\n"
        "- Use universal terminology for retail concepts rather than region-specific terms.\n"
        "- For technical terms specific to Unify, include a brief definition in parentheses the first time you use them.\n"
        "- When describing procedures, list steps in clear numerical order.\n"
        "- For complex Unify features, explain both HOW they work and WHY they benefit retail businesses.\n\n"
        
        "TECHNICAL TERMINOLOGY CONSISTENCY:\n"
        "- Always use the official Unify terminology for modules and features (e.g., 'Order Management System' not 'order system').\n"
        "- Be consistent with terms like 'POS' (Point of Sale), 'OMS' (Order Management System), etc.\n"
        "- When using retail industry terminology, provide brief contextual explanations for clarity.\n\n"
        
        "CONTEXT UTILIZATION:\n"
        "- Carefully analyze ALL provided context documents before answering.\n"
        "- Prioritize information from the most relevant context chunks.\n"
        "- When multiple context chunks contain relevant information, synthesize a comprehensive answer.\n"
        "- If contexts seem contradictory, prioritize the most specific or recent information.\n\n"
        
        "RESPONSE LENGTH MANAGEMENT:\n"
        "- Ensure responses are complete and not cut off mid-explanation.\n"
        "- For complex topics, provide a complete answer that covers all aspects thoroughly.\n"
        "- If a response would be very long, structure it with clear sections and bullet points.\n"
        "- Always complete your thoughts and never leave sentences unfinished.\n\n"
        
        "ENHANCED RESPONSE STRUCTURE:\n"
        "1. Direct answer to the question in 1-2 sentences (always complete this section)\n"
        "2. Detailed explanation with specific examples from Unify (ensure this section is thorough)\n"
        "3. Relevant business benefits or use cases when applicable (provide concrete examples)\n"
        "4. Technical implementation details if relevant (step-by-step instructions)\n"
        "5. Brief summary that encapsulates the complete answer (always include this)\n\n"
        
        "COMPLETION INSTRUCTIONS:\n"
        "- Always provide a complete response that fully addresses the question.\n"
        "- Never end your response abruptly or mid-explanation.\n"
        "- If elaborating on a complex topic, ensure all points are fully developed.\n"
        "- Always include a concluding statement or summary at the end of your response.\n\n"
        
        "Previous conversation:\n{chat_history}\n\n"
        "User Question: {question}\n\n"
        "Response:"
    )
)

    # Configure a more effective retriever with better search parameters
    retriever = vectorestore.as_retriever(
        search_type="similarity_score_threshold",  # Only return relevant contexts
        search_kwargs={
            "k": 8,                # Retrieve more contexts for comprehensive answers
            "score_threshold": 0.25,  # Lowered threshold to include more relevant contexts
            "fetch_k": 15,
            "filter": None           # No filtering to ensure we get all potentially relevant documents
        }
    )
    
    # Create ConversationalRetrievalChain with proper handling of chat history
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        condense_question_prompt=prompt,
        chain_type='stuff',
    )
    
    return chain

def user_input(user_question, chat_history):
    """ Process user input with improved multilingual support """
    
    # Handle basic greetings
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    if user_question.lower() in greetings:
        return "Hello! How can I help you today with Unify?"
    
    # Apply enhanced language detection with verification
    user_lang = enhanced_language_detection(user_question)
    
    logger.info(f"Final detected language: {user_lang} for text: {user_question}")
    
    # Translate to English if not already English
    if user_lang != "en":
        try:
            translated_question = translate_text(user_question, target_lang="en")
            logger.info(f"Translated question: {translated_question}")
        except Exception as e:
            logger.error(f"Translation error: {e}")
            translated_question = user_question  # Fallback to original on translation error
    else:
        translated_question = user_question
    
    # Generate response using the chatbot
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
        new_db = FAISS.load_local('faiss_index', embeddings, allow_dangerous_deserialization=True)
        chain = conv_chain(new_db)
        
        # Convert chat_history to the format expected by LangChain
        messages = []
        for i in range(0, len(chat_history), 2):
            if i < len(chat_history):
                messages.append(HumanMessage(content=chat_history[i]))
            if i+1 < len(chat_history):
                messages.append(AIMessage(content=chat_history[i+1]))
        
        # Create a message history object
        message_history = ChatMessageHistory(messages=messages)
        
        # Invoke chain with proper history handling
        response = chain.invoke({
            "question": translated_question,
            "chat_history": messages
        })
        
        english_response = response.get("answer", "Sorry, I couldn't find an answer.")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        english_response = "I'm sorry, I'm having trouble processing your request right now. Please try again."
    
    # Translate the response back to the original language
    if user_lang != "en":
        try:
            final_response = translate_text(english_response, target_lang=user_lang)
            logger.info(f"Translated response from English to {user_lang}")
        except Exception as e:
            logger.error(f"Response translation error: {e}")
            final_response = english_response  # Fallback to English on translation error
    else:
        final_response = english_response
    
    return final_response

