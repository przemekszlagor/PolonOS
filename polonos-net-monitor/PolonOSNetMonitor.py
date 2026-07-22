#!/usr/bin/env python3
import os
import sys

# Zapobieganie błędom renderingu WebKit2GTK pod Wayland (np. na kartach NVIDIA)
os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
os.environ["WEBKIT_DISABLE_DMABUF_RENDERER"] = "1"

import json
import time
import socket
import threading
import urllib.request
import io
import subprocess

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2, GLib, Gdk

class NetMonitor(threading.Thread):
    def __init__(self, update_callback):
        super().__init__()
        self.update_callback = update_callback
        self.daemon = True
        self.running = True
        self.active_iface = None
        self.last_rx = 0
        self.last_tx = 0
        self.last_time = time.time()
        
    def get_active_interface(self):
        try:
            with open("/proc/net/route", "r") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "00000000":
                        return parts[0]
        except Exception:
            pass
            
        try:
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()[2:]
            best_iface = None
            max_bytes = -1
            for line in lines:
                if ":" not in line:
                    continue
                iface, stats = line.split(":")
                iface = iface.strip()
                if iface == "lo" or iface.startswith("virbr") or iface.startswith("docker") or iface.startswith("veth"):
                    continue
                bytes_recv = int(stats.split()[0])
                if bytes_recv > max_bytes:
                    max_bytes = bytes_recv
                    best_iface = iface
            return best_iface
        except Exception:
            pass
        return None

    def read_iface_bytes(self, iface):
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    if iface + ":" in line:
                        parts = line.split(":")[1].split()
                        return int(parts[0]), int(parts[8]) # rx_bytes, tx_bytes
        except Exception:
            pass
        return 0, 0

    def get_wifi_details(self, iface):
        details = {"ssid": "", "signal": 0, "type": "ethernet"}
        if not iface:
            return details
            
        try:
            cmd = ["LC_ALL=C", "nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"]
            res = subprocess.check_output(" ".join(cmd), shell=True, text=True)
            for line in res.strip().split("\n"):
                parts = line.split(":")
                if len(parts) >= 4 and parts[0] == iface:
                    details["type"] = parts[1]
                    details["connection"] = parts[3]
                    
            if details["type"] == "wifi":
                wifi_cmd = ["LC_ALL=C", "nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL", "dev", "wifi"]
                wifi_res = subprocess.check_output(" ".join(wifi_cmd), shell=True, text=True)
                for line in wifi_res.strip().split("\n"):
                    if line.startswith("*"):
                        parts = line.split(":")
                        if len(parts) >= 3:
                            details["ssid"] = parts[1]
                            try:
                                details["signal"] = int(parts[2])
                            except ValueError:
                                details["signal"] = 0
        except Exception:
            pass
        return details

    def get_local_ip(self, iface):
        if not iface:
            return "-"
        try:
            cmd = f"ip -4 addr show {iface}"
            res = subprocess.check_output(cmd, shell=True, text=True)
            for line in res.split("\n"):
                if "inet " in line:
                    return line.split()[1].split("/")[0]
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("1.1.1.1", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            pass
        return "-"

    def run(self):
        while self.running:
            iface = self.get_active_interface()
            if iface != self.active_iface:
                self.active_iface = iface
                self.last_rx, self.last_tx = self.read_iface_bytes(iface) if iface else (0, 0)
                self.last_time = time.time()
                
            rx, tx = self.read_iface_bytes(iface) if iface else (0, 0)
            now = time.time()
            dt = now - self.last_time
            
            if dt > 0 and self.active_iface:
                down_speed = (rx - self.last_rx) / dt
                up_speed = (tx - self.last_tx) / dt
            else:
                down_speed = 0
                up_speed = 0
                
            self.last_rx = rx
            self.last_tx = tx
            self.last_time = now
            
            net_info = self.get_wifi_details(iface)
            local_ip = self.get_local_ip(iface)
            
            stats = {
                "interface": iface if iface else "Niezidentyfikowany",
                "connected": iface is not None,
                "down_speed": down_speed,
                "up_speed": up_speed,
                "total_rx": rx,
                "total_tx": tx,
                "wifi_ssid": net_info["ssid"],
                "wifi_signal": net_info["signal"],
                "connection_type": net_info["type"],
                "local_ip": local_ip
            }
            self.update_callback(stats)
            time.sleep(1.0)

class PolonOSNetMonitorApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="PolonOSNetMonitor")
        self.set_default_size(800, 560)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.set_title("PolonOSNetMonitor")
        hb.set_subtitle("Monitorowanie ruchu sieciowego w czasie rzeczywistym")
        
        context = hb.get_style_context()
        context.add_class("polonosnetmonitor-header")
        self.set_titlebar(hb)
        
        self.webview = WebKit2.WebView()
        settings = self.webview.get_settings()
        settings.set_allow_universal_access_from_file_urls(True)
        settings.set_allow_file_access_from_file_urls(True)
        settings.set_enable_developer_extras(True)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.webview)
        self.add(scrolled_window)
        
        content_manager = self.webview.get_user_content_manager()
        content_manager.register_script_message_handler("app")
        content_manager.connect("script-message-received::app", self.on_js_message)
        
        self.connect("destroy", self.on_destroy)
        
        self.monitor = NetMonitor(self.on_stats_updated)
        self.monitor.start()
        
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            
        self.ui_dir = os.path.join(script_dir, "ui")
        html_path = os.path.join(self.ui_dir, "index.html")
        
        if os.path.exists(html_path):
            self.webview.load_uri("file://" + os.path.abspath(html_path))
        else:
            fallback_html = "/usr/share/polonosnetmonitor/ui/index.html"
            if os.path.exists(fallback_html):
                self.webview.load_uri("file://" + fallback_html)
            else:
                print(f"Error: index.html not found!")
                
        self.was_connected = False
        self.trigger_ip_fetch()
        
    def send_to_js(self, event_type, data):
        GLib.idle_add(self._send_to_js, event_type, data)
        
    def _send_to_js(self, event_type, data):
        json_str = json.dumps({"type": event_type, "payload": data})
        escaped_json = json_str.replace("\\", "\\\\").replace("'", "\\'")
        js_code = f"window.dispatchEvent(new CustomEvent('polonosnetmonitor-event', {{ detail: '{escaped_json}' }}));"
        # evaluate_javascript zastępuje przestarzałe run_javascript
        self.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
    def on_stats_updated(self, stats):
        self.send_to_js("realtime-stats", stats)
        
        is_connected = stats["connected"]
        if is_connected and not self.was_connected:
            self.was_connected = True
            self.trigger_ip_fetch()
        elif not is_connected:
            self.was_connected = False

    def trigger_ip_fetch(self):
        threading.Thread(target=self._fetch_ip_details_thread, daemon=True).start()
        
    def _fetch_ip_details_thread(self):
        url = "https://speed.cloudflare.com/__down?bytes=0"
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=5) as response:
                headers = response.info()
                ip = headers.get("cf-meta-ip", "Niezidentyfikowany")
                city = headers.get("city", "N/A")
                country = headers.get("country", "PL")
                isp = headers.get("asn", "N/A")
                colo = headers.get("cf-meta-colo", "N/A")
                
                details = {
                    "ip": ip,
                    "city": city,
                    "country": country,
                    "isp": isp,
                    "colo": colo
                }
                self.send_to_js("ip-details", details)
        except Exception:
            self.send_to_js("ip-details", {
                "ip": "Brak internetu / Offline",
                "city": "-",
                "country": "-",
                "isp": "-",
                "colo": "-"
            })

    def on_js_message(self, user_content_manager, message):
        try:
            body = message.get_body()
            data = json.loads(body)
            action = data.get("action")
            
            if action == "get-ip-details":
                self.trigger_ip_fetch()
        except Exception as e:
            print("Error handling JS message:", e)

    def on_destroy(self, widget):
        self.monitor.running = False
        Gtk.main_quit()

if __name__ == "__main__":
    Gtk.init(None)
    app = PolonOSNetMonitorApp()
    app.show_all()
    Gtk.main()
