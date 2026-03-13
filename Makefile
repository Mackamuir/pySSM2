.PHONY: help install uninstall start stop restart status logs clean

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
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "ERROR: Must run as root. Use: sudo make install"; \
		exit 1; \
	fi
	@echo "Updating package list..."
	apt-get update
	@echo "Installing Python packages..."
	apt-get install -y python3-serial python3-pygame
	@echo "Dependencies installed"
	@echo ""
	@echo "Deploying files to /etc/pySSM2..."
	@echo "Creating directories..."
	mkdir -p /etc/pySSM2
	mkdir -p /etc/pySSM2/gui
	mkdir -p /etc/pySSM2/assets/fonts
	mkdir -p /var/log/subaru
	mkdir -p /var/log/subaru/python
	@echo "Copying source files..."
	cp src/logger.py /etc/pySSM2/logger.py
	cp src/PySSM2.py /etc/pySSM2/PySSM2.py
	cp src/ecu_capabilities.py /etc/pySSM2/ecu_capabilities.py
	cp config/config.py /etc/pySSM2/config.py
	cp src/gui/__init__.py /etc/pySSM2/gui/__init__.py
	cp src/gui/app.py /etc/pySSM2/gui/app.py
	cp src/gui/dashboard.py /etc/pySSM2/gui/dashboard.py
	cp src/gui/theme.py /etc/pySSM2/gui/theme.py
	cp assets/fonts/DS-DIGII.TTF /etc/pySSM2/assets/fonts/DS-DIGII.TTF
	@if [ -f src/powerMonitor.py ]; then \
		cp src/powerMonitor.py /etc/pySSM2/powerMonitor.py; \
	fi
	@echo "Setting permissions..."
	chmod +x /etc/pySSM2/logger.py
	chown -R mack:mack /etc/pySSM2
	chmod 755 /var/log/subaru
	@echo "Installing systemd service..."
	cp systemd/subaruLogger.service /etc/systemd/system/
	systemctl daemon-reload
	@echo ""
	@echo "Install complete. Start with: sudo make start"

uninstall:
	@echo "Uninstalling pySSM2..."
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "ERROR: Must run as root. Use: sudo make uninstall"; \
		exit 1; \
	fi
	@echo "Stopping services..."
	-systemctl stop subaruLogger.service
	-systemctl stop subaruPower.service
	@echo "Disabling services..."
	-systemctl disable subaruLogger.service
	-systemctl disable subaruPower.service
	@echo "Removing systemd services..."
	rm -f /etc/systemd/system/subaruLogger.service
	rm -f /etc/systemd/system/subaruPower.service
	systemctl daemon-reload
	@echo "Removing files..."
	rm -rf /etc/pySSM2
	@echo "Uninstall done"
	@echo ""
	@echo "Note: Log files in /var/log/subaru/ were preserved"
	@echo "To remove logs: sudo rm -rf /var/log/subaru/"

start:
	systemctl start subaruLogger.service

stop:
	systemctl stop subaruLogger.service

restart:
	systemctl restart subaruLogger.service

status:
	systemctl status subaruLogger.service

logs:
	journalctl -u subaruLogger.service -f
