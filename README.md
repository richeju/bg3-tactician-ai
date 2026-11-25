# BG3 Tactician AI

Prototype solo pour Baldur’s Gate 3. L’**Anneau du tacticien** donne au porteur deux commandes en français ou en anglais. En combat, **Déléguer le tour** confie un compagnon à l’IA de BG3. **Reprendre le contrôle** permet de le rejouer manuellement. La délégation expire aussi à la fin du combat. L’avatar reste aux commandes.

Ce premier prototype utilise les données du jeu, sans Script Extender ni MCM. Le choix des sorts, des cibles et des ressources appartient à l’IA native. Les rotations configurables par classe sont prévues pour une étape ultérieure.

## Essayer sur Mac

1. Télécharge l’artefact **TacticianAI** d’une compilation réussie dans GitHub Actions et décompresse le ZIP. Tu peux aussi compiler le projet avec les commandes ci-dessous.
2. Jeu fermé, copie `TacticianAI.pak` dans `~/Documents/Larian Studios/Baldur's Gate 3/Mods/`. Crée le dossier `Mods` si nécessaire.
3. Active **Tactician AI** dans l’onglet des mods installés du gestionnaire intégré. Charge une copie de sauvegarde où tu as accès au camp.
4. Ouvre le coffre du voyageur et équipe l’anneau sur ton personnage. Au tour du porteur, utilise **Déléguer le tour** sur un compagnon à 30 m ou moins qui doit encore agir. Laisse passer son tour puis utilise **Reprendre le contrôle** au prochain tour du porteur.

## Vérification en jeu

- Vérifie que l’avatar, un ennemi et une invocation ne peuvent pas être délégués.
- Délègue un seul compagnon et vérifie que les autres restent manuels. Regarde qui choisit ses actions et si son tour se termine.
- Reprends le contrôle avant le prochain tour du compagnon. Délègue-le une seconde fois, termine le combat, puis vérifie que son premier tour au combat suivant est manuel.
- Essaie une sauvegarde et un rechargement pendant la délégation. Pour revenir à l’état initial, recharge la copie conservée avant l’activation du mod.

## Compiler

Depuis la racine du dépôt, avec Python 3.10 ou ultérieur :

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install bg3forge==0.2.0
python tools/check.py
python tools/build.py
```

Le script compile les traductions et le modèle de l’anneau, crée `dist/TacticianAI.pak`, puis extrait et compare son contenu aux fichiers préparés pour le jeu. Les tests en combat se font dans BG3.

## Références de développement

- Les notes de l’auteur d’[AI Friends](https://www.nexusmods.com/baldursgate3/mods/705?tab=docs) documentent les indicateurs de contrôle allié utilisés pour ce prototype.
- Le guide de [Larian](https://baldursgate3.game/mods-how-to/) présente le gestionnaire de mods en jeu.
