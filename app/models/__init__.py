"""Agent input/output contracts (Pydantic).

These are runtime analysis contracts for agents and the CLI. They are not
SQLAlchemy persistence models (``app.db.models``) and are not the future
CV/LinkedIn ingestion payload.
"""

from app.models.profile import ExperienceItem, ProfileAnalysis, ProfileInput

__all__ = ["ExperienceItem", "ProfileAnalysis", "ProfileInput"]
