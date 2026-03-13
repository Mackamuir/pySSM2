.PHONY: help install uninstall start stop restart status logs clean

# Detect current user and Wayland environment automatically
CURRENT_USER  := $(shell whoami)
CURRENT_UID   := $(shell id -u)
WAYLAND_SOCK  := $(shell ls /run/user/$(CURRENT_UID)/wayland-* 2>/dev/null | head -1)
WAYLAND_DISP  := $(if $(WAYLAND_SOCK),$(notdir $(WAYLAND_SOCK)),wayland-1)

# Default target
help:
	@echo "pySSM2 Logger - Makefile Commands"
	@echo "=================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install        - Install dependencies and deploy to /etc/pySSM2"
	@echo "  make uninstall      - Remove systemd service and /etc/pySSM2"
	@echo ""
	@echo "Service:"
	@echo "  make start          - Start the logger service"
	@echo "  make stop           - Stop the logger service"
	@echo "  make restart        - Restart the logger service"
	@echo "  make status         - Show service status"
	@echo "  make logs           - Tail service logs"

# Installation
install:
	@echo "Installing pySSM2..."
	@echo "  User:            $(CURRENT_USER) (uid=$(CURRENT_UID))"
	@echo "  Wayland display: $(WAYLAND_DISP)"
	@echo ""
	@echo "Updating package list..."
	sudo apt-get update
	@echo "Installing Python packages..."
	sudo apt-get install -y python3-serial python3-pygame
	@echo "Dependencies installed"
	@echo ""
	@echo "Deploying files to /etc/pySSM2..."
	sudo mkdir -p /etc/pySSM2/gui
	sudo mkdir -p /etc/pySSM2/assets/fonts
	sudo mkdir -p /var/log/subaru/python
	@echo "Copying source files..."
	sudo cp src/logger.py /etc/pySSM2/logger.py
	sudo cp src/PySSM2.py /etc/pySSM2/PySSM2.py
	sudo cp src/ecu_capabilities.py /etc/pySSM2/ecu_capabilities.py
	sudo cp config/config.py /etc/pySSM2/config.py
	sudo cp src/gui/__init__.py /etc/pySSM2/gui/__init__.py
	sudo cp src/gui/app.py /etc/pySSM2/gui/app.py
	sudo cp src/gui/dashboard.py /etc/pySSM2/gui/dashboard.py
	sudo cp src/gui/theme.py /etc/pySSM2/gui/theme.py
	sudo cp assets/fonts/DS-DIGII.TTF /etc/pySSM2/assets/fonts/DS-DIGII.TTF
	@if [ -f src/powerMonitor.py ]; then \
		sudo cp src/powerMonitor.py /etc/pySSM2/powerMonitor.py; \
	fi
	@echo "Setting permissions..."
	sudo chmod +x /etc/pySSM2/logger.py
	sudo chown -R $(CURRENT_USER):$(CURRENT_USER) /etc/pySSM2
	sudo chmod 755 /var/log/subaru
	@echo "Generating and installing systemd service..."
	sed \
		-e 's/__USER__/$(CURRENT_USER)/g' \
		-e 's/__UID__/$(CURRENT_UID)/g' \
		-e 's/__WAYLAND_DISPLAY__/$(WAYLAND_DISP)/g' \
		systemd/subaruLogger.service > /tmp/subaruLogger.service
	sudo cp /tmp/subaruLogger.service /etc/systemd/system/subaruLogger.service
	rm /tmp/subaruLogger.service
	sudo systemctl daemon-reload
	@echo ""
	@echo "Install complete!"
	@echo "  User:            $(CURRENT_USER)"
	@echo "  XDG_RUNTIME_DIR: /run/user/$(CURRENT_UID)"
	@echo "  WAYLAND_DISPLAY: $(WAYLAND_DISP)"
	@echo ""
	@echo "Start with: make start"

uninstall:
	@echo "Uninstalling pySSM2..."
	-sudo systemctl stop subaruLogger.service
	-sudo systemctl stop subaruPower.service
	-sudo systemctl disable subaruLogger.service
	-sudo systemctl disable subaruPower.service
	sudo rm -f /etc/systemd/system/subaruLogger.service
	sudo rm -f /etc/systemd/system/subaruPower.service
	sudo systemctl daemon-reload
	sudo rm -rf /etc/pySSM2
	@echo "Uninstall done"
	@echo ""
	@echo "Note: Log files in /var/log/subaru/ were preserved"
	@echo "To remove logs: sudo rm -rf /var/log/subaru/"

start:
	sudo systemctl start subaruLogger.service

stop:
	sudo systemctl stop subaruLogger.service

restart:
	sudo systemctl restart subaruLogger.service

status:
	systemctl status subaruLogger.service

logs:
	journalctl -u subaruLogger.service -f
