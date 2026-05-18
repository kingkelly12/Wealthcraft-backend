#!/bin/bash

# 🚀 Adulting Backend - Cloud Run Quick Deploy Script
# Usage: ./deploy.sh [build|test|push|deploy|all]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID}"
IMAGE_NAME="Adulting-backend"
REGION="europe-west2"
REGISTRY="gcr.io"

# Function to print colored output
print_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if GCP_PROJECT_ID is set
check_project_id() {
    if [ -z "$PROJECT_ID" ]; then
        print_error "GCP_PROJECT_ID environment variable not set"
        echo "Set it with: export GCP_PROJECT_ID=your-project-id"
        exit 1
    fi
    print_success "Using GCP Project: $PROJECT_ID"
}

# Build Docker image locally
build() {
    print_step "Building Docker image: $IMAGE_NAME:latest"
    docker build -t $IMAGE_NAME:latest .
    print_success "Docker image built successfully"
}

# Test image locally
test() {
    print_step "Testing Docker image locally..."
    
    if [ ! -f ".env" ]; then
        print_warning "No .env file found. Creating template..."
        cat > .env.example << 'EOF'
FLASK_CONFIG=production
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret
GOOGLE_WEB_CLIENT_ID=your_google_client_id
QWEN_API_KEY=your_qwen_key
SECRET_KEY=your_secret_key
DATABASE_URL=your_postgres_url
EOF
        print_warning "Created .env.example - Copy and update with your values"
        exit 1
    fi
    
    print_step "Starting container on port 8080..."
    docker run -d \
        -p 8080:8080 \
        --env-file .env \
        --name $IMAGE_NAME-test \
        $IMAGE_NAME:latest
    
    # Wait for container to start
    sleep 3
    
    print_step "Testing health endpoint..."
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        print_success "Health check passed!"
        curl -s http://localhost:8080/health | jq .
    else
        print_error "Health check failed!"
        docker logs $IMAGE_NAME-test
        docker stop $IMAGE_NAME-test
        docker rm $IMAGE_NAME-test
        exit 1
    fi
    
    docker stop $IMAGE_NAME-test
    docker rm $IMAGE_NAME-test
    print_success "Local test passed!"
}

# Push image to GCR
push() {
    check_project_id
    
    print_step "Tagging image for Google Container Registry..."
    docker tag $IMAGE_NAME:latest $REGISTRY/$PROJECT_ID/$IMAGE_NAME:latest
    
    print_step "Pushing to GCR..."
    docker push $REGISTRY/$PROJECT_ID/$IMAGE_NAME:latest
    
    print_success "Image pushed to: $REGISTRY/$PROJECT_ID/$IMAGE_NAME:latest"
}

# Deploy to Cloud Run
deploy() {
    check_project_id
    
    print_step "Deploying to Cloud Run..."
    
    gcloud run deploy $IMAGE_NAME \
        --image $REGISTRY/$PROJECT_ID/$IMAGE_NAME:latest \
        --platform managed \
        --region $REGION \
        --memory 1Gi \
        --cpu 1 \
        --timeout 300 \
        --allow-unauthenticated \
        --set-env-vars "FLASK_CONFIG=production" \
        --max-instances 5

    
    print_success "Deployment complete!"
    
    print_step "Getting service URL..."
    SERVICE_URL=$(gcloud run services describe $IMAGE_NAME --region $REGION --format='value(status.url)')
    print_success "Your API is live at: $SERVICE_URL"
    print_success "Health check: curl $SERVICE_URL/health"
}

# Show logs
logs() {
    check_project_id
    print_step "Showing Cloud Run logs..."
    gcloud run logs read $IMAGE_NAME --limit 50 --region $REGION --follow
}

# Main script logic
case "${1:-all}" in
    build)
        build
        ;;
    test)
        test
        ;;
    push)
        build
        push
        ;;
    deploy)
        check_project_id
        deploy
        ;;
    logs)
        logs
        ;;
    all)
        build
        test
        push
        deploy
        ;;
    *)
        echo "Usage: $0 {build|test|push|deploy|logs|all}"
        echo ""
        echo "Commands:"
        echo "  build   - Build Docker image locally"
        echo "  test    - Test Docker image locally (requires .env)"
        echo "  push    - Build and push to Google Container Registry"
        echo "  deploy  - Deploy to Cloud Run"
        echo "  logs    - View Cloud Run logs"
        echo "  all     - Run all steps (build → test → push → deploy)"
        exit 1
        ;;
esac
