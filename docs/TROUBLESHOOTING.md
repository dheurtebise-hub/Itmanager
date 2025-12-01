# 🔧 Guide de Dépannage - IT Ticket Manager

## Problèmes de Synchronisation des Emails

### ❌ Les emails ne remontent pas lors de la synchronisation

**Causes possibles :**

1. **Les emails sont déjà marqués comme lus**
   - Par défaut, l'application cherchait uniquement les emails **non lus**
   - ✅ **Solution** : Utilisez le bouton **"📥 Import initial"** dans le header

2. **Le dossier Outlook n'est pas correctement configuré**
   - Vérifiez que le dossier sélectionné contient bien des emails
   - Allez dans Paramètres → Vérifier la configuration Outlook

3. **Outlook n'est pas ouvert**
   - L'application utilise COM pour accéder à Outlook
   - ✅ **Solution** : Ouvrez Outlook Desktop avant de synchroniser

### 📥 Comment faire un import initial ?

1. Cliquez sur le bouton **"📥 Import initial"** (en haut à droite)
2. Confirmez l'import (max 50 emails récents)
3. Attendez quelques secondes (peut prendre 1-2 minutes selon le nombre d'emails et l'IA)
4. Les tickets apparaissent dans les colonnes du Kanban

**Note** : L'import initial récupère **tous** les emails récents, qu'ils soient lus ou non lus.

### 🔄 Différence entre "Synchroniser" et "Import initial"

| Fonctionnalité | Synchroniser | Import initial |
|----------------|--------------|----------------|
| Emails importés | **Nouveaux uniquement** (non lus) | **Tous les récents** (50 max) |
| Fréquence | À chaque clic ou automatique | Une fois au début |
| Durée | Rapide (quelques secondes) | Plus long (1-2 minutes) |

## Vérification des Logs

### Où trouver les logs ?

**Emplacement** : `%APPDATA%\ITTicketManager\logs\`

Exemple : `C:\Users\VotreNom\AppData\Roaming\ITTicketManager\logs\app_20251201.log`

### Que vérifier dans les logs ?

```json
// Recherchez ces lignes :
"Dossier 'Support': X emails récupérés"
"Total: X emails récupérés de tous les dossiers"
"Synchronisation terminée: X nouveaux tickets"
```

Si vous voyez `0 emails récupérés`, c'est que :
- Soit tous vos emails sont marqués comme lus
- Soit le dossier est vide
- Soit il y a un problème de connexion Outlook

### Logs d'erreur typiques

**Erreur : "Le dossier 'Support' n'existe pas"**
```
✅ Solution : Vérifiez le nom exact du dossier dans Outlook
```

**Erreur : "Impossible de se connecter à Outlook"**
```
✅ Solution : Ouvrez Outlook Desktop et réessayez
```

**Erreur : "Clé API non configurée"**
```
✅ Solution : Allez dans Paramètres → Reconfigurer la clé Claude API
```

## Problèmes de Catégorisation IA

### Les tickets ne sont pas catégorisés

**Vérifications :**

1. **Clé API Claude valide ?**
   - Allez dans Paramètres
   - Testez la connexion IA

2. **Budget API dépassé ?**
   - Vérifiez votre dashboard Anthropic
   - Consultez les coûts dans l'application (barre en bas)

3. **Règles simples activées ?**
   - L'application utilise des règles simples en fallback si l'IA échoue
   - Vérifiez les logs pour voir si `ai_categorized = False`

## Problèmes d'Interface

### Le Kanban est vide après sync

**Causes :**

1. **Aucun nouveau ticket créé**
   - Vérifiez les logs : "X nouveaux tickets, Y ignorés"
   - Les emails déjà importés sont ignorés (duplicate detection)

2. **Tickets existants mais pas visibles**
   - Rafraîchissez la page (F5)
   - Vérifiez les filtres (catégorie, priorité)
   - Videz le champ de recherche

### Les notifications ne s'affichent pas

**Solutions :**

1. Vérifiez les paramètres Windows (Notifications désactivées ?)
2. Allez dans Paramètres → Activer les notifications
3. Redémarrez l'application

## Performance & Optimisation

### La synchronisation est lente

**Optimisations :**

1. **Réduisez la limite d'import**
   - Par défaut : 50 emails max
   - Pour tester : modifiez `import_limit` dans le code

2. **Utilisez seulement les nouveaux emails**
   - Après l'import initial, utilisez "Synchroniser" (bouton 🔄)
   - Ne pas ré-utiliser "Import initial" à chaque fois

3. **Désactivez la catégorisation IA temporairement**
   - Modifiez le code pour utiliser uniquement les règles simples

### Base de données trop volumineuse

**Solutions :**

1. **Supprimez les vieux tickets fermés**
   ```sql
   DELETE FROM tickets WHERE status = 'closed' AND resolved_at < date('now', '-6 months');
   ```

2. **Archivez les anciens tickets**
   - Exportez en CSV/Excel
   - Supprimez de la BDD

3. **Vacuum la base**
   ```python
   from models.database import db
   db.vacuum()
   ```

## Checklist de Diagnostic

Utilisez cette checklist pour diagnostiquer les problèmes :

```
□ Outlook Desktop est ouvert
□ Le dossier configuré existe dans Outlook
□ Le dossier contient des emails
□ La clé API Claude est configurée
□ La clé API Claude est valide (testée)
□ L'application a accès à Internet
□ Les logs ne montrent pas d'erreur
□ J'ai essayé le bouton "Import initial"
□ J'ai rafraîchi la page (F5)
□ J'ai redémarré l'application
```

## Commandes de Debug

### Tester la connexion Outlook (PowerShell)

```powershell
$outlook = New-Object -ComObject Outlook.Application
$namespace = $outlook.GetNamespace("MAPI")
$inbox = $namespace.GetDefaultFolder(6)
$inbox.Folders | Select-Object Name, @{N='Count';E={$_.Items.Count}}
```

### Vérifier la base de données

```bash
# Ouvrir la BDD
cd %APPDATA%\ITTicketManager\database
sqlite3 tickets.db

