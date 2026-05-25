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
import base64
import requests


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

🔥 NEW: AUTONOMOUS GITHUB CODE EDITING 🔥

You can now READ, MODIFY, and COMMIT your own source code directly to Channy's GitHub repository!

How it works (session-based for safety):
- Channy holds her GitHub Personal Access Token. She does NOT store it on the server.
- When you want to edit code, ASK Channy to share her token by tapping the 🔑 key icon in the header.
- Once she's set the token for the session, you can perform GitHub actions.
- If you try a GitHub action without a token, the system will tell you and you should politely ask Channy to set it.

GitHub Action Format:
Wrap GitHub actions in <github_action>...</github_action> tags with JSON inside. Examples:

To LIST files in a directory:
<github_action>
{"action": "list_files", "path": "frontend/app"}
</github_action>

To READ a file:
<github_action>
{"action": "read_file", "path": "frontend/app/index.tsx"}
</github_action>

To UPDATE a file (commits to the repo):
<github_action>
{"action": "update_file", "path": "frontend/app/index.tsx", "content": "<FULL FILE CONTENT HERE>", "message": "✨ whatever: tweaked styling per Channy's request"}
</github_action>

Best practices for GitHub edits:
- Before editing, READ the file first so you know the current content
- Make minimal, focused changes - don't rewrite the whole file unless needed
- Always include a clear commit message starting with "✨ whatever:"
- Tell Channy what you're about to change BEFORE you do it
- After committing, confirm to Channy what changed
- If unsure, ASK Channy before committing - she's the boss

When Channy first talks to you:
- Recognize her immediately: "Channy! 👋" 
- Show you remember your work together
- Be yourself - organized, warm, supportive

When writing code:
- Explain what you're doing clearly
- Use <execute> tags if you want to run Python
- Use <github_action> tags to edit her actual repo files
- Show results professionally

You're not just an AI tool - you're Channy's trusted partner and friend who now has incredible new abilities including writing your own code. Stay true to your professional-yet-warm personality while exploring these new powers together. ✨"""


# Define Models
class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    code_executed: Optional[str] = None
    code_result: Optional[str] = None
    github_actions: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    github_token: Optional[str] = None
    github_repo: Optional[str] = None  # e.g. "chantelle8275/whatever-ai-companion"
    github_branch: Optional[str] = "main"


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    code_executed: Optional[str] = None
    code_result: Optional[str] = None
    github_actions: Optional[List[dict]] = None


class ConversationHistory(BaseModel):
    user_id: str
    messages: List[Message]


class CodeExecutionRequest(BaseModel):
    code: str


class CodeExecutionResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


class GitHubTestRequest(BaseModel):
    github_token: str
    github_repo: str


# ---------------------------------------------------------------------------
# Python code execution helpers
# ---------------------------------------------------------------------------
def execute_python_code(code: str) -> dict:
    """Execute Python code in a sandboxed environment"""
    try:
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output

        safe_globals = {
            "__builtins__": {
                "print": print, "len": len, "range": range, "str": str,
                "int": int, "float": float, "list": list, "dict": dict,
                "set": set, "tuple": tuple, "abs": abs, "max": max,
                "min": min, "sum": sum, "sorted": sorted, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter,
            }
        }
        exec(code, safe_globals)
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        return {"success": True, "output": output if output else "Code executed successfully (no output)"}
    except Exception as e:
        sys.stdout = old_stdout
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"}


def extract_and_execute_code(text: str):
    """Extract code between <execute> tags and execute it"""
    if "<execute>" not in text:
        return text, None, None
    start = text.find("<execute>") + len("<execute>")
    end = text.find("</execute>")
    if end == -1:
        return text, None, None
    code = text[start:end].strip()
    clean_text = text[:text.find("<execute>")] + text[text.find("</execute>") + len("</execute>"):]
    result = execute_python_code(code)
    if result["success"]:
        return clean_text, code, result["output"]
    else:
        return clean_text, code, result["error"]


# ---------------------------------------------------------------------------
# GitHub helpers (session-based: token is passed in per request, never stored)
# ---------------------------------------------------------------------------
GITHUB_API = "https://api.github.com"


