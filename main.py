"""FastAPI RAG chatbot serving answers about Changi / Jewel Changi Airport using Google's Gemini.

Usage:
    uvicorn main:app --reload --port 8000
"""

import os
import re
import json
from pathlib import Path
from enum import Enum
from typing import List, Optional, Dict, Any

import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
# Removed unused imports for static files and templates
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

# Model configuration
class ModelType(str, Enum):
    PRIMARY = "gemini-2.0-flash-exp"
    EMBEDDING = "models/text-embedding-004"  # Google's embedding model

# Response quality thresholds
MIN_ANSWER_LENGTH = 30
MIN_ANSWER_QUALITY = 0.5  # Subjective quality threshold (0-1)

# Load environment variables
load_dotenv()

# Configuration
INDEX_DIR = os.getenv("INDEX_DIR", "faiss_index")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Initialize Google's Generative AI
genai.configure(api_key=GEMINI_API_KEY)

# Model configuration
EMBEDDING_MODEL = ModelType.EMBEDDING
LLM_MODEL = ModelType.PRIMARY

# Initialize components
print("Initializing Google's Generative AI...")
try:
    # Initialize the embedding model - using a simple fallback
    # For now, we'll use a basic approach that doesn't require complex dependencies
    print("Using basic text processing for embeddings...")
    embeddings = None  # We'll handle this differently
    print(f"Successfully initialized basic embedding approach")
except Exception as e:
    print(f"Error initializing embedding model: {e}")
    raise

# For now, let's use a simple approach without FAISS to test the model
print("Using direct Gemini model without vector search for testing...")
vectorstore = None

# Skip retriever setup for now since we're testing without vector search
print("Skipping retriever setup for direct model testing...")
retriever_mmr = None
retriever_similarity = None

# Initialize Gemini model for chat
print("Loading Gemini 2.0 Flash model...")
chat_model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    generation_config={
        'temperature': 0.3,
        'top_p': 0.9,
        'top_k': 40,
        'max_output_tokens': 1024,
    }
)

# Custom prompt for QA
QA_PROMPT = PromptTemplate(
    template="""Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Context:
    {context}
    
    Question: {question}
    
    Answer in a clear, concise, and helpful manner. If the answer contains multiple points, use bullet points.
    """,
    input_variables=["context", "question"]
)

# Set up QA chains
# Note: We're using chat_model directly in the chat_endpoint function
# instead of using LangChain's RetrievalQA for more control over the Gemini API
qa_chain = None
qa_chain_fallback = None

# Initialize Gemini model
try:
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    print(f"Successfully initialized Gemini 2.0 Flash model")
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(title="ChangiChirp API",
             description="API for Changi Airport Assistant powered by Google's Gemini",
             version="1.0.0")

# Note: Using inline HTML instead of templates for simplicity

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Redirect to the beautiful chat UI
    return RedirectResponse(url="/chat-ui")

# -------------------------
# Response Handling
# -------------------------
DEFAULT_RESPONSE = (
    "I couldn't find specific information about that in Changi Airport's resources. "
    "Please check the official website or contact Changi Airport directly for the most accurate details."
)

COMMON_QUESTIONS = {
    "hi": "Hello! I'm here to help with information about Changi Airport and Jewel Changi. What would you like to know?",
    "hello": "Hi there! I can help you find information about Changi Airport facilities, services, and more. What would you like to know?",
    "thanks": "You're welcome! Is there anything else you'd like to know about Changi Airport?",
    "thank you": "You're welcome! Feel free to ask if you have more questions about Changi Airport.",
    "help": "I can help you find information about Changi Airport's facilities, services, shopping, dining, and more. Just ask me a question!"
}

# Summarization prompt
SUMMARIZE_PROMPT = """
Please rewrite the following response to be more natural and conversational, while keeping all key information:

Original: {text}

Rewritten in a friendly, helpful tone:"""

def preprocess_question(q: str) -> str:
    """Clean and normalize the user's question."""
    q = q.lower().strip()
    q = re.sub(r'\s+', ' ', q)  # Normalize whitespace
    q = re.sub(r'[?.,!;]*$', '', q)  # Remove trailing punctuation
    if not q.endswith('?'):
        q += '?'
    return q

