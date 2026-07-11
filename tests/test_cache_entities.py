"""Pin tests for the entity-persistence split of the season cache.

The entity persistence layer (races / drivers / constructors / standings /
results upsert+select+get) lives in ``pitwall.cache.entities``;
``pitwall.cache.db`` re-exports the SAME function objects so every existing
``from pitwall.cache.db import ...`` call site keeps working.
"""

from pitwall.cache import db, entities

# Invariant: the full public entity-persistence surface moved in the split.
ENTITY_FUNCTIONS = (
    "upsert_races",
    "select_races",
    "upsert_drivers",
    "select_drivers",
    "get_driver",
    "upsert_constructors",
    "select_constructors",
    "get_constructor",
    "upsert_driver_standings",
    "select_driver_standings",
    "upsert_constructor_standings",
    "select_constructor_standings",
    "upsert_race_results",
    "select_race_results",
)


def test_entities_exposes_entity_persistence_functions():
    """pitwall.cache.entities exposes every moved entity-persistence function as a callable."""
    # Loop Bound: Constrained by the fixed ENTITY_FUNCTIONS tuple (PoT #2).
    for name in ENTITY_FUNCTIONS:
        assert callable(getattr(entities, name)), f"entities.{name} is not callable"


def test_db_reexports_entities_functions_as_same_objects():
    """pitwall.cache.db re-exports each entity-persistence function as the identical object."""
    # Loop Bound: Constrained by the fixed ENTITY_FUNCTIONS tuple (PoT #2).
    for name in ENTITY_FUNCTIONS:
        assert getattr(db, name) is getattr(entities, name), f"db.{name} is not entities.{name}"
