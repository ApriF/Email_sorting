import pytest
import os
from parser import EmailClassifier

# Initialize handlers
classifier_en = EmailClassifier()
classifier_fr = EmailClassifier(language="fr")


@pytest.mark.parametrize(
    "data, expected",
    [
        # security
        (
            {
                "subject": "Security Alert",
                "body": "Unauthorized signin detected",
                "sender": "alerts@service.com",
            },
            "Security",
        ),
        (
            {
                "subject": "Verification Code",
                "body": "Your two-step authentication code",
                "sender": "no-reply@service.com",
            },
            "Security",
        ),
        # finance
        (
            {
                "subject": "Invoice #001",
                "body": "Payment due tomorrow",
                "sender": "billing@company.com",
            },
            "Finance",
        ),
        (
            {
                "subject": "Bank transfer completed",
                "body": "Transaction successful",
                "sender": "bank@payments.com",
            },
            "Finance",
        ),
        # marketing
        (
            {
                "subject": "50% OFF – Limited Time",
                "body": "Unsubscribe here",
                "sender": "promo@shop.com",
            },
            "Marketing",
        ),
        (
            {
                "subject": "Newsletter",
                "body": "Black Friday deals inside",
                "sender": "news@brand.com",
            },
            "Marketing",
        ),
        # job market
        (
            {
                "subject": "Resume for Python Developer",
                "body": "CV attached",
                "sender": "candidate@email.com",
            },
            "Job Market",
        ),
        (
            {
                "subject": "Job Offer",
                "body": "Salary and onboarding details",
                "sender": "hr@company.com",
            },
            "Job Market",
        ),
        # tech
        (
            {
                "subject": "AWS Alarm",
                "body": "Server down due to timeout",
                "sender": "monitor@aws.com",
            },
            "Tech",
        ),
        (
            {
                "subject": "GitHub deploy failed",
                "body": "Exception during deployment",
                "sender": "ci@github.com",
            },
            "Tech",
        ),
        # meetings
        (
            {
                "subject": "Meeting Invitation",
                "body": "Zoom call scheduled",
                "sender": "calendar@company.com",
            },
            "Meetings",
        ),
        (
            {
                "subject": "Agenda for tomorrow",
                "body": "Google Meet link attached",
                "sender": "team@company.com",
            },
            "Meetings",
        ),
        # travel
        (
            {
                "subject": "Flight booking confirmed",
                "body": "Your ticket and reservation",
                "sender": "airline@travel.com",
            },
            "Travel",
        ),
        (
            {
                "subject": "Hotel reservation",
                "body": "Booking details inside",
                "sender": "hotel@travel.com",
            },
            "Travel",
        ),
        # social
        (
            {
                "subject": "LinkedIn notification",
                "body": "You have a new connection request",
                "sender": "linkedin@linkedin.com",
            },
            "Social",
        ),
        (
            {
                "subject": "You were mentioned",
                "body": "Someone mentioned you on Twitter",
                "sender": "notify@twitter.com",
            },
            "Social",
        ),
    ],
)
def test_classification_rules(data, expected):
    assert classifier_en.classify_email(data) == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        # École / Université
        (
            {
                "subject": "Notes d'examens",
                "body": "Consultez votre EDT sur le portail",
                "sender": "admin@univ.fr",
            },
            "École / Université",
        ),
        # Stages & Emploi
        (
            {
                "subject": "Offre de stage",
                "body": "Entretien pour le poste de développeur",
                "sender": "hr@startup.fr",
            },
            "Stages & Emploi",
        ),
        # Voyages & Mobilité
        (
            {
                "subject": "Votre billet SNCF",
                "body": "Confirmation de votre trajet en train",
                "sender": "noreply@sncf.fr",
            },
            "Voyages & Mobilité",
        ),
        # Achats & Services
        (
            {
                "subject": "Commande Amazon",
                "body": "Votre colis est en cours de livraison",
                "sender": "ship@amazon.fr",
            },
            "Achats & Services",
        ),
        # Administratif personnel
        (
            {
                "subject": "Dossier Assurance",
                "body": "Veuillez envoyer votre attestation",
                "sender": "contact@axa.fr",
            },
            "Administratif personnel",
        ),
    ],
)
def test_classification_fr(data, expected):
    assert classifier_fr.classify_email(data) == expected


def test_rule_precedence():
    """
    Subject contains Finance keyword.
    Body contains Tech keyword.
    Finance should win due to rule order / subject priority.
    """
    data = {
        "subject": "Invoice generation failed",
        "body": "Server down due to timeout",
        "sender": "system@company.com",
    }

    assert classifier_en.classify_email(data) == "Finance"


def test_subject_weight_wins():
    """
    Subject has 'Flight' (Travel, +3).
    Body has 'Invoice' (Finance, +1).
    Travel should win (3 > 1).
    """
    data = {
        "subject": "Flight Confirmation",
        "body": "Here is your invoice for the trip.",
        "sender": "airline@travel.com",
    }
    assert classifier_en.classify_email(data) == "Travel"


def test_general_fallback():
    data = {
        "subject": "Hello there",
        "body": "Just checking in",
        "sender": "friend@gmail.com",
    }

    assert classifier_en.classify_email(data) == "General"


def test_regex_boundaries_safety():
    """
    Ensure partial words do not trigger rules.
    'Office' contains 'off', but should NOT trigger Marketing.
    """
    data = {
        "subject": "Office Party",
        "body": "Let's meet at the coffee shop.",
        "sender": "boss@company.com",
    }
    # If regex \b was missing, this would be 'Marketing'
    # Because it's internal sender and no other keywords match,
    # it should likely be 'Internal' or 'General'.
    assert classifier_en.classify_email(data) != "Marketing"


def test_case_insensitivity():
    """
    Ensure mixed case still matches keywords.
    """
    data = {
        "subject": "Urgent iNvOiCe",
        "body": "Please PAY immediately",
        "sender": "billing@vendor.com",
    }
    assert classifier_en.classify_email(data) == "Finance"


def test_internal_domain_detection():
    """
    Test that the internal domain (from .env or default) overrides keywords.
    """
    # Force an internal domain check
    os.environ["INTERNAL_DOMAIN"] = "@ecole-mines.fr"
    cls = EmailClassifier(language="fr")

    data = {
        "subject": "Facture impayée",  # Finance keyword
        "body": "Relance paiement",
        "sender": "directeur@ecole-mines.fr",
    }
    # Even though it has Finance words, it's from an internal domain
    assert cls.classify_email(data) == "Internal"


def test_french_subject_weighting():
    """
    Verify French scoring: Subject (3pts) > Body (1pt).
    """
    data = {
        "subject": "Sécurité compte",  # Sécurité (3)
        "body": "Voici votre facture",  # Achats (1)
        "sender": "service@comptes.fr",
    }
    assert classifier_fr.classify_email(data) == "Sécurité & Comptes"


def test_language_fallback():
    """
    If an unsupported language is passed, it should fallback to English.
    """
    cls_weird = EmailClassifier(language="unknown")
    data = {"subject": "Invoice", "body": "", "sender": "x@y.com"}
    assert cls_weird.classify_email(data) == "Finance"