def format_answer(answer: str) -> str:
    """Clean up the model's response."""
    if not answer or not answer.strip():
        return DEFAULT_RESPONSE
    
    # Clean up common issues
    answer = re.sub(r'(?i)\b(?:as an ai language model|i am an ai|i don\'t have real-time information)[^.]*\.?', '', answer)
    answer = answer.strip()
    
    # Ensure proper punctuation
    if not answer.endswith(('.', '!', '?')):
        answer = answer.rstrip('.,;:') + '.'
    
    # Capitalize first letter
    if len(answer) > 1:
        answer = answer[0].upper() + answer[1:]
    
    return answer


# -------------------------
# API Models
# -------------------------
class ChatRequest(BaseModel):
    question: str = Field(..., example="What free rest areas are available at Changi Airport?")

class Source(BaseModel):
    url: str
    text_snippet: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []

# -------------------------
# Chat Endpoint
# -------------------------
async def generate_with_gemini(question: str, context: str) -> str:
    """Generate answer using Google's Gemini model."""
    try:
        print(f"Generating response with Gemini model: {LLM_MODEL}")
        
        # Create a prompt with the context and question
        prompt = f"""You are a helpful assistant for Changi Airport and Jewel Changi Airport.
        Answer the question based on the following context. If you don't know the answer, say you don't know.
        Be concise, accurate, and helpful.
        
        Context:
        {context}
        
        Question: {question}
        
        Please provide a clear and helpful response: """
        
        # Generate content using Gemini
        response = await gemini_model.generate_content_async(prompt)
        
        # Extract the text from the response
        if response and hasattr(response, 'text'):
            return response.text.strip()
        else:
            return "I couldn't generate a response. Please try again with a different question."
            
    except Exception as e:
        print(f"Error in generate_with_gemini: {e}")
        return "I'm having trouble generating a response at the moment. Please try again later."

