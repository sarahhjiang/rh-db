from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import pandas as pd
import os
from APIkeys import polygonAPIkey
from polygon import RESTClient
from datetime import datetime
import geopandas as gpd
import matplotlib.pyplot as plt
from io import BytesIO
from plotting import plot_donors_per_state

from models import db, ma, bcrypt, User, Organization, OrganizationProgram, Communication, CommunicationType, State, TrackerDonors, TrackerDonorDevices, DeviceModels, DeviceManufacturer

basedir = os.path.abspath(os.path.dirname(__file__))

# Create flask app instance
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'rh_app.db')
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)
ma.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Create client and authenticate w/ API key
client = RESTClient(polygonAPIkey)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables/db file
with app.app_context():
    db.create_all()

# Search page route
@app.route('/search')
@login_required
def search():
    return render_template('search.html')

# Search results route
@app.route('/search_results', methods=['GET'])
@login_required
def search_results():
    query = request.args.get('query')
    search_type = request.args.get('search_type')

    if not query or not search_type:
        return redirect(url_for('search'))

    results = []
    if search_type == 'donors':
        results = TrackerDonors.query.filter(
            (TrackerDonors.TrackerDonorsFirstName.ilike(f'%{query}%')) |
            (TrackerDonors.TrackerDonorsLastName.ilike(f'%{query}%'))
        ).all()
        print(f"Donors search results for '{query}': {results}")
    elif search_type == 'organizations':
        results = Organization.query.filter(
            Organization.OrganizationName.ilike(f'%{query}%')
        ).all()
        print(f"Organizations search results for '{query}': {results}")
    elif search_type == 'devices':
        results = DeviceModels.query.filter(
            DeviceModels.DeviceModelName.ilike(f'%{query}%'),
        ).all()
        print(f"Devices search results for '{query}': {results}")

    return render_template('results.html', results=results, search_type=search_type)


# Route to add a device
@app.route('/add_device', methods=['GET', 'POST'])
@login_required
def add_device():
    if request.method == 'POST':
        DeviceManufacturerKey = request.form.get('DeviceManufacturerKey')
        DeviceModelName = request.form.get('DeviceModelName')
        DeviceCount = request.form.get('DeviceCount')
        DonorName = request.form.get('DonorName')
        TrackerDonationDateReceived = request.form.get('TrackerDonationDateReceived')

        print("Received form data:")
        print("DeviceManufacturerKey:", DeviceManufacturerKey)
        print("DeviceModelName:", DeviceModelName)
        print("DeviceCount:", DeviceCount)
        print("DonorName:", DonorName)
        print("TrackerDonationDateReceived:", TrackerDonationDateReceived)

        if DeviceManufacturerKey and DeviceModelName and DeviceCount and DonorName and TrackerDonationDateReceived:
            donor = TrackerDonors.query.filter(
                (TrackerDonors.TrackerDonorsFirstName + ' ' + TrackerDonors.TrackerDonorsLastName) == DonorName
            ).first()

            if donor:
                new_device_model = DeviceModels(
                    DeviceManufacturerKey=DeviceManufacturerKey,
                    DeviceModelName=DeviceModelName,
                    DeviceCount=DeviceCount
                )
                db.session.add(new_device_model)
                db.session.flush()  # This will create the DeviceModelKey for the new device

                # Convert the date string from the form to a datetime object
                donation_date = datetime.strptime(TrackerDonationDateReceived, '%Y-%m-%d')

                new_device = TrackerDonorDevices(
                    TrackerDonorsKey=donor.TrackerDonorKey,
                    DeviceModelKey=new_device_model.DeviceModelKey,
                    TrackerDonationDateReceived=donation_date
                )
                db.session.add(new_device)
                db.session.commit()
                
                return redirect(url_for('create_main'))
            else:
                print("Donor not found")
                return "Donor not found", 400
        else:
            print("Form data missing")
            return "Form data missing", 400

    return render_template('add_device.html')

# Route to remove a device
@app.route('/remove_device', methods=['GET', 'POST'])
@login_required
def remove_device():
    if request.method == 'POST':
        device_id = request.form.get('DeviceModelKey')
        donor_id = request.form.get('DonorKey')

        print("Received form data for removal:")
        print("DeviceModelKey:", device_id)
        print("DonorKey:", donor_id)

        device = DeviceModels.query.get(device_id)
        donor = TrackerDonors.query.get(donor_id)

        if device:
            print("Device found:", device.DeviceModelName)
        else:
            print("Device not found")

        if donor:
            print("Donor found:", donor.TrackerDonorsFirstName, donor.TrackerDonorsLastName)
        else:
            print("Donor not found")

        if device and donor:
            # Ensure to remove the association first
            association = TrackerDonorDevices.query.filter_by(DeviceModelKey=device_id, TrackerDonorsKey=donor_id).first()
            if association:
                db.session.delete(association)
                db.session.commit()
                print("Device-donor association removed")
            else:
                print("No device-donor association found")

            # If the device is no longer associated with any donor, remove the device
            remaining_associations = TrackerDonorDevices.query.filter_by(DeviceModelKey=device_id).all()
            if not remaining_associations:
                db.session.delete(device)
                db.session.commit()
                print("Device removed as it is no longer associated with any donor")

            return redirect(url_for('create_main'))
        else:
            print("Device or donor not found")

    devices = DeviceModels.query.all()
    donors = TrackerDonors.query.all()
    return render_template('remove_device.html', devices=devices, donors=donors)

