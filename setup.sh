#!/bin/bash

# Home Broker Simulator - Development Setup Script

echo "🏠 Setting up Home Broker Trading Simulator..."
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
print_status "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if Node.js is installed
print_status "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
else
    print_error "Node.js is required but not installed"
    exit 1
fi

# Check if npm is installed
print_status "Checking npm installation..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_success "npm $NPM_VERSION found"
else
    print_error "npm is required but not installed"
    exit 1
fi

# Setup backend
print_status "Setting up backend dependencies..."
cd backend

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in backend directory"
    exit 1
fi

# Install Python dependencies
print_status "Installing Python packages..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    print_success "Backend dependencies installed successfully"
else
    print_error "Failed to install backend dependencies"
    exit 1
fi

cd ..

# Setup frontend
print_status "Setting up frontend dependencies..."
cd frontend

if [ ! -f "package.json" ]; then
    print_error "package.json not found in frontend directory"
    exit 1
fi

# Install Node.js dependencies
print_status "Installing Node.js packages (this may take a while)..."
npm install

if [ $? -eq 0 ]; then
    print_success "Frontend dependencies installed successfully"
else
    print_error "Failed to install frontend dependencies"
    exit 1
fi

cd ..

# Create run scripts
print_status "Creating run scripts..."

# Backend run script
cat > run-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Home Broker Backend..."
cd backend
python3 main.py
EOF

# Frontend run script
cat > run-frontend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Home Broker Frontend..."
cd frontend
npm start
EOF

# Combined run script
cat > run-dev.sh << 'EOF'
#!/bin/bash
echo "🏠 Starting Home Broker Trading Simulator in Development Mode"
echo "============================================================"

# Function to cleanup background processes
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap Ctrl+C
trap cleanup INT

# Start backend in background
echo "🚀 Starting backend server..."
cd backend && python3 main.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "🚀 Starting frontend server..."
cd ../frontend && npm start &
FRONTEND_PID=$!

# Wait for both processes
wait
EOF

# Make scripts executable
chmod +x run-backend.sh
chmod +x run-frontend.sh
chmod +x run-dev.sh

print_success "Run scripts created successfully"

# Final setup completed
print_success "Setup completed successfully!"
echo ""
echo "🎉 Home Broker Trading Simulator is ready to run!"
echo ""
echo "Quick start options:"
echo "  • Full development: ./run-dev.sh"
echo "  • Backend only:     ./run-backend.sh"
echo "  • Frontend only:    ./run-frontend.sh"
echo ""
echo "Manual start:"
echo "  • Backend:  cd backend && python3 main.py"
echo "  • Frontend: cd frontend && npm start"
echo ""
echo "URLs:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend:  http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo ""
print_status "Happy Trading! 📈🚀"
