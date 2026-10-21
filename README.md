# USTS Assistant Mail

Assistant de messagerie intelligent : synchronisation Gmail, classification IA,
priorisation, résumés quotidiens, relances intelligentes, réponses assistées
par IA et automatisation n8n.

## Fonctionnalités

- **Classification IA** : catégories fermées (client / facture / rendez-vous /
  newsletter / spam probable / autre), priorité 1-3, résumé en une phrase,
  action attendue — sortie structurée validée (Pydantic), retry puis repli
  garanti `autre` / `à vérifier`
- **Résumé quotidien IA** : top 5 des priorités avec raisons
- **Relances intelligentes** : e-mails prioritaires non traités remontent
  automatiquement (seuil réglable en heures via `FOLLOWUP_AFTER_HOURS`)
- **Brouillon de réponse IA** : 3 tons (formel / neutre / court), langue du
  mail respectée, aucune information inventée
- **Temps réel (SSE)** : nouveaux mails poussés au navigateur sans rechargement
- **Idempotence** : clé unique `gmail_message_id` (aucun doublon d'import),
  envoi protégé contre le double-clic
- **Webhook sécurisé** : header `X-Webhook-Secret` (401 sinon)

## Stack

| Couche | Technologie |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Backend | FastAPI, Pydantic, JWT (HS256) |
| Base de données | SQLite via SQLAlchemy |
| IA | Groq (`openai/gpt-oss-20b`) |
| Orchestration | n8n (sync planifié 10 min + Error Trigger) |
| Temps réel | SSE (EventSource) |
| Conteneurisation | Docker Compose |
| Tests | pytest (10 tests) |

## Architecture
