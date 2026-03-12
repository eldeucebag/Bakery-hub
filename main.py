#!/usr/bin/env python3
"""
Reticulum Flet App - Community Hub Browser
Connects to the community hub via RNS and displays micron pages.
Targets: Linux and Android
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path

import flet as ft

# Setup logging to file and console
# Use writable locations for Android compatibility
if sys.platform == "android":
    # On Android, use the app's internal files directory
    LOG_DIR = Path("/sdcard/Android/data") / "reticulum_hub_browser" / "logs"
elif sys.platform == "darwin":
    LOG_DIR = Path.home() / "Library" / "Logs" / "reticulum_hub_browser"
else:
    # Linux/other
    LOG_DIR = Path.home() / ".reticulum_hub_browser" / "logs"

try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / "app.log"
except PermissionError as e:
    # Fallback to temp directory if permission denied
    import tempfile
    LOG_DIR = Path(tempfile.gettempdir()) / "reticulum_hub_browser"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HubBrowser")

logger.info("=" * 60)
logger.info("App starting...")
logger.info(f"Log file: {LOG_FILE}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Platform: {sys.platform}")

# Community Hub identity hash (Yggdrasil address)
HUB_IDENTITY_HASH = "56c4f7b24c4d6e0380871c06533352666da9312d7bc9fa3b0bfeaeb4a49465e1"
# RNS Destination Hash for the hub's page service
HUB_DESTINATION_HASH = "f97f412b9ef6d1c2330ca5ee28ee9e31"
# App naming for the destination
APP_NAME = "nomadnet"
APP_INSTANCE = "page"


class ReticulumApp:
    """Main Flet application class"""

    def __init__(self, page: ft.Page):
        logger.info("ReticulumApp.__init__ starting")
        self.page = page
        self.rns = None
        self.destination = None
        self.link = None
        self.connected = False
        self.current_page_content = None
        self.page_title = "Community Hub"

        # UI components
        self.status_text = None
        self.connect_btn = None
        self.refresh_btn = None
        self.content_display = None

        logger.info("ReticulumApp.__init__ complete")

    def get_ui(self):
        """Get the main UI column"""
        logger.info("Building UI...")

        # Status bar
        self.status_text = ft.Text(
            "Ready - tap Connect to start",
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE,
        )

        self.status_bar = ft.Container(
            content=self.status_text,
            padding=10,
            bgcolor=ft.Colors.SURFACE_VARIANT,
            border_radius=5,
        )

        # Connection info
        conn_info = ft.Text(
            f"Hub: {HUB_IDENTITY_HASH[:32]}...",
            size=11,
            color=ft.Colors.GREY_700,
        )

        # Page title
        self.title_text = ft.Text(
            self.page_title,
            size=18,
            weight=ft.FontWeight.BOLD,
        )

        # Content display area
        self.content_display = ft.Container(
            content=ft.Text(
                "Tap Connect to load the hub page...",
                size=14,
                color=ft.Colors.GREY_600,
            ),
            padding=15,
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
        )

        # Buttons row
        self.refresh_btn = ft.ElevatedButton(
            "Refresh",
            icon=ft.icons.REFRESH,
            on_click=self.refresh_page,
            disabled=True,
        )

        self.connect_btn = ft.ElevatedButton(
            "Connect",
            icon=ft.icons.WIFI,
            on_click=self.toggle_connection,
        )

        button_row = ft.Row(
            controls=[self.refresh_btn, self.connect_btn],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        # Main layout
        ui = ft.Column(
            controls=[
                self.status_bar,
                conn_info,
                ft.Divider(height=10),
                self.title_text,
                ft.Divider(height=5),
                ft.Container(
                    content=self.content_display,
                    expand=True,
                ),
                button_row,
            ],
            expand=True,
            spacing=10,
        )

        logger.info("UI built successfully")
        return ui

    def update_status(self, status, color=ft.Colors.BLUE):
        """Update the status text"""
        logger.debug(f"Updating status: {status} (color: {color})")
        if self.status_text:
            self.status_text.value = status
            self.status_text.color = color
            try:
                self.status_bar.update()
            except Exception as e:
                logger.error(f"Error updating status bar: {e}")

    def toggle_connection(self, e):
        """Toggle connection to hub"""
        logger.info(f"Toggle connection, currently connected: {self.connected}")
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """Connect to the community hub"""
        logger.info("Connect() called")
        try:
            self.update_status("Initializing Reticulum...", ft.Colors.BLUE)
            self.page.update()
            logger.info("Page updated after status change")

            # Initialize RNS
            logger.info("Importing RNS module...")
            import RNS
            logger.info("RNS module imported successfully")

            logger.info("Initializing RNS.Reticulum()...")
            self.rns = RNS.Reticulum()
            logger.info("RNS initialized successfully")

            self.update_status("Reticulum initialized", ft.Colors.GREEN)
            self.page.update()

            # Create an identity for this client
            logger.info("Creating RNS Identity...")
            self.client_identity = RNS.Identity()
            logger.info("Identity created")

            # Check if we have a path to the destination
            self.update_status("Requesting path to hub...", ft.Colors.BLUE)
            self.page.update()

            destination_hash = bytes.fromhex(HUB_DESTINATION_HASH)
            logger.info(f"Destination hash: {destination_hash.hex()}")

            if not RNS.Transport.has_path(destination_hash):
                logger.info("Path not found, requesting path...")
                RNS.Transport.request_path(destination_hash)

                # Wait for path with timeout
                timeout = 30  # seconds
                start_time = time.time()
                while not RNS.Transport.has_path(destination_hash):
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Path request timed out after {timeout} seconds")
                    time.sleep(0.5)
                    self.page.update()

                logger.info("Path received")
            else:
                logger.info("Path already known")

            self.update_status("Path received, recalling identity...", ft.Colors.GREEN)
            self.page.update()

            # Recall the hub identity
            logger.info("Recalling hub identity...")
            hub_identity = RNS.Identity.recall(destination_hash)

            if hub_identity is None:
                logger.error("Could not recall hub identity")
                raise ValueError("Could not recall hub identity")

            logger.info("Hub identity recalled successfully")

            # Create destination for the hub's page service
            logger.info(f"Creating Destination with app name: {APP_NAME}, instance: {APP_INSTANCE}")
            self.destination = RNS.Destination(
                hub_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                APP_NAME,
                APP_INSTANCE
            )
            logger.info("Destination created")

            self.update_status("Creating link to hub...", ft.Colors.BLUE)
            self.page.update()

            # Create link to the hub
            logger.info("Creating RNS Link...")
            self.link = RNS.Link(self.destination)
            self.link.set_link_established_callback(self.link_established)
            self.link.set_link_closed_callback(self.link_closed)
            logger.info("Link created, waiting for establishment...")

            # Wait for link establishment with timeout
            timeout = 30
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
                self.page.update()

            if not self.connected:
                logger.error("Link establishment timed out")
                raise TimeoutError("Link establishment timed out")

            logger.info("Connect() completed successfully")

        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.update_status(error_msg, ft.Colors.RED)
            self.connected = False
            self.page.update()

    def link_established(self, link):
        """Callback when link is established"""
        logger.info("link_established() callback called")
        try:
            self.connected = True

            self.update_status("Connected to hub!", ft.Colors.GREEN)
            self.page.update()

            if self.connect_btn:
                self.connect_btn.text = "Disconnect"
                self.connect_btn.icon = ft.icons.WIFI_OFF
                self.connect_btn.bgcolor = ft.Colors.RED_200
                self.connect_btn.update()

            if self.refresh_btn:
                self.refresh_btn.disabled = False
                self.refresh_btn.update()

            # Load the index page
            logger.info("Loading index page...")
            self.load_page("/page/index.mu")

        except Exception as e:
            error_msg = f"Link error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.update_status(error_msg, ft.Colors.RED)
            self.page.update()

    def link_closed(self, link):
        """Callback when link is closed"""
        logger.info("link_closed() callback called")
        self.connected = False
        self.link = None

        if self.connect_btn:
            self.connect_btn.text = "Connect"
            self.connect_btn.icon = ft.icons.WIFI
            self.connect_btn.bgcolor = None
            self.connect_btn.update()

        if self.refresh_btn:
            self.refresh_btn.disabled = True
            self.refresh_btn.update()

        self.update_status("Disconnected", ft.Colors.ORANGE)
        self.page.update()

    def disconnect(self):
        """Disconnect from the hub"""
        logger.info("Disconnect() called")
        try:
            if self.link:
                logger.info("Tearing down link...")
                self.link.teardown()

            self.connected = False
            self.link = None

            if self.connect_btn:
                self.connect_btn.text = "Connect"
                self.connect_btn.icon = ft.icons.WIFI
                self.connect_btn.bgcolor = None
                self.connect_btn.update()

            if self.refresh_btn:
                self.refresh_btn.disabled = True
                self.refresh_btn.update()

            self.update_status("Disconnected", ft.Colors.ORANGE)
            self.page.update()

        except Exception as e:
            error_msg = f"Disconnect error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.update_status(error_msg, ft.Colors.RED)

    def load_page(self, path):
        """Request and load a micron page from the hub"""
        logger.info(f"load_page() called with path: {path}")
        try:
            if not self.link or not self.connected:
                logger.warning("Not connected to hub")
                self.update_status("Not connected to hub", ft.Colors.RED)
                return

            self.update_status(f"Loading {path}...", ft.Colors.BLUE)
            self.page.update()

            # Make a request for the page content
            logger.info(f"Making request for: {path}")
            self.link.request(
                path,
                data=None,
                response_callback=self.page_response,
                failed_callback=self.page_request_failed
            )

        except Exception as e:
            error_msg = f"Page load error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.update_status(error_msg, ft.Colors.RED)
            self.page.update()

    def page_response(self, request_receipt):
        """Handle page response from hub"""
        logger.info("page_response() callback called")
        try:
            request_id = request_receipt.request_id
            response = request_receipt.response
            logger.info(f"Got response, request_id: {request_id.hex()[:16]}...")

            if response:
                # Decode the response
                try:
                    page_content = response.decode('utf-8')
                    logger.info(f"Response decoded, length: {len(page_content)} chars")
                except Exception as decode_error:
                    logger.warning(f"UTF-8 decode failed: {decode_error}")
                    page_content = response.hex()

                self.current_page_content = page_content

                # Update UI on main thread
                logger.info("Scheduling display_page_content...")
                self.page.run_task(self.display_page_content, page_content)

                self.update_status("Page loaded successfully", ft.Colors.GREEN)
            else:
                logger.warning("Empty response from hub")
                self.update_status("Empty response from hub", ft.Colors.ORANGE)

        except Exception as e:
            error_msg = f"Response error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.update_status(error_msg, ft.Colors.RED)
            self.page.update()

    def page_request_failed(self, request_receipt):
        """Handle failed page request"""
        request_id = request_receipt.request_id
        error_msg = f"Page request failed: {request_id.hex()[:16]}..."
        logger.error(error_msg)
        self.update_status(error_msg, ft.Colors.RED)
        self.page.update()

    def display_page_content(self, content):
        """Display the page content in the UI"""
        logger.info(f"display_page_content() called, content length: {len(content)}")
        if self.content_display:
            # Simple micron markup rendering
            rendered = self.render_micron(content)
            logger.info(f"Rendered content length: {len(rendered)}")

            self.content_display.content = ft.Text(
                rendered,
                size=14,
                selectable=True,
            )
            self.content_display.update()
            logger.info("Content displayed successfully")

    def render_micron(self, content):
        """Simple micron markup renderer"""
        lines = content.split('\n')
        rendered_lines = []

        for line in lines:
            # Handle headings
            if line.startswith('# '):
                rendered_lines.append(f"══ {line[2:]} ══")
            elif line.startswith('## '):
                rendered_lines.append(f"─ {line[3:]} ─")
            elif line.startswith('### '):
                rendered_lines.append(line[4:])
            # Handle links
            elif line.startswith('[') and '](' in line:
                # Simple link display
                import re
                link_match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', line)
                if link_match:
                    text, url = link_match.groups()
                    rendered_lines.append(f"→ {text} [{url}]")
                else:
                    rendered_lines.append(line)
            # Handle bullet points
            elif line.startswith('- '):
                rendered_lines.append(f"• {line[2:]}")
            # Handle code blocks (simple handling)
            elif line.startswith('    '):
                rendered_lines.append(f"  {line[4:]}")
            else:
                rendered_lines.append(line)

        return '\n'.join(rendered_lines)

    def refresh_page(self, e):
        """Refresh the current page"""
        logger.info("Refresh page requested")
        self.load_page("/page/index.mu")


def main(page: ft.Page):
    """Main Flet app entry point"""
    logger.info("main() called")
    try:
        page.title = "Community Hub Browser"
        page.padding = 15
        page.spacing = 15
        page.theme_mode = ft.ThemeMode.LIGHT
        page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        page.vertical_alignment = ft.MainAxisAlignment.START

        logger.info("Page configured")

        # Add a debug text to confirm UI is working
        debug_text = ft.Text("UI initialized - tap Connect", color=ft.Colors.GREEN)
        page.add(debug_text)
        logger.info("Debug text added")

        # Add the main app
        logger.info("Creating ReticulumApp...")
        app = ReticulumApp(page)
        logger.info("ReticulumApp created, getting UI...")

        ui = app.get_ui()
        logger.info("UI obtained, adding to page...")

        page.add(ui)
        logger.info("UI added to page successfully")

        # Force update
        page.update()
        logger.info("Page updated")

    except Exception as e:
        error_msg = f"Error initializing app: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        try:
            page.add(ft.Text(error_msg, color=ft.Colors.RED, weight=ft.FontWeight.BOLD))
            page.add(ft.Text(traceback.format_exc(), size=10, color=ft.Colors.RED))
            page.update()
        except Exception as fallback_error:
            logger.error(f"Fallback error display failed: {fallback_error}")


if __name__ == "__main__":
    logger.info("Starting ft.app()...")
    try:
        ft.app(target=main, view=ft.AppView.FLET_APP)
    except Exception as e:
        logger.critical(f"ft.app() failed: {e}")
        logger.critical(traceback.format_exc())
        raise
