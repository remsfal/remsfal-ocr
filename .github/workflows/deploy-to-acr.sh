#!/usr/bin/env bash

###############################################################################
# REMSFAL OCR - Azure Container Registry Deployment Script
###############################################################################
#
# This script runs tests and builds a Docker image for the OCR microservice
# directly on Azure Container Registry (ACR) using ACR Build Tasks.
#
# NOTE: Uses 'az acr build' to build on Azure's amd64 infrastructure,
#       avoiding emulation issues on Apple Silicon Macs.
#
# SERVICE:
#   - remsfal-ocr (Port 8083) - OCR microservice for text extraction from images
#
# USAGE:
#   chmod +x .github/workflows/deploy-to-acr.sh
#   ./.github/workflows/deploy-to-acr.sh <ACR_NAME> [IMAGE_TAG] [--skip-tests]
#
# PREREQUISITES:
#   - Azure CLI installed and logged in (az login)
#   - Access to the ACR resource
#
# EXAMPLES:
#   # Deploy with tests
#   ./.github/workflows/deploy-to-acr.sh rmsfldevweuacr v1.0.0
#
#   # Deploy with latest tag
#   ./.github/workflows/deploy-to-acr.sh rmsfldevweuacr
#
#   # Deploy without tests (faster for debugging)
#   ./.github/workflows/deploy-to-acr.sh rmsfldevweuacr latest --skip-tests
#
# PULL AND RUN LOCALLY:
#   # 1. Login to ACR
#   az acr login --name rmsfldevweuacr
#
#   # 2. Pull image
#   docker pull rmsfldevweuacr.azurecr.io/remsfal-ocr:latest
#
#   # 3. Run container (requires env variables)
#   docker run -d -p 8083:8083 --name ocr \
#     -e STORAGE_PROVIDER=AZURE \
#     -e SECRETS_PROVIDER=AZURE_KEYVAULT \
#     -e KEYVAULT_URL=https://your-vault.vault.azure.net \
#     rmsfldevweuacr.azurecr.io/remsfal-ocr:latest
#
# CONTAINER APPS CONFIGURATION:
#   The OCR service requires the following environment variables (from Key Vault):
#   - STORAGE_PROVIDER: AZURE
#   - SECRETS_PROVIDER: AZURE_KEYVAULT
#   - KEYVAULT_URL: Key Vault endpoint
#   - KAFKA_PROVIDER: AZURE (for Event Hub)
#   - KAFKA_TOPIC_IN: ocr.documents.to_process
#   - KAFKA_TOPIC_OUT: ocr.documents.processed
#   - KAFKA_GROUP_ID: ocr-consumer-group
#
# PARAMETERS:
#   ACR_NAME      - Name of Azure Container Registry (e.g., rmsfldevweuacr)
#   IMAGE_TAG     - (Optional) Docker image tag (default: latest)
#   --skip-tests  - (Optional) Skip running pytest before build
#
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Parse arguments - separate flags from positional args
SKIP_TESTS="false"
POSITIONAL_ARGS=()

for arg in "$@"; do
    case $arg in
        --skip-tests)
            SKIP_TESTS="true"
            ;;
        *)
            POSITIONAL_ARGS+=("$arg")
            ;;
    esac
done

