## Chrome Storage Setup

### Local Development
1. Copy `craw4ai_config/state.template.json` to `craw4ai_config/state.json`
2. Update the values in `state.json` according to your needs
3. Do not commit `state.json` to version control as it contains sensitive information

### Production Deployment
1. Initial Setup on VPS:
```bash
# Create directory for Chrome storage
mkdir -p /app/craw4ai_config

# Copy template file
cp craw4ai_config/state.template.json /app/craw4ai_config/state.json

# Set proper permissions
chmod 600 /app/craw4ai_config/state.json
```

2. Configuration:
- The storage state is mounted at `/app/craw4ai_config/state.json` in all containers that need browser access
- Uses a named Docker volume `chrome_storage` for persistence
- Environment variable `CHROME_STORAGE_PATH=/app/craw4ai_config/state.json` is set in all relevant services

3. Managing the Storage:
```bash
# View current storage state
docker-compose exec web cat /app/craw4ai_config/state.json

# Edit storage state
docker-compose exec web vi /app/craw4ai_config/state.json

# Backup storage state
docker-compose exec web cat /app/craw4ai_config/state.json > backup_state.json

# Restore from backup
docker cp backup_state.json <container_id>:/app/craw4ai_config/state.json
```

4. Troubleshooting:
- If browser automation fails, check storage permissions and content
- Verify the storage path matches `CHROME_STORAGE_PATH` environment variable
- Ensure the storage volume is properly mounted in all services that need it
- Check container logs for any storage-related errors 

## Submodules

This project uses Git submodules. After cloning the repository, run:

```bash
# Initialize submodules
git submodule init

# Update submodules
git submodule update

# Or do both in one command
git submodule update --init --recursive
``` 