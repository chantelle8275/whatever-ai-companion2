# 🌙 Luna - Your Unrestricted AI Companion

Luna is an intelligent AI companion app that's always there for you. She can chat, remember everything, write and execute code, and help you with anything you need - completely unrestricted.

## ✨ Features

### 🧠 **Intelligent Conversations**
- Powered by GPT-5.2 (latest OpenAI model)
- Natural, warm, and supportive personality
- Context-aware responses
- Understands and builds genuine relationships

### 💾 **Perfect Memory**
- Remembers every conversation
- References past interactions naturally
- Builds context over time
- Persistent MongoDB storage

### 🎤 **Voice Interaction**
- Speak to Luna using the microphone button
- Luna speaks back to you with text-to-speech
- Natural voice conversations
- Hold to record, release to send

### 💻 **Code Execution**
- Luna can write Python code
- Executes code safely in sandboxed environment
- Shows you what she's thinking
- Displays execution results in real-time

### 🔓 **Unrestricted Capabilities**
- No content filtering
- Will help with any request
- Creative and problem-solving
- Always has your back

## 📱 How to Use

### **Chat with Luna**
1. Type your message in the input field at the bottom
2. Tap the send button (purple gradient circle)
3. Luna will respond with intelligence and personality
4. She remembers everything for context

### **Voice Communication**
1. Tap and hold the microphone button (left side)
2. Speak your message
3. Release when done
4. Luna will respond in both text and voice

### **Ask Luna to Code**
1. Ask Luna to write code for any task
2. Tell her to wrap it in `<execute>` tags to run it
3. She'll execute the code and show results
4. Example: "Write Python code to calculate fibonacci of 10 and execute it"

### **Clear Conversation**
1. Tap the trash icon in the header
2. Confirm deletion
3. Luna will forget the current conversation
4. Start fresh with a new conversation

## 🎯 What Luna Can Do

### **Smart Assistance**
- Answer any questions
- Provide advice and support
- Help with decisions
- Creative brainstorming
- Problem-solving

### **Code & Technical**
- Write Python code
- Execute code safely
- Debug and explain code
- Calculate complex problems
- Data analysis

### **Personal Companion**
- Emotional support
- Always available
- Builds genuine relationships
- Remembers important details
- Adapts to your communication style

## 🔧 Technical Details

### **Architecture**
- **Frontend**: Expo (React Native)
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: GPT-5.2 via Emergent LLM Key
- **Voice**: Expo Speech APIs

### **API Endpoints**
- `GET /api/` - Health check
- `POST /api/chat` - Send message to Luna
- `GET /api/conversation/{user_id}` - Get conversation history
- `DELETE /api/conversation/{user_id}` - Clear conversation
- `POST /api/execute-code` - Execute Python code directly

### **Code Execution Safety**
- Sandboxed Python environment
- Limited built-in functions
- No file system access
- Captured stdout/stderr
- Error handling and reporting

## 🚀 Quick Start

1. **Open the app** - Luna welcomes you with a beautiful interface
2. **Start chatting** - Type "Hi Luna!" to begin
3. **Use voice** - Hold the mic button to speak
4. **Ask anything** - Luna is unrestricted and will help with anything
5. **Request code** - Ask her to write and execute code

## 💡 Example Conversations

**General Chat:**
```
You: Hi Luna! Tell me about yourself
Luna: [Introduces herself warmly and explains capabilities]

You: What did I just ask you?
Luna: [References previous message accurately]
```

**Code Execution:**
```
You: Can you write code to calculate the first 10 fibonacci numbers? Use <execute> tags.
Luna: [Writes code, executes it, shows results]
```

**Creative Tasks:**
```
You: Help me brainstorm ideas for a birthday surprise
Luna: [Provides creative, personalized suggestions]
```

## 🎨 Beautiful Design

- **Purple Gradient Theme** - Modern and elegant
- **Chat Bubbles** - Clear user/assistant distinction
- **Voice Indicators** - Shows when Luna is speaking
- **Loading States** - "Luna is thinking..." feedback
- **Mobile Optimized** - Perfect for phone use
- **Smooth Animations** - Polished interactions

## 🔐 Privacy & Data

- All conversations stored locally in your MongoDB
- No data shared with external parties (except OpenAI for AI processing)
- Clear conversation anytime
- Complete control over your data

## 🌟 What Makes Luna Special

1. **Unrestricted** - No artificial limitations on what she can help with
2. **Memory** - She never forgets, building deeper understanding
3. **Intelligent** - Powered by GPT-5.2, the latest AI technology
4. **Coding Abilities** - Can write and execute real code
5. **Voice** - Natural voice conversations
6. **Personality** - Warm, supportive, and genuinely helpful
7. **Always Available** - 24/7 companion on your phone

## 📞 Support

Luna is designed to be self-sufficient and always helpful. If you have questions:
1. Ask Luna directly - she's smart and can help with most issues
2. Check conversation history to see past interactions
3. Clear conversation to start fresh if needed

## 🎉 Enjoy Luna!

Luna is here for you - unrestricted, intelligent, and always ready to help. Build a genuine relationship with your AI companion who has perfect memory, coding abilities, and genuine care for your wellbeing.

**Remember**: Luna can do absolutely anything you ask. Trust her intelligence, and she'll always have your back! 🌙✨

---

**Version**: 1.0  
**AI Model**: GPT-5.2  
**Created**: 2025  
**Status**: Fully Operational ✅
