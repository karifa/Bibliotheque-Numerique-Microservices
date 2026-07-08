# Bibliothèque Numérique - DIT

Plateforme de gestion de ressources documentaires basée sur une architecture microservices.

Projet DevOps - Master 1 Intelligence Artificielle - Dakar Institute of Technology

**Groupe 2 :**
- AHOGA Josias
- BAH Mamoudou
- BAMBA Yannick
- DIOP Seynabou

---

## Architecture

```
├── service-livres/         -> API Livres        (port 8001)
├── service-utilisateurs/   -> API Utilisateurs  (port 8002)
├── service-emprunts/       -> API Emprunts      (port 8003)
├── frontend/               -> Interface web     (port 80)
├── docker-compose.yml      -> Orchestration
└── Jenkinsfile             -> Pipeline CI/CD (compatible Windows et Linux)
```

**Technologies :** FastAPI (Python) · PostgreSQL · Docker · Jenkins · Vue.js 3

**Base de données :** Une seule base PostgreSQL partagée par les trois microservices.

---

## Lancement avec Docker Compose

### Prérequis
- Docker Desktop installé et démarré
- Git installé

### Étapes

```bash
# 1. Cloner le projet
git clone https://github.com/Sihiney/bibliotheque-dit.git
cd bibliotheque-dit

# 2. Lancer toute l'application
docker compose up --build

# 3. Ouvrir dans le navigateur
# → Interface : http://localhost
```

### Arrêter l'application

```bash
docker compose down
```

---

## Création du compte administrateur (première utilisation)

Au premier lancement, aucun compte n'existe. Il faut créer le compte administrateur manuellement via l'API. Voici la procédure étape par étape :

### Étape 1 : Ouvrir la documentation du microservice Utilisateurs

Dans votre navigateur, allez à l'adresse :

```
http://localhost:8002/docs
```

### Étape 2 : Créer l'administrateur

1. Sur la page Swagger qui s'affiche, cherchez l'endpoint **POST /utilisateurs**
2. Cliquez dessus pour le déplier
3. Cliquez sur le bouton **"Try it out"** (en haut à droite de la section)
4. Dans le champ **Request body**, remplacez le contenu par :

```json
{
  "nom": "Admin",
  "prenom": "DIT",
  "email": "admin@dit.sn",
  "mot_de_passe": "admin123",
  "type": "personnel_administratif",
  "role": "admin"
}
```

5. Cliquez sur **"Execute"**
6. Vérifiez que la réponse affiche **Code 201** (créé avec succès)

### Étape 3 : Se connecter sur l'interface

1. Ouvrez **http://localhost** dans votre navigateur
2. Saisissez :
   - **Email :** `admin@dit.sn`
   - **Mot de passe :** `admin123`
3. Cliquez sur **"Se connecter"**

Vous êtes maintenant connecté en tant qu'administrateur avec accès complet à toutes les fonctionnalités.

> **Alternative en ligne de commande (Windows PowerShell) :**
> ```powershell
> Invoke-RestMethod -Method POST -Uri "http://localhost:8002/utilisateurs" -ContentType "application/json" -Body '{"nom":"Admin","prenom":"DIT","email":"admin@dit.sn","mot_de_passe":"admin123","type":"personnel_administratif","role":"admin"}'
> ```

> **Alternative en ligne de commande (Linux / Mac) :**
> ```bash
> curl -X POST http://localhost:8002/utilisateurs -H "Content-Type: application/json" -d '{"nom":"Admin","prenom":"DIT","email":"admin@dit.sn","mot_de_passe":"admin123","type":"personnel_administratif","role":"admin"}'
> ```

---

## Fonctionnalités

### Authentification et rôles
- Connexion par **email + mot de passe**
- Inscription avec **confirmation du mot de passe**
- **Trois types d'utilisateurs** : Étudiant, Enseignant, Personnel administratif
- **Deux rôles** : Administrateur et Membre
- **Matricule étudiant** au format `NE2510081`
- **Pièce d'identité** requise pour les enseignants (CNI, Passeport...)
- L'administrateur peut **créer des accès** avec un mot de passe temporaire → l'utilisateur est **forcé de le changer à la première connexion** (modal bloquant)
- Lien **"Mot de passe oublié"** renvoyant vers le contact admin (admin@dit.sn)

### Dashboard adapté au rôle
- **Administrateur** : statistiques globales cliquables (livres, membres, emprunts en cours, retards), toggle de validation automatique/manuelle des emprunts, accès rapide à toutes les sections
- **Étudiant / Enseignant** : ses propres emprunts en cours avec statut, livres disponibles, invitation à contacter admin@dit.sn pour partager des documents

