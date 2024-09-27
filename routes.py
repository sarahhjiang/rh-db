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
from plotting import plot_donors_per_state, plot_devices_per_state

from models import db, ma, bcrypt, User, Organization, OrganizationProgram, Communication, CommunicationType, State, TrackerDonors, TrackerDonorDevices, DeviceModels, DeviceManufacturer

basedir = os.path.abspath(os.path.dirname(__file__))

# Create flask app instance
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

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

# Utility function to check if the user is an admin
def is_admin():
    return current_user.is_authenticated and current_user.role == 'admin'

# Custom decorator for admin routes
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Admin access required to view this page.', 'danger')
            return redirect(url_for('create_main'))
        return f(*args, **kwargs)
    return decorated_function

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
    elif search_type == 'organizations':
        results = Organization.query.filter(
            Organization.OrganizationName.ilike(f'%{query}%')
        ).all()
    elif search_type == 'devices':
        results = DeviceModels.query.filter(
            DeviceModels.DeviceModelName.ilike(f'%{query}%'),
        ).all()

    return render_template('results.html', results=results, search_type=search_type)


# Route to add a device (admin-only)
@app.route('/add_device', methods=['GET', 'POST'])
@login_required
@admin_required
def add_device():
    if request.method == 'POST':
        DeviceManufacturerKey = request.form.get('DeviceManufacturerKey')
        DeviceModelName = request.form.get('DeviceModelName')
        DeviceCount = request.form.get('DeviceCount')
        DonorName = request.form.get('DonorName')
        TrackerDonationDateReceived = request.form.get('TrackerDonationDateReceived')

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
                db.session.flush()

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
                return "Donor not found", 400
        else:
            return "Form data missing", 400

    return render_template('add_device.html')

# Route to remove a device (admin-only)
@app.route('/remove_device', methods=['GET', 'POST'])
@login_required
@admin_required
def remove_device():
    if request.method == 'POST':
        device_id = request.form.get('DeviceModelKey')
        donor_id = request.form.get('DonorKey')

        device = DeviceModels.query.get(device_id)
        donor = TrackerDonors.query.get(donor_id)

        if device and donor:
            association = TrackerDonorDevices.query.filter_by(DeviceModelKey=device_id, TrackerDonorsKey=donor_id).first()
            if association:
                db.session.delete(association)
                db.session.commit()

            remaining_associations = TrackerDonorDevices.query.filter_by(DeviceModelKey=device_id).all()
            if not remaining_associations:
                db.session.delete(device)
                db.session.commit()

            return redirect(url_for('create_main'))
        else:
            return "Device or donor not found", 400

    devices = DeviceModels.query.all()
    donors = TrackerDonors.query.all()
    return render_template('remove_device.html', devices=devices, donors=donors)

# Route to add a donor (admin-only)
@app.route('/add_donor', methods=['GET', 'POST'])
@login_required
@admin_required
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
            return "Form data missing", 400

    return render_template('add_donor.html')

# Route to remove a donor (admin-only)
@app.route('/remove_donor', methods=['GET', 'POST'])
@login_required
@admin_required
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

# Admin-only routes for adding/removing organizations
@app.route('/add_organization', methods=['GET', 'POST'])
@login_required
@admin_required
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
            return "Form data missing", 400

    return render_template('add_organization.html')

@app.route('/remove_organization', methods=['GET', 'POST'])
@login_required
@admin_required
def remove_organization():
    if request.method == 'POST':
        org_id = request.form.get('OrganizationKey')

        organization = Organization.query.get(org_id)
        if organization:
            db.session.delete(organization)
            db.session.commit()
            return redirect(url_for('create_main'))
        else:
            return "Organization not found", 400

    organizations = Organization.query.all()
    return render_template('remove_organization.html', organizations=organizations)

# Fulfilled requests (admin-only)
@app.route('/fulfilled_requests', methods=['GET'])
@login_required
@admin_required
def fulfilled_requests():
    fulfilled_requests = OrganizationProgram.query.filter(OrganizationProgram.OrganizationProgramTrackersNumberSent > 0).all()

    fulfilled_data = []
    for request in fulfilled_requests:
        devices = TrackerDonorDevices.query.filter_by(OrganizationProgramKey=request.OrganizationProgramKey).all()
        fulfilled_data.append({
            'request': request,
            'devices': devices
        })
    
    return render_template('fulfilled_requests.html', fulfilled_data=fulfilled_data)


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


