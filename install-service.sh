#!/bin/bash

# Script to install Telegram Post Evaluator Bot as a systemd service

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "🔧 Installing Telegram Post Evaluator Bot as systemd service"
echo "============================================================="
echo ""

# Get current directory and user
INSTALL_DIR=$(pwd)
CURRENT_USER=$(logname || echo $SUDO_USER)

echo "📁 Installation directory: $INSTALL_DIR"
echo "👤 Running as user: $CURRENT_USER"
echo ""

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/telegram-post-evaluator.service"

cat > $SERVICE_FILE << EOF
[Unit]
Description=Telegram Post Evaluator Bot
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/bot.log
StandardError=append:$INSTALL_DIR/bot.error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created: $SERVICE_FILE"

# Reload systemd
systemctl daemon-reload

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Available commands:"
echo "   sudo systemctl start telegram-post-evaluator    # Start bot"
echo "   sudo systemctl stop telegram-post-evaluator     # Stop bot"
echo "   sudo systemctl restart telegram-post-evaluator  # Restart bot"
echo "   sudo systemctl status telegram-post-evaluator   # Check status"
echo "   sudo systemctl enable telegram-post-evaluator   # Enable auto-start on boot"
echo ""
echo "📊 View logs:"
echo "   sudo journalctl -u telegram-post-evaluator -f   # Follow logs"
echo "   tail -f $INSTALL_DIR/bot.log                    # Application logs"
echo ""

read -p "Do you want to enable and start the service now? (y/n): " choice

if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    systemctl enable telegram-post-evaluator
    systemctl start telegram-post-evaluator
    echo ""
    echo "✅ Service enabled and started!"
    echo ""
    sleep 2
    systemctl status telegram-post-evaluator --no-pager
else
    echo ""
    echo "ℹ️  Service installed but not started"
    echo "   Run: sudo systemctl start telegram-post-evaluator"
fi
