"""Where to get help (India). Used by the Action Centre page AND the PDF summary,
so the two always list the same things.

What was checked (25 Oct 2026, during the hackathon):
- 112, 181 and 1930 appear in the Government of India directory at india.gov.in/directory/helpline.
- 181 details (toll-free, 24x7, referrals) come from publicservicesmap.in.
- The cybercrime portal is described at services.india.gov.in; the address below is the one
  our team was given, so OPEN IT BEFORE THE DEMO.
- StopNCII.org and takeitdown.ncmec.org descriptions come from their own home pages.

IMPORTANT: websites and phone services change. Before the demo, open every link and check
it still works and says what we describe.
"""

RESOURCES = [
    {
        "group": "Emergency (immediate danger)",
        "name": "112 - India's emergency number",
        "url": "",
        "what": "Police, fire and health emergency services. Call if you or someone else is in danger right now.",
    },
    {
        "group": "Emergency (immediate danger)",
        "name": "181 - Women Helpline",
        "url": "",
        "what": "Toll-free helpline for women in distress, listed as 24 hours a day. It can refer you to police, One Stop Centres, hospitals and legal services.",
    },
    {
        "group": "Reporting a cybercrime (not an emergency)",
        "name": "National Cyber Crime Reporting Portal",
        "url": "https://cybercrime.gov.in/",
        "what": "Government portal to report online crimes, with a focus on crimes against women and children. Kavach does not submit anything to it for you.",
    },
    {
        "group": "Reporting a cybercrime (not an emergency)",
        "name": "1930 - Cyber Crime Helpline",
        "url": "",
        "what": "Listed as the cyber crime helpline in the Government of India directory.",
    },
    {
        "group": "Getting an image removed",
        "name": "StopNCII.org",
        "url": "https://stopncii.org/",
        "what": "For adults (18+) who are in an intimate image or video that may be shared without consent. The fingerprint is made on your own device and the picture is not uploaded. Check on the site whether it works for you.",
    },
    {
        "group": "Getting an image removed",
        "name": "Take It Down (NCMEC)",
        "url": "https://takeitdown.ncmec.org/",
        "what": "For images or videos taken when you were under 18. The file stays on your device; only a fingerprint is shared.",
    },
    {
        "group": "Reporting to the platform",
        "name": "The report option inside the app or website",
        "url": "",
        "what": "Look for a report option on the post or profile (often a menu button). Choose the closest reason, for example impersonation, harassment or a picture shared without consent.",
    },
]

ACTIONS = [
    ("saved_evidence", "I saved screenshots, links and dates"),
    ("reported_platform", "I reported it to the platform"),
    ("reported_cybercrime", "I reported it on the cybercrime portal"),
    ("told_trusted", "I told someone I trust"),
]
