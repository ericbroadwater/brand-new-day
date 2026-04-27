#!/usr/bin/env bash
# Brand New Day installer — STUB.
#
# The real installer ships in Phase 1.5d. For the alpha, this is a placeholder
# so the README can reference `./install.sh` without 404-ing. The manual steps
# below work today.

set -euo pipefail

cat <<'EOF'
Brand New Day — Installer (stub)
================================

The automated installer lands in Phase 1.5d. For now, install manually:

  1. Choose your runtime directory, e.g. ~/brand-new-day
  2. Copy runtime contents into it:
        mkdir -p ~/brand-new-day/data
        cp -r runtime/* ~/brand-new-day/
        mv ~/brand-new-day/config.yml.example ~/brand-new-day/config.yml
        mv ~/brand-new-day/profile.md.example ~/brand-new-day/profile.md
        mv ~/brand-new-day/dashboard-template.html ~/brand-new-day/dashboard.html

  3. Copy the skill to Claude Code:
        cp -r skill ~/.claude/skills/brand-new-day

  4. Copy .env.example to ~/brand-new-day/.env and add your RAPIDAPI_KEY

  5. Set BND_HOME in your shell:
        export BND_HOME=~/brand-new-day

  6. Edit profile.md with your career context, then run /brand-new-day
     in Claude Code.

See README.md for full setup, cron configuration, and troubleshooting.
EOF
