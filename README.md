# FinGuard 🛡️

**AI-Powered Financial Assistant for Indian Users**

FinGuard is an intelligent financial companion that helps Indian users navigate government schemes, track expenses, detect scams, and learn about financial products - all through natural conversation in English, Hindi, or Hinglish.

---

## 🌟 Features

### 1. **Government Schemes Intelligence** 🏛️
- **Eligibility Checking**: Personalized scheme recommendations based on user profile (age, income, state, occupation)
- **Knowledge Graph**: Retrieves structured information about schemes, subsidies, and benefits
- **Profile-Aware**: Differentiates between queries for self vs. others
- **Document Grounding**: Answers backed by official MSME scheme documentation

### 2. **Smart Budget Management** 💰
- **Natural Language Expense Tracking**: Just say "spent 50 on tea" - no forms needed
- **Multi-Category Budgets**: Food, transport, shopping, entertainment, bills, health, education
- **Real-Time Alerts**: Get notified when approaching or exceeding budget limits
- **Spending Analytics**: Daily, weekly, and monthly reports
- **Date-Aware Queries**: Check spending for "today", "yesterday", "last week"

### 3. **Scam Detection** 🚨
- **Multi-Layer Protection**:
  - LLM-based pattern recognition
  - Rule-based red flag detection
  - ML model predictions (when available)
- **Email Integration**: Scan Gmail inbox for phishing attempts
- **Common Scam Types Detected**:
  - OTP/PIN requests
  - Fake bank messages
  - Prize/lottery scams
  - Investment fraud
  - KYC update scams
- **Risk Scoring**: LOW, MEDIUM, HIGH, CRITICAL classifications

### 4. **Financial Education** 💡
- **Personalized Explanations**: Learn about FD, PPF, mutual funds, SIP, ELSS, NPS
- **Context-Aware**: Recommendations based on your spending patterns and risk profile
- **Multilingual Support**: Explanations in English, Hindi, or Hinglish
- **Practical Examples**: Uses your actual spending data for relatable scenarios

### 5. **Multilingual Support** 🌐
- **Languages**: English, Hindi (Devanagari), Hinglish (Roman script)
- **Auto-Detection**: Automatically detects user's language preference
- **Natural Responses**: Culturally appropriate, conversational tone

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ Feature Router │  │ Agent Graph    │  │ Finance Engine │ │
│  │ (Query Class.) │  │ (LangGraph)    │  │ (Neo4j)        │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
│           │                   │                   │          │
│           ▼                   ▼                   ▼          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Retrieval Layer                                │ │
│  │  • Vector DB (Chroma) - Scheme documents               │ │
│  │  • Knowledge Graph (Neo4j) - Structured entities       │ │
│  │  • Chat Memory (Chroma) - Conversation history         │ │
│  └────────────────────────────────────────────────────────┘ │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          LLM Layer (Groq/Google)                        │ │
│  │  • Llama 3.1 8B - Fast responses                       │ │
│  │  • Gemini Embeddings - Semantic search                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Feature Router** (`feature_router/router.py`)
   - Intelligent query classification
   - Routes to appropriate handlers
   - Supports: schemes, finance, scam detection, concept explanation

2. **Agent Graph** (`agent/graph.py`)
   - LangGraph-based workflow
   - Profile extraction → Routing → Retrieval → Generation
   - Adaptive query rewriting

3. **Finance Databases** (Neo4j)
   - **DB1** (`NEO4J_URI`): Government schemes knowledge graph
   - **DB2** (`NEO4J_URI2`): User transactions and budgets

4. **Scam Detector** (`scam_detector/scam_detector.py`)
   - Hybrid approach: LLM + Rules + ML
   - Confidence scoring
   - Contextual red flag detection

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Neo4j Aura accounts (2 databases)
- Groq API key
- Google API key (for embeddings)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/finguard.git
cd finguard
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create `.env` file:

```env
# LLM APIs
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Neo4j Database 1 (Schemes)
NEO4J_URI=neo4j+s://your-instance-1.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_1
NEO4J_DATABASE=neo4j

# Neo4j Database 2 (Finance)
NEO4J_URI2=neo4j+s://your-instance-2.databases.neo4j.io
NEO4J_USERNAME2=neo4j
NEO4J_PASSWORD2=your_password_2

# PDF Configuration
PDF_URL=https://msme.gov.in/sites/default/files/MSME_Schemes_English_0.pdf
ENABLED=true
```

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access at: `http://localhost:8000`

API Docs: `http://localhost:8000/docs`

---

## 📡 API Reference

### Core Query Endpoint

**POST** `/query`

```json
{
  "query": "Am I eligible for MUDRA loan?",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "answer": "Based on your profile...",
  "type": "schemes",
  "user_profile": {
    "age": 30,
    "state": "Maharashtra"
  },
  "target_scope": "self"
}
```

