.PHONY: help install install-pip check-deps deploy uninstall start stop restart status logs clean test validate dev

# Default target
help:
	@echo "pySSM2 Logger - Makefile Commands"
	@echo "=================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install        - Install dependencies via apt (recommended)"
	@echo "  make uninstall      - Remove systemd service and /etc/pySSM2"

# Installation
install:
	@echo "Installing Python dependencies via apt..."
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "ERROR: Must run as root. Use: sudo make install"; \
		exit 1; \
	fi
	@echo "Updating package list..."
	apt-get update
	@echo "Installing Python packages..."
	apt-get install -y python3-serial python3-aiohttp python3-websockets
	@echo "Dependencies installed"
	@echo "Installing required files to /etc/pySSM2..."
	@echo "Creating directories..."
	mkdir -p /etc/pySSM2
	mkdir -p /var/log/subaru
	mkdir -p /var/log/subaru/python
	@echo "Copying files..."
	cp src/logger.py /etc/pySSM2/logger.py
	cp src/PySSM2.py /etc/pySSM2/PySSM2.py
	cp config/config.py /etc/pySSM2/config.py
	cp src/ecu_capabilities.py /etc/pySSM2/ecu_capabilities.py
	cp -r static /etc/pySSM2/
	@echo "Setting permissions..."
	chmod +x /etc/pySSM2/logger.py
	chmod +x /etc/pySSM2/PySSM2.py
	chmod +x /etc/pySSM2/config.py
	chmod +x /etc/pySSM2/ecu_capabilities.py

	chown -R root:root /etc/pySSM2
	chmod 755 /var/log/subaru
	@echo "Installing systemd service..."
	cp systemd/subaruLogger.service /etc/systemd/system/
	@if [ -f src/powerMonitor.py ]; then \
		cp src/powerMonitor.py /etc/pySSM2/powerMonitor.py; \
		chmod +x /etc/pySSM2/powerMonitor.py; \
		cp systemd/subaruPower.service /etc/systemd/system/; \
	fi
	systemctl daemon-reload
	@echo "Install done"

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
