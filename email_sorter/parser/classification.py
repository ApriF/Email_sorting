import os
import re
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()


class EmailClassifier:
    def __init__(self, language="en"):
        # Default to a generic placeholder if the .env key is missing
        self.internal_domain = os.getenv("INTERNAL_DOMAIN", "@mycompany.com").lower()
        # default to english
        self.language = language.lower()

        self._all_rules = {
            "en": {
                "Security": [
                    "security",
                    "verification",
                    "auth",
                    "2fa",
                    "sign-in",
                    "password",
                ],
                "Finance": [
                    "invoice",
                    "receipt",
                    "bill",
                    "payment",
                    "transfer",
                    "order #",
                ],
                "Marketing": [
                    "newsletter",
                    "unsubscribe",
                    "discount",
                    "promo",
                    " sale ",
                    " off ",
                ],  # note spaces
                "Job Market": ["resume", "cv", "hiring", "job offer", "candidate"],
                "Tech": [
                    "error",
                    "exception",
                    "timeout",
                    "deploy",
                    "server",
                    "aws",
                    "gitlab",
                ],
                "Meetings": ["meeting", "zoom", "invite", "scheduled", "agenda"],
                "Travel": [
                    "flight",
                    "hotel",
                    "booking",
                    "reservation",
                    "uber",
                    "train",
                ],
                "Social": [
                    "linkedin",
                    "twitter",
                    "facebook",
                    "instagram",
                    "connection",
                ],
            },
            "fr": {
                ##categories found by chatgpt to suit a profile of a french student (profile of Cyprien Biseau)
                "École / Université": [
                    "mines",
                    "nancy",
                    "université",
                    "scolarité",
                    "inscription",
                    "examens",
                    "notes",
                    "emploi du temps",
                    "edt",
                    "planning",
                    "secrétariat",
                    "administration",
                    "cours",
                    "tp",
                    "td",
                ],
                "Projets & Associations": [
                    "projet",
                    "association",
                    "asso",
                    "club",
                    "événement",
                    "hackathon",
                    "conférence",
                    "réunion",
                    "bde",
                    "bds",
                    "bda",
                ],
                "Stages & Emploi": [
                    "stage",
                    "offre",
                    "emploi",
                    "alternance",
                    "candidature",
                    "recrutement",
                    "cv",
                    "entretien",
                    "job",
                    "career",
                ],
                "Tech / Informatique": [
                    "github",
                    "gitlab",
                    "serveur",
                    "bug",
                    "erreur",
                    "api",
                    "cloud",
                    "aws",
                    "python",
                    "code",
                    "docker",
                    "linux",
                ],
                "Sécurité & Comptes": [
                    "sécurité",
                    "connexion",
                    "authentification",
                    "mot de passe",
                    "vérification",
                    "code",
                    "alerte",
                    "tentative",
                    "2fa",
                ],
                "Réseaux sociaux": [
                    "linkedin",
                    "instagram",
                    "facebook",
                    "discord",
                    "twitter",
                    "notification",
                    "invitation",
                    "message",
                ],
                "Voyages & Mobilité": [
                    "train",
                    "sncf",
                    "vol",
                    "billet",
                    "réservation",
                    "uber",
                    "taxi",
                    "tram",
                    "bus",
                    "blablacar",
                ],
                "Achats & Services": [
                    "commande",
                    "livraison",
                    "colis",
                    "amazon",
                    "facture",
                    "paiement",
                    "abonnement",
                    "netflix",
                    "spotify",
                ],
                "Administratif personnel": [
                    "contrat",
                    "assurance",
                    "mutuelle",
                    "attestation",
                    "banque",
                    "document",
                    "dossier",
                    "impôts",
                    "caf",
                    "revolut",
                ],
                "Marketing / Newsletters": [
                    "newsletter",
                    "promotion",
                    "offre",
                    "réduction",
                    "désinscription",
                    "publicité",
                    "soldes",
                ],
            },
        }

    def classify_email(self, email_data):
        subject = email_data.get("subject", "").lower()
        body = email_data.get("body", "").lower()
        sender = email_data.get("sender", "").lower()

        # if it is eg from the company user is currently employed at, treat as Internal
        if self.internal_domain in sender:
            return "Internal"

        # select ruleset
        rules = self._all_rules.get(self.language, self._all_rules["en"])
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

        if not scores:
            return "General"

        return max(scores, key=scores.get)
