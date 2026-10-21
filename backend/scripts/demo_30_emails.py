"""Demo: insere 30 e-mails de test, les classifie, mesure duree et taux de succes."""
import time

from app.db.session import SessionLocal
from app.models.email import Email
from app.services.classification_service import ClassificationService

SAMPLES = [
    ("Facture impayee n 2026-034", "Bonjour, la facture 2026-034 de 450 EUR reste impayee. Merci de regulariser sous 7 jours.", "compta@fournisseur.fr"),
    ("Invitation entretien jeudi", "Nous vous invitons a un entretien jeudi 14h au siege.", "rh@entreprise.com"),
    ("Votre abonnement premium", "Decouvrez les nouveautes de votre abonnement ce mois-ci.", "news@service.io"),
    ("URGENT: dossier bloque", "Votre dossier est bloque, intervention necessaire aujourd'hui.", "client.important@societe.fr"),
    ("Gagnez 10000 euros facilement", "Felicitations! Cliquez ici pour reclamer votre gain.", "promo@suspicious.xyz"),
    ("Compte-rendu reunion", "Voici le CR de notre reunion de ce matin.", "equipe@startup.dev"),
    ("Relance document manquant", "Le document Kbis manque toujours au dossier.", "gestion@banque.fr"),
    ("Offre speciale -50 pour cent", "Profitez de notre offre limitee ce week-end.", "marketing@shop.com"),
    ("RDV dentiste confirme", "Votre rendez-vous du 12 novembre est confirme.", "agenda@clinique.fr"),
    ("Question sur ma commande 8842", "Bonjour, ou en est ma commande 8842 ?", "client@mail.fr"),
    ("Facture 2026-035 disponible", "Votre facture de 129 EUR est disponible en ligne.", "billing@saas.io"),
    ("Webinar IA jeudi 18h", "Inscrivez-vous a notre webinar gratuit.", "events@tech.org"),
    ("Paiement refuse", "Votre paiement a ete refuse, mettez a jour votre CB.", "no-reply@banque.fr"),
    ("Demande de devis", "Pouvez-vous nous etablir un devis pour 50 licences ?", "achats@groupe.fr"),
    ("Votre colis est en route", "Colis 8Z44 en livraison, arrivee demain.", "tracking@logistics.com"),
    ("Mise a jour conditions generales", "Nos CGU ont ete mises a jour.", "legal@plateforme.fr"),
    ("SOLDE: dernier rappel", "Dernier rappel avant frais de retard.", "recouvrement@credit.fr"),
    ("Bienvenue dans la communaute", "Merci de votre inscription a notre newsletter.", "hello@communaute.fr"),
    ("Report de notre call", "Je propose de reporter notre call a vendredi.", "partenaire@alliance.fr"),
    ("Alerte securite: connexion inhabituelle", "Nouvelle connexion depuis Paris.", "security@compte.fr"),
    ("Facture rectificative 2026-036", "Veuillez trouver la facture rectificative de 89 EUR.", "compta@fournisseur.fr"),
    ("Candidature recue", "Nous avons bien recu votre candidature.", "recrutement@societe.fr"),
    ("Breaking news tech", "Les 10 actualites tech de la semaine.", "digest@technews.fr"),
    ("Renouvellement assurance", "Votre assurance expire dans 15 jours.", "contrats@assureur.fr"),
    ("Ticket support 5567 resolu", "Votre demande a ete traitee.", "support@logiciel.fr"),
    ("GROSSE PROMO cliquez vite", "Offre exclusive, ne manquez pas cette chance!!", "deal@promo-spam.biz"),
    ("Ordre de mission", "Vous etes designe pour la mission Lyon, details joints.", "direction@entreprise.fr"),
    ("Votre avis nous interesse", "Notez votre experience en 2 minutes.", "feedback@service.fr"),
    ("Extrait de compte disponible", "Votre releve mensuel est pret.", "notifications@banque.fr"),
    ("Onboarding etape 3", "Passez a l'etape finale de configuration.", "success@outil.fr"),
]


def run():
    db = SessionLocal()
    try:
        for i, (subject, body, sender) in enumerate(SAMPLES):
            mid = f"demo-30-{i:03d}"
            exists = db.query(Email).filter(Email.gmail_message_id == mid).first()
            if not exists:
                db.add(Email(gmail_message_id=mid, subject=subject, body=body, sender=sender))
        db.commit()
        emails = db.query(Email).filter(Email.gmail_message_id.like("demo-30-%")).all()
    finally:
        db.close()

    print(f"{len(emails)} e-mails demo, classification en cours...")
    t0 = time.time()
    ok, failed = 0, 0
    for e in emails:
        try:
            db2 = SessionLocal()
            try:
                ClassificationService(db2).classify_email(e.id)
            finally:
                db2.close()
            ok += 1
            print(f"  [{ok + failed}/30] OK id={e.id}")
        except Exception as ex:
            failed += 1
            print(f"  [{ok + failed}/30] ECHEC id={e.id}: {type(ex).__name__}")
    duration = time.time() - t0

    print("\n===== METRIQUES =====")
    print(f"Duree totale: {duration:.1f} s")
    print(f"Valides du premier coup: {ok}/{len(emails)} ({100 * ok / len(emails):.0f} %)")
    print(f"Echecs: {failed}")


if __name__ == "__main__":
    run()