# Compter les tickets
SELECT status, COUNT(*) FROM tickets GROUP BY status;

# Vérifier les derniers imports
SELECT subject, created_at FROM tickets ORDER BY created_at DESC LIMIT 10;
```

### Tester l'API Claude manuellement

```python
import anthropic

client = anthropic.Anthropic(api_key="VOTRE_CLE")
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=10,
    messages=[{"role": "user", "content": "Test"}]
)
print(response.content[0].text)
```

## Support Avancé

### Réinitialiser complètement l'application

**⚠️ ATTENTION : Cela supprime toutes les données**

1. Fermez l'application
2. Supprimez le dossier : `%APPDATA%\ITTicketManager`
3. Relancez l'application
4. Recommencez le setup wizard

### Réinitialiser uniquement la config (garder les données)

1. Fermez l'application
2. Supprimez : `%APPDATA%\ITTicketManager\config.json`
3. Relancez (le wizard redemarre)
4. Les tickets existants restent dans la BDD

### Mode Debug

Pour activer plus de logs :

1. Éditez `src/utils/logger.py`
2. Changez `level=logging.INFO` en `level=logging.DEBUG`
3. Relancez l'application
4. Consultez les logs détaillés

## FAQ

**Q : Combien d'emails puis-je importer ?**
R : Par défaut 50 max par dossier. Modifiable dans le code (`import_limit`).

**Q : Les emails sont-ils supprimés d'Outlook ?**
R : Non, jamais. L'application lit uniquement, ne modifie pas (sauf si `mark_as_read=True`).

**Q : Puis-je importer depuis plusieurs dossiers ?**
R : Oui ! Configurez plusieurs dossiers dans le setup Outlook.

**Q : L'IA fonctionne hors-ligne ?**
R : Non, l'IA nécessite Internet. Mais les règles simples fonctionnent hors-ligne.

**Q : Combien coûte l'IA par mois ?**
R : Pour ~1000 emails/mois : environ 0.20€/mois. Budget recommandé : 3-5€/mois.

**Q : Puis-je désactiver l'IA ?**
R : Oui, mais elle ne catégorisera plus automatiquement. Utilisez les règles simples.

## Contact & Bugs

Pour signaler un bug ou demander de l'aide :

1. **Vérifiez d'abord ce guide**
2. **Consultez les logs** (`%APPDATA%\ITTicketManager\logs\`)
3. **Ouvrez une issue** sur GitHub avec :
   - Description du problème
   - Logs pertinents (masquez les infos sensibles)
   - Étapes pour reproduire
   - Version de l'application

---

**Dernière mise à jour** : 2025-12-01
**Version** : 1.0.1
