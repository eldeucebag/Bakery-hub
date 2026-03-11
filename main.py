#!/usr/bin/env python3
"""
Reticulum Flet App - Community Server Announce Viewer
Connects to a specific community server and displays received announces.
Targets: Linux and Android
"""

import RNS
import flet as ft

# Community server identity hash and port
COMMUNITY_SERVER_HASH = "99b91c274bd7c2b926426618a3c2dbbd480cae10eadf9d53aabb873d2bbbbb71"
COMMUNITY_SERVER_PORT = 4242


class AnnounceCard(ft.Card):
    """Card widget to display a single announce"""
    
    def __init__(self, announce_data, **kwargs):
        super().__init__(**kwargs)
        self.elevation = 2
        self.margin = 5
        
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Icon(ft.icons.RADIO, size=16, color=ft.colors.GREEN),
                        ft.Text(
                            f"Source: {announce_data['source']}",
                            weight=ft.FontWeight.BOLD,
                            size=14,
                        ),
                    ]),
                    ft.Divider(height=5),
                    ft.Text(
                        f"Data: {announce_data['data']}",
                        size=12,
                        selectable=True,
                    ),
                    ft.Text(
                        f"Time: {announce_data['time']}",
                        size=10,
                        color=ft.colors.GREY_600,
                        italic=True,
                    ),
                ],
                spacing=3,
            ),
            padding=10,
        )


class ReticulumApp(ft.UserControl):
    """Main Flet application control"""
    
    def __init__(self):
        super().__init__()
        self.rns = None
        self.destination = None
        self.announce_list = []
        self.connected = False
    
    def build(self):
        """Build the UI"""
        # Status bar
        self.status_text = ft.Text(
            "Initializing Reticulum...",
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE,
        )
        
        self.status_bar = ft.Container(
            content=self.status_text,
            padding=10,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=5,
        )
        
        # Connection info
        self.conn_info = ft.Text(
            f"Server: {COMMUNITY_SERVER_HASH[:32]}...:{COMMUNITY_SERVER_PORT}",
            size=11,
            color=ft.colors.GREY_700,
        )
        
        # Announces list
        self.announces_list = ft.ListView(
            spacing=5,
            expand=True,
            auto_scroll=True,
        )
        
        # Buttons row
        self.clear_btn = ft.ElevatedButton(
            "Clear",
            icon=ft.icons.DELETE_SWEEP,
            on_click=self.clear_announces,
        )
        
        self.connect_btn = ft.ElevatedButton(
            "Connect",
            icon=ft.icons.WIFI,
            on_click=self.toggle_connection,
        )
        
        button_row = ft.Row(
            controls=[self.clear_btn, self.connect_btn],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )
        
        # Main layout
        return ft.Column(
            controls=[
                self.status_bar,
                self.conn_info,
                ft.Divider(height=10),
                ft.Row([
                    ft.Icon(ft.icons.ANNOUNCEMENT, size=20),
                    ft.Text("Received Announces:", weight=ft.FontWeight.BOLD),
                ]),
                ft.Container(
                    content=self.announces_list,
                    expand=True,
                    border=ft.border.all(1, ft.colors.GREY_400),
                    border_radius=5,
                ),
                button_row,
            ],
            expand=True,
            spacing=10,
        )
    
    def update_status(self, status, color=ft.colors.BLUE):
        """Update the status text"""
        self.status_text.value = status
        self.status_text.color = color
        self.status_bar.update()
    
    def add_announce(self, announce_data):
        """Add a new announce to the list"""
        card = AnnounceCard(announce_data)
        self.announces_list.controls.append(card)
        self.announces_list.update()
    
    def clear_announces(self, e):
        """Clear all displayed announces"""
        self.announces_list.controls.clear()
        self.announce_list = []
        self.announces_list.update()
        self.update_status("Announces cleared", ft.colors.GREEN)
    
    def toggle_connection(self, e):
        """Toggle connection to server"""
        if self.connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """Connect to the community server"""
        try:
            self.update_status("Initializing Reticulum...", ft.colors.BLUE)
            
            # Initialize RNS
            self.rns = RNS.Reticulum()
            
            self.update_status("Reticulum initialized", ft.colors.GREEN)
            
            # Create a destination for receiving announces
            self.destination = RNS.Destination(
                self.rns,
                RNS.Destination.IN,
                RNS.Destination.SINGLE,
                "reticulum",
                "community",
                "viewer"
            )
            
            # Set announce handler
            self.destination.set_announce_handler(self.handle_announce)
            
            # Create a client for the community server
            self.client = RNS.Client(self.rns, "community_viewer")
            
            self.connected = True
            self.connect_btn.text = "Disconnect"
            self.connect_btn.icon = ft.icons.WIFI_OFF
            self.connect_btn.bgcolor = ft.colors.RED_200
            self.connect_btn.update()
            
            self.update_status(f"Connected to {COMMUNITY_SERVER_HASH[:16]}...", ft.colors.GREEN)
            
            # Request initial announces
            self.request_announces()
            
        except Exception as e:
            self.update_status(f"Connection error: {str(e)}", ft.colors.RED)
            self.connected = False
    
    def disconnect(self):
        """Disconnect from the server"""
        try:
            if self.rns:
                RNS.Reticulum.shutdown()
            
            self.connected = False
            self.connect_btn.text = "Connect"
            self.connect_btn.icon = ft.icons.WIFI
            self.connect_btn.bgcolor = None
            self.connect_btn.update()
            
            self.update_status("Disconnected", ft.colors.ORANGE)
            
        except Exception as e:
            self.update_status(f"Disconnect error: {str(e)}", ft.colors.RED)
    
    def handle_announce(self, path, data, request_id, requested_by, interface_id=None):
        """Handle received announces"""
        try:
            # Get source identity
            source = "Unknown"
            if path:
                source = path[:32] + "..."
            
            # Decode data if present
            data_str = ""
            if data:
                try:
                    data_str = data.decode('utf-8')
                except:
                    data_str = data.hex()[:64] + "..."
            
            announce_data = {
                'source': source,
                'data': data_str if data_str else "(no data)",
                'time': RNS.timestamp_to_date(RNS.now())
            }
            
            self.announce_list.append(announce_data)
            
            # Update UI on main thread
            self.page.run_task(lambda _: self.add_announce(announce_data))
            
        except Exception as e:
            print(f"Error handling announce: {e}")
    
    def request_announces(self):
        """Request announces from the server"""
        try:
            dest_hash = bytes.fromhex(COMMUNITY_SERVER_HASH)
            RNS.request_announce(dest_hash)
        except Exception as e:
            print(f"Error requesting announces: {e}")


def main(page: ft.Page):
    """Main Flet app entry point"""
    page.title = "Reticulum Community Viewer"
    page.padding = 15
    page.spacing = 15
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Set window size for desktop
    page.window_width = 800
    page.window_height = 600
    
    # Add the main control
    app = ReticulumApp()
    page.add(app)
    
    # Auto-connect on start
    page.run_task(lambda _: app.connect())


if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER)