# Route to add a donor
@app.route('/add_donor', methods=['GET', 'POST'])
@login_required
def add_donor():
    if request.method == 'POST':
        first_name = request.form.get('FirstName')
        last_name = request.form.get('LastName')
        address1 = request.form.get('Address1')
        address2 = request.form.get('Address2')
        city = request.form.get('City')
        state_key = request.form.get('StateKey')
        zip_code = request.form.get('ZipCode')

        if first_name and last_name and address1 and city and state_key and zip_code:
            new_donor = TrackerDonors(
                TrackerDonorsFirstName=first_name,
                TrackerDonorsLastName=last_name,
                TrackerDonorsAddress1=address1,
                TrackerDonorsAddress2=address2,
                TrackerDonorsCity=city,
                TrackerDonorsStateKey=state_key,
                TrackerDonorsZipCode=zip_code
            )

            db.session.add(new_donor)
            db.session.commit()
            
            return redirect(url_for('create_main'))
        else:
            print("Form data missing")

    return render_template('add_donor.html')

# Route to remove a donor
@app.route('/remove_donor', methods=['GET', 'POST'])
@login_required
def remove_donor():
    if request.method == 'POST':
        donor_id = request.form.get('TrackerDonorKey')

        if donor_id:
            donor = TrackerDonors.query.get_or_404(donor_id)
            db.session.delete(donor)
            db.session.commit()
            flash('Donor and associated devices removed successfully.', 'success')
            return redirect(url_for('create_main'))
        else:
            flash('Donor ID not provided.', 'danger')

    donors = TrackerDonors.query.all()
    return render_template('remove_donor.html', donors=donors)

# Route to add an organization
@app.route('/add_organization', methods=['GET', 'POST'])
@login_required
def add_organization():
    if request.method == 'POST':
        org_name = request.form.get('OrganizationName')
        org_type_key = request.form.get('OrganizationTypeKey')
        address1 = request.form.get('Address1')
        address2 = request.form.get('Address2')
        city = request.form.get('City')
        state_key = request.form.get('StateKey')
        zip_code = request.form.get('ZipCode')
        contact_first_name = request.form.get('ContactFirstName')
        contact_last_name = request.form.get('ContactLastName')
        contact_email = request.form.get('ContactEmailAddress')
        contact_phone = request.form.get('ContactPhoneNumber')

        if org_name and org_type_key and address1 and city and state_key and zip_code and contact_first_name and contact_last_name and contact_email and contact_phone:
            new_org = Organization(
                OrganizationName=org_name,
                OrganizationTypeKey=org_type_key,
                OrganizationAddress1=address1,
                OrganizationCity=city,
                OrganizationStateKey=state_key,
                OrganizationZipCode=zip_code,
                OrganizationContactFirstName=contact_first_name,
                OrganizationContactLastName=contact_last_name,
                OrganizationContactEmailAddress=contact_email,
                OrganizationContactPhoneNumber=contact_phone
            )

            db.session.add(new_org)
            db.session.commit()
            
            return redirect(url_for('create_main'))
        else:
            print("Form data missing")

    return render_template('add_organization.html')

# Route to remove an organization
@app.route('/remove_organization', methods=['GET', 'POST'])
@login_required
def remove_organization():
    if request.method == 'POST':
        org_id = request.form.get('OrganizationKey')

        organization = Organization.query.get(org_id)
        if organization:
            db.session.delete(organization)
            db.session.commit()
            return redirect(url_for('create_main'))
        else:
            print("Organization not found")

    organizations = Organization.query.all()
    return render_template('remove_organization.html', organizations=organizations)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            return "User already exists"
        
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/donor/<int:donor_id>/devices', methods=['GET'])
@login_required
def donor_devices(donor_id):
    donor = TrackerDonors.query.get_or_404(donor_id)
    devices = TrackerDonorDevices.query.filter_by(TrackerDonorsKey=donor_id).all()
    return render_template('donor_devices.html', donor=donor, devices=devices)

@app.route('/organization_requests/<int:org_id>', methods=['GET'])
@login_required
def organization_requests(org_id):
    organization = Organization.query.get_or_404(org_id)
    requests = OrganizationProgram.query.filter_by(OrganizationKey=org_id).all()
    return render_template('organization_requests.html', organization=organization, requests=requests)

