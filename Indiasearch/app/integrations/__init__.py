# app/integrations/__init__.py
# 🔌 Integrations Layer — External API Wrappers
# ----------------------------------------
# Each file in this package wraps ONE external service.
# Rules:
#   - Integrations are DUMB — they only send/receive HTTP, no logic.
#   - All business logic stays in services/.
#   - Each client handles its own auth headers and base URLs.
#   - Raise specific exceptions on API errors (not raw exceptions).
