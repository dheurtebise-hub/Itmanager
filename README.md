# 🎫 IT Ticket Manager

Application Windows Desktop autonome pour la gestion des tickets de support IT.

## 🎯 Fonctionnalités

- **Import automatique** depuis Outlook
- **Catégorisation intelligente** via IA (Claude)
- **Interface Kanban** intuitive type Trello
- **Suggestions de résolution** basées sur l'historique
- **Gestion SLA** avec alertes
- **Templates email** personnalisables
- **Export** CSV/Excel
- **Mode sombre**
- **Installation** en 3 clics

## 🏗️ Stack Technique

- **Backend** : Python 3.11+ avec Flask
- **Frontend** : HTML/CSS/JavaScript (Vanilla)
- **Base de données** : SQLite
- **IA** : API Anthropic (Claude Haiku + Sonnet)
- **Email** : pywin32 (COM Automation Outlook)
- **Distribution** : PyInstaller + Inno Setup

## 📦 Installation

### Pour les utilisateurs

1. Téléchargez `ITTicketManagerSetup.exe`
2. Exécutez l'installeur
3. Suivez le wizard de configuration
4. C'est prêt !

### Pour les développeurs

```bash
# Cloner le repository
git clone https://github.com/dheurtebise-hub/Itmanager.git
cd Itmanager

# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python src/main.py
```

## 🔧 Configuration

Au premier lancement, un wizard vous guide :

1. **Clé API Claude** : Entrez votre clé API Anthropic
2. **Configuration Outlook** : Sélectionnez les dossiers à surveiller
3. **Personnalisation** : Catégories, thème, notifications
4. **Finalisation** : Première synchronisation

## 📚 Documentation

- [Guide utilisateur](docs/user_guide.md)
- [Guide développeur](docs/developer_guide.md)
- [API Reference](docs/api_reference.md)

## 🧪 Tests

```bash
pytest tests/
```

## 📦 Build

```bash
# Installer les dépendances de build
pip install -r requirements-build.txt

# Créer l'exécutable
pyinstaller build_config.spec

# Créer l'installeur (nécessite Inno Setup)
cd installer
build_installer.bat
```

## 📄 Licence

MIT License - voir [LICENSE](LICENSE)

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez [CONTRIBUTING.md](CONTRIBUTING.md)

## 📧 Contact

Pour toute question : [issues](https://github.com/dheurtebise-hub/Itmanager/issues)
