# BG3 Tactician AI

L’**Anneau du tacticien** donne un seul sort, **Contrôle de l’IA**. Lance-le sur toi ou sur un compagnon à portée (30 m) pour activer son IA de combat. Relance le même sort sur la même cible pour la désactiver. Chaque personnage a son propre réglage. Le sort est gratuit et fonctionne aussi hors combat, sans Script Extender ni MCM.

Le statut **IA activée** indique qui jouera automatiquement au prochain combat. L’IA garde ce réglage d’un affrontement à l’autre. Entre les combats, tu contrôles ton personnage et peux changer d’avis. Si tu joues seul et que tu confies ton tour à l’IA, tu pourras repasser en manuel dès la sortie du combat.

## Capacités du personnage dans la version de test 1.1.1.0

Quand tu actives l’IA, le mod interroge BG3 sur le personnage ciblé. Son catalogue couvre **419 sorts et actions** du jeu de base. Il enregistre ceux que le personnage possède et, séparément, ceux que le moteur signale comme préparés. Chaque entrée a une catégorie principale parmi dégâts, contrôle, soins, soutien et utilité. Le mod vérifie aussi **385 passifs** de classe, de sous-classe ou de don et relève le score des armes principales de mêlée et à distance équipées.

Tu peux donc confier Ombrecœur à l’IA avec la classe, les sorts et l’équipement que tu lui as donnés. Un passif enregistré indique qu’elle le possède. Les bascules de passifs, les capacités propres à d’autres mods et les passifs exclusifs aux objets sortent du périmètre de ce premier catalogue.

Le mod actualise ces informations à la prise de contrôle en combat, au chargement du niveau et lors d’un changement d’équipement, d’une montée de niveau, d’une respécialisation ou de l’apprentissage d’un sort. Si tu modifies uniquement tes sorts préparés et veux voir le résultat avant le prochain combat, désactive puis réactive l’IA sur le personnage. La désactivation efface le relevé de cette cible.

## Décisions de combat

Le mod réévalue chaque personnage délégué à l’activation du contrôle et au début de ses tours. BG3 choisit ensuite l’action et sa cible parmi les possibilités qu’il sait utiliser. Les mêmes règles s’appliquent à Ombrecœur, à un avatar personnalisé et à un personnage qui vient de changer de classe.

- **Armes.** Le mod compare le score que BG3 donne à chaque arme équipée pour ce personnage. Si l’arme à distance est maîtrisée et dépasse de plus de 10 % le score de l’arme de mêlée, l’IA privilégie un peu plus la distance et la hauteur. Un arc seul peut aussi convenir. Un spécialiste du combat à mains nues peut garder sa position habituelle.
- **Soins.** Si le personnage a au plus un tiers de ses PV ou qu’un allié du même combat est à terre à portée, le mod recherche trois sorts préparés, *Mot de guérison*, *Soin des blessures* et *Guérison*. Il vérifie aussi l’action ou l’action bonus et l’emplacement nécessaires. Le soin prend alors plus de poids dans la décision. Un personnage qui connaît un soin peut continuer à se battre à l’arc tout le reste du temps.
- **Autres actions.** Les chances de toucher et l’interruption de la concentration ennemie pèsent davantage dans le choix du moteur. Les sorts offensifs, buffs, déplacements et attaques restent à sa disposition. L’anneau conserve son unique commande.

Les priorités personnalisées de cette version portent sur le placement à distance et les soins d’urgence. Le journal de combat donne l’action effectivement choisie par BG3. La validation de cette version en partie sur Mac reste à faire.

## Installer le mod sur Mac

