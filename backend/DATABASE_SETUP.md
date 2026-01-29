# Database Setup - WellnessWay Diet Planner

This document describes the PostgreSQL database configuration and setup for the WellnessWay Diet Planner application.

## Database Schema

The application uses PostgreSQL with the following main tables:

### Core Tables

1. **users** - User profile information
   - Basic demographics (name, age, gender, height, weight)
   - Body composition data (body fat %, muscle mass)
   - Activity level for TDEE calculation
   - Timestamps for creation and updates

2. **health_goals** - User health objectives
   - Primary goal (fat loss, muscle gain, maintenance)
   - Target weight and timeline
   - Links to user profile

3. **diet_preferences** - Dietary restrictions and preferences
   - Diet type (vegetarian, non-vegetarian, vegan)
   - Allergies and foods to avoid (stored as JSON arrays)
   - Meal frequency and lifestyle constraints
   - Links to user profile

4. **health_context_documents** - Versioned health profiles
   - Immutable markdown documents containing complete health context
   - Calculated metabolic values (BMR, TDEE, safety constraints)
   - Version tracking for profile changes
   - Only one active version per user

5. **diet_plans** - Generated meal plans
   - Weekly or daily plan types
   - Complete meal structure stored as JSON
   - Links to user and health context document used
   - Creation timestamps

### Key Features

- **UUID Primary Keys**: All tables use UUID primary keys for better scalability
- **Data Validation**: Comprehensive check constraints for data integrity
- **JSON Storage**: Flexible storage for allergies, food preferences, and meal plans
- **Versioning**: Health context documents support immutable versioning
- **Indexes**: Performance-optimized indexes on frequently queried fields

## Database Configuration

### Connection Settings

The application uses SQLAlchemy with the following configuration:

```python
# Database URL format
DATABASE_URL = "postgresql://username:password@host:port/database_name"

# Connection pooling
POOL_SIZE = 5
MAX_OVERFLOW = 10
```

### Environment Variables

Required environment variables:

```bash
DATABASE_URL=postgresql://wellnessway:password@localhost:5432/wellnessway_db
POSTGRES_USER=wellnessway
POSTGRES_PASSWORD=password
POSTGRES_DB=wellnessway_db
```

## Migration Management

The application uses Alembic for database migrations:

### Initial Setup

1. **Initialize Alembic** (already done):
   ```bash
   cd backend
   python -m alembic init alembic
   ```

2. **Create Initial Migration**:
   ```bash
   python -m alembic revision -m "Initial database schema"
   ```

3. **Apply Migrations**:
   ```bash
   python -m alembic upgrade head
   ```

### Migration Commands

- **Create new migration**: `python -m alembic revision --autogenerate -m "Description"`
- **Apply migrations**: `python -m alembic upgrade head`
- **Rollback migration**: `python -m alembic downgrade -1`
- **Show current version**: `python -m alembic current`
- **Show migration history**: `python -m alembic history`

## Development Setup

### Using Docker Compose

1. **Start PostgreSQL**:
   ```bash
   docker-compose up -d database
   ```

2. **Apply migrations**:
   ```bash
   cd backend
   python -m alembic upgrade head
   ```

3. **Initialize sample data** (optional):
   ```bash
   python -m app.database.init_db
   ```

### Local PostgreSQL

If using a local PostgreSQL installation:

1. Create database:
   ```sql
   CREATE DATABASE wellnessway_db;
   CREATE USER wellnessway WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE wellnessway_db TO wellnessway;
   ```

2. Update `DATABASE_URL` in `.env` file
3. Apply migrations as above

## Testing

### Database Tests

Run database model tests:

```bash
cd backend
python -m pytest tests/test_database.py -v
```

### Test Database

Tests use an in-memory SQLite database for fast execution:

```python
# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
```

## Data Validation

### User Profile Constraints

- Age: 0 < age < 150
- Height: 50 < height_cm < 300
- Weight: 20 < weight_kg < 500
- Body fat: 0 ≤ body_fat_percentage ≤ 100 (optional)
- Gender: 'male', 'female', 'other'
- Activity level: 'sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active'

### Health Goals Constraints

- Primary goal: 'fat_loss', 'muscle_gain', 'maintenance'
- Target weight: 20 < target_weight_kg < 500 (optional)
- Timeline: 0 < timeline_weeks ≤ 104 (optional, max 2 years)

### Diet Preferences Constraints

- Diet type: 'vegetarian', 'non_vegetarian', 'vegan'
- Meals per day: 1 ≤ meals_per_day ≤ 8

### Health Context Document Constraints

- BMR calories > 0
- TDEE calories > BMR calories
- Min daily calories ≥ BMR calories
- Max calorie deficit > 0
- Min protein grams > 0
- Version > 0
- Unique (user_id, version) combination

### Diet Plan Constraints

- Plan type: 'weekly', 'daily'

## Performance Considerations

### Indexes

The following indexes are created for optimal query performance:

- `ix_users_created_at` - User creation date queries
- `ix_health_goals_user_id` - User's health goals lookup
- `ix_diet_preferences_user_id` - User's diet preferences lookup
- `ix_health_context_documents_user_id` - User's HCD lookup
- `ix_health_context_documents_is_active` - Active HCD queries
- `ix_diet_plans_user_id` - User's diet plans lookup
- `ix_diet_plans_hcd_id` - Plans by HCD lookup
- `ix_diet_plans_created_at` - Recent plans queries

### Connection Pooling

SQLAlchemy connection pooling is configured for optimal performance:

- Pool size: 5 connections
- Max overflow: 10 additional connections
- Pre-ping: Validates connections before use

## Security

### Data Protection

- All sensitive data should be encrypted at rest (configured at PostgreSQL level)
- Use HTTPS for all API communications
- Validate all inputs before database operations
- Use parameterized queries (SQLAlchemy ORM handles this)

### Access Control

- Database user has minimal required privileges
- No direct database access from frontend
- All database operations go through FastAPI backend
- Input validation at both Pydantic model and database constraint levels

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure PostgreSQL is running and accessible
2. **Migration conflicts**: Check migration history and resolve conflicts
3. **Constraint violations**: Review data validation rules
4. **Performance issues**: Check query patterns and index usage

### Health Checks

The application provides database health check endpoints:

- `/health` - Basic application health
- `/db-health` - Database connectivity check

### Logging

Database operations are logged when `DEBUG=true`:

- SQL queries are logged to console
- Connection pool status is monitored
- Error details are captured for troubleshooting

## Future Enhancements

### Planned Improvements

1. **Foreign Key Constraints**: Add explicit foreign key relationships
2. **Audit Logging**: Track all data changes with timestamps
3. **Data Archival**: Implement soft deletes and data retention policies
4. **Read Replicas**: Configure read-only replicas for scaling
5. **Backup Strategy**: Automated backup and point-in-time recovery
6. **Monitoring**: Database performance metrics and alerting