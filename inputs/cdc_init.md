A# Cahier des Charges : Dashboard TUI de Suivi de Risque de Change

## 1. Contexte et Objectif
Développer une application terminal (TUI) interactive permettant de surveiller visuellement l'évolution de paires de devises étrangères.
*   **Public cible :** Investisseurs particuliers suivant des actifs à l'étranger.
*   **Usage :** Suivi de risque de change (medium/long terme), **pas** de trading intra-day.
*   **Philosophie :** Interface propre, graphique ("belles courbes" lissées, pas d'ASCII brut), modulaire et intuitive.

## 2. Stack Technique Imposée
*   **Langage :** Python 3.10+
*   **Framework TUI :** `textual` (pour la gestion des onglets, widgets, layout réactif).
*   **Graphiques :** Widgets natifs `textual` (LineChart) ou intégration légère de `matplotlib` (backend non-GUI) pour des courbes lissées professionnelles.
*   **Données (API) :** Uniquement des API **gratuites**, sans clé API obligatoire si possible.
    *   *Recommandé :* `Frankfurter.app` (données BCE, historique gratuit) ou `Currency-API` (GitHub).
    *   *Fréquence de mise à jour :* Suffisante pour du quotidien/hebdo (pas de WebSocket temps réel nécessaire).
*   **Dépendances principales :** `textual`, `requests`, `pandas` (optionnel pour le traitement data), `matplotlib` (si besoin).

## 3. Fonctionnalités Détaillées

### 3.1. Structure Générale
L'application doit comporter une interface à **onglets** :
1.  **Onglet "Dashboard" :** Vue principale avec la grille de widgets.
2.  **Onglet "Configuration" :** Gestion globale des préférences (devise de base, seuils d'alerte futurs).

### 3.2. Onglet "Dashboard" (Cœur du système)
*   **Layout :** Une grille dynamique (`Grid` dans Textual) accueillant des widgets de devises.
*   **Widget "Devise" (Unité de base) :**
    *   **Affichage :**
        *   En-tête : Nom de la paire (ex: `EUR/USD`).
        *   Indicateur : Taux actuel + Variation % (coloré vert/rouge).
        *   Corps : Graphique linéaire montrant l'historique (courbe lissée, axes lisibles).
    *   **Interactions (au clic ou via menu contextuel) :**
        *   **Modifier la paire :** Input pour changer les codes devises (ex: passer de `USD` à `JPY`).
        *   **Changer l'échelle de temps :** Boutons ou sélecteur pour : `7J`, `1M`, `6M`, `1A`, `5A`.
        *   **Supprimer :** Bouton pour retirer le widget de la grille.
*   **Ajout de widget :**
    *   Un bouton "+" visible en bas de grille ou dans une barre d'outils.
    *   Action : Ajoute un nouveau widget vide (ou avec des valeurs par défaut EUR/USD) à la grille.
    *   La grille doit s'adapter automatiquement (responsive).

### 3.3. Gestion des Données
*   **Récupération :** Appel asynchrone aux API gratuites au chargement et via un intervalle de temps (ex: toutes les 30 min ou 1h).
*   **Historique :** Capacité à fetcher l'historique selon l'échelle choisie (ex: points journaliers pour "1A", points horaires pour "7J" si l'API le permet).
*   **Gestion d'erreurs :** Affichage clair dans le widget si l'API est indisponible ou si la paire est invalide.

## 4. Spécifications Techniques & Contraintes

*   **Performance :** L'application doit rester fluide. Les appels API ne doivent pas bloquer la boucle d'événements (`async/await` requis).
*   **Design :**
    *   Utiliser le système de CSS de Textual pour un rendu moderne (bords arrondis, ombres légères si supporté, couleurs distinctes pour hausse/baisse).
    *   Les graphiques doivent être lisibles même dans un terminal de taille standard (80x24 minimum, idéalement 120x40).
*   **Configuration persistante (Optionnel mais recommandé) :** Sauvegarder la disposition des widgets et les paires choisies dans un fichier JSON local (`config.json`) pour les retrouver au prochain lancement.
*   **Code :**
    *   Architecture modulaire (séparer la logique de fetch des données, la définition des widgets, et l'application principale).
    *   Typage fort (Type hints) recommandé.
    *   Commentaires clairs sur les parties complexes (intégration graphique).

## 5. Livrable Attendu
1.  Le code source complet Python (fichier unique ou structure modulaire).
2.  Un fichier `requirements.txt`.
3.  Un court README expliquant comment lancer l'application et comment ajouter de nouvelles paires.
4.  **Impératif :** Le code doit être fonctionnel immédiatement avec les API gratuites citées (aucune configuration de clé API complexe requise pour le test de base).

---
*Note pour l'IA de codage : Prioriser la librairie `textual` version récente. Si le widget graphique natif est trop limité, utiliser `matplotlib` pour générer le graphique en mémoire et l'afficher dans un widget `Static` de Textual.*
