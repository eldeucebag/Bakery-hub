#!/usr/bin/env python3
"""
Reticulum Flet App - Community Hub Browser
Connects to the community hub via RNS and displays micron pages.
Targets: Linux and Android
"""

import time
import traceback
from datetime import datetime
import RNS
import flet as ft

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

    def get_ui(self):
        """Get the main UI column"""
        # Status bar
        self.status_text = ft.Text(
            "Initializing Reticulum...",
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
                "Connect to the hub to load the index page...",
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
        return ft.Column(
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

    def update_status(self, status, color=ft.Colors.BLUE):
        """Update the status text"""
        if self.status_text:
            self.status_text.value = status
            self.status_text.color = color
            self.status_bar.update()

    def toggle_connection(self, e):
        """Toggle connection to hub"""
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """Connect to the community hub"""
        try:
            self.update_status("Initializing Reticulum...", ft.Colors.BLUE)
            self.page.update()

            # Initialize RNS
            self.rns = RNS.Reticulum()

            self.update_status("Reticulum initialized", ft.Colors.GREEN)
            self.page.update()

            # Create an identity for this client
            self.client_identity = RNS.Identity()

            # Check if we have a path to the destination
            self.update_status("Requesting path to hub...", ft.Colors.BLUE)
            self.page.update()

            destination_hash = bytes.fromhex(HUB_DESTINATION_HASH)

            if not RNS.Transport.has_path(destination_hash):
                RNS.Transport.request_path(destination_hash)

                # Wait for path with timeout
                timeout = 30  # seconds
                start_time = time.time()
                while not RNS.Transport.has_path(destination_hash):
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Path request timed out after {timeout} seconds")
                    time.sleep(0.5)
                    self.page.update()

            self.update_status("Path received, recalling identity...", ft.Colors.GREEN)
            self.page.update()

            # Recall the hub identity
            hub_identity = RNS.Identity.recall(destination_hash)

            if hub_identity is None:
                raise ValueError("Could not recall hub identity")

            # Create destination for the hub's page service
            self.destination = RNS.Destination(
                hub_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                APP_NAME,
                APP_INSTANCE
            )

            self.update_status("Creating link to hub...", ft.Colors.BLUE)
            self.page.update()

            # Create link to the hub
            self.link = RNS.Link(self.destination)
            self.link.set_link_established_callback(self.link_established)
            self.link.set_link_closed_callback(self.link_closed)

            # Wait for link establishment with timeout
            timeout = 30
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
                self.page.update()

            if not self.connected:
                raise TimeoutError("Link establishment timed out")

        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            self.update_status(error_msg, ft.Colors.RED)
            self.connected = False
            self.page.update()

    def link_established(self, link):
        """Callback when link is established"""
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
            self.load_page("/page/index.mu")

        except Exception as e:
            error_msg = f"Link error: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            self.update_status(error_msg, ft.Colors.RED)
            self.page.update()

    def link_closed(self, link):
        """Callback when link is closed"""
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
        try:
            if self.link:
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
            self.update_status(f"Disconnect error: {str(e)}", ft.Colors.RED)

    def load_page(self, path):
        """Request and load a micron page from the hub"""
        try:
            if not self.link or not self.connected:
                self.update_status("Not connected to hub", ft.Colors.RED)
                return

            self.update_status(f"Loading {path}...", ft.Colors.BLUE)
            self.page.update()

            # Make a request for the page content
            self.link.request(
                path,
                data=None,
                response_callback=self.page_response,
                failed_callback=self.page_request_failed
            )

        except Exception as e:
            self.update_status(f"Page load error: {str(e)}", ft.Colors.RED)
            self.page.update()

    def page_response(self, request_receipt):
        """Handle page response from hub"""
        try:
            request_id = request_receipt.request_id
            response = request_receipt.response

            if response:
                # Decode the response
                try:
                    page_content = response.decode('utf-8')
                except:
                    page_content = response.hex()

                self.current_page_content = page_content
                
                # Update UI on main thread
                self.page.run_task(self.display_page_content, page_content)
                
                self.update_status("Page loaded successfully", ft.Colors.GREEN)
            else:
                self.update_status("Empty response from hub", ft.Colors.ORANGE)

        except Exception as e:
            self.update_status(f"Response error: {str(e)}", ft.Colors.RED)
            self.page.update()

    def page_request_failed(self, request_receipt):
        """Handle failed page request"""
        request_id = request_receipt.request_id
        self.update_status(f"Page request failed: {RNS.prettyhexrep(request_id)}", ft.Colors.RED)
        self.page.update()

    def display_page_content(self, content):
        """Display the page content in the UI"""
        if self.content_display:
            # Simple micron markup rendering
            rendered = self.render_micron(content)
            
            self.content_display.content = ft.Text(
                rendered,
                size=14,
                selectable=True,
            )
            self.content_display.update()

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
        if self.current_page_content:
            self.load_page("/page/index.mu")
        else:
            self.load_page("/page/index.mu")


def main(page: ft.Page):
    """Main Flet app entry point"""
    page.title = "Community Hub Browser"
    page.padding = 15
    page.spacing = 15
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # Add the main app
    try:
        app = ReticulumApp(page)
        page.add(app.get_ui())
    except Exception as e:
        print(f"Error initializing app: {e}")
        print(traceback.format_exc())
        page.add(ft.Text(f"Error: {e}", color=ft.Colors.RED))


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
