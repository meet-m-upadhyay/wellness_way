# Supabase Migration Checklist for Teams

This checklist helps teams migrate from Docker to Supabase or set up with Supabase from the start.

## Pre-Migration Planning

- [ ] **Decide on setup approach**
  - [ ] All team members using Supabase (recommended)
  - [ ] Some using Docker locally, some using Supabase
  - [ ] Gradual migration from Docker to Supabase

- [ ] **Identify project reference**
  - [ ] Create Supabase account
  - [ ] Create project in Supabase dashboard
  - [ ] Document Project Reference (e.g., `abc123xyz`)

- [ ] **Set up Supabase project**
  - [ ] Go to https://supabase.com/dashboard
  - [ ] Click "New Project"
  - [ ] Select region (closest to team location)
  - [ ] Create strong database password
  - [ ] Wait for project initialization

- [ ] **Extract credentials**
  - [ ] Settings → Database
  - [ ] Note Project Reference
  - [ ] Note Database Password
  - [ ] Test connection string format

---

## Individual Developer Setup

### For Each Team Member

#### Step 1: Clone Repository
```bash
- [ ] git clone <repository-url>
- [ ] cd wellnessway-diet-planner
```

#### Step 2: Environment Configuration
```bash
- [ ] cp .env.supabase.example .env.supabase
- [ ] Edit .env.supabase with team's Supabase credentials
- [ ] cp .env.supabase .env
```

#### Step 3: Verify Connection
```bash
- [ ] cd backend
- [ ] python setup_supabase.py --test-connection
  - [ ] Connection successful ✓
  - [ ] Host correct
  - [ ] Database accessible
```

#### Step 4: Setup Database
```bash
- [ ] python -m alembic upgrade head
  - [ ] All migrations applied
  - [ ] No errors in output
```

#### Step 5: Verify Schema
```bash
- [ ] python setup_supabase.py --verify-tables
  - [ ] Tables created
  - [ ] Counts displayed for each table
```

#### Step 6: Test Queries
```bash
- [ ] python setup_supabase.py --test-query
  - [ ] All test queries pass
  - [ ] Version check works
  - [ ] Table enumeration works
```

#### Step 7: Start Application
```bash
- [ ] Backend:
  - [ ] cd backend
  - [ ] python start_backend.py
  - [ ] Server running on port 8000
- [ ] Frontend (new terminal):
  - [ ] cd frontend
  - [ ] npm install
  - [ ] npm start
  - [ ] Application accessible on port 3000
```

#### Step 8: Test Application
```bash
- [ ] Frontend loads (http://localhost:3000)
- [ ] Can create user account
- [ ] Can create diet plan
- [ ] API endpoints respond
- [ ] Database queries work
```

---

## Team Lead Setup Tasks

- [ ] **Repository Updates**
  - [ ] Commit `.env.supabase.example` to repository
  - [ ] Update README.md with Supabase setup instructions (if not done)
  - [ ] Commit setup scripts (setup_supabase.py)
  - [ ] Commit migration guide (docs/SUPABASE_MIGRATION.md)

- [ ] **Credentials Management**
  - [ ] Create secure credentials document (NOT committed to git)
  - [ ] Share with team via:
    - [ ] 1Password / LastPass
    - [ ] Private shared document
    - [ ] Environment variables in CI/CD
  - [ ] Document sharing method

- [ ] **Team Communication**
  - [ ] Announce Supabase migration to team
  - [ ] Share this checklist
  - [ ] Provide Supabase credentials securely
  - [ ] Set deadline for setup completion
  - [ ] Create support channel for issues

- [ ] **CI/CD Integration** (if applicable)
  - [ ] Update GitHub Actions with Supabase DATABASE_URL secret
  - [ ] Update deployment scripts
  - [ ] Test automated migrations in CI/CD

- [ ] **Backup Strategy**
  - [ ] Enable Supabase backups (automatic on paid plans)
  - [ ] Document backup location and recovery process
  - [ ] Test backup restoration

---

## Migration from Docker to Supabase

### Before Migration
- [ ] Back up existing Docker database
- [ ] Communicate migration date/time to team
- [ ] Ensure all pending work is committed

### Migration Steps
```bash
# 1. Verify current Docker setup
- [ ] docker-compose ps (all running)
- [ ] Backend accessible on port 8000
- [ ] Frontend accessible on port 3000

# 2. Stop Docker services
- [ ] docker-compose down
- [ ] Verify services stopped

# 3. Update environment
- [ ] cp .env.supabase.example .env.supabase
- [ ] Add Supabase credentials to .env.supabase
- [ ] cp .env.supabase .env
- [ ] Verify .env updated correctly

# 4. Test Supabase connection
- [ ] cd backend
- [ ] python setup_supabase.py --test-connection
- [ ] Connection successful ✓

# 5. Run migrations
- [ ] python -m alembic upgrade head
- [ ] All migrations applied
- [ ] No errors

# 6. Verify schema
- [ ] python setup_supabase.py --verify-tables
- [ ] All expected tables present

# 7. Start backend
- [ ] python start_backend.py
- [ ] Backend running
- [ ] API accessible

# 8. Start frontend
- [ ] npm start (in frontend directory)
- [ ] Frontend running
- [ ] Application accessible

# 9. Test application
- [ ] All features working
- [ ] No data loss
- [ ] API endpoints responsive
```