@app.route('/donor/<int:donor_id>/devices', methods=['GET'])
@login_required
def donor_devices(donor_id):
    donor = TrackerDonors.query.get_or_404(donor_id)
    devices = TrackerDonorDevices.query.filter_by(TrackerDonorsKey=donor_id).all()
    return render_template('donor_devices.html', donor=donor, devices=devices)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/export_data/<string:data_type>', methods=['GET'])
@login_required
@admin_required
def export_data(data_type):
    # Define the appropriate query based on the data type requested
    if data_type == 'fulfilled_requests':
        data = db.session.query(OrganizationProgram, TrackerDonorDevices, DeviceModels, TrackerDonors).join(
            TrackerDonorDevices, TrackerDonorDevices.OrganizationProgramKey == OrganizationProgram.OrganizationProgramKey
        ).join(
            DeviceModels, TrackerDonorDevices.DeviceModelKey == DeviceModels.DeviceModelKey
        ).join(
            TrackerDonors, TrackerDonorDevices.TrackerDonorsKey == TrackerDonors.TrackerDonorKey
        ).filter(OrganizationProgram.OrganizationProgramTrackersNumberSent > 0).all()

        # Prepare the data for export
        rows = [{
            'Request Description': request.OrganizationProgram.OrganizationProgramDescription,
            'Trackers Sent': request.OrganizationProgram.OrganizationProgramTrackersNumberSent,
            'Device Model': request.DeviceModels.DeviceModelName,
            'Donor': f"{request.TrackerDonors.TrackerDonorsFirstName} {request.TrackerDonors.TrackerDonorsLastName}",
            'Date Sent': request.TrackerDonorDevices.TrackerDonationDateSentOut.strftime('%Y-%m-%d') if request.TrackerDonorDevices.TrackerDonationDateSentOut else 'N/A'
        } for request in data]
        
    elif data_type == 'donors':
        data = TrackerDonors.query.all()
        rows = [{
            'First Name': donor.TrackerDonorsFirstName,
            'Last Name': donor.TrackerDonorsLastName,
            'Address': f"{donor.TrackerDonorsAddress1}, {donor.TrackerDonorsAddress2}",
            'City': donor.TrackerDonorsCity,
            'State': donor.state.StateName if donor.state else 'N/A',
            'Zip Code': donor.TrackerDonorsZipCode
        } for donor in data]

    elif data_type == 'organizations':
        data = Organization.query.all()
        rows = [{
            'Organization Name': org.OrganizationName,
            'City': org.OrganizationCity,
            'State': org.state.StateName if org.state else 'N/A',
            'Zip Code': org.OrganizationZipCode,
            'Contact Name': f"{org.OrganizationContactFirstName} {org.OrganizationContactLastName}",
            'Contact Email': org.OrganizationContactEmailAddress
        } for org in data]
        
    else:
        flash('Invalid data type for export', 'danger')
        return redirect(url_for('create_main'))

    # Convert data to DataFrame
    df = pd.DataFrame(rows)

    # Convert to CSV or Excel depending on query string param
    export_format = request.args.get('format', 'csv')
    if export_format == 'csv':
        file_name = f'{data_type}_export.csv'
        csv_data = df.to_csv(index=False)
        return send_file(BytesIO(csv_data.encode('utf-8')), mimetype='text/csv', attachment_filename=file_name, as_attachment=True)
    elif export_format == 'excel':
        file_name = f'{data_type}_export.xlsx'
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', attachment_filename=file_name, as_attachment=True)
    else:
        flash('Unsupported export format', 'danger')
        return redirect(url_for('create_main'))


@app.route('/plot_donors', methods=['GET'])
@login_required
def plot_donors():
    plot_path = plot_donors_per_state(os.getenv('DATABASE_URL')) 
    if plot_path:
        return render_template('plot_donors.html', plot_path=plot_path)
    else:
        flash('Unable to generate plot', 'danger')
        return redirect(url_for('create_main'))


@app.route('/plot_devices', methods=['GET'])
@login_required
def plot_devices():
    plot_path = plot_devices_per_state(os.getenv('DATABASE_URL')) 
    if plot_path:
        return render_template('plot.html', plot_path=plot_path)
    else:
        flash('Unable to generate plot', 'danger')
        return redirect(url_for('create_main'))
