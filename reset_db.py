from run import app  # Import your Flask app instance
from models import db, User, State, Organization, OrganizationProgram, TrackerDonors, TrackerDonorDevices, DeviceModels, DeviceManufacturer
from datetime import datetime

# Flush and reload the database
with app.app_context():
    # Drop all existing tables
    print("Dropping all tables...")
    db.drop_all()

    # Recreate tables
    print("Recreating all tables...")
    db.create_all()

    # Optional: Seed the database with test data
    print("Seeding database with test data...")

    # Add states
    state = State(StateKey=1, StateName="Test State", StateAbbrev="TS")
    db.session.add(state)

    # Add an organization
    org = Organization(
        OrganizationKey=1,
        OrganizationName="Test Organization",
        OrganizationTypeKey="Non-Profit",
        OrganizationAddress1="123 Test Street",
        OrganizationCity="Test City",
        OrganizationStateKey=1,
        OrganizationZipCode="12345",
        OrganizationContactFirstName="John",
        OrganizationContactLastName="Doe",
        OrganizationContactEmailAddress="john.doe@example.com",
        OrganizationContactPhoneNumber="123-456-7890"
    )
    db.session.add(org)

    # Add a request for the organization
    request = OrganizationProgram(
        OrganizationProgramKey=1,
        OrganizationKey=1,
        OrganizationProgramDescription="Test Request Description",
        OrganizationProgramDateRequested=datetime.now(),
        OrganizationProgramTrackersNumberRequested=10
    )
    db.session.add(request)

    # Add a donor
    donor = TrackerDonors(
        TrackerDonorKey=1,
        TrackerDonorsFirstName="Jane",
        TrackerDonorsLastName="Smith",
        TrackerDonorsAddress1="456 Test Lane",
        TrackerDonorsCity="Testville",
        TrackerDonorsStateKey='NC',
        TrackerDonorsZipCode="67890"
    )
    db.session.add(donor)

    # Add a device model
    device_model = DeviceModels(
        DeviceModelKey=1,
        DeviceManufacturerKey=1,
        DeviceModelName="Test Device Model",
        DeviceCount=5
    )
    db.session.add(device_model)

    # Add a device manufacturer
    manufacturer = DeviceManufacturer(
        DeviceManufacturerKey=1,
        DeviceManufacturerName="Test Manufacturer"
    )
    db.session.add(manufacturer)

    # Add a device associated with the donor
    device = TrackerDonorDevices(
        TrackerDonorDevicesKey=1,
        TrackerDonorsKey=1,
        DeviceModelKey=1,
        TrackerDonationDateReceived=datetime.now()
    )
    db.session.add(device)

    # Commit changes to the database
    db.session.commit()

    print("Database reset and test data loaded.")