### After Migration
- [ ] All team members migrated
- [ ] Document any issues encountered
- [ ] Update team documentation
- [ ] Archive Docker setup documentation (if not needed)

---

## Verification Checklist

### For Each Setup
```bash
# Connection Test
- [ ] python setup_supabase.py --test-connection
  - Output: "✅ Database connection successful!"

# Schema Verification
- [ ] python setup_supabase.py --verify-tables
  - Output: Shows all expected tables

# Query Test
- [ ] python setup_supabase.py --test-query
  - Output: All tests pass

# Migration Status
- [ ] python setup_supabase.py --check-migrations
  - Output: All migrations applied

# Complete Diagnostic
- [ ] python setup_supabase.py --diagnose
  - Output: All checks pass
```

---

## Team Development Workflow

### Daily Development
```bash
# Start of day:
1. [ ] Pull latest code: git pull
2. [ ] Check migrations: python -m alembic history
3. [ ] Apply any new migrations: python -m alembic upgrade head
4. [ ] Start backend: python start_backend.py
5. [ ] Start frontend: npm start

# During development:
1. [ ] Make code changes
2. [ ] Create migrations if needed: python -m alembic revision --autogenerate
3. [ ] Test changes locally

# End of day:
1. [ ] Commit changes: git commit -m "description"
2. [ ] Push code: git push
3. [ ] Stop servers when done
```

### Before Each Sprint/Release
```bash
- [ ] All migrations reviewed and tested
- [ ] Database schema documented
- [ ] Migration rollback plan created
- [ ] Backup taken
- [ ] Team trained on new features
```

---

## Troubleshooting During Setup

### Connection Issues
```bash
- [ ] Verify .env file exists
- [ ] Check DATABASE_URL format
- [ ] Verify password doesn't contain special characters
- [ ] Test Supabase project is active
- [ ] Run: python setup_supabase.py --test-connection -v
```

### Migration Errors
```bash
- [ ] Clear existing schema (if safe):
  - [ ] Use Supabase SQL editor
  - [ ] DROP SCHEMA public CASCADE;
  - [ ] CREATE SCHEMA public;
- [ ] Re-run migrations: python -m alembic upgrade head
- [ ] Verify: python setup_supabase.py --verify-tables
```

### API Won't Start
```bash
- [ ] Check port 8000 is free
- [ ] Verify database connection
- [ ] Check Python virtual environment activated
- [ ] Review backend logs: tail -f backend/logs/app.log
```

### Tables Not Found
```bash
- [ ] Check migrations applied: python -m alembic history
- [ ] Run migrations if needed: python -m alembic upgrade head
- [ ] Verify tables exist: python setup_supabase.py --verify-tables
```

---

## Security Checklist

- [ ] Credentials stored securely (not in git)
- [ ] `.env` added to `.gitignore`
- [ ] No credentials in commit messages
- [ ] Team members use different Supabase accounts if possible
- [ ] Strong passwords (15+ characters with special chars)
- [ ] Regular password rotation in production
- [ ] Backups configured and tested
- [ ] IP whitelist configured (if needed)
- [ ] SSL connections verified
- [ ] Audit logs enabled

---

## Documentation Checklist

- [ ] README.md updated with setup instructions
- [ ] SUPABASE_MIGRATION.md created and shared
- [ ] setup_supabase.py script available and working
- [ ] Team has access to migration guides
- [ ] Emergency procedures documented
- [ ] Rollback procedures documented
- [ ] Support contacts documented

---

## Success Criteria

- ✅ All team members can access the same database
- ✅ Migrations work consistently across all machines
- ✅ Application features work identically in Docker and Supabase
- ✅ No data loss during migration
- ✅ Team productivity maintained or improved
- ✅ All automated tests passing
- ✅ Deployment process works
- ✅ Backups are configured and tested

---

## Post-Migration Tasks

- [ ] **Monitor Performance**
  - [ ] Check query performance
  - [ ] Monitor connection pooling
  - [ ] Review Supabase dashboard metrics

- [ ] **Team Training**
  - [ ] Review new setup with team
  - [ ] Train on troubleshooting
  - [ ] Provide documentation links

- [ ] **Cleanup**
  - [ ] Archive old Docker setup docs (if not needed)
  - [ ] Remove old local database backups
  - [ ] Update project documentation

- [ ] **Optimization**
  - [ ] Review connection pool settings
  - [ ] Optimize frequently-used queries
  - [ ] Consider caching strategies

---

## Support Resources

- **Supabase Docs**: https://supabase.com/docs
- **Setup Script**: `backend/setup_supabase.py`
- **Migration Guide**: `docs/SUPABASE_MIGRATION.md`
- **Project README**: `README.md`
- **Quick Start**: `QUICK_START_SUPABASE.md`

---

## Notes

Use this section to track team-specific information:

```
Team Lead: _____________________
Supabase Project Reference: _____________________
Migration Date: _____________________
Backup Location: _____________________
Support Contact: _____________________

Additional Notes:
___________________________________________________________
___________________________________________________________
___________________________________________________________
```

---

**✅ Checklist Complete!** Your team is ready to use Supabase.
