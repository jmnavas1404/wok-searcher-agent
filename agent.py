import requests
from bs4 import BeautifulSoup
import os
import json
import urllib.parse
import base64
import argparse
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config

if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)

# Colour palettes per LUH institute (each with its own visual style)
INSTITUTE_PALETTES = {
    "IMES": {
        "border": "#2563eb",      # Vibrant blue
        "bg": "#eff6ff",          # Soft blue background
        "badge_bg": "#dbeafe",    # Blue badge
        "text": "#1e40af",        # Dark blue text
    "name": "Institute of Mechatronic Systems"
    },
    "IRT": {
        "border": "#059669",      # Emerald green
        "bg": "#ecfdf5",          # Mint background
        "badge_bg": "#d1fae5",    # Green badge
        "text": "#065f46",        # Dark green text
        "name": "Institute of Automatic Control"
    },
    "IFW": {
        "border": "#d97706",      # Amber / golden orange
        "bg": "#fffbeb",          # Warm background
        "badge_bg": "#fef3c7",    # Amber badge
        "text": "#92400e",        # Brown/amber text
        "name": "Institute of Production Engineering and Machine Tools"
    },
    "IDS": {
        "border": "#7c3aed",      # Violet / purple
        "bg": "#f5f3ff",          # Light purple background
        "badge_bg": "#ede9fe",    # Violet badge
        "text": "#5b21b6",        # Deep violet text
        "name": "Institute of Dynamics and Vibrations"
    },
    "IAL": {
        "border": "#0891b2",      # Cyan / turquoise
        "bg": "#ecfeff",          # Soft cyan background
        "badge_bg": "#cffafe",    # Cyan badge
        "text": "#155e75",        # Dark cyan text
        "name": "Institute of Drive Systems and Power Electronics"
    },
    "IFA": {
        "border": "#e11d48",      # Crimson red
        "bg": "#fff1f2",          # Faint pink background
        "badge_bg": "#ffe4e6",    # Soft pink badge
        "text": "#9f1239",        # Wine red text
        "name": "Institute of Factory Systems and Logistics"
    },
    "LUIS": {
        "border": "#475569",      # Elegant slate grey
        "bg": "#f8fafc",          # Soft slate background
        "badge_bg": "#e2e8f0",    # Grey badge
        "text": "#1e293b",        # Dark slate text
        "name": "Leibniz Universität IT Services"
    },
    "IQO": {
        "border": "#9333ea",      # Electric purple
        "bg": "#faf5ff",          # Lavender background
        "badge_bg": "#f3e8ff",    # Lavender badge
        "text": "#6b21a8",        # Purple text
        "name": "Institute of Quantum Optics"
    },
    "ITA": {
        "border": "#ea580c",      # Burnt orange
        "bg": "#fff7ed",          # Soft orange background
        "badge_bg": "#ffedd5",    # Orange badge
        "text": "#9a3412",        # Rust text
        "name": "Institute of Transport and Automation Technology"
    },
    "IW": {
        "border": "#0d9488",      # Deep teal
        "bg": "#f0fdfa",          # Soft aqua background
        "badge_bg": "#ccfbf1",    # Aqua badge
        "text": "#115e59",        # Dark aqua text
        "name": "Institute of Materials Science"
    },
    "HOT": {
        "border": "#ca8a04",      # Golden mustard
        "bg": "#fefce8",          # Faint yellow background
        "badge_bg": "#fef08a",    # Yellow badge
        "text": "#854d0e",        # Mustard text
        "name": "Hannover Centre for Optical Technologies"
    },
    "MATCH": {
        "border": "#4f46e5",      # Indigo
        "bg": "#eef2ff",          # Soft indigo background
        "badge_bg": "#e0e7ff",    # Indigo badge
        "text": "#3730a3",        # Dark indigo text
    "name": "Mechatronics Centre Hannover"
    }
}

