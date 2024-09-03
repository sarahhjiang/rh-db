from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.exc import NoSuchTableError

# Update with your actual database URL
db_url = 'sqlite:///rh_app.db'
engine = create_engine(db_url)

metadata = MetaData()

# Reflect the existing database
metadata.reflect(bind=engine)

try:
    # Check if the table exists
    organization_program_table = Table('tblOrganizationProgram', metadata, autoload_with=engine)
    
    # Add the new 'status' column if it doesn't already exist
    if not hasattr(organization_program_table.c, 'status'):
        with engine.connect() as connection:
            connection.execute('ALTER TABLE tblOrganizationProgram ADD COLUMN status VARCHAR(50) DEFAULT "unfulfilled"')
        print("Status column added successfully.")
    else:
        print("Status column already exists.")
except NoSuchTableError:
    print("Table 'tblOrganizationProgram' does not exist.")