1. Télécharge le [paquet de test 1.1.1.0](downloads/1.1.1.0/TacticianAI_6d136abe-15aa-4127-a699-f3a6b0df2d67.pak?raw=1). La [version stable 1.0.3.0](https://github.com/richeju/bg3-tactician-ai/releases/tag/v1.0.3.0) est aussi disponible.
2. Quitte BG3. Dans le Finder, appuie sur ⌘⇧G et ouvre `~/Documents/Larian Studios/Baldur's Gate 3/Mods/`. Copie le paquet dans ce dossier en remplaçant la version précédente. Garde un seul paquet Tactician AI dans ce dossier.
3. Relance BG3 et coche **Tactician AI** dans les mods installés avant de créer ou de charger ta partie.

## Où trouver l’anneau

- **Nouvelle partie** — Dès que tu contrôles ton personnage sur le Nautiloïde, ouvre son inventaire et équipe l’**Anneau du tacticien**. Le mod en attribue un à chaque avatar présent au démarrage, y compris un personnage d’origine comme Ombrecœur. L’attribution au réveil a été confirmée sur Mac avec la version 1.0.2.0.
- **Partie en cours** — Garde ton anneau si tu l’as déjà. Au besoin, déséquipe-le puis équipe-le à nouveau pour actualiser le sort dans ta barre de raccourcis. Si tu ne l’as pas encore récupéré, il t’attend dans le coffre du voyageur au camp. Le coffre propose aussi un exemplaire de secours dans les nouvelles parties.

La version [1.0.0.1](downloads/1.0.0.1/TacticianAI_6d136abe-15aa-4127-a699-f3a6b0df2d67.pak?raw=1) a été détectée en jeu sur Mac et l’anneau est apparu dans le coffre.

## Vérifier la bascule en jeu

Hors combat, équipe l’anneau et lance **Contrôle de l’IA** sur toi. Le statut **IA activée** doit apparaître, puis disparaître au deuxième lancement. Essaie ensuite sur un compagnon et vérifie que seul son statut change. Pour tester en solo, active l’IA avant le combat, laisse ton personnage jouer puis relance le sort sur toi après le combat. Le sort de la version 1.0.3.0 a été testé en jeu sur Mac.

## Vérifier ce que le mod a détecté

1. Hors combat, choisis un personnage qui peut préparer *Mot de guérison* et *Immobilisation de personne*, par exemple Ombrecœur en clerc de niveau 3. Prépare uniquement le premier des deux, équipe un arc, active l’IA et crée une sauvegarde A.
2. Remplace *Mot de guérison* par *Immobilisation de personne* dans les sorts préparés et change d’arme à distance. Désactive puis réactive l’IA et crée une sauvegarde B.
3. Pour lire les deux relevés, ouvre un terminal à la racine du dépôt. L’inspecteur ci-dessous est facultatif et lit les fichiers `.lsv` en lecture seule. Sur Mac, les sauvegardes se trouvent habituellement dans `~/Documents/Larian Studios/Baldur's Gate 3/PlayerProfiles/Public/Savegames/Story/`.

Avec Python 3.11 ou ultérieur, remplace les deux chemins par ceux des sauvegardes.

```sh
python3 -m venv .venv-inspection
. .venv-inspection/bin/activate
python -m pip install 'bg3-savefile-parser @ git+https://github.com/DanFinchUK/bg3-savefile-parser.git@9578ff7c46a1aa40c805f6b7beecf907f10fb3b8'
python tools/inspect_capabilities.py "/chemin/vers/A.lsv" > avant.json
python tools/inspect_capabilities.py "/chemin/vers/B.lsv" > apres.json
diff -u avant.json apres.json
```

Pour le même personnage, la liste `prepared_spells` doit passer de `Target_HealingWord` à `Target_HoldPerson` et `weapon_scores` doit refléter la nouvelle arme. Le score peut être identique entre deux armes. Le relevé donne aussi les capacités possédées dans `owned_spells` et les passifs reconnus dans `known_passives`. Le statut `detector_absent` indique une sauvegarde dépourvue des données du détecteur. Avec `no_saved_actors`, les tables existent mais aucun relevé de personnage n’est enregistré.

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

Les deux catalogues sont inclus dans le dépôt. Pour vérifier qu’ils correspondent aux données installées, donne le chemin du dossier contenant `Shared.pak`, `Gustav.pak` et `GustavX.pak` aux commandes suivantes. Retire `--check` pour les régénérer après une mise à jour de BG3.

```sh
python tools/generate_capabilities.py --game-data "/chemin/vers/Data" --check
python tools/generate_passives.py "/chemin/vers/Data" --check
```

## Références de développement

- Les notes de l’auteur d’[AI Friends](https://www.nexusmods.com/baldursgate3/mods/705?tab=docs) documentent les indicateurs de contrôle allié utilisés pour ce prototype.
- Le guide de [Larian](https://baldursgate3.game/mods-how-to/) présente le gestionnaire de mods en jeu.