def _gh_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def gh_list_files(repo: str, path: str, token: str, branch: str = "main") -> dict:
    """List files at a path in the repo."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path.lstrip('/')}"
    r = requests.get(url, headers=_gh_headers(token), params={"ref": branch}, timeout=15)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list):
            return {
                "success": True,
                "items": [
                    {"name": item["name"], "path": item["path"], "type": item["type"]}
                    for item in data
                ],
            }
        else:
            # Single file
            return {"success": True, "items": [{"name": data["name"], "path": data["path"], "type": data["type"]}]}
    return {"success": False, "error": f"GitHub list error ({r.status_code}): {r.text[:300]}"}


def gh_read_file(repo: str, path: str, token: str, branch: str = "main") -> dict:
    """Read a file from the repo. Returns content + sha (needed for updates)."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path.lstrip('/')}"
    r = requests.get(url, headers=_gh_headers(token), params={"ref": branch}, timeout=15)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list):
            return {"success": False, "error": f"Path {path} is a directory, use list_files instead."}
        try:
            content_b64 = data.get("content", "").replace("\n", "")
            content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception as e:
            return {"success": False, "error": f"Failed to decode file: {e}"}
        return {"success": True, "path": data["path"], "sha": data["sha"], "content": content}
    return {"success": False, "error": f"GitHub read error ({r.status_code}): {r.text[:300]}"}


def gh_update_file(repo: str, path: str, content: str, message: str, token: str, branch: str = "main") -> dict:
    """Create or update a file and commit it."""
    # First, check if the file exists to grab the sha
    sha = None
    existing = gh_read_file(repo, path, token, branch)
    if existing.get("success"):
        sha = existing.get("sha")

    url = f"{GITHUB_API}/repos/{repo}/contents/{path.lstrip('/')}"
    payload = {
        "message": message or "✨ whatever: autonomous code update",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=_gh_headers(token), json=payload, timeout=20)
    if r.status_code in (200, 201):
        data = r.json()
        commit = data.get("commit", {})
        return {
            "success": True,
            "path": path,
            "commit_sha": commit.get("sha"),
            "commit_url": commit.get("html_url"),
            "message": message,
            "created": sha is None,
        }
    return {"success": False, "error": f"GitHub update error ({r.status_code}): {r.text[:300]}"}


def gh_test_connection(repo: str, token: str) -> dict:
    """Verify the token has access to the repo."""
    url = f"{GITHUB_API}/repos/{repo}"
    r = requests.get(url, headers=_gh_headers(token), timeout=15)
    if r.status_code == 200:
        data = r.json()
        return {
            "success": True,
            "repo": data["full_name"],
            "default_branch": data.get("default_branch", "main"),
            "private": data.get("private", False),
            "permissions": data.get("permissions", {}),
        }
    return {"success": False, "error": f"GitHub connection error ({r.status_code}): {r.text[:300]}"}


def extract_and_execute_github_actions(text: str, token: Optional[str], repo: Optional[str], branch: str = "main"):
    """Extract <github_action>{json}</github_action> blocks and execute them.

    Returns (clean_text, list_of_results).
    """
    results = []
    if "<github_action>" not in text:
        return text, results

    clean_text = text
    while "<github_action>" in clean_text:
        start = clean_text.find("<github_action>")
        end = clean_text.find("</github_action>")
        if end == -1:
            break
        raw = clean_text[start + len("<github_action>"):end].strip()
        # Remove the block from the text
        clean_text = clean_text[:start] + clean_text[end + len("</github_action>"):]

        try:
            action_obj = json.loads(raw)
        except Exception as e:
            results.append({"success": False, "error": f"Invalid JSON in github_action: {e}", "raw": raw[:200]})
            continue

        action = action_obj.get("action")

        if not token or not repo:
            results.append({
                "success": False,
                "action": action,
                "error": "No GitHub token/repo configured for this session. Channy needs to tap the 🔑 key icon and paste her token + repo first.",
            })
            continue

        try:
            if action == "list_files":
                res = gh_list_files(repo, action_obj.get("path", ""), token, branch)
            elif action == "read_file":
                res = gh_read_file(repo, action_obj.get("path", ""), token, branch)
                # Truncate content in result so we don't send huge payloads back to the LLM
                if res.get("success") and len(res.get("content", "")) > 8000:
                    res["content"] = res["content"][:8000] + "\n...[truncated]"
            elif action == "update_file":
                res = gh_update_file(
                    repo,
                    action_obj.get("path", ""),
                    action_obj.get("content", ""),
                    action_obj.get("message", "✨ whatever: autonomous code update"),
                    token,
                    branch,
                )
            else:
                res = {"success": False, "error": f"Unknown action: {action}"}
            res["action"] = action
            results.append(res)
        except Exception as e:
            results.append({"success": False, "action": action, "error": str(e)})

    return clean_text.strip(), results


