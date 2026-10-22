# USTS Assistant Mail

Assistant de messagerie intelligent propulsé par l'IA : synchronisation Gmail,
classification automatique, priorisation, résumés quotidiens, relances
intelligentes, réponses rédigées par IA et automatisation complète via n8n.

**Projet réalisé dans le cadre du test technique USTS.**

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Fonctionnalités](#fonctionnalités)
3. [Stack technique](#stack-technique)
4. [Architecture](#architecture)
5. [Métriques mesurées](#métriques-mesurées)
6. [Prérequis](#prérequis)
7. [Lancement rapide (Docker)](#lancement-rapide-docker)
8. [Lancement manuel](#lancement-manuel)
9. [Variables d'environnement](#variables-denvironnement)
10. [API](#api)
11. [Tests](#tests)
12. [Sécurité](#sécurité)
13. [Structure du projet](#structure-du-projet)
14. [Points forts IA engineering](#points-forts-ia-engineering)
15. [Limites et améliorations](#limites-et-améliorations)

---

## Vue d'ensemble

Une boîte de réception professionnelle reçoit un flux hétérogène : clients,
factures, rendez-vous, newsletters, spam. Trier, prioriser et répondre est
chronophage et source d'oublis.

**USTS Assistant Mail** synchronise Gmail, puis pour chaque e-mail :

- le **classe** dans une liste de catégories *fermée* (client / facture /
  rendez-vous / newsletter / spam probable / autre) ;
- lui attribue une **priorité** de 1 à 3 ;
- génère un **résumé** en une phrase et une **action attendue** ;
- propose un **brouillon de réponse** rédigé par IA (3 tons au choix) ;
- remonte les **relances** : e-mails prioritaires non traités depuis X heures ;
- pousse les nouveaux messages en **temps réel** dans le navigateur (SSE).

Toute l'intelligence vit dans un backend FastAPI ; n8n orchestre la
planification (sync toutes les 10 minutes) et la gestion des erreurs.

## Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| Classification IA | Catégories fermées, priorité 1-3, résumé, action attendue — sortie JSON structurée validée par Pydantic |
| Robustesse IA | Retry sur sortie invalide, puis repli garanti `autre` / `à vérifier` — le pipeline ne plante jamais |
| Résumé quotidien IA | Bloc « Aujourd'hui » : top 5 des priorités avec raisons |
| Relances intelligentes | E-mails prioritaires non traités depuis X h (seuil : `FOLLOWUP_AFTER_HOURS`) |
| Brouillon IA | 3 tons (formel / neutre / court), langue du mail respectée, ≤ 150 mots, aucune information inventée |
| Temps réel | SSE (EventSource) : nouveau mail poussé au navigateur, sans rechargement |
| Filtres combinables | Recherche texte + catégorie + priorité + statut |
| Idempotence | `gmail_message_id` unique → aucun doublon d'import ; verrou de statut → aucun double envoi |
| Webhook sécurisé | Header `X-Webhook-Secret` obligatoire (401 sinon) |
| API documentée | Swagger UI auto-généré (`/docs`) — testable depuis le navigateur |

## Stack technique

| Couche | Technologie | Justification |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | Composants typés, rechargement à chaud, build rapide |
| Backend | FastAPI + Pydantic | Async natif (SSE), validation des sorties IA, Swagger auto |
| Base de données | SQLite via SQLAlchemy | ORM portable, déploiement sans serveur de BD |
| Modèle IA | Groq (`openai/gpt-oss-20b`) | Faible latence, bonne conformité JSON structuré |
| Auth | JWT HS256 (1 h) | Stateless, expiration configurable |
| Orchestration | n8n | Planification 10 min + Error Trigger, sans logique métier |
| Temps réel | SSE (EventSource) | Push HTTP simple, reconnect automatique |
| Conteneurisation | Docker Compose | Stack reproductible en une commande |
| Tests | pytest + TestClient | Tests HTTP sans lancer le serveur |

## Architecture

```
                        +------------------+
                        |   GMAIL (OAuth2) |
                        +--------+---------+
                                 |  sync (read-only)
                                 v
+-----------+   JWT + SSE  +---------------+   SQL   +----------+
| FRONTEND  |&lt;------------&gt;| BACKEND FastAPI|&lt;------&gt;|  SQLite  |
| React+TS  |              |               |         +----------+
|  :5173    |              |  - Auth JWT   |
+-----------+              |  - /emails    |&lt;--+
                           |  - /summary   |   | X-Webhook-Secret
                           |  - /draft     |   |
                           |  - SSE/events |   |
                           +-------+-------+   |
                                   | Groq API  |
                                   v           |
                           +---------------+   |
                           |  GROQ (LLM)   |   |
                           +---------------+   |
                           +---------------+---+
                           |  n8n          |
                           |  - planif     |
                           |    10 min     |
                           |  - Error      |
                           |    Trigger    |
                           +---------------+
```

**Principe directeur :** n8n est l'orchestrateur (le plombier), FastAPI est le
cerveau. Toute l'IA et les données vivent dans le backend — testables
indépendamment de n8n.

**Flux de données :**

1. n8n réveille le backend toutes les 10 min via `POST /webhooks/n8n` (secret) ;
2. le backend tire les nouveaux mails de Gmail et les stocke (idempotent) ;
3. pour chaque mail, appel Groq → JSON validé → catégorie / priorité / résumé / action sauvegardés ;
4. le frontend (JWT) affiche boîte, filtres, résumé du jour, relances ;
5. les nouveaux mails arrivent en push SSE ; les erreurs remontent vers le workflow Error Trigger.

## Métriques mesurées

Script `scripts/demo_30_emails.py` : 30 e-mails de test variés insérés, puis
classification réelle via l'API Groq (quota gratuit, 8000 TPM).

| Métrique | Résultat |
|---|---|
| Durée de classification de 30 e-mails | **61,6 s** (~2,0 s/e-mail) |
| Sorties IA valides du premier coup | **30/30 (100 %)** |
| Échecs définitifs | **0** |
| Rate-limits (429) absorbés | **3** — backoff exponentiel 10-12 s + jitter |

Les 3 événements 429 n'ont jamais propagé d'échec : le client Groq applique un
backoff exponentiel avec jitter (attente doublée par tentative, plafonnée,
aléa anti-thundering-herd).

## Prérequis

- Python 3.12 + pip
- Node.js 20 + npm
- Une clé API Groq (gratuite) : https://console.groq.com
- (Optionnel) `credentials.json` OAuth Google à la racine de `backend/`
- (Optionnel) Docker + Docker Compose

## Lancement rapide (Docker)

    cp .env.example .env

Éditer `.env` : renseigner `GROQ_API_KEY` et `WEBHOOK_SECRET`, puis :

    docker-compose up --build

Puis ouvrir : frontend http://localhost:5173 · API http://localhost:8000/docs ·
n8n http://localhost:5678.

## Lancement manuel

**1. Backend** (depuis la racine du projet, terminal 1) :

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r backend/requirements.txt

    $env:GROQ_API_KEY = "gsk_..."
    python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

**2. Frontend** (terminal 2) :

    cd frontend
    npm install
    npm run dev

Ouvrir http://localhost:5173 — se connecter, la boîte se charge et les
nouveaux mails arrivent en temps réel.

**3. n8n** (optionnel, via Docker) :

    docker run -d -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n

Importer `n8n-workflows/sync-10min.json` et `n8n-workflows/error-trigger.json`,
renseigner la variable `WEBHOOK_SECRET`, activer le workflow.

**4. Synchronisation Gmail** :

Déposer `credentials.json` dans `backend/` (Google Cloud Console → OAuth
client ID, type « application de bureau »), ajouter le compte en
**utilisateur de test**, puis appeler `POST /gmail/sync` depuis Swagger.

## Variables d'environnement

| Variable | Description | Défaut |
|---|---|---|
| `GROQ_API_KEY` | Clé API Groq (obligatoire) | — |
| `GROQ_MODEL` | Modèle utilisé | `openai/gpt-oss-20b` |
| `SECRET_KEY` | Clé de signature JWT | à changer en production |
| `WEBHOOK_SECRET` | Secret partagé n8n ↔ backend | à changer en production |
| `DATABASE_URL` | URL SQLAlchemy | SQLite local |
| `FOLLOWUP_AFTER_HOURS` | Seuil des relances (heures) | `48` |

## API

Documentation interactive : **http://localhost:8000/docs** (Swagger).

| Méthode | Route | Description |
|---|---|---|
| POST | `/auth/login` | Authentification → JWT |
| GET | `/emails` | Liste paginée + filtres (catégorie, priorité, statut, recherche) |
| GET | `/emails/{id}` | Détail d'un e-mail |
| POST | `/emails/{id}/draft?tone=` | Brouillon de réponse IA (formal / neutral / short) |
| POST | `/emails/{id}/send` | Envoi idempotent (double-clic sûr) |
| GET | `/summary/today` | Résumé du jour IA + relances |
| GET | `/events?token=` | Flux SSE temps réel |
| POST | `/gmail/sync` | Synchronisation Gmail incrémentale |
| POST | `/webhooks/n8n` | Webhook n8n (`X-Webhook-Secret` requis) |
| POST | `/webhooks/n8n/error` | Réception des erreurs n8n |

Codes d'erreur contractuels : 401 (auth / secret), 404 (e-mail absent),
422 (paramètre invalide), 502 (échec génération IA).

## Tests

    cd backend
    python -m pytest tests -v

Résultat : **10 passed (2,36 s)**.

- Sortie IA valide → analyse conforme
- Sortie IA invalide (JSON corrompu) → retry automatique
- Deux sorties invalides → repli garanti `autre` / `à vérifier`
- Webhook sans secret → 401
- Webhook mauvais secret → 401
- Webhook bon secret → 200
- Double import (même `gmail_message_id`) → erreur d'intégrité, aucun doublon
- Double envoi → second appel refusé (`already_sent: true`)
- Service de classification → sauvegarde correcte, 404 si absent

## Sécurité

- JWT HS256 (1 h) vérifié sur chaque route sensible
- Webhook : `X-Webhook-Secret` obligatoire, secret externalisé en variable d'environnement
- `credentials.json` / `token.json` (OAuth Google) exclus de git
- Anti-injection prompt : le contenu des e-mails est transmis au modèle comme
  une **donnée**, jamais comme une instruction
- Sortie IA validée (Pydantic) avant toute sauvegarde

## Structure du projet

    usts-assistant-mail/
    ├── backend/
    │   ├── app/
    │   │   ├── api/routes/       # auth, emails, replies, summary, events, webhooks
    │   │   ├── services/         # classification, résumé, brouillon, sync, Gmail
    │   │   ├── models/           # Email, utilisateur
    │   │   ├── schemas/          # schémas Pydantic (contrats API)
    │   │   ├── core/             # config, sécurité JWT
    │   │   ├── ai/               # provider Groq (retry, backoff, finish_reason)
    │   │   └── db/               # session SQLAlchemy
    │   ├── tests/                # pytest (10 tests)
    │   ├── scripts/              # demo_30_emails.py (métriques mesurées)
    │   └── Dockerfile
    ├── frontend/                 # React 18 + TypeScript + Vite
    ├── n8n-workflows/            # sync-10min.json + error-trigger.json
    ├── docker-compose.yml
    ├── .env.example
    └── report-usts.md            # rapport détaillé (captures commentées)

## Points forts IA engineering

- **Sortie structurée validée** : retry + repli garanti, le pipeline ne casse jamais
- **Température calibrée par tâche** : 0,1 (classification), 0,2 (résumé), 0,4 (rédaction)
- **Backoff exponentiel + jitter** sur les rate-limits Groq (429)
- **Idempotence** : clé unique `gmail_message_id`, verrou de statut sur l'envoi
- **Webhook authentifié** et **tests sur les cas limites** du cahier des charges
- **Métriques réellement mesurées** (61,6 s / 30 mails, 100 % valides), non estimées
- **SSE** : push temps réel sans WebSocket

## Limites et améliorations

- Envoi Gmail réel (API `users.messages.send`) à brancher sur le point
  d'entrée idempotent `/emails/{id}/send`
- Golden dataset annoté pour mesurer précision / rappel par catégorie et
  calibrer la taxonomie
- Couche RAG sur l'historique pour des réponses plus contextuelles
- PostgreSQL + file de messages (Celery / Redis) pour la montée en charge
- Workflow n8n de classification déclenché par webhook entrant

## Rapport détaillé

Voir `report-usts.md` : contexte, architecture, captures d'écran commentées,
métriques, sécurité, tests et limites.
