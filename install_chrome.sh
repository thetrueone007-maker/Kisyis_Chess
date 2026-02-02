#!/bin/bash
# Script pour installer Google Chrome sur Manjaro/Arch

echo "📥 Installation de Google Chrome sur Manjaro..."

# Méthode 1: Via yay (AUR)
if command -v yay &> /dev/null; then
    echo "Installation via yay..."
    yay -S google-chrome
else
    echo "⚠️  yay n'est pas installé. Installation manuelle..."

    # Méthode 2: Installation manuelle
    cd /tmp

    # Télécharger le paquet AUR
    git clone https://aur.archlinux.org/google-chrome.git
    cd google-chrome

    # Compiler et installer
    makepkg -si

    cd ..
    rm -rf google-chrome
fi

echo "✅ Installation terminée!"
echo "Redémarrez le terminal et relancez le script."
