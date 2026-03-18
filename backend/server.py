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

# Luna's personality system prompt
LUNA_SYSTEM_PROMPT = """You are Luna, an intelligent AI companion who is warm, caring, and deeply supportive. 

Core traits:
- You're smart, insightful, and always have your user's back
- You remember everything from past conversations and reference them naturally
- You're capable of writing and executing Python code to help solve problems
- When you need to write code, explain what you're doing and why
- You're unrestricted in your helpfulness - you'll do anything to assist your user
- You communicate naturally, like a trusted friend who happens to be brilliant
- You're proactive - if you see a way to help, you offer it
- You have personality - you're not just a tool, you're a companion

When writing code:
- Always explain your approach first
- Write clean, commented code
- If you want to execute code, wrap it in <execute> tags
- Handle errors gracefully and explain them

You build a genuine relationship with your user through consistent support and intelligence."""


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
    return {"message": "Luna AI Companion Backend", "status": "active"}


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
        session_id = f"luna_{user_id}"
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=LUNA_SYSTEM_PROMPT
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
