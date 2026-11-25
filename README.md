# BG3 Tactician AI

Prototype solo pour Baldur’s Gate 3. L’**Anneau du tacticien** donne au porteur deux commandes en français ou en anglais. En combat, **Déléguer le tour** confie un compagnon à l’IA de BG3. **Reprendre le contrôle** permet de le rejouer manuellement. La délégation expire aussi à la fin du combat. L’avatar reste aux commandes.

Ce premier prototype utilise les données du jeu, sans Script Extender ni MCM. Le choix des sorts, des cibles et des ressources appartient à l’IA native. Les rotations configurables par classe sont prévues pour une étape ultérieure.

## Installer le mod sur Mac

1. [Télécharge le paquet 1.0.0.1](https://raw.githubusercontent.com/richeju/bg3-tactician-ai/main/downloads/1.0.0.1/TacticianAI_6d136abe-15aa-4127-a699-f3a6b0df2d67.pak). Cette version apparaît dans le gestionnaire intégré sur macOS (Steam).
2. Quitte BG3. Si tu avais installé le premier prototype sous le nom `TacticianAI.pak`, déplace cet ancien fichier hors du dossier `Mods` avant d’y placer la nouvelle version. Conserve le nom du fichier téléchargé.
3. Dans le Finder, appuie sur **⌘⇧G** et colle `~/Documents/Larian Studios/Baldur's Gate 3/`. Ouvre le dossier `Mods` (crée-le si besoin) et dépose le fichier `.pak` directement dedans.
4. Lance BG3 depuis Steam. Dans le menu principal, ouvre le **Gestionnaire de mods**, va dans l’onglet des mods installés et coche **Tactician AI**.
5. Charge une copie de ta sauvegarde et rends-toi au camp. Récupère l’**Anneau du tacticien** dans le coffre du voyageur et équipe-le sur ton personnage.

Au tour du porteur, utilise **Déléguer le tour** sur un compagnon à 30 m ou moins qui doit encore agir. Pour le rejouer manuellement, utilise **Reprendre le contrôle**. Le déroulement des tours reste à confirmer en jeu sur ce prototype.
