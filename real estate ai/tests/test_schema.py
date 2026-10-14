from sqlalchemy import inspect

EXPECTED_TABLES = {
    "cities",
    "location_zones",
    "localities",
    "locality_zone_links",
    "property_types",
    "projects",
    "property_configurations",
    "units",
    "amenities",
    "project_amenities",
    "configuration_amenities",
    "project_images",
    "configuration_floor_plans",
    "project_nearby_places",
    "project_rera_entries",
    "conversations",
    "conversation_messages",
    "leads",
    "lead_project_interests",
    "site_visits",
}


def test_all_tables_exist(engine):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Missing tables: {sorted(missing)}"


def test_project_configuration_fk(engine):
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("property_configurations")
    targets = {fk["referred_table"] for fk in fks}
    assert "projects" in targets