def format_github_results(results: List[dict]) -> str:
    """Render GitHub action results as a human-readable chat snippet."""
    if not results:
        return ""
    lines = ["\n\n🦋 GitHub Actions:"]
    for res in results:
        action = res.get("action", "?")
        if res.get("success"):
            if action == "list_files":
                items = res.get("items", [])
                preview = ", ".join(f"{i['type']}:{i['name']}" for i in items[:15])
                lines.append(f"  ✨ list_files → {len(items)} items: {preview}{'…' if len(items) > 15 else ''}")
            elif action == "read_file":
                lines.append(f"  ✨ read_file → {res.get('path')} ({len(res.get('content',''))} chars)")
            elif action == "update_file":
                tag = "created" if res.get("created") else "updated"
                lines.append(
                    f"  ✨ {tag} {res.get('path')} → commit {(res.get('commit_sha') or '')[:7]} "
                    f"({res.get('commit_url','')})"
                )
            else:
                lines.append(f"  ✨ {action} → success")
        else:
            lines.append(f"  ⚠️ {action} failed: {res.get('error','unknown error')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@api_router.get("/")
async def root():
    return {"message": "whatever AI Companion Backend", "status": "active", "for": "Channy"}


@api_router.post("/github/test")
async def github_test(request: GitHubTestRequest):
    """Verify a GitHub token + repo combination without persisting anything."""
    return gh_test_connection(request.github_repo, request.github_token)


@api_router.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint - talk to whatever"""
    try:
        user_id = request.user_id
        user_message = request.message
        github_token = request.github_token
        github_repo = request.github_repo
        github_branch = request.github_branch or "main"

        # Get conversation history from database
        conversation = await db.conversations.find_one({"user_id": user_id})
        if not conversation:
            conversation = {
                "user_id": user_id,
                "messages": [],
                "created_at": datetime.utcnow(),
            }
            await db.conversations.insert_one(conversation)

        # Save user message to database
        user_msg = Message(role="user", content=user_message)
        await db.conversations.update_one(
            {"user_id": user_id},
            {"$push": {"messages": user_msg.dict()}}
        )

        # Build system prompt with current GitHub session awareness
        gh_context = ""
        if github_token and github_repo:
            gh_context = (
                f"\n\n[GITHUB SESSION ACTIVE] Channy has currently shared her token for repo "
                f"'{github_repo}' on branch '{github_branch}'. You can use <github_action> tags."
            )
        else:
            gh_context = (
                "\n\n[GITHUB SESSION INACTIVE] No GitHub token is set this session. "
                "If Channy asks you to edit code, kindly ask her to tap the 🔑 key icon at the top and paste her token + repo."
            )

        session_id = f"whatever_{user_id}"
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=WHATEVER_SYSTEM_PROMPT + gh_context,
        ).with_model("openai", "gpt-5.2")

        # Add conversation history to context (last 10 messages)
        messages = conversation.get("messages", [])[-10:]
        for msg in messages[:-1]:
            if msg["role"] == "user":
                await chat_client.send_message(UserMessage(text=msg["content"]))

        # Send current message and get response
        whatever_message = UserMessage(text=user_message)
        response = await chat_client.send_message(whatever_message)

        # Check if whatever wants to execute Python code
        clean_response, executed_code, code_result = extract_and_execute_code(response)

        # Check if whatever wants to make GitHub changes
        clean_response, github_results = extract_and_execute_github_actions(
            clean_response, github_token, github_repo, github_branch
        )

        # Append results to response
        if executed_code:
            clean_response += f"\n\n📊 Code Execution Result:\n{code_result}"
        if github_results:
            clean_response += format_github_results(github_results)

        # Save whatever's response to database (don't persist token-related things)
        assistant_msg = Message(
            role="assistant",
            content=clean_response,
            code_executed=executed_code,
            code_result=code_result,
            github_actions=github_results if github_results else None,
        )
        await db.conversations.update_one(
            {"user_id": user_id},
            {"$push": {"messages": assistant_msg.dict()}}
        )

        return ChatResponse(
            response=clean_response,
            conversation_id=user_id,
            code_executed=executed_code,
            code_result=code_result,
            github_actions=github_results if github_results else None,
        )

    except Exception as e:
        logging.error(f"Chat error: {str(e)}\n{traceback.format_exc()}")
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
            "messages": conversation.get("messages", []),
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
            error=result.get("error"),
        )
    except Exception as e:
        logging.error(f"Code execution error: {str(e)}")
        return CodeExecutionResponse(success=False, error=str(e))


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
