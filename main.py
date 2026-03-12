#!/usr/bin/env python3
"""
Reticulum Flet App - Community Hub Browser
Connects to the community hub via RNS and displays micron pages.
"""

import sys
import time
import traceback
from pathlib import Path

import flet as ft

# Simple logging to file
LOG_FILE = Path("/tmp/hub_browser.log")
try:
    with open(LOG_FILE, "w") as f:
        f.write(f"App starting, platform: {sys.platform}\n")
except:
    pass

def log(msg):
    """Simple logging function"""
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{msg}\n")
        print(msg)
    except:
        pass

log("=" * 50)
log(f"Platform: {sys.platform}")
log(f"Python: {sys.version}")

# Community Hub config
HUB_IDENTITY_HASH = "56c4f7b24c4d6e0380871c06533352666da9312d7bc9fa3b0bfeaeb4a49465e1"
HUB_DESTINATION_HASH = "f97f412b9ef6d1c2330ca5ee28ee9e31"
APP_NAME = "nomadnet"
APP_INSTANCE = "page"


class ReticulumApp:
    def __init__(self, page):
        log("ReticulumApp init")
        self.page = page
        self.rns = None
        self.link = None
        self.connected = False
        self.current_page_content = None
        
        self.status_text = None
        self.connect_btn = None
        self.refresh_btn = None
        self.content_display = None

    def get_ui(self):
        log("Building UI")
        
        self.status_text = ft.Text("Ready - tap Connect")
        self.status_bar = ft.Container(
            content=self.status_text,
            padding=10,
            bgcolor="#e0e0e0",
            border_radius=5,
        )

        conn_info = ft.Text(f"Hub: {HUB_IDENTITY_HASH[:32]}...", size=11)
        self.title_text = ft.Text("Community Hub", size=18, weight="bold")

        self.content_display = ft.Container(
            content=ft.Text("Tap Connect to load the hub page..."),
            padding=15,
            expand=True,
            border=ft.border.all(1, "#cccccc"),
            border_radius=5,
        )

        self.refresh_btn = ft.ElevatedButton("Refresh", on_click=self.refresh_page, disabled=True)
        self.connect_btn = ft.ElevatedButton("Connect", on_click=self.toggle_connection)

        return ft.Column(
            controls=[
                self.status_bar,
                conn_info,
                ft.Divider(height=10),
                self.title_text,
                ft.Divider(height=5),
                self.content_display,
                ft.Row(controls=[self.refresh_btn, self.connect_btn], alignment="spaceEvenly"),
            ],
            expand=True,
            spacing=10,
        )

    def update_status(self, status, color="blue"):
        if self.status_text:
            self.status_text.value = status
            self.status_text.color = color
            try:
                self.status_bar.update()
            except Exception as e:
                log(f"Error updating status: {e}")

    def toggle_connection(self, e):
        log(f"Toggle, connected={self.connected}")
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        log("Connect called")
        try:
            self.update_status("Initializing Reticulum...", "blue")
            self.page.update()

            import RNS
            log("RNS imported")
            self.rns = RNS.Reticulum()
            log("RNS initialized")

            self.update_status("Reticulum initialized", "green")
            self.page.update()

            self.client_identity = RNS.Identity()
            log("Identity created")

            self.update_status("Requesting path to hub...", "blue")
            self.page.update()

            dest_hash = bytes.fromhex(HUB_DESTINATION_HASH)
            
            if not RNS.Transport.has_path(dest_hash):
                log("Requesting path...")
                RNS.Transport.request_path(dest_hash)
                timeout = 30
                start = time.time()
                while not RNS.Transport.has_path(dest_hash):
                    if time.time() - start > timeout:
                        raise TimeoutError("Path request timed out")
                    time.sleep(0.5)
                    self.page.update()
                log("Path received")

            self.update_status("Recalling identity...", "green")
            self.page.update()

            hub_identity = RNS.Identity.recall(dest_hash)
            if not hub_identity:
                raise ValueError("Could not recall hub identity")
            log("Identity recalled")

            self.destination = RNS.Destination(
                hub_identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                APP_NAME,
                APP_INSTANCE
            )
            log("Destination created")

            self.update_status("Creating link...", "blue")
            self.page.update()

            self.link = RNS.Link(self.destination)
            self.link.set_link_established_callback(self.link_established)
            self.link.set_link_closed_callback(self.link_closed)
            log("Link created, waiting...")

            timeout = 30
            start = time.time()
            while not self.connected and time.time() - start < timeout:
                time.sleep(0.1)
                self.page.update()

            if not self.connected:
                raise TimeoutError("Link timed out")
            log("Connected!")

        except Exception as e:
            log(f"Connect error: {e}")
            log(traceback.format_exc())
            self.update_status(f"Error: {str(e)}", "red")
            self.connected = False
            self.page.update()

    def link_established(self, link):
        log("Link established callback")
        try:
            self.connected = True
            self.update_status("Connected!", "green")
            self.page.update()

            if self.connect_btn:
                self.connect_btn.text = "Disconnect"
                self.connect_btn.update()

            if self.refresh_btn:
                self.refresh_btn.disabled = False
                self.refresh_btn.update()

            self.load_page("/page/index.mu")
        except Exception as e:
            log(f"Link established error: {e}")
            log(traceback.format_exc())

    def link_closed(self, link):
        log("Link closed callback")
        self.connected = False
        self.link = None
        if self.connect_btn:
            self.connect_btn.text = "Connect"
            self.connect_btn.update()
        if self.refresh_btn:
            self.refresh_btn.disabled = True
            self.refresh_btn.update()
        self.update_status("Disconnected", "orange")
        self.page.update()

    def disconnect(self):
        log("Disconnect called")
        try:
            if self.link:
                self.link.teardown()
            self.connected = False
            self.link = None
            if self.connect_btn:
                self.connect_btn.text = "Connect"
                self.connect_btn.update()
            if self.refresh_btn:
                self.refresh_btn.disabled = True
                self.refresh_btn.update()
            self.update_status("Disconnected", "orange")
            self.page.update()
        except Exception as e:
            log(f"Disconnect error: {e}")

    def load_page(self, path):
        log(f"Loading page: {path}")
        try:
            if not self.link or not self.connected:
                self.update_status("Not connected", "red")
                return

            self.update_status(f"Loading {path}...", "blue")
            self.page.update()

            self.link.request(
                path,
                data=None,
                response_callback=self.page_response,
                failed_callback=self.page_request_failed
            )
        except Exception as e:
            log(f"Load page error: {e}")
            self.update_status(f"Error: {str(e)}", "red")
            self.page.update()

    def page_response(self, request_receipt):
        log("Page response callback")
        try:
            response = request_receipt.response
            if response:
                try:
                    content = response.decode('utf-8')
                except:
                    content = response.hex()
                self.current_page_content = content
                self.page.run_task(self.display_content, content)
                self.update_status("Page loaded", "green")
            else:
                self.update_status("Empty response", "orange")
        except Exception as e:
            log(f"Page response error: {e}")
            self.update_status(f"Error: {str(e)}", "red")

    def page_request_failed(self, request_receipt):
        log("Page request failed")
        self.update_status("Request failed", "red")

    def display_content(self, content):
        log(f"Displaying content, len={len(content)}")
        rendered = self.render_micron(content)
        self.content_display.content = ft.Text(rendered, size=14, selectable=True)
        self.content_display.update()
        log("Content displayed")

    def render_micron(self, content):
        lines = content.split('\n')
        out = []
        for line in lines:
            if line.startswith('# '):
                out.append(f"== {line[2:]} ==")
            elif line.startswith('## '):
                out.append(f"- {line[3:]} -")
            elif line.startswith('- '):
                out.append(f"* {line[2:]}")
            else:
                out.append(line)
        return '\n'.join(out)

    def refresh_page(self, e):
        log("Refresh")
        self.load_page("/page/index.mu")


def main(page: ft.Page):
    log("main() called")
    try:
        page.title = "Hub Browser"
        page.padding = 15
        page.spacing = 15
        page.theme_mode = ft.ThemeMode.LIGHT
        page.horizontal_alignment = "center"
        page.vertical_alignment = "start"
        log("Page configured")

        debug = ft.Text("UI loaded - tap Connect", color="green")
        page.add(debug)
        log("Debug text added")

        app = ReticulumApp(page)
        log("App created")
        page.add(app.get_ui())
        log("UI added")
        page.update()
        log("Page updated")

    except Exception as e:
        log(f"Main error: {e}")
        log(traceback.format_exc())
        try:
            page.add(ft.Text(f"Error: {e}", color="red"))
            page.update()
        except:
            pass


if __name__ == "__main__":
    log("Starting ft.app")
    ft.app(target=main)