FALLBACK_PALETTES = [
    {"border": "#0284c7", "bg": "#f0f9ff", "badge_bg": "#e0f2fe", "text": "#0369a1"},
    {"border": "#16a34a", "bg": "#f0fdf4", "badge_bg": "#dcfce7", "text": "#15803d"},
    {"border": "#9333ea", "bg": "#faf5ff", "badge_bg": "#f3e8ff", "text": "#7e22ce"},
    {"border": "#c026d3", "bg": "#fdf4ff", "badge_bg": "#fae8ff", "text": "#a21caf"},
    {"border": "#f59e0b", "bg": "#fffbeb", "badge_bg": "#fef3c7", "text": "#b45309"},
    {"border": "#e11d48", "bg": "#fff1f2", "badge_bg": "#ffe4e6", "text": "#be123c"}
]

INSTITUTE_PATTERNS = [
    (r'\bimes\b|mechatronische[n\s]+systeme', 'IMES'),
    (r'\birt\b|regelungstechnik', 'IRT'),
    (r'\bifw\b|fertigungstechnik|werkzeugmaschinen|fräsprozess', 'IFW'),
    (r'\bids\b|dynamik\s+und\s+schwingungen|gtm\b', 'IDS'),
    (r'\bial\b|antriebssysteme|leistungselektronik', 'IAL'),
    (r'\bifa\b|fabrikanlagen|produktionsmanagement|logistik', 'IFA'),
    (r'\bluis\b|it-services|it-auskunft|systemadministration', 'LUIS'),
    (r'\biqo\b|quantenoptik|hörsaalsammlung', 'IQO'),
    (r'\bita\b|transport-\s*und\s*automatisierung|einstein-elevator|fördergurt', 'ITA'),
    (r'\biw\b|werkstoffkunde', 'IW'),
    (r'\bhot\b|optische\s+technologien', 'HOT'),
    (r'\bmatch\b|mechatronik-zentrum', 'MATCH'),
]

def get_institute_color(acronym):
    acronym = (acronym or "").upper().strip()
    if acronym in INSTITUTE_PALETTES:
        return INSTITUTE_PALETTES[acronym]
    idx = sum(ord(c) for c in acronym) % len(FALLBACK_PALETTES)
    pal = FALLBACK_PALETTES[idx].copy()
    pal["name"] = acronym
    return pal

def resolve_luh_institute(title="", email="", text="", hint=None):
    combined = f"{title} {email} {text} {hint or ''}".lower()
    
    # Check institutional email subdomain (e.g. @ifw.uni-hannover.de -> IFW)
    m_email = re.search(r'@([a-z0-9]+)\.uni-hannover\.de', email.lower())
    if m_email:
        domain = m_email.group(1).upper()
        if domain in INSTITUTE_PALETTES:
            return domain
            
    # Check acronym and German name patterns
    for pat, acr in INSTITUTE_PATTERNS:
        if re.search(pat, combined):
            return acr
            
    if hint:
        return hint.upper()
        
    return "LUH"

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', config.SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Missing 'credentials.json'. Download it from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', config.SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def read_profile():
    with open(config.PROFILE_PATH, "r", encoding="utf-8") as file:
        return file.read()

