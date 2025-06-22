#!/bin/bash
# Crypto Trading Bot v2.0 - One-Click Installation Script
# This script handles the complete installation process

set -e  # Exit on any error

echo "🚀 Crypto Trading Bot v2.0 - One-Click Installation"
echo "=================================================="

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

# Check if running on supported OS
check_os() {
    print_status "Checking operating system..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_success "Linux detected"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_success "macOS detected"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        print_success "Windows detected"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python 3.8+
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        required_version="3.8"
        
        if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
            print_success "Python $python_version found (✓)"
        else
            print_error "Python 3.8+ required, found $python_version"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        print_success "pip found (✓)"
    else
        print_error "pip not found. Please install pip."
        exit 1
    fi
    
    # Check git (optional but recommended)
    if command -v git &> /dev/null; then
        print_success "git found (✓)"
    else
        print_warning "git not found (optional)"
    fi
    
    # Check curl
    if command -v curl &> /dev/null; then
        print_success "curl found (✓)"
    else
        print_warning "curl not found (optional)"
    fi
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    case $OS in
        linux)
            # Detect Linux distribution
            if command -v apt-get &> /dev/null; then
                print_status "Installing dependencies with apt-get..."
                sudo apt-get update
                sudo apt-get install -y python3-pip python3-venv curl wget
            elif command -v yum &> /dev/null; then
                print_status "Installing dependencies with yum..."
                sudo yum install -y python3-pip python3-venv curl wget
            elif command -v pacman &> /dev/null; then
                print_status "Installing dependencies with pacman..."
                sudo pacman -S --noconfirm python-pip python-virtualenv curl wget
            else
                print_warning "Unknown package manager. Please install python3-pip and python3-venv manually."
            fi
            ;;
        macos)
            if command -v brew &> /dev/null; then
                print_status "Installing dependencies with Homebrew..."
                brew install python3
            else
                print_warning "Homebrew not found. Please install manually or install Homebrew first."
            fi
            ;;
        windows)
            print_warning "Windows detected. Please ensure Python 3.8+ and pip are installed."
            ;;
    esac
    
    print_success "System dependencies installed"
}

# Create virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    print_success "Virtual environment setup complete"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found. Installing basic dependencies..."
        pip install flask flask-socketio requests numpy pandas python-dotenv
        print_success "Basic dependencies installed"
    fi
}

# Setup configuration
setup_config() {
    print_status "Setting up configuration..."
    
    # Run Python setup script
    if [ -f "setup.py" ]; then
        python3 setup.py
    else
        print_warning "setup.py not found. Creating basic configuration..."
        
        # Create basic .env.local if it doesn't exist
        if [ ! -f ".env.local" ]; then
            cat > .env.local << EOF
# Crypto Trading Bot v2.0 - Basic Configuration
ENVIRONMENT=production
DATABASE_URL=sqlite:///crypto_trading_bot.db
ARBITRAGE_THRESHOLD=1.5
WEB_HOST=0.0.0.0
WEB_PORT=5000
LOG_LEVEL=INFO
EOF
            print_success "Basic configuration created"
        fi
    fi
}

# Create startup scripts
create_scripts() {
    print_status "Creating startup scripts..."
    
    # Make existing scripts executable
    chmod +x start.sh 2>/dev/null || true
    chmod +x setup.py 2>/dev/null || true
    
    print_success "Scripts configured"
}

# Run health check
health_check() {
    print_status "Running health check..."
    
    # Test Python imports
    python3 -c "
import sys
try:
    import flask
    import requests
    print('✅ Core dependencies OK')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
"
    
    # Test configuration
    if [ -f ".env.local" ]; then
        print_success "Configuration file found"
    else
        print_warning "Configuration file not found"
    fi
    
    print_success "Health check passed"
}

# Show completion message
show_completion() {
    echo ""
    echo "🎉 Installation completed successfully!"
    echo "======================================"
    echo ""
    echo "📊 Quick Start:"
    echo "  ./start.sh                    # Start the trading bot"
    echo "  ./start.sh --with-monitor     # Start with 24/7 monitoring"
    echo ""
    echo "🌐 Web Dashboard:"
    echo "  http://localhost:5000"
    echo ""
    echo "📚 Documentation:"
    echo "  README.md                     # Getting started guide"
    echo "  docs/                         # Detailed documentation"
    echo ""
    echo "🔧 Configuration:"
    echo "  .env.local                    # Edit this file to customize settings"
    echo ""
    echo "Ready to start trading! 🚀"
}

# Main installation process
main() {
    echo "Starting installation process..."
    echo ""
    
    check_os
    check_requirements
    
    # Ask for confirmation
    echo ""
    read -p "Do you want to continue with the installation? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Installation cancelled"
        exit 0
    fi
    
    # Run installation steps
    install_system_deps
    setup_venv
    install_python_deps
    setup_config
    create_scripts
    health_check
    
    show_completion
}

# Handle errors
error_handler() {
    print_error "Installation failed at step: $1"
    echo "Please check the error messages above and try again."
    exit 1
}

# Set error trap
trap 'error_handler "Unknown step"' ERR

# Run main function
main "$@"