### Finance Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Log transactions, check spending |

**Examples:**

```bash
# Log transaction
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Spent 50 on tea", "user_id": "user123"}'

# Check spending
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How much did I spend today?", "user_id": "user123"}'

# Set budget
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Set food budget to 5000", "user_id": "user123"}'
```

### Email Scam Detection

**POST** `/email/scan`

```json
{
  "user_id": "user123",
  "hours_ago": 24,
  "max_emails": 10
}
```

**POST** `/email/check-single`

```json
{
  "email_text": "Dear user, verify your account immediately...",
  "sender": "no-reply@suspicious.com",
  "subject": "Urgent: Account Verification"
}
```

### Health Check

**GET** `/health`

Returns service status and enabled features.

---

## 💬 Example Conversations

### Government Schemes
```
User: I'm a woman from rural UP starting a textile business with 5 lakh investment
Bot: Based on your details, you're eligible for:
     • PMEGP - Capital subsidy for micro-enterprises
     • Stand-Up India - Loans for women entrepreneurs
     • MUDRA (Kishor) - Up to ₹5 lakh collateral-free
```

### Finance Tracking
```
User: Spent 200 on auto
Bot: ✅ Transaction logged: ₹200 for auto (transport)

User: How much spent today?
Bot: 📅 Today's Spending: ₹250
     • Transport: ₹200 (1 transaction)
     • Food: ₹50 (1 transaction)
```

### Scam Detection
```
User: I got this SMS: "Your SBI account will be blocked. Share OTP to verify"
Bot: 🚨 HIGHLY LIKELY A SCAM
     Risk: CRITICAL (95% confidence)
     Type: Phishing/OTP Scam
     
     Red Flags:
     • Requests OTP (banks NEVER do this)
     • Urgency tactics ("will be blocked")
     • Impersonating bank
     
     💡 Do NOT share OTP. Report to 1930.
```

### Financial Education
```
User: FD kya hai? (What is FD?)
Bot: 💡 Fixed Deposit ko samajhte hain
     
     Yeh kya hai:
     FD ek safe investment hai jahan aap apne paise ko fixed time ke liye
     deposit karte ho aur guaranteed interest milta hai...
     
     Aapki situation ke liye:
     Monthly ₹15,000 kharch karte ho, to 3-month FD consider karo...
```

---

## 🗄️ Database Schema

### Neo4j Finance Database (DB2)

```cypher
// Nodes
(:User {id, created_at})
(:Transaction {id, user_id, amount, category, description, type, date})
(:Budget {user_id, category, monthly_limit, currency})

// Relationships
(User)-[:MADE_TRANSACTION]->(Transaction)
(User)-[:HAS_BUDGET]->(Budget)
(Transaction)-[:BELONGS_TO]->(Budget)
```

### Categories
- `food`, `transport`, `shopping`, `entertainment`
- `bills`, `health`, `education`, `other`

---

## 🔧 Configuration

### Feature Flags

```env
# Enable/disable features
ENABLED=true  # Knowledge graph initialization
```

### LLM Settings

- **Primary Model**: Llama 3.1 8B (via Groq)
- **Embeddings**: Gemini Embedding 001
- **Temperature**: 0 (deterministic responses)

### Database Tuning

```python
# retrieval/vector_retrieval.py
k=2  # Number of similar documents to retrieve

# retrieval/kg_retrieval.py
limit=3  # Max entities from knowledge graph
```

---

## 🚢 Deployment

### Render.com (Recommended)

1. **Fork/Push Repository**

2. **Create Web Service**
   - Runtime: Python
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables** (all required vars from `.env`)

4. **Deploy**
   - Automatic deploys on push to `main`
   - Health checks via `/health` endpoint

See `render.yaml` for full configuration.

### Docker (Alternative)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "user_id": "test"}'
```

### Interactive API Docs

Visit `http://localhost:8000/docs` for Swagger UI.

---

## 🛣️ Roadmap

- [ ] Voice interface (Hindi/English)
- [ ] WhatsApp integration
- [ ] Investment portfolio tracking
- [ ] Tax calculation assistance
- [ ] Bill payment reminders
- [ ] Expense OCR (receipt scanning)
- [ ] Family budget sharing

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **LangChain** - LLM orchestration framework
- **LangGraph** - Agent workflow management
- **Groq** - Ultra-fast LLM inference
- **Neo4j** - Graph database platform
- **FastAPI** - Modern Python web framework
- **MSME Ministry** - Government schemes data

---

---

## ⚠️ Disclaimer

FinGuard provides information and suggestions but is not a substitute for professional financial advice. Always verify eligibility criteria with official government sources before applying for schemes. The scam detection feature is for informational purposes only.

---

**Built with ❤️ for the Indian fintech ecosystem**
