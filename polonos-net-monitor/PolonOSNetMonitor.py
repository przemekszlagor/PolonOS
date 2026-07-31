#!/usr/bin/env python3
# PolonOS NetMonitor v1.1 - Aplikacja do monitorowania łącz sieciowych w PolonOS
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
import urllib.parse
import ssl
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
        # 1. Spróbuj wykryć połączony interfejs przez nmcli (NetworkManager)
        try:
            cmd = ["LC_ALL=C", "nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device"]
            res = subprocess.check_output(" ".join(cmd), shell=True, text=True, stderr=subprocess.DEVNULL)
            
            connected_ethernet = None
            connected_wifi = None
            connected_other = None
            
            for line in res.strip().split("\n"):
                parts = line.split(":")
                if len(parts) >= 3:
                    dev, dev_type, state = parts[0], parts[1], parts[2]
                    if state == "connected":
                        if dev_type == "ethernet":
                            connected_ethernet = dev
                        elif dev_type == "wifi":
                            connected_wifi = dev
                        elif dev_type not in ["loopback", "bridge"]:
                            connected_other = dev
                            
            if connected_ethernet:
                return connected_ethernet
            if connected_wifi:
                return connected_wifi
            if connected_other:
                return connected_other
        except Exception:
            pass

        # 2. Fallback do odczytu trasy domyślnej
        try:
            with open("/proc/net/route", "r") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "00000000":
                        return parts[0]
        except Exception:
            pass
            
        # 3. Drugi fallback: interfejs z największym ruchem
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
        super().__init__(title="PolonOS NetMonitor")
        self.set_default_size(800, 560)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Ustawienie ikony okna aplikacji
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.realpath(__file__))
        ui_dir = os.path.join(script_dir, "ui")
        icon_path = os.path.join(ui_dir, "icon.png")
        if not os.path.exists(icon_path):
            icon_path = "/usr/share/polonosnetmonitor/ui/icon.png"
            
        if os.path.exists(icon_path):
            try:
                self.set_icon_from_file(icon_path)
            except Exception as e:
                print("Error setting window icon:", e)
        
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.set_title("PolonOS NetMonitor")
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
        
        self.content_manager = self.webview.get_user_content_manager()
        self.content_manager.register_script_message_handler("app")
        self.content_manager.connect("script-message-received", self.on_js_message)
        self.webview.connect("notify::title", self.on_title_changed)
        
        self.connect("destroy", self.on_destroy)
        
        self.was_connected = False
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
                
        self.trigger_ip_fetch()
        
    def send_to_js(self, event_type, data):
        GLib.idle_add(self._send_to_js, event_type, data)
        
    def _send_to_js(self, event_type, data):
        import base64
        json_str = json.dumps({"type": event_type, "payload": data})
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        js_code = f"window.dispatchEvent(new CustomEvent('polonosnetmonitor-event', {{ detail: atob('{b64_str}') }}));"
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
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=context, timeout=5) as response:
                headers = response.info()
                ip = headers.get("cf-meta-ip", "Niezidentyfikowany")
                city = headers.get("city", "N/A")
                city = urllib.parse.unquote(city)
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
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_to_js("ip-details", {
                "ip": "Brak internetu / Offline",
                "city": "-",
                "country": "-",
                "isp": "-",
                "colo": "-"
            })

    def _run_speedtest_thread(self):
        def update_cb(status, speed, progress):
            self.send_to_js("speedtest-update", {
                "status": status,
                "speed": speed,
                "progress": progress
            })

        # 1. Download test
        update_cb("downloading", 0.0, 5)
        down_speed = self.run_download_test(update_cb)
        
        # 2. Upload test
        update_cb("uploading", 0.0, 55)
        up_speed = self.run_upload_test(update_cb)
        
        # 3. Complete
        update_cb("complete", {"download": down_speed, "upload": up_speed}, 100)

    def run_download_test(self, update_cb):
        url = "https://speed.cloudflare.com/__down?bytes=10000000"  # 10MB (Cloudflare maximum parameter limit)
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        try:
            context = ssl._create_unverified_context()
            start_time = time.time()
            total_bytes = 0
            # We run for max 4 seconds
            with urllib.request.urlopen(req, context=context, timeout=5) as response:
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    elapsed = time.time() - start_time
                    if elapsed > 4.0:
                        break
                    speed_mbps = (total_bytes * 8) / (elapsed * 1000000)
                    progress = min(50, int((elapsed / 4.0) * 50))
                    update_cb("downloading", speed_mbps, progress)
            elapsed = time.time() - start_time
            if elapsed > 0:
                return (total_bytes * 8) / (elapsed * 1000000)
            return 0.0
        except Exception as e:
            print("Download speedtest failed:", e)
            return 0.0

    def run_upload_test(self, update_cb):
        # 1.2 MB payload
        data = b"0" * 1200000
        url = "https://speed.cloudflare.com/__up"
        req = urllib.request.Request(url, data=data, method="POST", headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Content-Type': 'application/octet-stream'
        })
        try:
            context = ssl._create_unverified_context()
            start_time = time.time()
            update_cb("uploading", 0.0, 60)
            with urllib.request.urlopen(req, context=context, timeout=8) as response:
                response.read()
            elapsed = time.time() - start_time
            if elapsed > 0:
                speed_mbps = (len(data) * 8) / (elapsed * 1000000)
                update_cb("uploading", speed_mbps, 95)
                return speed_mbps
            return 0.0
        except Exception as e:
            print("Upload speedtest failed:", e)
            return 0.0

    def on_js_message(self, user_content_manager, message):
        try:
            js_val = message.get_js_value()
            body = js_val.to_string()
            print("Received JS message:", body)
            data = json.loads(body)
            action = data.get("action")
            
            if action == "get-ip-details":
                self.trigger_ip_fetch()
            elif action == "run-speedtest":
                threading.Thread(target=self._run_speedtest_thread, daemon=True).start()
        except Exception as e:
            print("Error handling JS message:", e)

    def on_title_changed(self, webview, pspec):
        title = webview.get_title()
        print("Webview Title Changed to:", title)

    def on_destroy(self, widget):
        self.monitor.running = False
        Gtk.main_quit()

if __name__ == "__main__":
    Gtk.init(None)
    app = PolonOSNetMonitorApp()
    app.show_all()
    Gtk.main()
