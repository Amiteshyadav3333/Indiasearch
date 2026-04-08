# app/services/__init__.py
# ⚡ Services Layer — Business Logic (MAIN BRAIN)
# ----------------------------------------
# Services contain ALL domain logic.
# They are called by routes and call integrations/cache.
#
# Rule: Services NEVER import from routes.
#       Services CAN import from integrations, cache, models, utils.