# Validate input parameters
if [ ${#POSITIONAL_ARGS[@]} -lt 1 ]; then
    log_error "Missing required parameters"
    echo ""
    echo "Usage: $0 <ACR_NAME> [IMAGE_TAG] [--skip-tests]"
    echo ""
    echo "Prerequisites:"
    echo "  - Azure CLI installed and logged in (az login)"
    echo "  - Access to the ACR resource"
    echo ""
    echo "Examples:"
    echo "  $0 rmsfldevweuacr v1.0.0"
    echo "  $0 rmsfldevweuacr latest --skip-tests"
    echo ""
    echo "Flags:    --skip-tests  Skip running pytest before build"
    exit 1
fi

ACR_NAME="${POSITIONAL_ARGS[0]}"
IMAGE_TAG="${POSITIONAL_ARGS[1]:-latest}"

# Configuration
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
SERVICE_NAME="remsfal-ocr"
SERVICE_PORT="8083"
DOCKERFILE_PATH="docker/Dockerfile"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Change to project root
cd "${PROJECT_ROOT}"

echo "======================================================================"
log_info "REMSFAL OCR Deployment to Azure Container Registry"
echo "======================================================================"
echo ""
log_info "ACR:         ${ACR_LOGIN_SERVER}"
log_info "Image Tag:   ${IMAGE_TAG}"
log_info "Service:     ${SERVICE_NAME}"
log_info "Project:     ${PROJECT_ROOT}"
log_info "Skip Tests:  ${SKIP_TESTS}"
log_info "Build Mode:  ACR Build Tasks (remote amd64)"
echo ""

###############################################################################
# Step 1: Check prerequisites
###############################################################################
log_step "Step 1: Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    log_error "Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Determine Python command
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$(${PYTHON_CMD} --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo "${PYTHON_VERSION}" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "${PYTHON_VERSION}" | cut -d'.' -f2)

if [ "${PYTHON_MAJOR}" -lt 3 ] || ([ "${PYTHON_MAJOR}" -eq 3 ] && [ "${PYTHON_MINOR}" -lt 11 ]); then
    log_error "Python 3.11+ is required. Found: ${PYTHON_VERSION}"
    exit 1
fi

log_success "Python ${PYTHON_VERSION} found"

# Check pip
if ! ${PYTHON_CMD} -m pip --version &> /dev/null; then
    log_error "pip is not installed. Please install pip first."
    exit 1
fi

# Check Azure CLI
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed. Please install it first:"
    log_info "  brew install azure-cli  (macOS)"
    log_info "  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash  (Linux)"
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Please run: az login"
    exit 1
fi

AZURE_ACCOUNT=$(az account show --query name -o tsv)
log_success "Logged in to Azure: ${AZURE_ACCOUNT}"

# Check ACR access
if ! az acr show --name "${ACR_NAME}" &> /dev/null; then
    log_error "Cannot access ACR: ${ACR_NAME}"
    log_info "Make sure you have access to this registry."
    exit 1
fi

log_success "All prerequisites are met (Python ${PYTHON_VERSION}, pip, Azure CLI, ACR access)"
echo ""

###############################################################################
# Step 2: Install test dependencies and run tests
###############################################################################
if [ "${SKIP_TESTS}" = "true" ]; then
    log_warning "Step 2: Skipping tests (--skip-tests flag set)"
else
    log_step "Step 2: Installing test dependencies and running tests..."
    
    # Install test dependencies
    log_info "Installing test dependencies..."
    ${PYTHON_CMD} -m pip install --quiet --upgrade pip
    ${PYTHON_CMD} -m pip install --quiet ".[test]" \
        || { log_error "Failed to install test dependencies"; exit 1; }
    
    log_success "Test dependencies installed"
    
    # Run tests
    log_info "Running pytest..."
    ${PYTHON_CMD} -m pytest test/ -v --tb=short \
        || { log_error "Tests failed! Fix the tests before deploying."; exit 1; }
    
    log_success "All tests passed"
fi

echo ""

###############################################################################
# Step 3: Build and Push Docker image using ACR Build Tasks
###############################################################################
log_step "Step 3: Building Docker image on Azure (ACR Build Tasks)..."

FULL_IMAGE_NAME="${ACR_LOGIN_SERVER}/${SERVICE_NAME}:${IMAGE_TAG}"

log_info "Building on Azure's amd64 infrastructure (avoids local emulation issues)"
log_info "This may take several minutes due to PaddleOCR model downloads..."
log_info "Target image: ${FULL_IMAGE_NAME}"
echo ""

az acr build \
    --registry "${ACR_NAME}" \
    --image "${SERVICE_NAME}:${IMAGE_TAG}" \
    --file "${DOCKERFILE_PATH}" \
    --platform linux/amd64 \
    . \
    || { log_error "ACR Build failed"; exit 1; }

log_success "Built and pushed: ${FULL_IMAGE_NAME}"
echo ""

###############################################################################
# Summary
###############################################################################
echo "======================================================================"
log_success "DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "======================================================================"
echo ""
echo "Deployed Image:"
echo "  - ${FULL_IMAGE_NAME} (Port ${SERVICE_PORT})"
echo ""
echo "Next Steps:"
echo "  1. Update Container App to use new image"
echo "  2. Verify Key Vault secrets are configured"
echo "  3. Check Container App logs after deployment"
echo ""
echo "Container App Update Command:"
echo "  az containerapp update --name <app-name> --resource-group <rg> \\"
echo "    --image ${FULL_IMAGE_NAME}"
echo ""
echo "Required Environment Variables (from Key Vault or direct):"
echo "  - STORAGE_PROVIDER=AZURE"
echo "  - SECRETS_PROVIDER=AZURE_KEYVAULT"
echo "  - KEYVAULT_URL=https://<vault>.vault.azure.net"
echo "  - KAFKA_PROVIDER=AZURE"
echo "  - KAFKA_TOPIC_IN=ocr.documents.to_process"
echo "  - KAFKA_TOPIC_OUT=ocr.documents.processed"
echo "  - KAFKA_GROUP_ID=ocr-consumer-group"
echo ""
echo "======================================================================"
