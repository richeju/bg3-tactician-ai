# BG3 Tactician AI

L’**Anneau du tacticien** donne un seul sort, **Contrôle de l’IA**. Lance-le sur toi ou sur un compagnon à portée (30 m) pour activer son IA de combat. Relance le même sort sur la même cible pour la désactiver. Chaque personnage a son propre réglage. Le sort est gratuit et fonctionne aussi hors combat, sans Script Extender ni MCM.

Le statut **IA activée** indique qui jouera automatiquement au prochain combat. L’IA garde ce réglage d’un affrontement à l’autre. Entre les combats, tu contrôles ton personnage et peux changer d’avis. Si tu joues seul et que tu confies ton tour à l’IA, tu pourras repasser en manuel dès la sortie du combat.

## Décisions de combat dans la version de test 1.1.0.0

Le mod réévalue chaque personnage délégué à l’activation du contrôle et au début de ses tours. BG3 choisit ensuite l’action et sa cible parmi les possibilités qu’il sait utiliser. Les mêmes règles s’appliquent à Ombrecœur, à un avatar personnalisé et à un personnage qui vient de changer de classe.

- **Armes.** Le mod compare le score que BG3 donne à chaque arme équipée pour ce personnage. Si l’arme à distance est maîtrisée et dépasse de plus de 10 % le score de l’arme de mêlée, l’IA privilégie un peu plus la distance et la hauteur. Un arc seul peut aussi convenir. Un spécialiste du combat à mains nues peut garder sa position habituelle.
- **Soins.** Si le personnage a au plus un tiers de ses PV ou qu’un allié du même combat est à terre à portée, le mod recherche trois sorts préparés, *Mot de guérison*, *Soin des blessures* et *Guérison*. Il vérifie aussi l’action ou l’action bonus et l’emplacement nécessaires. Le soin prend alors plus de poids dans la décision. Un personnage qui connaît un soin peut continuer à se battre à l’arc tout le reste du temps.
- **Autres actions.** Les chances de toucher et l’interruption de la concentration ennemie pèsent davantage dans le choix du moteur. Les sorts offensifs, buffs, déplacements et attaques restent à sa disposition. L’anneau conserve son unique commande.

Pour comparer sur Mac, reprends une sauvegarde avant combat avec Ombrecœur équipée d’un arc et *Mot de guérison* préparé. Observe d’abord son choix avec le groupe en bonne santé, puis lorsqu’un allié à portée tombe à terre. Recommence sans le sort préparé. Le journal de combat donne l’action effectivement choisie. Cette version est à tester en jeu.

## Installer le mod sur Mac

1. Télécharge le [paquet de test 1.1.0.0](downloads/1.1.0.0/TacticianAI_6d136abe-15aa-4127-a699-f3a6b0df2d67.pak?raw=1). La [version stable 1.0.3.0](https://github.com/richeju/bg3-tactician-ai/releases/tag/v1.0.3.0) est aussi disponible.
2. Quitte BG3. Dans le Finder, appuie sur ⌘⇧G et ouvre `~/Documents/Larian Studios/Baldur's Gate 3/Mods/`. Copie le paquet dans ce dossier en remplaçant la version précédente. Garde un seul paquet Tactician AI dans ce dossier.
3. Relance BG3 et coche **Tactician AI** dans les mods installés avant de créer ou de charger ta partie.

## Où trouver l’anneau

- **Nouvelle partie** — Dès que tu contrôles ton personnage sur le Nautiloïde, ouvre son inventaire et équipe l’**Anneau du tacticien**. Le mod en attribue un à chaque avatar présent au démarrage, y compris un personnage d’origine comme Ombrecœur. L’attribution au réveil a été confirmée sur Mac avec la version 1.0.2.0.
- **Partie en cours** — Garde ton anneau si tu l’as déjà. Au besoin, déséquipe-le puis équipe-le à nouveau pour actualiser le sort dans ta barre de raccourcis. Si tu ne l’as pas encore récupéré, il t’attend dans le coffre du voyageur au camp. Le coffre propose aussi un exemplaire de secours dans les nouvelles parties.

La version [1.0.0.1](downloads/1.0.0.1/TacticianAI_6d136abe-15aa-4127-a699-f3a6b0df2d67.pak?raw=1) a été détectée en jeu sur Mac et l’anneau est apparu dans le coffre.

## Vérifier la bascule en jeu

Hors combat, équipe l’anneau et lance **Contrôle de l’IA** sur toi. Le statut **IA activée** doit apparaître, puis disparaître au deuxième lancement. Essaie ensuite sur un compagnon et vérifie que seul son statut change. Pour tester en solo, active l’IA avant le combat, laisse ton personnage jouer puis relance le sort sur toi après le combat. Le sort de la version 1.0.3.0 a été testé en jeu sur Mac.

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