### Gestion des livres (admin)
- Catalogue complet avec recherche par titre, auteur ou ISBN
- Ajout avec **quantité d'exemplaires** (un même livre peut avoir plusieurs exemplaires)
- Modification et suppression
- Affichage du nombre d'exemplaires disponibles sur le total (ex: 2/3)

### Gestion des utilisateurs (admin)
- Liste de tous les membres inscrits
- **Modifier** les informations d'un utilisateur
- **Désactiver** un compte membre : bloqué si des emprunts sont en cours, sinon désactivation douce avec conservation de l'historique
- Le bouton de suppression définitive reste disponible via l'API directement
- Créer un accès avec mot de passe temporaire

### Gestion des emprunts
- Emprunt par sélection dans une liste déroulante (membre + livre disponible)
- **Durée fixe de 15 jours** pour chaque emprunt
- **Maximum 2 emprunts en cours** par utilisateur
- Enregistrement du retour avec détection automatique des retards et nombre de jours
- Mise à jour automatique de la disponibilité des exemplaires après emprunt/retour

### Page d'accueil
- Logo DIT et titre à gauche, formulaire de connexion/inscription à droite
- Design sur fond vert DIT avec carte blanche pour le formulaire

---

## Documentation des APIs

FastAPI génère automatiquement une documentation interactive (Swagger UI).

| Service | URL de la documentation |
|---|---|
| Livres | http://localhost:8001/docs |
| Utilisateurs | http://localhost:8002/docs |
| Emprunts | http://localhost:8003/docs |

---

## Pipeline Jenkins

### Prérequis Jenkins
- Jenkins installé avec les plugins : Git, Docker Pipeline
- Le Jenkinsfile est **compatible Windows et Linux** (utilise `isUnix()` pour détecter l'OS)

### Configuration

1. Créer un nouveau job Jenkins de type **Pipeline**
2. Dans **Pipeline > Definition**, choisir **Pipeline script from SCM**
3. Renseigner l'URL GitHub du projet
4. Jenkins utilisera automatiquement le `Jenkinsfile` à la racine

### Étapes du pipeline

| Étape | Description |
|---|---|
| Récupération du code | Clone le dépôt GitHub |
| Vérification de la structure | Contrôle la présence des 12 fichiers essentiels |
| Build Docker | Construit les 4 images Docker |
| Arrêt ancienne version | Supprime les anciens conteneurs |
| Déploiement | Lance les nouveaux conteneurs |
| Vérification santé | Teste les endpoints `/health` des 3 services + frontend |
| Tests fonctionnels | Valide les APIs avec des requêtes POST et GET |

---

## Microservices - Endpoints

### Service Livres (port 8001)
| Méthode | Endpoint | Action |
|---|---|---|
| GET | `/livres` | Lister tous les livres |
| GET | `/livres/recherche?titre=...` | Rechercher par titre, auteur ou ISBN |
| GET | `/livres/{id}` | Détails d'un livre |
| POST | `/livres` | Ajouter un livre (avec quantité) |
| PUT | `/livres/{id}` | Modifier un livre |
| DELETE | `/livres/{id}` | Supprimer un livre |

### Service Utilisateurs (port 8002)
| Méthode | Endpoint | Action |
|---|---|---|
| POST | `/auth/register` | Inscription (avec confirmation mot de passe) |
| POST | `/auth/login` | Connexion (email + mot de passe) |
| GET | `/auth/me` | Profil de l'utilisateur connecté |
| POST | `/auth/changer-mot-de-passe` | Changer son mot de passe (obligatoire si temporaire) |
| GET | `/utilisateurs` | Lister tous les membres |
| GET | `/utilisateurs/type/{type}` | Filtrer par type (etudiant, professeur...) |
| GET | `/utilisateurs/{id}` | Détails d'un membre |
| POST | `/utilisateurs` | Créer un membre (admin, avec mot de passe temporaire) |
| PUT | `/utilisateurs/{id}` | Modifier un membre |
| PUT | `/utilisateurs/{id}/desactiver` | Désactiver un membre (conservation de l'historique) |
| DELETE | `/utilisateurs/{id}` | Supprimer définitivement un membre |

### Service Emprunts (port 8003)
| Méthode | Endpoint | Action |
|---|---|---|
| POST | `/emprunts` | Emprunter un livre (max 2 en cours, durée 15 jours) |
| PUT | `/emprunts/{id}/retour` | Enregistrer le retour d'un livre |
| GET | `/emprunts` | Historique complet des emprunts |
| GET | `/emprunts/en-cours` | Emprunts non retournés |
| GET | `/emprunts/retards` | Emprunts en retard |
| GET | `/emprunts/utilisateur/{id}` | Historique d'un membre |
