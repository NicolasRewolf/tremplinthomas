#!/bin/bash
# ─────────────────────────────────────────────
# REWOLF Starter — Bootstrap Script
# Usage: bash scripts/setup.sh   (depuis la racine du repo)
# ─────────────────────────────────────────────

set -e

echo ""
echo "▸ REWOLF Starter — Installation"
echo ""

# Install dependencies
echo "→ npm install..."
npm install

# Add shadcn/ui components
echo "→ shadcn/ui components..."
npx shadcn@latest add card badge button table tabs dialog dropdown-menu tooltip --yes

echo ""
echo "✓ Setup terminé."
echo ""
echo "  npm run dev    → démarrer le serveur"
echo "  npm run build  → build production"
echo ""
