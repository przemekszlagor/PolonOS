import os
import json
import random
import wsgiref.simple_server
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow, _RedirectWSGIApp, _WSGIRequestHandler
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Domyślne klucze Google OAuth 2.0 (aplikacja Desktop)
# Możesz wkleić tutaj swoje klucze, aby logowanie działało natychmiast po kliknięciu
CLIENT_ID = "992395622709-kl71ebonoqocjcjq1dg66miakirokjvj.apps.googleusercontent.com"
CLIENT_SECRET = "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"

class GoogleCalendarSync:
    def __init__(self, db_manager, credentials_path=None):
        self.db = db_manager
        if credentials_path is None:
            config_dir = os.path.expanduser("~/.config/polonos-kalendarz")
            credentials_path = os.path.join(config_dir, "credentials.json")
        self.credentials_path = credentials_path

    def authenticate_real_account(self, client_id=None, client_secret=None, browser_opener=None):
        """
        Runs the OAuth2 flow using a local loopback server.
        Checks sources: passed args -> database settings -> hardcoded constants -> credentials.json
        """
        c_id = client_id
        c_sec = client_secret
        
        # 1. Sprawdź bazę danych settings
        if not c_id or not c_sec:
            c_id = self.db.get_setting("client_id")
            c_sec = self.db.get_setting("client_secret")
            
        # 2. Sprawdź stałe w kodzie
        if (not c_id or not c_sec) or ("YOUR_CLIENT_ID_HERE" in c_id):
            c_id = CLIENT_ID
            c_sec = CLIENT_SECRET
            
        # 3. Sprawdź plik credentials.json (szukaj w kilku lokalizacjach)
        if (not c_id or not c_sec) or ("YOUR_CLIENT_ID_HERE" in str(c_id)):
            possible_paths = [
                self.credentials_path,
                os.path.expanduser("~/.config/polonos-kalendarz/credentials.json"),
                os.path.expanduser("~/.config/polonos-calendar/credentials.json"),
                "/opt/polonos-kalendarz/credentials.json",
                "/opt/polonos-calendar/credentials.json",
                "credentials.json",
                os.path.join(os.path.expanduser("~"), "credentials.json"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "credentials.json")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r') as f:
                            cfg = json.load(f)
                            inst = cfg.get("installed", {})
                            c_id = inst.get("client_id")
                            c_sec = inst.get("client_secret")
                            if c_id and c_sec:
                                break
                    except Exception as e:
                        print(f"Błąd podczas wczytywania pliku credentials.json ({path}): {e}")
                    
        # Weryfikacja kluczy
        if not c_id or not c_sec or "YOUR_CLIENT_ID_HERE" in c_id:
            raise ValueError(
                "Brak poprawnych kluczy Google OAuth.\n"
                "Uzupełnij CLIENT_ID i CLIENT_SECRET w pliku src/google_sync.py,\n"
                "wgraj plik credentials.json do katalogu projektu lub ~/.config/polonos-kalendarz/."
            )

        client_config = {
            "installed": {
                "client_id": c_id,
                "client_secret": c_sec,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"]
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        
        # 1. Uruchomienie lokalnego serwera przekierowania
        wsgi_app = _RedirectWSGIApp('Logowanie zakończone pomyślnie. Możesz zamknąć to okno przeglądarki.')
        wsgiref.simple_server.WSGIServer.allow_reuse_address = False
        local_server = wsgiref.simple_server.make_server(
            'localhost', 0, wsgi_app, handler_class=_WSGIRequestHandler
        )
        
        try:
            # 2. Konfiguracja URI i URL autoryzacji
            flow.redirect_uri = f"http://localhost:{local_server.server_port}/"
            auth_url, _ = flow.authorization_url(prompt='select_account')
            
            # 3. Otwarcie przeglądarki w wątku głównym
            if browser_opener:
                browser_opener(auth_url)
            else:
                import webbrowser
                webbrowser.open(auth_url)
                
            # 4. Oczekiwanie na zapytanie zwrotne (blokujące wywołanie w osobnym wątku)
            local_server.handle_request()
            
            # 5. Odczytanie kodu i pobranie tokenu
            authorization_response = wsgi_app.last_request_uri.replace("http", "https")
            flow.fetch_token(authorization_response=authorization_response)
        finally:
            local_server.server_close()

        creds = flow.credentials
        
        # Build service to get user email
        service = build('calendar', 'v3', credentials=creds)
        
        # Get primary calendar summary (usually user's email)
        primary_cal = service.calendars().get(calendarId='primary').execute()
        email = primary_cal.get('id')
        display_name = primary_cal.get('summary', email)
        
        # Save credentials (refresh token is what we need for offline access)
        creds_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        # Save to database
        self.db.save_account(email, json.dumps(creds_data), display_name, is_demo=0)
        return email

    def add_demo_account(self, email=None):
        """
        Adds a simulated account with mock calendars and events.
        """
        if not email:
            email = f"demo.{random.randint(100, 999)}@gmail.com"
        
        display_name = f"Konto Demo ({email})"
        self.db.save_account(email, "MOCK_TOKEN", display_name, is_demo=1)
        
        # Create 3 mock calendars
        calendars = [
            {"id": f"cal_{email}_work", "summary": "Praca", "color": "#0288D1"},
            {"id": f"cal_{email}_personal", "summary": "Prywatne", "color": "#E53935"},
            {"id": f"cal_{email}_hobby", "summary": "Hobby / Sport", "color": "#43A047"}
        ]
        
        for cal in calendars:
            self.db.save_calendar(cal["id"], email, cal["summary"], cal["color"], selected=1)
            
        # Generate mock events
        self.sync_demo_events(email, calendars)
        return email

    def sync_demo_events(self, email, calendars):
        """
        Generates mock events relative to current time to populate the calendar.
        """
        events = []
        now = datetime.now()
        
        # Generate events for -30 to +30 days
        for day_offset in range(-30, 31):
            target_date = now + timedelta(days=day_offset)
            weekday = target_date.weekday()
            
            # --- WORK CALENDAR EVENTS (weekday 0-4, Mon-Fri) ---
            if weekday < 5:
                # Daily standup (9:00 - 9:30)
                start_dt = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                end_dt = start_dt + timedelta(minutes=30)
                events.append({
                    "id": f"evt_standup_{day_offset}_{email}",
                    "calendar_id": f"cal_{email}_work",
                    "account_email": email,
                    "summary": "Daily Standup",
                    "description": "Krótkie spotkanie statusowe zespołu projektowego.",
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "location": "Google Meet"
                })
                
                # Main work tasks (e.g. coding, planning)
                if weekday == 0: # Monday Planning
                    start_dt = target_date.replace(hour=10, minute=0, second=0, microsecond=0)
                    end_dt = start_dt + timedelta(hours=1, minutes=30)
                    events.append({
                        "id": f"evt_planning_{day_offset}_{email}",
                        "calendar_id": f"cal_{email}_work",
                        "account_email": email,
                        "summary": "Planowanie Sprintu",
                        "description": "Ustalenie celów na bieżący tydzień.",
                        "start_time": start_dt.isoformat(),
                        "end_time": end_dt.isoformat(),
                        "location": "Salka konferencyjna A"
                    })
                elif weekday == 4: # Friday Demo
                    start_dt = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                    end_dt = start_dt + timedelta(hours=1)
                    events.append({
                        "id": f"evt_demo_{day_offset}_{email}",
                        "calendar_id": f"cal_{email}_work",
                        "account_email": email,
                        "summary": "Demo i Retro",
                        "description": "Prezentacja wyników i retrospekcja.",
                        "start_time": start_dt.isoformat(),
                        "end_time": end_dt.isoformat(),
                        "location": "Online"
                    })
                
                # Random work meeting
                if random.random() > 0.4:
                    hour = random.choice([11, 13, 15])
                    start_dt = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    events.append({
                        "id": f"evt_meeting_{day_offset}_{email}",
                        "calendar_id": f"cal_{email}_work",
                        "account_email": email,
                        "summary": random.choice(["Konsultacje techniczne", "Review projektu", "Sync z Product Ownerem"]),
                        "description": "Omówienie bieżących zagadnień technicznych.",
                        "start_time": start_dt.isoformat(),
                        "end_time": (start_dt + timedelta(hours=1)).isoformat(),
                        "location": "Slack Call"
                    })
            
            # --- PERSONAL CALENDAR EVENTS ---
            # Weekend lunch/dinner or evening tasks
            if weekday >= 5: # Sat-Sun
                # Family dinner
                if weekday == 6: # Sunday
                    start_dt = target_date.replace(hour=15, minute=0, second=0, microsecond=0)
                    events.append({
                        "id": f"evt_dinner_{day_offset}_{email}",
                        "calendar_id": f"cal_{email}_personal",
                        "account_email": email,
                        "summary": "Obiad rodzinny",
                        "description": "Obiad u rodziców.",
                        "start_time": start_dt.isoformat(),
                        "end_time": (start_dt + timedelta(hours=3)).isoformat(),
                        "location": "Dom rodzinny"
                    })
                else: # Saturday Shopping
                    start_dt = target_date.replace(hour=10, minute=0, second=0, microsecond=0)
                    events.append({
                        "id": f"evt_shopping_{day_offset}_{email}",
                        "calendar_id": f"cal_{email}_personal",
                        "account_email": email,
                        "summary": "Tygodniowe zakupy",
                        "description": "Zakupy spożywcze i domowe.",
                        "start_time": start_dt.isoformat(),
                        "end_time": (start_dt + timedelta(hours=2)).isoformat(),
                        "location": "Supermarket"
                    })
            else: # Weekday evening tasks
                if random.random() > 0.7:
                    start_dt = target_date.replace(hour=18, minute=30, second=0, microsecond=0)
                    events.append({
                        "id": f"evt_personal_todo_{day_offset}_{email}",
                        "calendar_id": f"cal_{email}_personal",
                        "account_email": email,
                        "summary": random.choice(["Wizyta u lekarza", "Serwis samochodu", "Opłacenie rachunków"]),
                        "description": "Ważne sprawy bieżące.",
                        "start_time": start_dt.isoformat(),
                        "end_time": (start_dt + timedelta(hours=1)).isoformat(),
                        "location": "Miasto"
                    })
            
            # --- HOBBY / SPORT CALENDAR EVENTS ---
            # Gym / training on Tue/Thu/Sat
            if weekday in [1, 3, 5]: # Tue, Thu, Sat
                start_dt = target_date.replace(hour=18 if weekday != 5 else 11, minute=0, second=0, microsecond=0)
                events.append({
                    "id": f"evt_gym_{day_offset}_{email}",
                    "calendar_id": f"cal_{email}_hobby",
                    "account_email": email,
                    "summary": "Trening na siłowni",
                    "description": "Trening siłowy (FBW). Pamiętaj o wodzie!",
                    "start_time": start_dt.isoformat(),
                    "end_time": (start_dt + timedelta(hours=1, minutes=30)).isoformat(),
                    "location": "Gym Fitness Club"
                })
            
            # Evening relax / reading club on Wednesday
            if weekday == 2:
                start_dt = target_date.replace(hour=20, minute=0, second=0, microsecond=0)
                events.append({
                    "id": f"evt_hobby_relax_{day_offset}_{email}",
                    "calendar_id": f"cal_{email}_hobby",
                    "account_email": email,
                    "summary": "Klub filmowy / Książka",
                    "description": "Czas na odpoczynek przy dobrej książce lub filmie.",
                    "start_time": start_dt.isoformat(),
                    "end_time": (start_dt + timedelta(hours=2)).isoformat(),
                    "location": "Dom"
                })

            # --- ALL DAY EVENTS (DEMO) ---
            # Birthday every 7 days
            if day_offset % 7 == 0:
                events.append({
                    "id": f"evt_allday_bday_{day_offset}_{email}",
                    "calendar_id": f"cal_{email}_personal",
                    "account_email": email,
                    "summary": "Urodziny znajomego",
                    "description": "Pamiętaj o złożeniu życzeń!",
                    "start_time": target_date.strftime("%Y-%m-%dT00:00:00"),
                    "end_time": target_date.strftime("%Y-%m-%dT23:59:59"),
                    "location": "",
                    "is_all_day": 1
                })
            # Conference every 14 days
            if day_offset % 14 == 5:
                next_day = target_date + timedelta(days=1)
                events.append({
                    "id": f"evt_allday_conf_{day_offset}_{email}",
                    "calendar_id": f"cal_{email}_work",
                    "account_email": email,
                    "summary": "Konferencja Branżowa",
                    "description": "Dwudniowa konferencja i warsztaty.",
                    "start_time": target_date.strftime("%Y-%m-%dT00:00:00"),
                    "end_time": next_day.strftime("%Y-%m-%dT23:59:59"),
                    "location": "Warszawa",
                    "is_all_day": 1
                })
            # 7 all-day events on today (offset 0) to test expansion (>5 events)
            if day_offset == 0:
                for idx in range(1, 8):
                    events.append({
                        "id": f"evt_allday_test_{idx}_{email}",
                        "calendar_id": f"cal_{email}_personal" if idx % 2 == 0 else f"cal_{email}_work",
                        "account_email": email,
                        "summary": f"Całodniowe wydarzenie testowe {idx}",
                        "description": "Test mechanizmu zwijania i rozwijania powyżej 5 wydarzeń.",
                        "start_time": target_date.strftime("%Y-%m-%dT00:00:00"),
                        "end_time": target_date.strftime("%Y-%m-%dT23:59:59"),
                        "location": "",
                        "is_all_day": 1
                    })
                
        self.db.save_events(events)

    def sync_account(self, email):
        """
        Synchronizes calendars and events for the given account.
        Checks if it's a demo or real account, and routes accordingly.
        """
        accounts = self.db.get_accounts()
        account = next((a for a in accounts if a['email'] == email), None)
        if not account:
            return False

        if account['is_demo']:
            # For demo accounts, we just refresh mock events (which is simple)
            calendars = self.db.get_calendars(email)
            self.sync_demo_events(email, calendars)
            return True

        # Real Google Account
        try:
            creds_data = json.loads(account['refresh_token'])
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
            
            # Refresh if expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Update saved credentials
                new_creds_data = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                self.db.save_account(email, json.dumps(new_creds_data), account['display_name'], is_demo=0)
            
            service = build('calendar', 'v3', credentials=creds)
            
            # Fetch calendar list
            calendar_list = service.calendarList().list().execute()
            
            fetched_cals = []
            for entry in calendar_list.get('items', []):
                cal_id = entry['id']
                summary = entry.get('summary', cal_id)
                # Google colors are numeric, we can use their color id or mapping. Let's extract bg color.
                color = entry.get('backgroundColor', '#0288D1') # default blue
                
                # Save calendar to db (keeps its existing 'selected' setting)
                self.db.save_calendar(cal_id, email, summary, color)
                     # Now fetch events for selected calendars in range -180 days to +365 days
            now = datetime.utcnow()
            time_min = (now - timedelta(days=180)).isoformat() + 'Z'
            time_max = (now + timedelta(days=365)).isoformat() + 'Z'
            
            # Synchronize events for each calendar
            db_calendars = self.db.get_calendars(email)
            for cal in db_calendars:
                if not cal['selected']:
                    # Optional: We could skip syncing, but let's sync and just not display. 
                    # If we skip, we should clear existing cache
                    self.db.clear_events_for_calendar(cal['id'])
                    continue
                
                # Fetch events with pagination support to fetch all events in range
                events_items = []
                page_token = None
                while True:
                    events_result = service.events().list(
                        calendarId=cal['id'],
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime',
                        maxResults=250,
                        pageToken=page_token
                    ).execute()
                    events_items.extend(events_result.get('items', []))
                    page_token = events_result.get('nextPageToken')
                    if not page_token:
                        break
                
                db_events = []
                
                # Clear existing events for this calendar to prevent orphans
                self.db.clear_events_for_calendar(cal['id'])
                
                for item in events_items:
                    # Skip all-day events start/end time parsing standard
                    start = item.get('start', {})
                    end = item.get('end', {})
                    
                    start_str = start.get('dateTime') or start.get('date')
                    end_str = end.get('dateTime') or end.get('date')
                    
                    if not start_str or not end_str:
                        continue
                    
                    # Convert to standard ISO (without timezone Z offset for simplified sorting/matching)
                    # or keep as is. Let's parse and strip timezone offset to simplify comparison in sqlite
                    is_all_day = 0
                    try:
                        # Parse ISO formats. Google API returns e.g. "2026-07-22T09:00:00+02:00"
                        # We will convert it to local naive datetime in database
                        if 'dateTime' in start:
                            # dateTime format
                            # we can take the first 19 chars: "YYYY-MM-DDTHH:MM:SS"
                            start_naive = start_str[:19]
                            end_naive = end_str[:19]
                        else:
                            # date format (all day event) e.g. "2026-07-22"
                            start_naive = f"{start_str}T00:00:00"
                            # end_str is exclusive for all-day events, subtract 1 day
                            try:
                                end_dt = datetime.strptime(end_str, "%Y-%m-%d") - timedelta(days=1)
                                end_naive = end_dt.strftime("%Y-%m-%dT23:59:59")
                            except Exception:
                                end_naive = f"{end_str}T23:59:59"
                            is_all_day = 1
                    except Exception:
                        start_naive = start_str
                        end_naive = end_str
 
                    db_events.append({
                        "id": item['id'],
                        "calendar_id": cal['id'],
                        "account_email": email,
                        "summary": item.get('summary', '(Brak tytułu)'),
                        "description": item.get('description', ''),
                        "start_time": start_naive,
                        "end_time": end_naive,
                        "location": item.get('location', ''),
                        "is_all_day": is_all_day
                    })
                
                if db_events:
                    self.db.save_events(db_events)
                    
            return True
        except Exception as e:
            print(f"Error syncing account {email}: {e}")
            return False
