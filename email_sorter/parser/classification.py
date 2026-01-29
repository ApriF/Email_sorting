import re
from collections import defaultdict

class EmailClassifier:
    def __init__(self, internal_domain="@mycompany.com"):
        self.internal_domain = internal_domain.lower()
        self.rules = {
            "Security": ["security", "verification", "auth", "2fa", "sign-in", "password"],
            "Finance": ["invoice", "receipt", "bill", "payment", "transfer", "order #"],
            "Marketing": ["newsletter", "unsubscribe", "discount", "promo", " sale ", " off "], # note spaces
            "Job Market": ["resume", "cv", "hiring", "job offer", "candidate"],
            "Tech": ["error", "exception", "timeout", "deploy", "server", "aws", "gitlab"],
            "Meetings": ["meeting", "zoom", "invite", "scheduled", "agenda"],
            "Travel": ["flight", "hotel", "booking", "reservation", "uber", "train"],
            "Social": ["linkedin", "twitter", "facebook", "instagram", "connection"],
        }

    def classify_email(self, email_data):
        subject = email_data.get("subject", "").lower()
        body = email_data.get("body", "").lower()
        sender = email_data.get("sender", "").lower()

        scores = defaultdict(int)

        for category, keywords in self.rules.items():
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
        if self.internal_domain in sender:
            return "Internal"

        if not scores:
            return "General"
        
        return max(scores, key=scores.get)