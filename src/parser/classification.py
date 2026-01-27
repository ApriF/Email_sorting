import re
from collections import defaultdict

def classify_email(email_data):
    subject = email_data.get("subject", "").lower()
    body = email_data.get("body", "").lower()
    sender = email_data.get("sender", "").lower()

    rules = {
        "Security": ["security", "verification", "auth", "2fa", "sign-in", "password"],
        "Finance": ["invoice", "receipt", "bill", "payment", "transfer", "order #"],
        "Marketing": ["newsletter", "unsubscribe", "discount", "promo", " sale ", " off "], # note spaces
        "Job Market": ["resume", "cv", "hiring", "job offer", "candidate"],
        "Tech": ["error", "exception", "timeout", "deploy", "server", "aws", "gitlab"],
        "Meetings": ["meeting", "zoom", "invite", "scheduled", "agenda"],
        "Travel": ["flight", "hotel", "booking", "reservation", "uber", "train"],
        "Social": ["linkedin", "twitter", "facebook", "instagram", "connection"],
    }
    
    scores = defaultdict(int)

    for category, keywords in rules.items():
        for k in keywords:
            # \b ensures "off" does not match eg "coffee"
            pattern = r"\b" + re.escape(k) + r"\b"
            
            # check subject (high weight)
            if re.search(pattern, subject, re.IGNORECASE):
                scores[category] += 3
            
            # check body (low weight)
            if re.search(pattern, body, re.IGNORECASE):
                scores[category] += 1

    # if it is eg from the company user is currently employed at, treat as Internal
    if "@mycompany.com" in sender:
        return "Internal"

    if not scores:
        return "General"
    
    return max(scores, key=scores.get)  

   