# Handling PyPI CDN Timeouts

## Overview
This document explains how the Pancake MCP Server handles PyPI CDN timeouts during Docker builds and package installations.

## Changes Made

### 1. Dockerfile Improvements
- Added timeout configurations for pip installations (600 seconds timeout)
- Implemented retry logic with 5 attempts for failed installations
- Added default timeout values (100 seconds) for individual operations
- Created a retry script that handles individual package installations with exponential backoff
- Added pip configuration file with global timeout settings

### 2. Installation Strategy
- Split dependencies into groups to reduce installation complexity
- Install core dependencies first, then image processing libraries, then dev dependencies
- Added build-essential to handle compilation of native packages
- Implemented environment variables for timeout control

### 3. Docker Compose Updates
- Updated docker-compose files to explicitly reference the Dockerfile
- Ensured build context is properly configured

## Configuration Details

### Timeout Settings
- `PIP_TIMEOUT=600`: Global timeout for pip operations
- `PIP_RETRIES=5`: Number of retry attempts for failed installations
- `PIP_DEFAULT_TIMEOUT=100`: Default timeout for individual requests

### Retry Logic
The system implements a retry script that:
- Attempts to install each dependency up to 5 times
- Waits 10 seconds between retry attempts
- Provides detailed logging of installation attempts
- Exits with error code if all retries fail

## Alternative Dockerfiles
Two Dockerfiles are provided:
1. `Dockerfile` - Standard approach with timeout handling
2. `Dockerfile.optimized` - Enhanced approach with individual retry logic for each dependency

## Usage
The system automatically handles timeout issues during Docker builds. Simply use the standard build commands:

```bash
# Standard build
docker-compose up --build

# Production build
docker-compose -f docker-compose.prod.yml up --build
```

## Benefits
- Reduced build failures due to CDN timeouts
- Improved reliability in low-bandwidth environments
- Better error handling and recovery
- More informative logging during installation