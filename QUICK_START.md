# WellnessWay Diet Planner - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 16+
- Docker & Docker Compose
- OpenAI API Key (for AI meal generation)

### 1. Setup Database
```bash
# Start PostgreSQL database
docker-compose up -d
```

### 2. Setup Backend
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Test backend (optional)
cd ..
python test_backend.py
```

### 3. Setup AI Provider (Choose One)

#### Option 1: Mock AI (Recommended for Testing) 🆓
```bash
# Interactive setup script
python setup_ai.py
# Choose option 1 for Mock AI
```

**Benefits:**
- ✅ Completely free
- ✅ No API key needed
- ✅ Generates realistic meal plans
- ✅ Perfect for development and testing

#### Option 2: Groq (Free & Fast) 🚀
```bash
# Get free API key from https://console.groq.com/
python setup_ai.py
# Choose option 2 and enter your Groq API key
```

**Benefits:**
- ✅ 14,400 requests/day free
- ✅ Very fast inference
- ✅ Uses Llama 3.1 model
- ✅ High quality results

#### Option 3: Ollama (Local & Free) 🏠
```bash
# Install Ollama first: https://ollama.ai/
ollama serve
ollama pull llama3.1

# Then configure
python setup_ai.py
# Choose option 3
```

**Benefits:**
- ✅ Completely free
- ✅ Runs locally (no internet needed)
- ✅ Privacy-focused
- ✅ No rate limits

#### Option 4: OpenAI (Paid) 💰
```bash
python setup_ai.py
# Choose option 4 and enter your OpenAI API key
```

**Manual Setup:**
Edit `.env` file and set:
```bash
AI_PROVIDER=mock  # or groq, ollama, openai
GROQ_API_KEY=your-groq-key-here  # if using Groq
```

### 4. Setup Frontend
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Build frontend (optional test)
npm run build
```

### 5. Start Application
```bash
# Terminal 1: Start Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Start Frontend
cd frontend
npm start
```

### 6. Test Complete Flow
1. Open http://localhost:3000
2. Click "Get Started" to create a profile
3. Fill out the multi-step form:
   - Basic Info (name, age, gender, height, weight, activity level)
   - Health Goals (fat loss, muscle gain, or maintenance)
   - Diet Preferences (vegetarian/vegan/non-vegetarian, allergies, etc.)
4. Review and submit your profile
5. Navigate to "Diet Plans" to generate meal plans
6. Choose "Weekly" or "Daily" plan
7. Click "Generate Plan" and wait for AI to create your personalized meals

## 🔧 Troubleshooting

### Backend Issues
```bash
# Check if database is running
docker ps

# Check backend logs
cd backend
python -m uvicorn app.main:app --reload --log-level debug

# Test database connection
python test_backend.py
```

### Frontend Issues
```bash
# Check for TypeScript errors
cd frontend
npm run build

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### AI Provider Issues
- **"AI provider not configured"**: Run `python setup_ai.py`
- **Mock AI**: No setup needed, generates fake but realistic meal plans
- **Groq errors**: Check API key is valid and you haven't exceeded free limits
- **Ollama errors**: Make sure `ollama serve` is running and model is installed
- **OpenAI errors**: Check API key and account has sufficient credits

### Navigation Issues
- **Blank pages**: Check browser console for errors
- **Routes not working**: Make sure both backend and frontend are running
- **API errors**: Check that backend is running on port 8000

## 📊 API Endpoints

### Backend (http://localhost:8000)
- **Health Check**: GET `/health`
- **API Docs**: GET `/docs` (Swagger UI)
- **User Profile**: POST/GET/PUT `/api/v1/users/profile`
- **Diet Plans**: POST `/api/v1/diet-plans/weekly` or `/daily`

### Frontend (http://localhost:3000)
- **Home**: `/`
- **Profile Setup**: `/profile-setup`
- **Diet Plans**: `/diet-plans`

## 🎯 What's Working

✅ **Complete Backend API**
- User profile management
- Health Context Document generation
- AI-powered diet plan generation
- Plan regeneration (meal/day/week)
- Database operations with PostgreSQL

✅ **Complete Frontend UI**
- Multi-step profile creation
- Diet plan generation interface
- Plan viewing and navigation
- Meal regeneration controls

✅ **AI Integration**
- OpenAI GPT-4 integration
- Structured meal plan generation
- Safety constraints and validation
- Nutritional calculations

## 🚧 What's Next

The core application is fully functional! Optional enhancements:

- [ ] JWT Authentication (currently uses simplified headers)
- [ ] Unit tests for API endpoints
- [ ] E2E testing with Playwright
- [ ] Performance optimization
- [ ] Production deployment setup

## 💡 Tips

1. **First Time Setup**: Use the test user ID that's automatically loaded
2. **Development**: Both backend and frontend have hot reload
3. **Testing**: Use the provided test scripts to verify setup
4. **Debugging**: Check browser console and backend logs for errors
5. **API Testing**: Use the Swagger UI at http://localhost:8000/docs

## 🆘 Need Help?

1. Run `python test_backend.py` to diagnose backend issues
2. Check the browser console for frontend errors
3. Verify all services are running with `docker ps`
4. Make sure ports 3000 (frontend) and 8000 (backend) are available

Happy meal planning! 🍽️✨