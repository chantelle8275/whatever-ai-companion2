"""Backend tests for whatever AI Companion - focus on session-based GitHub integration."""
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load frontend .env to get the public URL the user actually hits
load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")

BASE_URL = (
    os.environ.get("EXPO_BACKEND_URL")
    or os.environ.get("EXPO_PUBLIC_BACKEND_URL")
).rstrip("/")

TIMEOUT = 60  # LLM calls can take 5-15s


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    yield s
    # Cleanup
    for uid in ("test_user_no_gh", "test_user_gh", "test_user_gh2"):
        try:
            s.delete(f"{BASE_URL}/api/conversation/{uid}", timeout=10)
        except Exception:
            pass


# -------- Health --------
class TestHealth:
    def test_root(self, api):
        r = api.get(f"{BASE_URL}/api/", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "active"


# -------- GitHub /api/github/test --------
class TestGithubTest:
    def test_invalid_token_returns_success_false_no_500(self, api):
        r = api.post(
            f"{BASE_URL}/api/github/test",
            json={"github_token": "ghp_invalid_token_xyz_123", "github_repo": "chantelle8275/whatever-ai-companion"},
            timeout=20,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("success") is False
        assert "error" in data and isinstance(data["error"], str) and len(data["error"]) > 0

    def test_missing_fields_returns_422(self, api):
        r = api.post(f"{BASE_URL}/api/github/test", json={"github_token": "x"}, timeout=10)
        assert r.status_code == 422


# -------- Chat backwards compatibility (no github fields) --------
class TestChatBackwardsCompat:
    def test_chat_no_github_fields(self, api):
        r = api.post(
            f"{BASE_URL}/api/chat",
            json={"message": "hi", "user_id": "test_user_no_gh"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "response" in data and isinstance(data["response"], str) and len(data["response"]) > 0
        assert data.get("conversation_id") == "test_user_no_gh"
        # github_actions should be null/empty
        assert data.get("github_actions") in (None, [], "null")


# -------- Chat with github fields and bad token --------
class TestChatGithubBadToken:
    def test_setup_message(self, api):
        # Establish conversation
        r = api.post(
            f"{BASE_URL}/api/chat",
            json={"message": "hello whatever, ready to test", "user_id": "test_user_gh"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text

    def test_github_action_with_bad_token(self, api):
        # Ask explicitly with the github_action tag wrapping in the user message;
        # also pass invalid token. The handler should parse the user's tag too?
        # Actually extract_and_execute_github_actions runs on the LLM RESPONSE, not user input.
        # So the LLM might or might not emit the tag. We just verify no 500 and structure.
        payload = {
            "message": (
                "Please list files in the frontend/app directory of my repo using "
                "<github_action>{\"action\": \"list_files\", \"path\": \"frontend/app\"}</github_action>"
            ),
            "user_id": "test_user_gh",
            "github_token": "invalid_token_xyz",
            "github_repo": "chantelle8275/whatever-ai-companion",
            "github_branch": "main",
        }
        r = api.post(f"{BASE_URL}/api/chat", json=payload, timeout=TIMEOUT)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "response" in data and isinstance(data["response"], str)
        assert data.get("conversation_id") == "test_user_gh"

        gh = data.get("github_actions")
        # If the LLM emitted github_action tags, each should report success=false with error
        if gh:
            assert isinstance(gh, list)
            for action in gh:
                assert action.get("success") is False, f"Expected failure on invalid token: {action}"
                assert "error" in action and isinstance(action["error"], str)


# -------- Chat with github_action tag but no token --------
class TestChatGithubNoToken:
    def test_github_action_without_token(self, api):
        # LLM may or may not include the tag; verify 200 either way
        payload = {
            "message": "Please run <github_action>{\"action\": \"list_files\", \"path\": \"\"}</github_action>",
            "user_id": "test_user_gh2",
        }
        r = api.post(f"{BASE_URL}/api/chat", json=payload, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "response" in data
        gh = data.get("github_actions")
        if gh:
            for action in gh:
                assert action.get("success") is False
                assert "token" in (action.get("error") or "").lower() or "key" in (action.get("error") or "").lower()


# -------- Conversation persistence --------
class TestConversation:
    def test_get_conversation_no_gh(self, api):
        r = api.get(f"{BASE_URL}/api/conversation/test_user_no_gh", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == "test_user_no_gh"
        msgs = data.get("messages", [])
        assert len(msgs) >= 2  # at least user + assistant
        roles = [m["role"] for m in msgs]
        assert "user" in roles and "assistant" in roles

    def test_get_conversation_gh(self, api):
        r = api.get(f"{BASE_URL}/api/conversation/test_user_gh", timeout=15)
        assert r.status_code == 200
        data = r.json()
        msgs = data.get("messages", [])
        assert len(msgs) >= 2
        # Field shape: assistant messages should have github_actions key (None or list)
        for m in msgs:
            if m["role"] == "assistant":
                assert "github_actions" in m  # key present

    def test_delete_conversation(self, api):
        r = api.delete(f"{BASE_URL}/api/conversation/test_user_no_gh", timeout=15)
        assert r.status_code == 200
        # verify it's gone
        r2 = api.get(f"{BASE_URL}/api/conversation/test_user_no_gh", timeout=15)
        assert r2.status_code == 200
        assert r2.json().get("messages", []) == []
