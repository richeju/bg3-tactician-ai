# BG3 Tactician AI

L’**Anneau du tacticien** donne trois commandes de combat en français et en anglais. **Déléguer mon tour** vise le porteur, y compris un avatar qui joue seul. La commande ne coûte ni action ni action bonus. Son statut confie le reste du tour à l’IA native et expire à la fin du tour ou du combat.

**Déléguer le tour** permet toujours de choisir un compagnon à 30 m ou moins. Cette délégation dure jusqu’à la fin du combat ou jusqu’à l’utilisation de **Reprendre le contrôle**. Le mod fonctionne sans Script Extender ni MCM.

## Installer le mod sur Mac

1. Télécharge le [paquet de test 1.0.2.0](downloads/1.0.2.0/TacticianAI_6d136abe-15aa-4127-a699-f3a6b0df2d67.pak?raw=1).
2. Quitte BG3. Dans le Finder, appuie sur ⌘⇧G et ouvre `~/Documents/Larian Studios/Baldur's Gate 3/Mods/`. Copie le paquet dans ce dossier en remplaçant la version précédente. Garde un seul paquet Tactician AI dans ce dossier.
3. Relance BG3 et coche **Tactician AI** dans les mods installés avant de créer ou de charger ta partie.

## Où trouver l’anneau

- **Nouvelle partie** — Dès que tu contrôles ton personnage sur le Nautiloïde, ouvre son inventaire et équipe l’**Anneau du tacticien**. Le mod en attribue un à chaque avatar présent au démarrage, y compris un personnage d’origine comme Ombrecœur. Tu peux ainsi essayer **Déléguer mon tour** dès le premier combat. L’attribution sur le Nautiloïde reste à confirmer en jeu sur Mac.
- **Partie en cours** — Garde ton anneau si tu l’as déjà. Au besoin, déséquipe-le puis équipe-le à nouveau pour actualiser ses commandes. Si tu ne l’as pas encore récupéré, il t’attend dans le coffre du voyageur au camp. Le coffre propose aussi un exemplaire de secours dans les nouvelles parties.

La version [1.0.0.1](downloads/1.0.0.1/TacticianAI_6d136abe-15aa-4127-a699-f3a6b0df2d67.pak?raw=1) a été détectée en jeu sur Mac et l’anneau est apparu dans le coffre.

## Tester un tour solo

Équipe l’anneau sur ton avatar et entre en combat. Au début de son tour, avec une cible accessible et une action disponible, lance **Déléguer mon tour**. Laisse le jeu dérouler le tour. Vérifie si l’IA agit immédiatement, si le statut disparaît en fin de tour et si tu peux choisir ta première action au tour suivant. La compilation vérifie les données du mod. La prise de contrôle d’un avatar dont le tour a déjà commencé reste à confirmer dans BG3.

## Compiler

Depuis la racine du dépôt, avec Python 3.10 ou ultérieur et la bibliothèque native LZ4 1.11.1. Sur Mac, Homebrew fournit la formule `lz4`.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install bg3forge==0.2.0
python tools/check.py
python tools/build.py
shasum -a 256 dist/TacticianAI.pak
```

Le script compile les traductions et les métadonnées de l’interface, vérifie que le modèle binaire de l’anneau correspond à son XML, puis relit chaque fichier du paquet. Le modèle du projet a été compilé avec LSLib v1.20.4. Après une modification du XML du modèle, exécute `tools/compile-template.ps1 -Divine <chemin-vers-divine.exe>` sous Windows pour mettre à jour la copie de `compiled/`.

## Références de développement

- Les notes de l’auteur d’[AI Friends](https://www.nexusmods.com/baldursgate3/mods/705?tab=docs) documentent les indicateurs de contrôle allié utilisés pour ce prototype.
- Le guide de [Larian](https://baldursgate3.game/mods-how-to/) présente le gestionnaire de mods en jeu.
