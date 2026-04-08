# app/routes/__init__.py
# 🔥 API Layer — Thin Controllers
# ----------------------------------------
# Routes are thin controllers. They ONLY:
#   1. Accept request input (parse JSON / query params)
#   2. Call the corresponding service
#   3. Return formatted response via response_formatter
#
# NO business logic should live here.
