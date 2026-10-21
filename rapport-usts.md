# USTS Assistant Mail - Rapport technique

**Candidat :** Walid | **Date :** octobre 2026 | **Test technique USTS**

## 1. Contexte et objectif

Assistant de messagerie intelligent : synchronisation Gmail, classification IA
(client / facture / rendez-vous / newsletter / spam probable / autre), priorisation
(1-3), résumé en une phrase, action attendue, réponses assistées par IA et
automatisation n8n. Backend FastAPI entre l'interface et les workflows.

## 2. Architecture

- **Frontend** : React 18 + TypeScript + Vite (boite de reception, filtres
  combinables, vue detaillee, resume IA, relances, brouillon IA, SSE temps reel)
- **Backend** : FastAPI + SQLAlchemy + SQLite (JWT HS256, 1 h)
- **IA** : Groq (openai/gpt-oss-20b), temperature 0.1 (classification),
  0.2 (resume), 0.4 (brouillon), sortie structuree validee avant sauvegarde
- **Automatisation** : n8n (planification 10 min + Error Trigger)
- **Deploiement** : docker-compose (backend + n8n)

## 3. Fonctionnalites livrees

1. Synchronisation Gmail OAuth2 (incrementale, curseur)
2. Classification IA a categories fermees + priorite + resume + action attendue
3. Resume quotidien genere par IA (anti-injection : le contenu est traite
   comme des donnees, jamais comme des instructions)
4. Bloc "Aujourd'hui" : top 5 priorites + raisons
5. Relances intelligentes : e-mails prioritaires non traites depuis X heures
6. Brouillon de reponse IA : 3 tons (formel / neutre / court), langue du mail
   respectee, <= 150 mots, aucune information inventee
7. Temps reel SSE : nouveau mail pousse au navigateur sans rechargement
8. Idempotence : gmail_message_id unique (pas de doublon d'import),
   envoi protege contre le double-clic
9. Webhook securise : header X-Webhook-Secret (401 sinon)

## 4. Securite

- JWT 1 h sur toutes les routes sensibles
- Secret partage obligatoire pour les appels n8n
- credentials.json / token.json exclus de git
- Garde-fou injection prompt sur tous les appels IA

## 5. Tests (pytest, 5 tests)

- Webhook sans secret -> 401
- Webhook mauvais secret -> 401
- Webhook bon secret -> 200
- Double import (meme gmail_message_id) -> IntegrityError, aucun doublon
- Double envoi -> second appel refuse (deja envoye)

## 6. Workflows n8n (dossier n8n-workflows/)

1. **sync-10min.json** : declencheur planifie toutes les 10 minutes, appel HTTP
   POST vers le backend avec le header secret.
2. **error-trigger.json** : Error Trigger n8n -> signalement au backend
   (journalisation centralisee des erreurs d'execution).

## 7. Metriques mesurees (script demo_30_emails.py)

| Metrique | Resultat |
|---|---|
| Duree de classification de 30 e-mails | **61,6 s** (~2 s/e-mail) |
| Sorties IA valides du premier coup | **30/30 (100 %)** |
| Echecs definitifs | **0** |
| Evenements rate-limit (429) absorbes | **3**, retries exponentiels 10-12 s |

Conditions : quota gratuit Groq (8000 TPM), corps de mail tronques ~3000
caracteres, temperature 0.1.

## 8. Lancement

    docker-compose up --build

ou manuellement : backend (uvicorn :8000), frontend (vite :5173),
n8n (docker, :5678). Variables : voir .env.example.

## 9. Limites connues et ameliorations

- Envoi Gmail reel via API a brancher sur le bouton "Preparer l'envoi"
- Evaluation quantitative sur golden dataset (precision/rappel par categorie)
- RAG sur l'historique pour des reponses plus contextuelles
- Passage PostgreSQL pour la production

---

**Points forts IA engineering** : sortie structuree validee (Pydantic) avec
retry + repli "autre / a verifier", calibration de temperature par tache,
backoff exponentiel + jitter sur les 429, idempotence par cle unique,
webhook authentifie, tests d'integration sur les cas limites du cahier des charges.
