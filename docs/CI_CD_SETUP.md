# WellnessWay CI/CD Pipeline Documentation

## Overview

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the WellnessWay Diet Planner application. The pipeline is implemented using GitHub Actions and includes automated testing, security scanning, building, and deployment processes.

## Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Code Push     │───▶│   CI Pipeline   │───▶│   CD Pipeline   │
│   Pull Request  │    │   (Testing)     │    │   (Deployment)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Monitoring    │
                       │   & Alerting    │
                       └─────────────────┘
```

## Workflows

### 1. Main CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

This is the primary workflow that runs on every push and pull request.

#### Stages:

1. **Backend Testing**
   - Unit tests with pytest
   - Property-based tests with Hypothesis
   - Code coverage reporting
   - Linting with flake8
   - Type checking with mypy

2. **Frontend Testing**
   - Unit tests with Jest/React Testing Library
   - Property-based tests with fast-check
   - Code coverage reporting
   - Linting with ESLint
   - Type checking with TypeScript

3. **Security Scanning**
   - Vulnerability scanning with Trivy
   - Dependency security checks
   - SARIF report generation

4. **Build Docker Images**
   - Multi-stage Docker builds
   - Image tagging and versioning
   - Push to GitHub Container Registry

5. **Integration Testing**
   - End-to-end tests with Playwright
   - Service integration tests
   - Health checks

6. **Deployment**
   - Staging deployment (develop branch)
   - Production deployment (main branch)
   - Environment-specific configurations

#### Triggers:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

### 2. Dependency Updates (`.github/workflows/dependency-update.yml`)

Automated dependency management and security monitoring.

#### Features:
- Weekly dependency updates
- Security vulnerability scanning
- Automated pull request creation
- Secrets scanning with TruffleHog

#### Schedule:
- Runs every Monday at 9 AM UTC
- Can be triggered manually

### 3. Performance Testing (`.github/workflows/performance-test.yml`)

Performance monitoring and benchmarking.

#### Tests:
- Backend API performance with Locust
- Frontend performance with Lighthouse
- Database performance benchmarks
- Bundle size analysis

#### Schedule:
- Runs daily at 2 AM UTC
- Runs on pushes to main branch
- Can be triggered manually

## Environment Configuration

### Development Environment
- **File**: `.env`
- **Compose**: `docker-compose.yml`
- **Purpose**: Local development and testing

### Staging Environment
- **File**: `.env.testing`
- **Compose**: `docker-compose.yml`
- **Purpose**: Pre-production testing and validation

### Production Environment
- **File**: `.env.production`
- **Compose**: `docker-compose.prod.yml`
- **Purpose**: Live production deployment

## Deployment Scripts

### Bash Script (`scripts/deploy.sh`)
For Unix-like systems (Linux, macOS):

```bash
# Deploy to staging
./scripts/deploy.sh staging latest

# Deploy to production
./scripts/deploy.sh production v1.0.0

# Rollback deployment
./scripts/deploy.sh --rollback
```

### PowerShell Script (`scripts/deploy.ps1`)
For Windows systems:

```powershell
# Deploy to staging
.\scripts\deploy.ps1 -Environment staging -Version latest

# Deploy to production
.\scripts\deploy.ps1 -Environment production -Version v1.0.0