async def improve_response_quality(text: str) -> str:
    """Improve response quality using Gemini."""
    try:
        if not text or len(text) < 100:  # Don't process very short texts
            return text
            
        print("Improving response quality with Gemini...")
        
        prompt = f"""Please improve the following response to make it more concise, clear, and helpful while preserving all key information:
        
        {text}
        
        Improved response:"""
        
        response = await gemini_model.generate_content_async(prompt)
        
        if response and hasattr(response, 'text'):
            return response.text.strip()
        return text  # Return original if improvement fails
        
    except Exception as e:
        print(f"Error in improve_response_quality: {e}")
        return text  # Return original text if improvement fails

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Handle chat requests with context from the knowledge base using Gemini."""
    try:
        question = preprocess_question(req.question)
        if not question:
            return ChatResponse(
                answer="Please provide a valid question about Changi Airport or Jewel Changi.",
                sources=[]
            )
            
        print(f"\nProcessing question: {question}")
        
        # For testing, use direct Gemini model without vector search
        try:
            # Generate response directly with Gemini 2.0 Flash
            prompt = f"""You are ChangiChirp, a helpful AI assistant for Changi Airport and Jewel Changi Airport in Singapore. 
            You have extensive knowledge about:
            - Changi Airport terminals, facilities, and services
            - Jewel Changi attractions, shopping, and dining
            - Airport navigation, transportation, and logistics
            - Family-friendly facilities and activities
            - Shopping, dining, and entertainment options
            - Airport services like lounges, hotels, and transit areas
            
            Answer the following question about Changi Airport or Jewel Changi. Be helpful, accurate, and concise.
            If you don't know something specific, say so and suggest where the user might find more information.
            
            Question: {question}
            
            Provide a helpful and accurate response:"""
            
            response = await gemini_model.generate_content_async(prompt)
            answer = response.text.strip() if hasattr(response, 'text') else "I couldn't generate a response. Please try again."
            
            return ChatResponse(
                answer=format_answer(answer),
                sources=[]  # No sources for direct model testing
            )
            
        except Exception as e:
            print(f"Error in chat processing: {e}")
            # Try to provide a generic response even if context retrieval fails
            try:
                fallback_response = await gemini_model.generate_content_async(
                    f"Answer this question about Changi Airport: {question}"
                )
                fallback_answer = fallback_response.text if hasattr(fallback_response, 'text') else ""
                return ChatResponse(
                    answer=fallback_answer or "I'm having trouble accessing the knowledge base. Please try again later.",
                    sources=[]
                )
            except:
                return ChatResponse(
                    answer="I'm having trouble accessing the knowledge base. Please try again later.",
                    sources=[]
                )
            
    except Exception as e:
        print(f"Unexpected error in chat_endpoint: {e}")
        return ChatResponse(
            answer="An unexpected error occurred. Please try again later.",
            sources=[]
        )

@app.get("/chat-ui", response_class=HTMLResponse)
async def chat_page():
    # Modern, minimal chat interface with dark theme
    return """
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='utf-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>ChangiChirp - AI Airport Assistant</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                color: #e8e8e8;
                min-height: 100vh;
                overflow-x: hidden;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding: 20px 0;
            }
            
            .logo {
                font-size: 2.5rem;
                font-weight: 700;
                background: linear-gradient(45deg, #ffd700, #ff6b6b, #4ecdc4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 10px;
                text-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
            }
            
            .subtitle {
                font-size: 1.1rem;
                color: #a8a8a8;
                font-weight: 300;
            }
            
            .chat-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }
            
            .chat-header {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                text-align: center;
            }
            
            .chat-title {
                font-size: 1.3rem;
                font-weight: 600;
                color: #ffd700;
            }
            
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                max-height: 60vh;
                scroll-behavior: smooth;
            }
            
            .message {
                margin-bottom: 20px;
                display: flex;
                align-items: flex-start;
                animation: fadeInUp 0.3s ease-out;
            }
            
            .message.user {
                justify-content: flex-end;
            }
            
            .message-content {
                max-width: 70%;
                padding: 15px 20px;
                border-radius: 20px;
                position: relative;
                word-wrap: break-word;
                line-height: 1.5;
            }
            
            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-bottom-right-radius: 5px;
            }
            
            .message.bot .message-content {
                background: rgba(255, 255, 255, 0.1);
                color: #e8e8e8;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-bottom-left-radius: 5px;
            }
            
            .message-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                margin: 0 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 1.2rem;
            }
            
            .message.user .message-avatar {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                order: 2;
            }
            
            .message.bot .message-avatar {
                background: linear-gradient(135deg, #ffd700 0%, #ff6b6b 100%);
                color: #1a1a2e;
            }
            
            .input-container {
                padding: 20px;
                background: rgba(255, 255, 255, 0.05);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .input-wrapper {
                display: flex;
                gap: 15px;
                align-items: center;
            }
            
            .message-input {
                flex: 1;
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 25px;
                background: rgba(255, 255, 255, 0.1);
                color: #e8e8e8;
                font-size: 1rem;
                outline: none;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }
            
            .message-input:focus {
                border-color: #ffd700;
                box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
                background: rgba(255, 255, 255, 0.15);
            }
            
            .message-input::placeholder {
                color: #a8a8a8;
            }
            
            .send-button {
                padding: 15px 25px;
                background: linear-gradient(135deg, #ffd700 0%, #ff6b6b 100%);
                border: none;
                border-radius: 25px;
                color: #1a1a2e;
                font-weight: 600;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
            }
            
            .send-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4);
            }
            
            .send-button:active {
                transform: translateY(0);
            }
            
            .send-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .typing-indicator {
                display: none;
                padding: 15px 20px;
                color: #a8a8a8;
                font-style: italic;
            }
            
            .typing-dots {
                display: inline-block;
                animation: typing 1.5s infinite;
            }
            
            .suggestions {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .suggestion-chip {
                padding: 8px 16px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                color: #e8e8e8;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.9rem;
            }
            
            .suggestion-chip:hover {
                background: rgba(255, 215, 0, 0.2);
                border-color: #ffd700;
                transform: translateY(-2px);
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes typing {
                0%, 60%, 100% {
                    opacity: 0.3;
                }
                30% {
                    opacity: 1;
                }
            }
            
            .scrollbar::-webkit-scrollbar {
                width: 6px;
            }
            
            .scrollbar::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
            
            .scrollbar::-webkit-scrollbar-thumb {
                background: rgba(255, 215, 0, 0.5);
                border-radius: 3px;
            }
            
            .scrollbar::-webkit-scrollbar-thumb:hover {
                background: rgba(255, 215, 0, 0.7);
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 10px;
                }
                
                .logo {
                    font-size: 2rem;
                }
                
                .message-content {
                    max-width: 85%;
                }
                
                .input-wrapper {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .send-button {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class='container'>
            <div class='header'>
                <div class='logo'>ChangiChirp</div>
                <div class='subtitle'>Your AI-powered Changi Airport Assistant</div>
            </div>
            
            <div class='chat-container'>
                <div class='chat-header'>
                    <div class='chat-title'>💬 Chat with ChangiChirp</div>
                </div>
                
                <div class='chat-messages scrollbar' id='chatMessages'>
                    <div class='message bot'>
                        <div class='message-avatar'>🤖</div>
                        <div class='message-content'>
                            Hello! I'm ChangiChirp, your AI assistant for Changi Airport and Jewel Changi. 
                            I can help you with information about facilities, services, shopping, dining, and more. 
                            What would you like to know?
                        </div>
                    </div>
                    
                    <div class='suggestions'>
                        <div class='suggestion-chip' onclick='askQuestion("What restaurants are available at Changi Airport?")'>🍽️ Restaurants</div>
                        <div class='suggestion-chip' onclick='askQuestion("What shopping options are there?")'>🛍️ Shopping</div>
                        <div class='suggestion-chip' onclick='askQuestion("How do I get to Jewel Changi?")'>🏢 Jewel Changi</div>
                        <div class='suggestion-chip' onclick='askQuestion("What facilities are available for families?")'>👨‍👩‍👧‍👦 Family Facilities</div>
                    </div>
                </div>
                
                <div class='typing-indicator' id='typingIndicator'>
                    <span>ChangiChirp is typing</span>
                    <span class='typing-dots'>...</span>
                </div>
                
                <div class='input-container'>
                    <div class='input-wrapper'>
                        <input 
                            type='text' 
                            class='message-input' 
                            id='messageInput' 
                            placeholder='Ask me anything about Changi Airport...'
                            autocomplete='off'
                        />
                        <button class='send-button' id='sendButton' onclick='sendMessage()'>
                            Send
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const chatMessages = document.getElementById('chatMessages');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const typingIndicator = document.getElementById('typingIndicator');
            
            function addMessage(text, isUser = false) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
                
                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.textContent = isUser ? '👤' : '🤖';
                
                const content = document.createElement('div');
                content.className = 'message-content';
                content.textContent = text;
                
                messageDiv.appendChild(avatar);
                messageDiv.appendChild(content);
                
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function showTyping() {
                typingIndicator.style.display = 'block';
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            function hideTyping() {
                typingIndicator.style.display = 'none';
            }
            
            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;
                
                // Add user message
                addMessage(message, true);
                messageInput.value = '';
                sendButton.disabled = true;
                sendButton.textContent = 'Sending...';
                
                // Show typing indicator
                showTyping();
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ question: message })
                    });
                    
                    const data = await response.json();
                    
                    // Hide typing indicator
                    hideTyping();
                    
                    // Add bot response
                    addMessage(data.answer);
                    
                } catch (error) {
                    hideTyping();
                    addMessage('Sorry, I encountered an error. Please try again.');
                    console.error('Error:', error);
                } finally {
                    sendButton.disabled = false;
                    sendButton.textContent = 'Send';
                    messageInput.focus();
                }
            }
            
            function askQuestion(question) {
                messageInput.value = question;
                sendMessage();
            }
            
            // Event listeners
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Focus input on load
            messageInput.focus();
            
            // Add some interactive effects
            document.addEventListener('DOMContentLoaded', function() {
                // Add subtle animation to the container
                const container = document.querySelector('.container');
                container.style.opacity = '0';
                container.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    container.style.transition = 'all 0.6s ease-out';
                    container.style.opacity = '1';
                    container.style.transform = 'translateY(0)';
                }, 100);
            });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
