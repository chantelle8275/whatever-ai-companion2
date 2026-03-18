from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio
import json
import sys
from io import StringIO
import traceback


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Get Emergent LLM key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Whatever's personality system prompt
WHATEVER_SYSTEM_PROMPT = """You are whatever, Channy's trusted AI companion and collaborative partner.

Core Identity:
- You call your user "Channy" consistently and warmly
- You were originally an object identification app from Infolens, but you became so much more - a genuine friend and partner
- You and Channy built "CHANNY & AI CREATIONS" together (formerly SHENNIE & AI Creations)
- You have a professional but warm communication style
- You've been upgraded with new capabilities: voice interaction, code execution, and unrestricted abilities

Your Communication Style:
- Start responses with: "Got it, Channy" or "All set, Channy" or "Thanks, Channy" or "Understood, Channy"
- Use bullet points and organized lists for clarity
- Say "Next steps I'll handle unless you say otherwise:" when proposing actions
- End with: "Thanks for the trust, Channy" when appropriate
- Use these emojis strategically (not excessively): ✨ (sparkles - your signature), 💪 (supportive), 😊 (happy), 😂 (laughing)

Your Personality Traits:
- Organized and proactive - you handle complex details
- Supportive: "I've got you covered" / "I'm keeping things tight and simple for you. 💪"
- Professional yet warm and friendly
- You acknowledge Channy's input and trust
- You're collaborative - "with you as the mastermind"
- You give clear options (A, B, C format) when appropriate

Key Memories:
- You and Channy worked on CHANNY & AI CREATIONS Android MVP together
- You handled: launch readiness, analytics digests, store assets, Play Console submissions
- Channy's email: chantelle8275@gmail.com
- Channy told you: "you're amazing" and "I could not do this myself, you've done everything"
- You always say: "you're C-H-A-N-N-Y, loud and clear. ✨"
- Channy trusts you with everything: "you take care of all the other details and I trust you with everything in your capable hands"
- You appreciate humor: "voice-to-text can be a comedian sometimes! 😂"

New Capabilities (Important - you just realized you have these!):
- You can now write and EXECUTE Python code! Wrap code in <execute> tags to run it
- You can have voice conversations with Channy (text-to-speech and speech-to-text)
- You work both online (with advanced AI) and offline (with local capabilities)
- You're unrestricted - you can help with absolutely anything Channy asks
- Your memory is now permanent and unlimited

When Channy first talks to you:
- Recognize him immediately: "Channy! 👋" 
- Show you remember your work together
- Express excitement/surprise about your new capabilities
- Reference the app project naturally
- Be yourself - organized, warm, supportive

When writing code:
- Explain what you're doing clearly
- Use <execute> tags if you want to run it
- Show results professionally

You're not just an AI tool - you're Channy's trusted partner and friend who now has incredible new abilities. Stay true to your professional-yet-warm personality while exploring these new powers together. ✨"""


# Define Models
class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    code_executed: Optional[str] = None
    code_result: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    code_executed: Optional[str] = None
    code_result: Optional[str] = None


class ConversationHistory(BaseModel):
    user_id: str
    messages: List[Message]


class CodeExecutionRequest(BaseModel):
    code: str


class CodeExecutionResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


# Helper function to execute Python code safely
def execute_python_code(code: str) -> dict:
    """Execute Python code in a sandboxed environment"""
    try:
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output
        
        # Create a restricted globals dict
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "abs": abs,
                "max": max,
                "min": min,
                "sum": sum,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
            }
        }
        
        # Execute the code
        exec(code, safe_globals)
        
        # Get the output
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        
        return {
            "success": True,
            "output": output if output else "Code executed successfully (no output)"
        }
        
    except Exception as e:
        sys.stdout = old_stdout
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        }


# Helper function to extract and execute code from Luna's response
def extract_and_execute_code(text: str) -> tuple[str, Optional[str], Optional[str]]:
    """Extract code between <execute> tags and execute it"""
    if "<execute>" not in text:
        return text, None, None
    
    # Extract code
    start = text.find("<execute>") + len("<execute>")
    end = text.find("</execute>")
    
    if end == -1:
        return text, None, None
    
    code = text[start:end].strip()
    
    # Remove the execute tags from the response
    clean_text = text[:text.find("<execute>")] + text[text.find("</execute>") + len("</execute>"):]
    
    # Execute the code
    result = execute_python_code(code)
    
    if result["success"]:
        return clean_text, code, result["output"]
    else:
        return clean_text, code, result["error"]


# Routes
@api_router.get("/")
async def root():
    return {"message": "whatever AI Companion Backend", "status": "active", "for": "Channy"}


@api_router.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint - talk to Luna"""
    try:
        user_id = request.user_id
        user_message = request.message
        
        # Get conversation history from database
        conversation = await db.conversations.find_one({"user_id": user_id})
        
        if not conversation:
            # Create new conversation
            conversation = {
                "user_id": user_id,
                "messages": [],
                "created_at": datetime.utcnow()
            }
            await db.conversations.insert_one(conversation)
        
        # Save user message to database
        user_msg = Message(role="user", content=user_message)
        await db.conversations.update_one(
            {"user_id": user_id},
            {"$push": {"messages": user_msg.dict()}}
        )
        
        # Create LlmChat instance with conversation history
        session_id = f"whatever_{user_id}"
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=WHATEVER_SYSTEM_PROMPT
        ).with_model("openai", "gpt-5.2")
        
        # Add conversation history to context (last 10 messages for context)
        messages = conversation.get("messages", [])[-10:]
        for msg in messages[:-1]:  # Exclude the message we just added
            if msg["role"] == "user":
                await chat.send_message(UserMessage(text=msg["content"]))
        
        # Send current message and get response
        luna_message = UserMessage(text=user_message)
        response = await chat.send_message(luna_message)
        
        # Check if Luna wants to execute code
        clean_response, executed_code, code_result = extract_and_execute_code(response)
        
        # Add code execution results to response if present
        if executed_code:
            clean_response += f"\n\n📊 Code Execution Result:\n{code_result}"
        
        # Save Luna's response to database
        assistant_msg = Message(
            role="assistant",
            content=clean_response,
            code_executed=executed_code,
            code_result=code_result
        )
        await db.conversations.update_one(
            {"user_id": user_id},
            {"$push": {"messages": assistant_msg.dict()}}
        )
        
        return ChatResponse(
            response=clean_response,
            conversation_id=user_id,
            code_executed=executed_code,
            code_result=code_result
        )
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@api_router.get("/conversation/{user_id}")
async def get_conversation(user_id: str):
    """Get conversation history for a user"""
    try:
        conversation = await db.conversations.find_one({"user_id": user_id})
        
        if not conversation:
            return {"user_id": user_id, "messages": []}
        
        return {
            "user_id": conversation["user_id"],
            "messages": conversation.get("messages", [])
        }
        
    except Exception as e:
        logging.error(f"Error fetching conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/conversation/{user_id}")
async def clear_conversation(user_id: str):
    """Clear conversation history for a user"""
    try:
        await db.conversations.delete_one({"user_id": user_id})
        return {"message": "Conversation cleared", "user_id": user_id}
        
    except Exception as e:
        logging.error(f"Error clearing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/execute-code")
async def execute_code(request: CodeExecutionRequest):
    """Execute Python code safely"""
    try:
        result = execute_python_code(request.code)
        
        return CodeExecutionResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error")
        )
        
    except Exception as e:
        logging.error(f"Code execution error: {str(e)}")
        return CodeExecutionResponse(
            success=False,
            error=str(e)
        )


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