# Rollback deployment
.\scripts\deploy.ps1 -Rollback
```

## Monitoring and Alerting

### Components

1. **Prometheus** - Metrics collection
2. **Grafana** - Visualization and dashboards
3. **AlertManager** - Alert routing and notifications
4. **Node Exporter** - System metrics
5. **cAdvisor** - Container metrics

### Setup

```bash
# Start monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Access dashboards
# Grafana: http://localhost:3001 (admin/admin123)
# Prometheus: http://localhost:9090
# AlertManager: http://localhost:9093
```

### Alerts

The system monitors:
- CPU and memory usage
- Disk space
- Service availability
- HTTP error rates
- Database connections
- Response times
- Container restarts

## Security Features

### Vulnerability Scanning
- **Trivy**: Container and filesystem scanning
- **Safety**: Python dependency vulnerability checks
- **npm audit**: Node.js dependency security checks
- **TruffleHog**: Secrets detection in code

### Security Best Practices
- Non-root container users
- Minimal base images
- Regular dependency updates
- Secrets management with environment variables
- HTTPS enforcement in production

## Testing Strategy

### Unit Tests
- **Backend**: pytest with coverage reporting
- **Frontend**: Jest with React Testing Library
- **Coverage**: Minimum 80% coverage required

### Property-Based Tests
- **Backend**: Hypothesis for testing business logic properties
- **Frontend**: fast-check for testing UI component properties
- **Focus**: Correctness properties from design document

### Integration Tests
- **End-to-End**: Playwright for full user journey testing
- **API**: Integration tests for backend services
- **Database**: Migration and query performance tests

### Performance Tests
- **Load Testing**: Locust for API load testing
- **Frontend**: Lighthouse for web performance
- **Database**: pgbench for database performance

## Secrets Management

### GitHub Secrets
Required secrets for CI/CD:

```
GITHUB_TOKEN          # Automatically provided
OPENAI_API_KEY        # For AI integration tests
DATABASE_URL          # Test database connection
SENTRY_DSN           # Error tracking (optional)
```

### Environment Variables
Managed through environment files:

```bash
# Database configuration
POSTGRES_USER=wellnessway
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=wellnessway_db

# Application configuration
SECRET_KEY=your-secret-key
DEBUG=false
ENVIRONMENT=production

# External services
OPENAI_API_KEY=your-openai-key
SENTRY_DSN=your-sentry-dsn
```

## Deployment Environments

### Local Development
- **URL**: http://localhost:3000
- **API**: http://localhost:8000
- **Database**: localhost:5432
- **Purpose**: Development and testing

### Staging
- **URL**: http://staging.wellnessway.com
- **API**: http://api-staging.wellnessway.com
- **Purpose**: Pre-production validation
- **Auto-deploy**: On push to `develop` branch

### Production
- **URL**: https://wellnessway.com
- **API**: https://api.wellnessway.com
- **Purpose**: Live application
- **Auto-deploy**: On push to `main` branch

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check test results in GitHub Actions
   - Verify environment variables are set
   - Check Docker image build logs

2. **Deployment Failures**
   - Verify environment configuration
   - Check service health endpoints
   - Review deployment script logs

3. **Test Failures**
   - Check test coverage reports
   - Review property-based test failures
   - Verify database migrations

### Debugging Commands

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs backend
docker-compose logs frontend

# Run tests locally
cd backend && pytest tests/ -v
cd frontend && npm test

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:3000
```

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review dependency update PRs
   - Check security scan results
   - Monitor performance metrics

2. **Monthly**
   - Update base Docker images
   - Review and update alert thresholds
   - Clean up old Docker images

3. **Quarterly**
   - Security audit and penetration testing
   - Performance optimization review
   - Disaster recovery testing

### Monitoring Checklist

- [ ] All services are healthy
- [ ] No critical alerts firing
- [ ] Performance metrics within acceptable ranges
- [ ] Security scans passing
- [ ] Backup systems functioning
- [ ] SSL certificates valid

## Contributing

### Adding New Tests
1. Add unit tests for new features
2. Include property-based tests for business logic
3. Update integration tests for new endpoints
4. Ensure coverage requirements are met

### Modifying Pipeline
1. Test changes in a feature branch
2. Update documentation
3. Get approval from team leads
4. Monitor deployment after changes

### Security Considerations
1. Never commit secrets to code
2. Use environment variables for configuration
3. Keep dependencies updated
4. Follow security scanning recommendations

## Support

For issues with the CI/CD pipeline:

1. Check GitHub Actions logs
2. Review this documentation
3. Contact the DevOps team
4. Create an issue in the repository

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Playwright Documentation](https://playwright.dev/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)