# Route to plot devices per state
@app.route('/plot_donors', methods=['GET'])
@login_required
def plot_donors():
    db_url = 'sqlite:///' + os.path.join(basedir, 'rh_app.db')
    plot_path = plot_donors_per_state(db_url)
    return render_template('plot_donors.html', plot_path=plot_path)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('create_main'))
        
        return "Invalid username or password"
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
@login_required
def create_main():
    if current_user.role == 'admin':
        all_data = Organization.query.join(OrganizationProgram, Organization.OrganizationKey == OrganizationProgram.OrganizationKey)\
                                     .join(TrackerDonorDevices, OrganizationProgram.OrganizationProgramKey == TrackerDonorDevices.OrganizationProgramKey)\
                                     .join(TrackerDonors, TrackerDonorDevices.TrackerDonorsKey == TrackerDonors.TrackerDonorKey)\
                                     .join(DeviceModels, TrackerDonorDevices.DeviceModelKey == DeviceModels.DeviceModelKey)\
                                     .add_columns(Organization.OrganizationName,
                                                  Organization.OrganizationContactFirstName,
                                                  Organization.OrganizationContactLastName,
                                                  OrganizationProgram.OrganizationProgramDescription,
                                                  TrackerDonors.TrackerDonorsFirstName,
                                                  TrackerDonors.TrackerDonorsLastName,
                                                  DeviceModels.DeviceModelName)\
                                     .all()
        
        devices = DeviceModels.query.all()
        donors = TrackerDonors.query.all()
        organizations = Organization.query.all()

        return render_template('index.html', devices=devices, donors=donors, organizations=organizations)
    else:
        # Query for public data
        organizations = Organization.query.all()
        device_counts = db.session.query(DeviceModels.DeviceModelName, db.func.sum(DeviceModels.DeviceCount).label('DeviceCount'))\
                                  .group_by(DeviceModels.DeviceModelName)\
                                  .all()

        organizations_df = [{
            'OrganizationName': org.OrganizationName,
            'OrganizationTypeKey': org.OrganizationTypeKey,
            'OrganizationAddress1': org.OrganizationAddress1,
            'OrganizationCity': org.OrganizationCity,
            'OrganizationStateKey': org.OrganizationStateKey,
            'OrganizationZipCode': org.OrganizationZipCode,
            'OrganizationContactFirstName': org.OrganizationContactFirstName,
            'OrganizationContactLastName': org.OrganizationContactLastName,
            'OrganizationContactEmailAddress': org.OrganizationContactEmailAddress,
            'OrganizationContactPhoneNumber': org.OrganizationContactPhoneNumber,
            'OrganizationKey': org.OrganizationKey  # Ensure OrganizationKey is included
        } for org in organizations]

        devices = DeviceModels.query.all()

        return render_template('index.html', organizations=organizations_df, devices=devices)

# Route to add a request for an organization
@app.route('/add_request', methods=['GET', 'POST'])
@login_required
def add_request():
    if request.method == 'POST':
        organization_key = request.form.get('OrganizationKey')
        description = request.form.get('Description')
        trackers_requested = request.form.get('TrackersRequested')
        date_requested = request.form.get('DateRequested')

        if organization_key and description and trackers_requested and date_requested:
            new_request = OrganizationProgram(
                OrganizationKey=organization_key,
                OrganizationProgramDescription=description,
                OrganizationProgramTrackersNumberRequested=trackers_requested,
                OrganizationProgramDateRequested=datetime.strptime(date_requested, '%Y-%m-%d')
            )

            db.session.add(new_request)
            db.session.commit()
            
            return redirect(url_for('create_main'))
        else:
            print("Form data missing")
            return "Form data missing", 400

    organizations = Organization.query.all()
    return render_template('add_request.html', organizations=organizations)

# Route to fulfill a request for an organization
@app.route('/fulfill_request', methods=['GET', 'POST'])
@login_required
def fulfill_request():
    if request.method == 'POST':
        request_id = request.form.get('RequestId')
        trackers_sent = request.form.get('TrackersSent')
        date_sent = request.form.get('DateSent')

        request_obj = OrganizationProgram.query.get(request_id)

        if request_obj and trackers_sent and date_sent:
            request_obj.OrganizationProgramTrackersNumberSent = trackers_sent
            request_obj.OrganizationProgramDateSentOut = datetime.strptime(date_sent, '%Y-%m-%d')
            
            db.session.commit()
            
            return redirect(url_for('create_main'))
        else:
            print("Form data missing")
            return "Form data missing", 400

    requests = OrganizationProgram.query.all()
    return render_template('fulfill_request.html', requests=requests)

if __name__ == '__main__':
    app.run(debug=True)
