# Microservices CI/CD Test

This repository demonstrates a CI/CD workflow for managing multiple microservices with automated port assignments and environment transitions.

## Directory Structure

```
environments/
  development/
    microServiceCICDTest/  # Your microservice name
      feature-example/     # Your feature branch name
        .env              # Environment-specific config (port 5xxx)
        app.py           # Application code
        Dockerfile       # Container configuration
        tests/          # Test suites
  staging/
    microServiceCICDTest/
      .env              # Staging config (port 6xxx)
      app.py
      Dockerfile
      tests/
  production/
    microServiceCICDTest/
      .env              # Production config (port 7xxx)
      app.py
      Dockerfile
      tests/
```

## Special Branches

### feature-test-infra
This is a protected branch that contains the initial infrastructure setup and testing framework. Do not delete this branch as it serves as a reference implementation.

## Port Ranges

Each environment has its own port range to prevent conflicts:
- Development: 5000-5999
- Staging: 6000-6999
- Production: 7000-7999

## Working with Feature Branches

### Creating a Feature Branch
```bash
git checkout -b feature-{name} 
git push origin feature-{name}
git pull origin feature-{name} --rebase
```

### Running Your Feature Branch Locally
```bash
# The .env file will be in environments/development/microservice-name/feature-name/
docker compose --env-file environments/development/microservice-name/feature-name/.env up -d
```

### Running Staging Environment
```bash
# The .env file will be in environments/staging/microservice-name/
docker compose --env-file environments/staging/microservice-name/.env up -d
```

### Running Production Environment
```bash
# The .env file will be in environments/production/microservice-name/
docker compose --env-file environments/production/microservice-name/.env up -d
```

### Cleaning Up Feature Branches
```bash
git branch -D feature-{name}
git push origin --delete feature-{name}
```

## Environment Transitions

1. Development to Staging:
   - Create PR from feature branch to staging
   - Feature branch environment remains active for continued development
   - A new staging environment is created with a port in 6xxx range
   - Original feature branch port (5xxx) remains available for development
   - Feature environment is only cleaned up when the feature branch is explicitly deleted

2. Staging to Production:
   - Create PR from staging to master
   - Port will be migrated from 6xxx to 7xxx range
   - Staging port will be released

## Additional Setup

### Creating the Docker Network
```bash
docker network create app-network
```

### Setting Up Development Environment
```bash
./setup.sh
```

## Understanding the Workflow

1. When you create a feature branch:
   - Gets assigned a port in the 5000-5999 range
   - Creates environment files in `environments/development/microservice-name/feature-name/`

2. When you merge to staging:
   - Gets assigned a port in the 6000-6999 range
   - Creates environment files in `environments/staging/microservice-name/`
   - Releases the development port

3. When you merge to production (master):
   - Gets assigned a port in the 7000-7999 range
   - Creates environment files in `environments/production/microservice-name/`
   - Releases the staging port

Each environment directory contains:
- `.env` file with environment-specific configuration
- `README.md` with environment details and instructions
- Application code and tests
- Test reports and coverage data

## Troubleshooting

If you need to sync your local branch with master:
```bash
git stash
git pull origin master --rebase
git stash pop
git add -A
git commit -m "your commit message"
git push origin master
```

If you need to manually reset the staging branch to match master:
```bash
# First, backup any important staging-specific configurations
git checkout staging
git diff origin/master > staging-changes.patch

# Reset staging to match master
git fetch origin
git reset --hard origin/master
git push -f origin staging

# If needed, reapply staging-specific configurations
git apply staging-changes.patch
git add .
git commit -m "Restore staging-specific configurations"
git push origin staging
```

## CI/CD Pipeline Workflow

Our CI/CD pipeline automates the entire process of developing, testing, and deploying microservices across different environments. Here's a detailed guide on how it works:

### 1. Feature Branch Development

When you create a new feature branch:
```bash
# Create and push feature branch
git checkout -b feature-your-feature-name
git push -u origin feature-your-feature-name
```

The pipeline automatically:
- Assigns a unique port in the 5000-5999 range
- Creates a development environment at `environments/development/microServiceCICDTest/feature-your-feature-name/`
- Copies template files (app.py, Dockerfile, tests, etc.)
- Updates the .env file with the assigned port
- Runs all test suites (mandatory, recommended, optional)
- Builds and pushes a Docker image

### 2. Migrating to Staging

When ready to test in staging:
```bash
# First, ensure you're on your feature branch
git checkout feature-your-feature-name

# Create a pull request to staging
# You can do this through GitHub UI or command line
```

The pipeline automatically:
- Creates the staging environment at `environments/staging/microServiceCICDTest/`
- Migrates the port from 5xxx to 6xxx range
- Updates all configuration files with new port
- Runs all tests again
- Builds and pushes a new Docker image for staging
- Releases the development port

### 3. Migrating to Production

When staging is verified and ready for production:
```bash
# Create a pull request from staging to master
# You can do this through GitHub UI or command line
```

The pipeline automatically:
- Creates the production environment at `environments/production/microServiceCICDTest/`
- Migrates the port from 6xxx to 7xxx range
- Updates all configuration files with new port
- Runs all tests one final time
- Builds and pushes a production Docker image
- Releases the staging port

### 4. Cleanup Process

When a feature branch is deleted or PR is closed:
```bash
# Delete feature branch locally and remotely
git branch -D feature-your-feature-name
git push origin --delete feature-your-feature-name
```

The pipeline automatically:
- Releases the assigned port
- Removes the environment directory
- Cleans up Docker resources
- Updates ports.json

### 5. Testing Different Environments

To run your service in different environments:

```bash
# Development (Feature Branch)
docker compose --env-file environments/development/microServiceCICDTest/feature-your-feature-name/.env up -d

# Staging
docker compose --env-file environments/staging/microServiceCICDTest/.env up -d

# Production
docker compose --env-file environments/production/microServiceCICDTest/.env up -d
```

### 6. Monitoring and Debugging

- Check GitHub Actions for pipeline status and logs
- View test reports in the Actions tab
- Check ports.json for current port assignments
- Environment-specific logs are in their respective directories

### 7. Common Issues and Solutions

1. Port Conflicts:
   - Check ports.json for current assignments
   - Ensure no local services use the same ports
   - Delete unused feature branches to release ports

2. Failed Tests:
   - Check test reports in GitHub Actions
   - Tests are in the tests/ directory of each environment
   - Development branches can proceed with failed tests

3. Directory Issues:
   - Ensure you're using the correct environment path
   - Check permissions if getting access errors
   - Use absolute paths with docker compose

4. Docker Issues:
   - Ensure Docker is running
   - Check if the app-network exists
   - Try rebuilding the image with --no-cache

Remember: The pipeline is designed to be fully automated. Let it handle port assignments, directory creation, and environment transitions. Don't manually modify ports.json or environment directories unless absolutely necessary.