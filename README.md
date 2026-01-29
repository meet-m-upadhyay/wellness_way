# WellnessWay Diet Planner

An AI-powered health planning application that helps users design personalized diet plans based on their health profile, goals, and preferences.

## Project Structure

```
wellnessway-diet-planner/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── models/         # Pydantic models and database models
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Business logic and calculations
│   │   ├── services/       # External service integrations (AI, etc.)
│   │   └── database/       # Database configuration and migrations
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # React.js frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client and services
│   │   ├── types/          # TypeScript type definitions
│   │   ├── utils/          # Utility functions
│   │   └── App.tsx        # Main App component
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile        # Frontend container
├── docker-compose.yml     # Local development environment
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md           # This file
```

## Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React.js with TypeScript
- **Database**: PostgreSQL 15+
- **Styling**: Tailwind CSS
- **AI Integration**: OpenAI GPT-4
- **Containerization**: Docker & Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd wellnessway-diet-planner
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file and add your OpenAI API key:
   # OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Start the database**
   ```bash
   docker-compose up -d database
   ```

4. **⚠️ IMPORTANT: Run database migrations**
   
   The database starts empty and needs migrations to create tables:
   ```bash
   cd backend
   
   # Windows PowerShell:
   .\venv\Scripts\python.exe -m alembic upgrade head
   
   # macOS/Linux:
   python -m alembic upgrade head
   ```
   
   **Why this step is needed**: The PostgreSQL container creates an empty database. The application tables (users, diet_plans, etc.) are created by running Alembic migrations. Without this step, you'll see an empty database in database tools like SQLTools.

5. **Start all services**
   ```bash
   docker-compose up -d
   ```

6. **Verify setup**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: localhost:5432 (wellnessway_db, user: wellnessway, password: password)

### Database Access

You can connect to the PostgreSQL database using:

**Connection Details:**
- Host: localhost
- Port: 5432
- Database: wellnessway_db
- Username: wellnessway
- Password: password

**Using psql command line:**
```bash
docker exec -it wellnessway-db psql -U wellnessway -d wellnessway_db
```

**Using database tools:**
- SQLTools (VS Code/Kiro extension)
- pgAdmin, DBeaver, TablePlus, etc.

**Quick database status check:**
```bash
# Check if tables exist
docker exec wellnessway-db psql -U wellnessway -d wellnessway_db -c "\dt"

# View table structures
docker exec wellnessway-db psql -U wellnessway -d wellnessway_db -c "\d users"
```

## Development Workflow

### Backend Development
1. **Work in the `backend/` directory**
2. **Activate virtual environment**: `.\venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` (macOS/Linux)
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Run tests**: `pytest`
5. **Start development server**: `uvicorn app.main:app --reload`

## Quick Commands for Future Reference to kill backend port manually:
### Check what's using port 8000
netstat -ano | findstr :8000
### Kill specific process by PID
taskkill /PID <PID_NUMBER> /F
### Kill all Python processes (use carefully!)
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
### Test if port is free
Test-NetConnection -ComputerName localhost -Port 8000

### Frontend Development
1. **Work in the `frontend/` directory**
2. **Install dependencies**: `npm install`
3. **Start development server**: `npm start`
4. **Run tests**: `npm test`
5. **Build for production**: `npm run build`

### Database Changes
1. **Create new migration**: `alembic revision --autogenerate -m "description"`
2. **Apply migrations**: `alembic upgrade head`
3. **Rollback migration**: `alembic downgrade -1`
4. **View migration history**: `alembic history`

### Common Issues and Solutions

**Problem**: "No tables visible in database tools"
- **Solution**: Run database migrations: `alembic upgrade head`

**Problem**: "AI service not working"
- **Solution**: Set OPENAI_API_KEY in your .env file

**Problem**: "Database connection failed"
- **Solution**: Ensure PostgreSQL container is running: `docker-compose up -d database`

**Problem**: "Import errors in Python"
- **Solution**: Activate virtual environment and install dependencies

## Core Features

- **User Profile Management**: Create and manage health profiles with BMR/TDEE calculations
- **Health Context Documents**: Versioned, immutable health summaries for AI planning
- **AI-Powered Diet Planning**: Generate personalized weekly and daily meal plans
- **Safety Constraints**: Built-in calorie limits, protein requirements, and dietary restrictions
- **Plan Regeneration**: Regenerate individual meals, days, or entire plans
- **Nutritional Tracking**: Comprehensive macro and micronutrient tracking
- **Preference Compliance**: Strict enforcement of allergies and dietary preferences

## API Endpoints

### User Management
- `POST /api/users/profile` - Create user profile
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update user profile

### Health Context
- `GET /api/health-context` - Get current health context document
- `POST /api/health-context/update` - Update profile and create new HCD

### Diet Plans
- `POST /api/diet-plans/weekly` - Generate weekly diet plan
- `POST /api/diet-plans/daily` - Generate daily diet plan
- `GET /api/diet-plans` - List user's diet plans
- `GET /api/diet-plans/{id}` - Get specific diet plan
- `POST /api/diet-plans/{id}/regenerate-meal` - Regenerate specific meal
- `POST /api/diet-plans/{id}/regenerate-day` - Regenerate specific day
- `POST /api/diet-plans/{id}/regenerate` - Regenerate entire plan

Full API documentation available at: http://localhost:8000/docs

## Safety and Compliance

This application includes built-in safety constraints:
- Minimum daily calorie limits
- Maximum calorie deficit restrictions
- Protein requirement validation
- Allergy and dietary restriction enforcement
- Medical disclaimers and safety warnings

## Contributing

1. Follow the established project structure
2. Write tests for new features
3. Use property-based testing for correctness validation
4. Follow code formatting standards (Black for Python, Prettier for TypeScript)
5. Update documentation as needed

## License

[Add your license here]