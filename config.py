import os
from dotenv import load_dotenv

load_dotenv()

PROFILE_PATH = "profile.md"
TEMPLATE_PATH = "report.html"
USER_EMAIL = "juanma.alv.14@gmail.com"
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Job source URLs by category
JOB_SOURCES = {
    "🏛️ LUH General Job Board": [
        "https://www.uni-hannover.de/universitaet/stellenangebote-arbeit-an-der-uni/jobboerse"
    ],
    "⚙️ Mechanics, Robotics & Control Institutes (LUH)": [
        "https://www.imes.uni-hannover.de/studium/hiwi-stellenangebote",           # IMES - Mechatronic Systems
        "https://www.irt.uni-hannover.de/de/institut/stellenangebote/",            # IRT - Control Engineering (Regelungstechnik)
        "https://www.ifw.uni-hannover.de/studium/hiwi-jobs-und-abschlussarbeiten", # IFW - Manufacturing & Machine Tools (Fertigungstechnik)
        "https://www.ids.uni-hannover.de/de/institut/stellenangebote/",            # IDS - Dynamics & Vibrations (Dynamik und Schwingungen)
        "https://www.ial.uni-hannover.de/studium/hiwi-jobs"                        # IAL - Drive Systems & Power Electronics
    ],
    "🎓 Stellenwerk Hannover (Student Job Portal)": [
        "https://www.stellenwerk.de/hannover/"
    ],
    "🏢 German Federal Employment Agency": [
        "https://www.arbeitsagentur.de/jobsuche/suche?suchbereich=jobs&was=Maschinenbau&wo=Hannover&umkreis=25&arbeitszeit=tz&veroeffentlichtseit=28&arbeitsort=Hannover",
        "https://www.arbeitsagentur.de/jobsuche/suche?suchbereich=jobs&was=Mechatronik&wo=Hannover&umkreis=25&arbeitszeit=tz;snw;mj&veroeffentlichtseit=28&arbeitsort=Hannover"
    ],
    "💼 Schwarzes Brett (LUH)": [
        "https://studip.uni-hannover.de/plugins.php/schwarzesbrettplugin/category/view/1b94d8963d1beab68bf8ec7f547d2452#/"
    ]
}

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "").strip()
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "linkedin-jobs-search.p.rapidapi.com").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Stud.IP / Shibboleth SSO credentials (LUH) — set in .env
LUH_USERNAME = os.getenv("LUH_USERNAME", "").strip()
LUH_PASSWORD = os.getenv("LUH_PASSWORD", "").strip()

GEMINI_MODEL_OPTIONS = [
    # Latest primary models (3.8 and 3.7 family)
    "gemini-3.8-flash",
    "gemini-3.7-flash",

    # Intermediate and standard models (family 3)
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",

    # Lightweight options (Flash-Lite) for lower cost and high speed
    "gemini-3.8-flash-lite-tts",  # (or base version for text-only)
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",

    # Multimedia, voice and translation models (new gen 3)
    "gemini-omni-1.1-flash",
    "gemini-3.8-live",
    "gemini-3.8-flash-tts",
    "gemini-3.5-live-translate-preview",

    # Image models (visual generation)
    "gemini-3.1-flash-image",
    "gemini-3.1-flash-lite-image",
    "gemini-3-pro-image",

    # Advanced Pro and specialised models
    "gemini-3.1-pro-preview",
    "gemini-3.5-transcribe"
]