def fetch_jobs(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def fetch_luh_jobboerse(url):
    """Fetches job listings from the LUH general job board, including the official posting and details."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = soup.find_all(class_='c-jobsitem')
        keywords = ['maschinenbau', 'mechatronik', 'robot', 'student', 'hilfskraft', 'hiwi', 'ingenieur', 
                    'produktion', 'fertigung', 'systemadministration', 'it-', 'lehre', 'simulation', 'cad', 'optik', 'elektronik']
        
        relevant_jobs = []
        for item in items:
            text = item.get_text(' ', strip=True)
            a = item.find('a')
            if not a:
                continue
            title = a.get_text(strip=True)
            link = urllib.parse.urljoin('https://www.uni-hannover.de', a['href'])
            
            combined = (text + ' ' + title).lower()
            if any(kw in combined for kw in keywords):
                deadline_div = item.find(class_=re.compile(r'deadline|applicationend'))
                deadline = deadline_div.get_text(' ', strip=True).replace('Bewerbungsfrist:', '').strip() if deadline_div else 'Not specified'
                relevant_jobs.append({'title': title, 'url': link, 'deadline': deadline})
                
        def fetch_detail(job):
            try:
                resp = requests.get(job['url'], headers=headers, timeout=10)
                dsoup = BeautifulSoup(resp.text, 'html.parser')
                main = dsoup.find('main') or dsoup.find('article') or dsoup
                dtext = main.get_text(' ', strip=True)
                
                # Extract institutional email addresses
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.uni-hannover\.de', dtext)
                email = emails[0] if emails else 'Not specified'
                
                # Extract institute acronym
                acronym = resolve_luh_institute(title=job['title'], email=email, text=dtext)
                
                return {
                    'title': job['title'],
                    'institute': acronym,
                    'url': job['url'],
                    'deadline': job['deadline'],
                    'contact_email': email,
                    'description': dtext[:1500]
                }
            except Exception as e:
                return {
                    'title': job['title'],
                    'institute': resolve_luh_institute(title=job['title']),
                    'url': job['url'],
                    'deadline': job['deadline'],
                    'contact_email': 'Not specified',
                    'description': ''
                }

        with ThreadPoolExecutor(max_workers=5) as executor:
            detailed_jobs = list(executor.map(fetch_detail, relevant_jobs))

        output_text = "=== LUH GENERAL JOB BOARD LISTINGS (WITH DETAILS & INSTITUTE) ===\n\n"
        for dj in detailed_jobs:
            output_text += f"[INSTITUTE: {dj['institute']}]\n"
            output_text += f"Title: {dj['title']}\n"
            output_text += f"Posting link: {dj['url']}\n"
            output_text += f"Deadline: {dj['deadline']}\n"
            output_text += f"Contact email: {dj['contact_email']}\n"
            output_text += f"Description: {dj['description']}\n\n"
            
        return output_text
    except Exception as e:
        print(f"Error processing LUH general job board: {e}")
        return fetch_jobs(url)

def fetch_luh_institute_page(url):
    """Fetches job listings from individual institute pages, clearly associating their acronym."""
    domain_match = re.search(r'https?://(?:www\.)?([a-z0-9]+)\.uni-hannover\.de', url)
    acronym = domain_match.group(1).upper() if domain_match else "LUH"
    
    text = fetch_jobs(url)
    return f"[INSTITUTE: {acronym}] [URL: {url}]\n" + text

def fetch_studip_schwarzes_brett(url):
    """
    Accesses the Stud.IP Schwarzes Brett (bulletin board) by authenticating
    automatically via the LUH Shibboleth SSO flow (SAML2).

    Requires LUH_USERNAME and LUH_PASSWORD in .env.
    Returns the page text for analysis with Gemini.
    """
    username = config.LUH_USERNAME
    password = config.LUH_PASSWORD

    if not username or not password:
        print("⚠️  LUH_USERNAME or LUH_PASSWORD not set in .env — skipping Schwarzes Brett.")
        return ""

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'
        })

        # ── Step 1: Start SP → IdP flow (Shibboleth.sso/Login) ──────────────
        sp_login_url = (
            'https://studip.uni-hannover.de/Shibboleth.sso/Login'
            '?target=https%3A%2F%2Fstudip.uni-hannover.de%2Fdispatch.php'
            '%2Flogin%3Fagain%3Dyes%26sso%3Dshib%26cancel_login%3D1'
            '&entityID=https%3A%2F%2Fsso.idm.uni-hannover.de%2Fidp%2Fshibboleth'
        )
        r1 = session.get(sp_login_url, allow_redirects=True, timeout=15)
        soup1 = BeautifulSoup(r1.text, 'html.parser')
        form1 = soup1.find('form')
        if not form1:
            print("❌ IdP form not found (step 1).")
            return ""

        idp_base = 'https://sso.idm.uni-hannover.de'
        action1 = idp_base + form1.get('action')
        payload1 = {
            inp.get('name'): inp.get('value', '')
            for inp in form1.find_all('input')
            if inp.get('name')
        }

        # ── Step 2: POST localStorage check → credentials form ────────────
        r2 = session.post(action1, data=payload1, allow_redirects=True, timeout=15)
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        form2 = soup2.find('form')
        if not form2:
            print("❌ Credentials form not found (step 2).")
            return ""

        action2 = idp_base + form2.get('action')
        payload2 = {
            inp.get('name'): inp.get('value', '')
            for inp in form2.find_all('input')
            if inp.get('name')
        }
        payload2['j_username'] = username
        payload2['j_password'] = password
        # Do not mark "donotcache" to keep a clean session
        payload2.pop('donotcache', None)

        # ── Step 3: POST credentials → SAML assertion → Stud.IP ─────────────
        r3 = session.post(action2, data=payload2, allow_redirects=True, timeout=15)

        # The IdP returns an HTML page with an auto-submit form that sends the SAMLResponse to the SP
        soup3 = BeautifulSoup(r3.text, 'html.parser')
        saml_form = soup3.find('form')
        if saml_form:
            saml_action = saml_form.get('action')
            # IMPORTANT: The SAML form action may be relative — ensure it is absolute.
            if saml_action and not saml_action.startswith('http'):
                saml_action = urllib.parse.urljoin(r3.url, saml_action)
            
            saml_payload = {
                inp.get('name'): inp.get('value', '')
                for inp in saml_form.find_all('input')
                if inp.get('name')
            }
            r4 = session.post(saml_action, data=saml_payload, allow_redirects=True, timeout=15)
        else:
            r4 = r3  # May have already redirected fully

        # Verify login success by checking the final URL
        if 'login' in r4.url.lower() or 'again=yes' in r4.url:
            print("❌ Stud.IP authentication failed — check LUH_USERNAME and LUH_PASSWORD in .env")
            return ""

        # ── Step 4: Access the Schwarzes Brett as authenticated user ─────────
        r5 = session.get(url, allow_redirects=True, timeout=15)
        soup5 = BeautifulSoup(r5.text, 'html.parser')

        # Try to extract the main announcements section
        content = soup5.find('main') or soup5.find(id='content') or soup5.find(id='layout_container') or soup5
        text = content.get_text(separator=' ', strip=True)

        if not text or len(text) < 100:
            print("⚠️  Schwarzes Brett: content too short — authentication may not have completed.")
        else:
            print(f"✅ Schwarzes Brett fetched ({len(text)} chars).")

        return text

    except Exception as e:
        print(f"❌ Error in fetch_studip_schwarzes_brett: {e}")
        return ""

def fetch_arbeitsagentur_jobs(urls):
    """Fetches and parses job listings from the German Federal Employment Agency, preserving the exact application link."""
    all_jobs = []
    seen_urls = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.find_all('li', class_='listeneintrag')
            
            for item in items:
                link_elem = item.find('a', href=lambda h: h and 'jobdetail' in h)
                link = link_elem.get('href', '') if link_elem else ''
                if link.startswith('/'):
                    link = urllib.parse.urljoin('https://www.arbeitsagentur.de', link)
                
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)
                
                titel_div = item.find('div', class_='titel-lane')
                title = titel_div.get_text(' ', strip=True) if titel_div else ''
                if not title and link_elem:
                    title = link_elem.get_text(' ', strip=True)
                title = re.sub(r'^\d+[\.\\:]\s*', '', title).strip()
                
                firma_div = item.find('div', class_='firma-lane')
                company = firma_div.get_text(' ', strip=True) if firma_div else 'Not specified'
                
                gehalt_elem = item.find(id=lambda i: i and 'gehaltsspanne' in i)
                salary = gehalt_elem.get_text(' ', strip=True) if gehalt_elem else 'Not specified'
                
                ort_elem = item.find(id=lambda i: i and 'arbeitsort' in i)
                location = ort_elem.get_text(' ', strip=True) if ort_elem else 'Hannover'
                location = location.replace('Arbeitsort:', '').strip()
                
                art_elem = item.find(id=lambda i: i and 'anstellungsart' in i)
                work_type = art_elem.get_text(' ', strip=True) if art_elem else 'Teilzeit'
                work_type = work_type.replace('Anstellungsart:', '').strip()
                
                bef_elem = item.find(id=lambda i: i and 'befristung' in i)
                contract = bef_elem.get_text(' ', strip=True) if bef_elem else 'Not specified'
                contract = contract.replace('Befristung:', '').strip()
                
                date_elem = item.find(id=lambda i: i and 'veroeffentlichungsdatum' in i)
                published_date = 'Not specified'
                if date_elem:
                    published_date = date_elem.get('title', date_elem.get_text(' ', strip=True))
                    published_date = published_date.replace('Veröffentlichungsdatum:', '').strip()
                    
                all_jobs.append({
                    'title': title,
                    'company': company,
                    'application_url': link,
                    'salary_info': salary,
                    'location': location,
                    'work_type': work_type,
                    'contract': contract,
                    'published_date': published_date
                })
        except Exception as e:
            print(f"Error fetching Arbeitsagentur {url}: {e}")
            
    return all_jobs

def analyze_and_draft_agency(agency_jobs, profile_text):
    """Analyze German Federal Employment Agency listings with Gemini, preserving the exact application_url."""
    if not agency_jobs:
        return {"jobs": []}, "None"
        
    prompt = f"""
    You are an expert assistant in employment and technical recruitment in Germany.
    Here are the job listings found on the German Federal Employment Agency website:
    {json.dumps(agency_jobs, ensure_ascii=False, indent=2)}

    Here is the candidate's profile (Mechanical Engineering B.Sc. and M.Sc. student in Mechatronics and Robotics at Leibniz Universität Hannover, German level B2.2):
    {profile_text}

    Your goal:
    1. Filter relevant technical or semi-technical positions (mechatronics, mechanics, simulation, CAD, control, assembly, technical support, inspection, quality, teaching).
    2. For each selected position:
       - Keep EXACTLY: 'title', 'company', 'application_url', 'salary_info', 'location', 'work_type', 'contract', 'published_date'.
       - Write a professional and concise application message IN ENGLISH ('draft_message'), connecting the candidate's experience and background to the role.
       - If the text or name contains a contact person or email, extract it; otherwise use 'Not specified'.
   
    Only include Teilzeit or Minijob positions.
    Return ONLY a valid JSON with this exact structure:
    {{
        "jobs": [
            {{
                "title": "...",
                "company": "...",
                "application_url": "...",
                "salary_info": "...",
                "location": "...",
                "work_type": "...",
                "contract": "...",
                "published_date": "...",
                "contact_name": "Not specified",
                "contact_email": "Not specified",
                "draft_message": "..."
            }}
        ]
    }}
    If no relevant positions are found, return {{"jobs": []}}.
    """
    
    successful_model = "None"
    response_text = ""
    
    for model_name in config.GEMINI_MODEL_OPTIONS:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"temperature": 0.1}
            )
            response = model.generate_content(prompt)
            if response.text:
                response_text = response.text.strip()
                successful_model = model_name
                break
        except Exception as e:
            continue
            
    if not response_text:
        return {"jobs": []}, successful_model

    try:
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
        return json.loads(response_text), successful_model
    except json.JSONDecodeError:
        return {"jobs": []}, successful_model

def analyze_and_draft_luh(text, profile_text, default_institute=None):
    """Analyses LUH and Institute job listings with Gemini, extracting the institute acronym for each position."""
    if not text.strip():
        return {"jobs": []}, "None"
        
    prompt = f"""
    You are an expert recruitment assistant in Germany. Here is the text from LUH and engineering institute job portals:
    {text}
    
    Here is the candidate's profile (Mechanical Engineering B.Sc. and M.Sc. student in Mechatronics and Robotics, German level B2.2):
    {profile_text}
    
    Look for technical positions (Hiwi, engineering, simulation, CAD, manufacturing, control, robotics) or support/teaching/assistant roles.
    
    IMPORTANT: FOR THIS RUN, DO NOT FILTER ANY LISTING. SHOW ALL POSITIONS FOUND IN THE TEXT, REGARDLESS OF WHETHER THEY STRICTLY MEET THE TECHNICAL CRITERIA.
    
    CRITICAL INSTITUTE REQUIREMENT:
    For each listing, you MUST identify and extract the INSTITUTE ACRONYM in uppercase (field 'institute', e.g.: IMES, IRT, IFW, IDS, IAL, IFA, LUIS, IQO, ITA, IW, etc.).
    If the listing comes from a section labelled [INSTITUTE: XXX], use exactly those acronyms.
    If the institute name is mentioned (e.g. Institut für Fertigungstechnik und Werkzeugmaschinen -> IFW, Institut für Mechatronische Systeme -> IMES, Institut für Regelungstechnik -> IRT, Institut für Dynamik und Schwingungen -> IDS, etc.), extract the acronym. NEVER use 'General' or 'Not specified' in 'institute'.

    Also extract: title ('title'), contact name and email, publication date ('published_date'),
    application deadline ('deadline'), salary or compensation info ('salary_info'),
    direct link to the posting if available ('application_url'),
    and write a professional application message IN ENGLISH ('draft_message').
    If the publication date, deadline or salary is not stated, use "Not specified".

    Please do not omit any position that meets the technical criteria, and do not invent information.
    If there is no contact, use "Not specified" for 'contact_name' and 'contact_email'.

    Return ONLY a valid JSON with this exact structure:
    {{
        "jobs": [
            {{
                "title": "...",
                "institute": "IMES",
                "contact_name": "...",
                "contact_email": "...",
                "published_date": "...",
                "deadline": "...",
                "salary_info": "...",
                "application_url": "...",
                "draft_message": "..."
            }}
        ]
    }}
    If no relevant positions are found, return {{"jobs": []}}.
    """
    
    successful_model = "None"
    response_text = ""
    
    for model_name in config.GEMINI_MODEL_OPTIONS:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"temperature": 0.1}
            )
            response = model.generate_content(prompt)
            if response.text:
                response_text = response.text.strip()
                successful_model = model_name
                break
        except Exception as e:
            continue
            
    if not response_text:
        return {"jobs": []}, successful_model

    try:
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
        return json.loads(response_text), successful_model
    except json.JSONDecodeError:
        return {"jobs": []}, successful_model

def generate_html_report(categorized_jobs, successful_model):
    # Process colours, acronyms and links per category
    for category, jobs_list in categorized_jobs.items():
    is_agency_cat = "Employment Agency" in category
        is_luh_cat = "LUH" in category or "Institutes" in category
        is_schwarzes_brett_cat = "Schwarzes Brett" in category

        for job in jobs_list:
            title = job.get("title", "Position")
            email = job.get("contact_email", "")
            draft = job.get("draft_message", "")

            # Mark card type
            job["is_agency"] = is_agency_cat
            job["is_luh"] = is_luh_cat
            job["is_schwarzes_brett"] = is_schwarzes_brett_cat
            
            # Enrich LUH entries with exact acronym and colour palette
            if is_luh_cat or not is_agency_cat:
                raw_inst = job.get("institute", "")
                resolved_inst = resolve_luh_institute(
                    title=title, 
                    email=email, 
                    text=draft, 
                    hint=raw_inst if raw_inst and raw_inst not in ["General", "Not specified"] else None
                )
                job["institute"] = resolved_inst
                job["color_style"] = get_institute_color(resolved_inst)
            
            # mailto link only if the email is valid
            if email and "@" in email and email != "Not specified":
                subject = urllib.parse.quote(f"Bewerbung als Studentische Hilfskraft - {title}")
                body = urllib.parse.quote(draft)
                job["mailto_link"] = f"mailto:{email}?subject={subject}&body={body}"
            else:
                job["mailto_link"] = None
            
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(config.TEMPLATE_PATH)
    return template.render(categorized_jobs=categorized_jobs, successful_model=successful_model)

def send_html_email(html_content):
    service = get_gmail_service()
    user_email = config.USER_EMAIL
    
    msg = MIMEMultipart('alternative')
    msg['From'] = user_email
    msg['To'] = user_email
    msg['Subject'] = "🤖 Job Opportunities: LUH, Institutes, and German Federal Employment Agency"
    
    msg.attach(MIMEText("Enable HTML in your email client to view the interactive report.", 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw_message}).execute()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LUH and German Federal Employment Agency job search agent")
    parser.add_argument("--no-email", action="store_true", help="Generate the HTML report in the 'tests' folder without sending the email.")
    args = parser.parse_args()

    profile_data = read_profile()
    categorized_results = {}
    last_model = "None"
    
    for category, urls in config.JOB_SOURCES.items():
        print(f"Scanning category: {category}...")
        
        if "Employment Agency" in category:
            # Specialized processing for the German Federal Employment Agency
            agency_jobs_raw = fetch_arbeitsagentur_jobs(urls)
            print(f"Analyzing {len(agency_jobs_raw)} listings from the Federal Employment Agency with Gemini...")
            results, model = analyze_and_draft_agency(agency_jobs_raw, profile_data)
            categorized_results[category] = results.get("jobs", [])
            if model != "None":
                last_model = model
                
        elif "General Job Board" in category or "Bolsa General" in category:
            # Specialised processing for the LUH general job board with calls to official postings
            luh_text = ""
            for url in urls:
                luh_text += fetch_luh_jobboerse(url) + "\n\n"
            print(f"Analysing {category} with Gemini...")
            results, model = analyze_and_draft_luh(luh_text, profile_data)
            categorized_results[category] = results.get("jobs", [])
            if model != "None":
                last_model = model
                
        elif "Institutes" in category or "Institutos" in category:
            # Processing for LUH mechanical institute pages
            institutes_text = ""
            for url in urls:
                institutes_text += fetch_luh_institute_page(url) + "\n\n"
            print(f"Analysing {category} with Gemini...")
            results, model = analyze_and_draft_luh(institutes_text, profile_data)
            categorized_results[category] = results.get("jobs", [])
            if model != "None":
                last_model = model
                
        elif "Schwarzes Brett" in category:
            # Processing with Shibboleth SSO authentication for Stud.IP
            sb_text = ""
            for url in urls:
                sb_text += fetch_studip_schwarzes_brett(url) + "\n\n"
            if sb_text.strip():
                print(f"Analysing {category} with Gemini...")
                results, model = analyze_and_draft_luh(sb_text, profile_data)
                categorized_results[category] = results.get("jobs", [])
                if model != "None":
                    last_model = model
            else:
                categorized_results[category] = []

        else:
            # Other portals (e.g. Stellenwerk)
            category_text = ""
            for url in urls:
                category_text += fetch_jobs(url) + "\n\n"
            print(f"Analysing {category} with Gemini...")
            results, model = analyze_and_draft_luh(category_text, profile_data)
            categorized_results[category] = results.get("jobs", [])
            if model != "None":
                last_model = model

    html_report = generate_html_report(categorized_results, last_model)

    if args.no_email:
        tests_dir = os.path.join(os.path.dirname(__file__), "tests")
        os.makedirs(tests_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(tests_dir, f"report_test_{timestamp}.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_report)
        print(f"--no-email mode: Email NOT sent. Report saved to: {output_file}")
    else:
        print("Generating HTML report and sending by email...")
        send_html_email(html_report)
        print("Categorised report sent successfully.")
