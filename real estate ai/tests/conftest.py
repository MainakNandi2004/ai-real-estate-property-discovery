import os
from collections.abc import Generator

from dotenv import load_dotenv

load_dotenv()
from decimal import Decimal

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Amenity,
    City,
    Locality,
    LocalityZoneLink,
    LocationZone,
    Project,
    ProjectAmenity,
    PropertyConfiguration,
    PropertyType,
)


def _database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", "")


@pytest.fixture(scope="session")
def engine():
    url = _database_url()
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set; integration tests need an isolated database")

    development_url = os.environ.get("DATABASE_URL")
    if development_url:
        test_target = make_url(url)
        development_target = make_url(development_url)
        if (
            test_target.host == development_target.host
            and test_target.port == development_target.port
            and test_target.database == development_target.database
        ):
            pytest.fail("TEST_DATABASE_URL must not point at the development database")

    eng = create_engine(url, pool_pre_ping=True, future=True)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", str(url).replace("%", "%%"))
    command.upgrade(alembic_cfg, "head")

    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(
        bind=connection,
        expire_on_commit=False,
        class_=Session,
        join_transaction_mode="create_savepoint",
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def sample_catalog(db_session: Session) -> dict:
    """Minimal non-branded catalog for automated tests only."""
    city = City(name="Test Metro", slug="test-metro", state="Test State", country="India")
    zone = LocationZone(city=city, name="Test South", slug="test-south")
    locality = Locality(city=city, name="Test Locality", slug="test-locality")
    db_session.add_all([city, zone, locality])
    db_session.flush()
    db_session.add(LocalityZoneLink(locality_id=locality.id, zone_id=zone.id))

    ptype = PropertyType(code="apartment", label="Apartment")
    parking = Amenity(code="parking", name="Parking")
    pool = Amenity(code="swimming_pool", name="Swimming Pool")
    db_session.add_all([ptype, parking, pool])
    db_session.flush()

    project = Project(
        name="Test Project Alpha",
        slug="test-project-alpha",
        locality_id=locality.id,
        property_type_id=ptype.id,
        project_status="under_construction",
        is_active=True,
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(ProjectAmenity(project_id=project.id, amenity_id=parking.id))

    configs = [
        PropertyConfiguration(
            project_id=project.id,
            label="2 BHK",
            bhk=Decimal("2"),
            area_value=Decimal("950"),
            area_unit="sqft",
            price=Decimal("6500000"),
            price_unit="total",
            availability_status="available",
            parking_included=True,
            sort_order=1,
            is_active=True,
        ),
        PropertyConfiguration(
            project_id=project.id,
            label="3 BHK",
            bhk=Decimal("3"),
            area_value=Decimal("1250"),
            area_unit="sqft",
            price=Decimal("9500000"),
            price_unit="total",
            availability_status="available",
            sort_order=2,
            is_active=True,
        ),
    ]
    db_session.add_all(configs)
    db_session.flush()

    return {
        "city": city,
        "zone": zone,
        "locality": locality,
        "project": project,
        "configs": configs,
        "amenity_parking": parking,
    }


@pytest.fixture
def postgres_available(engine) -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
