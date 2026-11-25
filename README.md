# BG3 Tactician AI

Prototype solo pour Baldur’s Gate 3. L’**Anneau du tacticien** donne au porteur deux commandes en français ou en anglais. En combat, **Déléguer le tour** confie un compagnon à l’IA de BG3. **Reprendre le contrôle** permet de le rejouer manuellement. La délégation expire aussi à la fin du combat. L’avatar reste aux commandes.

Ce premier prototype utilise les données du jeu, sans Script Extender ni MCM. Le choix des sorts, des cibles et des ressources appartient à l’IA native. Les rotations configurables par classe sont prévues pour une étape ultérieure.

## Installer le mod sur Mac

1. Connecte-toi à GitHub et [télécharge TacticianAI.zip](https://github.com/richeju/bg3-tactician-ai/actions/runs/45623202651/artifacts/15027750410). Pour une version plus récente, ouvre une [compilation réussie](https://github.com/richeju/bg3-tactician-ai/actions?query=workflow%3A%22Build+BG3+mod%22) et clique sur **TacticianAI** dans la section **Artifacts**.
2. Quitte BG3 et décompresse le ZIP. Tu y trouveras le fichier `TacticianAI.pak`.
3. Dans le Finder, appuie sur **⌘⇧G** et colle `~/Documents/Larian Studios/Baldur's Gate 3/`. Ouvre le dossier `Mods` (crée-le si besoin) et dépose le fichier `.pak` directement dedans.
4. Lance BG3 depuis Steam. Dans le menu principal, ouvre le **Gestionnaire de mods**, va dans l’onglet des mods installés et coche **Tactician AI**.
5. Charge une copie de ta sauvegarde et rends-toi au camp. Récupère l’**Anneau du tacticien** dans le coffre du voyageur et équipe-le sur ton personnage.

Au tour du porteur, utilise **Déléguer le tour** sur un compagnon à 30 m ou moins qui doit encore agir. Pour le rejouer manuellement, utilise **Reprendre le contrôle**. Le déroulement des tours reste à confirmer en jeu sur ce prototype.
