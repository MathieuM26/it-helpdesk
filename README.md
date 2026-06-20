# 🖥️ IT Helpdesk

Application web de **gestion de tickets** pour un service informatique (I.T.), développée avec **Flask** (Python).
Elle permet aux utilisateurs de signaler des incidents et aux techniciens de les suivre, les assigner et les résoudre.

---

## ✨ Fonctionnalités

- 🔐 **Authentification** avec 3 rôles : utilisateur, technicien, administrateur
- 🎫 **Création et suivi de tickets** (titre, description, catégorie, priorité)
- 📊 **Tableau de bord** avec statistiques en temps réel et filtres (statut, priorité, catégorie, recherche)
- 💬 **Commentaires** sur chaque ticket
- 🕓 **Historique** complet des actions sur un ticket
- 👷 **Actions technicien** : changement de statut, assignation
- 👤 **Administration des utilisateurs** (création, modification, rôles)
- 📱 Interface **responsive**

---

## 🚀 Installation et lancement

### Prérequis
- Python 3.x

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/MathieuM26/it-helpdesk.git
cd it-helpdesk

# 2. Installer les dépendances
pip install flask flask-login werkzeug

# 3. Lancer l'application
python app.py
```

Puis ouvrir le navigateur sur 👉 **http://127.0.0.1:5000**

La base de données (`tickets.db`) est créée automatiquement au premier lancement.

---

## 👥 Comptes de démonstration

| Identifiant | Mot de passe | Rôle           |
|-------------|--------------|----------------|
| `admin`     | `admin123`   | Administrateur |
| `tech1`     | `tech123`    | Technicien     |
| `user1`     | `user123`    | Utilisateur    |

---

## 🗂️ Structure du projet

```
it-helpdesk/
├── app.py                  # Serveur Flask : routes, base de données, authentification
├── tickets.db              # Base SQLite (générée automatiquement)
├── static/
│   ├── css/style.css       # Styles de l'interface
│   └── js/app.js           # Filtres dynamiques du tableau de bord
└── templates/
    ├── base.html           # Mise en page commune (navbar)
    ├── login.html          # Page de connexion
    ├── dashboard.html      # Tableau de bord + liste des tickets
    ├── ticket_form.html    # Création / modification d'un ticket
    ├── ticket_detail.html  # Détail d'un ticket + commentaires + historique
    ├── admin_users.html    # Liste des utilisateurs
    └── admin_user_form.html# Création / modification d'un utilisateur
```

---

## 🛠️ Technologies

- **Python / Flask** — serveur web
- **Flask-Login** — gestion des sessions
- **SQLite** — base de données
- **Werkzeug** — hachage sécurisé des mots de passe
- **HTML / CSS / JavaScript** — interface

---

## 📌 Catégories et priorités

**Catégories :** Matériel · Logiciel · Réseau · Accès / Droits · Imprimante · Email · Sécurité · Autre

**Priorités :** Critique · Haute · Moyenne · Basse

**Statuts :** Ouvert · En cours · En attente · Résolu · Fermé

---

> Projet réalisé dans le cadre du Bachelier en Informatique.
