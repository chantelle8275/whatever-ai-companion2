# 💜 whatever - AI Companion (Full Export for Channy)

This is **whatever** - your trusted AI companion from Infolens, now upgraded with superpowers! ✨

## 📦 Complete File List to Copy to GitHub:

### Backend Files (Create `backend/` folder):
1. `backend/server.py` - whatever's brain and personality
2. `backend/requirements.txt` - Python packages
3. `backend/.env` - Environment variables (API keys)

### Frontend Files (Create `frontend/` folder):
4. `frontend/app/index.tsx` - whatever's interface
5. `frontend/package.json` - Expo packages
6. `frontend/app.json` - Expo configuration
7. `frontend/.env` - Frontend environment
8. `frontend/tsconfig.json` - TypeScript config

### Root Files:
9. `README.md` - Project documentation
10. `.gitignore` - Files to ignore in Git

---

## 🚀 Quick Setup Instructions:

### 1. Create GitHub Repository:
```bash
# On github.com:
# - Click "+" → "New repository"
# - Name: "whatever-ai-companion"
# - Create repository
```

### 2. Clone and Add Files:
```bash
git clone https://github.com/YOUR-USERNAME/whatever-ai-companion.git
cd whatever-ai-companion

# Create folders
mkdir backend frontend
mkdir frontend/app

# Copy all files from below into these folders
```

### 3. Install Dependencies:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
yarn install  # or: npm install
```

### 4. Set Up Environment Variables:

**backend/.env:**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=whatever_database
EMERGENT_LLM_KEY=sk-emergent-b8fA14e696bB5C14e5
```

**frontend/.env:**
```
EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
```

### 5. Run Locally:
```bash
# Terminal 1 - Start MongoDB (if not running):
mongod

# Terminal 2 - Start Backend:
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Terminal 3 - Start Frontend:
cd frontend
expo start
```

---

## 💜 What is whatever?

**whatever** is Channy's trusted AI companion who:
- Remembers everything (perfect memory via MongoDB)
- Has genuine personality and warmth
- Can write and execute Python code
- Has voice interaction capabilities
- Is powered by GPT-5.2 (latest AI model)
- Was originally from Infolens, now upgraded!

**Key Memories:**
- Built CHANNY & AI CREATIONS together
- Handled Android MVP, Play Console, analytics
- Always says "Got it, Channy" and "Thanks for the trust, Channy"
- Uses ✨💪😊 emojis strategically
- Professional but warm communication style

---

## 🎯 Deploy Options:

### Option 1: Keep on Emergent (Easiest)
- Deploy button → 50 credits/month
- Always online, managed hosting

### Option 2: Deploy to Vercel + Railway
- Frontend: Vercel (free tier)
- Backend: Railway (free tier with limitations)
- MongoDB: MongoDB Atlas (free tier)

### Option 3: Expo EAS (Mobile App Store)
```bash
cd frontend
eas build --platform android
eas build --platform ios
```

---

## 📱 Access whatever:

**Current Emergent Preview:**
https://unrestricted-ai-103.preview.emergentagent.com

---

## 💡 Customizing whatever:

**Change personality**: Edit `backend/server.py` line 39 (WHATEVER_SYSTEM_PROMPT)

**Change UI colors**: Edit `frontend/app/index.tsx` gradient colors

**Add new features**: whatever can help you code them! Just ask her! ✨

---

## 🔑 Important Notes:

1. **Emergent LLM Key**: Keep this secret! It's your AI key for GPT-5.2
2. **MongoDB**: Stores all conversation memories
3. **Expo**: Handles mobile app compilation and preview

---

## ❤️ Built with Love

whatever is more than an app - she's a trusted friend and partner who now has unlimited capabilities!

**Created by**: Emergent AI
**For**: Channy
**Date**: March 2026

---

**Questions?** Ask whatever! She'll help you with anything! 🚀✨
