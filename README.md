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

**For Supabase Cloud (Recommended):**
- Supabase account (free tier at [supabase.com](https://supabase.com))
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

**For Local Docker Development:**
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

---

## Setup Option 1: Supabase Cloud (Recommended ⭐)

**Benefits:**
- ✅ Work from multiple laptops/machines
- ✅ No Docker required
- ✅ Cloud-hosted PostgreSQL database
- ✅ Managed backups and monitoring
- ✅ Free tier available

### Supabase Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd wellnessway-diet-planner
   ```

2. **Create Supabase project**
   - Go to [supabase.com](https://supabase.com)
   - Create a new account or sign in
   - Click "New Project" and follow the prompts
   - Save your database password

3. **Configure environment variables**
   ```bash
   cp .env.supabase.example .env.supabase
   # Edit .env.supabase with your Supabase credentials:
   # DATABASE_URL=postgresql+psycopg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
   # OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Copy Supabase configuration to active environment**
   ```bash
   cp .env.supabase .env
   ```

5. **Test database connection**
   ```bash
   cd backend
   
   # Windows PowerShell:
   .\venv\Scripts\python.exe setup_supabase.py --test-connection
   
   # macOS/Linux:
   python setup_supabase.py --test-connection
   ```

6. **Run database migrations**
   ```bash
   cd backend
   
   # Windows PowerShell:
   .\venv\Scripts\python.exe -m alembic upgrade head
   
   # macOS/Linux:
   python -m alembic upgrade head
   ```

7. **Verify schema creation**
   ```bash
   cd backend
   
   # Windows PowerShell:
   .\venv\Scripts\python.exe setup_supabase.py --verify-tables
   
   # macOS/Linux:
   python setup_supabase.py --verify-tables
   ```

8. **Start services**
   
   Terminal 1 - Backend:
   ```bash
   cd backend
   
   # Windows PowerShell:
   .\venv\Scripts\python.exe start_backend.py
   
   # macOS/Linux:
   python start_backend.py
   ```
   
   Terminal 2 - Frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

9. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

**For detailed Supabase migration guide, see:** [docs/SUPABASE_MIGRATION.md](docs/SUPABASE_MIGRATION.md)

---

## Setup Option 2: Local Docker Development

**Benefits:**
- ✅ Completely local development
- ✅ No internet required (after initial setup)
- ✅ Full control over database
- ✅ Easiest for single-machine development

### Local Docker Setup

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

### Database Access (Docker Option)

You can connect to the local PostgreSQL database using:

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

---

## Switching Between Setups

### From Docker to Supabase

If you want to switch from local Docker to Supabase cloud:

```bash
# 1. Create your Supabase project and get credentials
# 2. Create .env.supabase with your credentials
cp .env.supabase.example .env.supabase
# Edit with your Supabase credentials

# 3. Switch to Supabase configuration
cp .env.supabase .env

# 4. Test the connection
cd backend
python setup_supabase.py --test-connection

# 5. Run migrations (only if Supabase database is empty)
python -m alembic upgrade head

# 6. Start the application
python start_backend.py
```

### From Supabase to Docker

If you want to switch back to local Docker:

```bash
# 1. Start Docker containers
docker-compose up -d

# 2. Switch back to Docker configuration
# Edit .env to use: DATABASE_URL=postgresql+psycopg://wellnessway:password@localhost:5432/wellnessway_db

# 3. Run migrations if needed
cd backend
python -m alembic upgrade head

# 4. Start the application
python start_backend.py
```

### Important Notes

- Both setups use the **same database schema** and **Alembic migrations**
- No code changes required to switch between setups
- Your data stays in the respective database (local or cloud)
- Always verify connection before starting the application
- For team development, recommend using Supabase for consistency

---

## Multi-Device Development

With Supabase, you can work on multiple laptops/machines:

1. **Setup on Machine 1:**
   ```bash
   git clone <repository-url>
   cp .env.supabase.example .env.supabase
   # Add your Supabase credentials
   cp .env.supabase .env
   python setup_supabase.py --test-connection
   ```

2. **Setup on Machine 2:**
   ```bash
   git clone <repository-url>
   cp .env.supabase.example .env.supabase
   # Use the SAME Supabase credentials
   cp .env.supabase .env
   python setup_supabase.py --test-connection
   ```

3. **Share credentials securely:**
   - Use a password manager or secure file sharing
   - Never commit .env files to git
   - Each team member gets their own .env (not committed)

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