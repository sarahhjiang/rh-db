from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
ma = Marshmallow()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='public')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class Organization(db.Model):
    __tablename__ = 'tblOrganization'
    OrganizationKey = db.Column(db.Integer, primary_key=True)
    OrganizationName = db.Column(db.String, nullable=True)
    OrganizationTypeKey = db.Column(db.String, nullable=True)
    OrganizationAddress1 = db.Column(db.String, nullable=True)
    OrganizationCity = db.Column(db.String, nullable=True)
    OrganizationStateKey = db.Column(db.Integer, db.ForeignKey('tlkpState.StateKey'), nullable=True)
    OrganizationZipCode = db.Column(db.String, nullable=True)
    OrganizationContactFirstName = db.Column(db.String, nullable=True)
    OrganizationContactLastName = db.Column(db.String, nullable=True)
    OrganizationContactEmailAddress = db.Column(db.String, nullable=True)
    OrganizationContactPhoneNumber = db.Column(db.String, nullable=True)
    OrganizationContactPhoneExtension = db.Column(db.String, nullable=True)
    OrganizationContactTitle = db.Column(db.String, nullable=True)
    OrganizationAmenabletoDonation = db.Column(db.String, nullable=True)
    OrganizationShareSuccessStory = db.Column(db.String, nullable=True)
    OrganizationDateCreatedTS = db.Column(db.DateTime, nullable=True)

class OrganizationProgram(db.Model):
    __tablename__ = 'tblOrganizationProgram'
    OrganizationProgramKey = db.Column(db.Integer, primary_key=True)
    OrganizationKey = db.Column(db.Integer, db.ForeignKey('tblOrganization.OrganizationKey'), nullable=False)
    OrganizationProgramDescription = db.Column(db.String, nullable=True)
    OrganizationProgramDateRequested = db.Column(db.DateTime, nullable=True)
    OrganizationProgramDateSentOut = db.Column(db.DateTime, nullable=True)
    OrganizationProgramTrackersNumberRequested = db.Column(db.Integer, nullable=True)
    OrganizationProgramTrackersNumberSent = db.Column(db.Integer, nullable=True)
    OrganizationProgramShippingCost = db.Column(db.Float, nullable=True)
    OrganizationProgramAmountPaid = db.Column(db.Float, nullable=True)
    ProgramStatusKey = db.Column(db.Integer, nullable=True)
    OrganizationProgramDateCreatedTS = db.Column(db.DateTime, nullable=True)

class Communication(db.Model):
    __tablename__ = 'tblOrganizationCommunication'
    OrganizationCommunicationKey = db.Column(db.Integer, primary_key=True)
    OrganizationKey = db.Column(db.Integer, db.ForeignKey('tblOrganization.OrganizationKey'), nullable=False)
    CommunicationTypeKey = db.Column(db.Integer, db.ForeignKey('tlkpCommunicationType.CommunicationTypeKey'), nullable=False)
    CommunicationTypeDate = db.Column(db.DateTime, nullable=True)
    CommunicationTypeNote = db.Column(db.String, nullable=True)
    CommunicationTypeDateCreatedTS = db.Column(db.DateTime, nullable=True)

class CommunicationType(db.Model):
    __tablename__ = 'tlkpCommunicationType'
    CommunicationTypeKey = db.Column(db.Integer, primary_key=True)
    CommunicationTypeName = db.Column(db.String, nullable=True)
    CommunicationTypeDescription = db.Column(db.String, nullable=True)
    CommunicationTypeCreateTS = db.Column(db.DateTime, nullable=True)

class State(db.Model):
    __tablename__ = 'tlkpState'
    StateKey = db.Column(db.Integer, primary_key=True)
    StateName = db.Column(db.String, nullable=True)
    StateAbbrev = db.Column(db.String, nullable=True)
    StateCreateTS = db.Column(db.DateTime, nullable=True)

class TrackerDonors(db.Model):
    __tablename__ = 'tblTrackerDonors'
    TrackerDonorKey = db.Column(db.Integer, primary_key=True)
    TrackerDonorsFirstName = db.Column(db.String(50))
    TrackerDonorsLastName = db.Column(db.String(50))
    TrackerDonorsAddress1 = db.Column(db.String(100))
    TrackerDonorsAddress2 = db.Column(db.String(100))
    TrackerDonorsCity = db.Column(db.String(50))
    TrackerDonorsStateKey = db.Column(db.Integer, db.ForeignKey('tlkpState.StateKey'))
    TrackerDonorsZipCode = db.Column(db.String(10))

class TrackerDonorDevices(db.Model):
    __tablename__ = 'tblTrackerDonorDevices'
    TrackerDonorDevicesKey = db.Column(db.Integer, primary_key=True)
    TrackerDonorsKey = db.Column(db.Integer, db.ForeignKey('tblTrackerDonors.TrackerDonorKey', ondelete="CASCADE"), nullable=False)
    TrackerDonationDateReceived = db.Column(db.DateTime, nullable=True)
    TrackerDonationLetter = db.Column(db.String, nullable=True)
    DeviceModelKey = db.Column(db.Integer, db.ForeignKey('tlkpDeviceModels.DeviceModelKey'), nullable=False)
    OrganizationProgramKey = db.Column(db.Integer, db.ForeignKey('tblOrganizationProgram.OrganizationProgramKey'), nullable=True)  # Make nullable
    TrackerDonationDateSentOut = db.Column(db.DateTime, nullable=True)
    TrackerDonorDevicesDateCreateTS = db.Column(db.DateTime, nullable=True)
    device_model = db.relationship('DeviceModels', backref='tracker_donor_devices', lazy=True)

class DeviceModels(db.Model):
    __tablename__ = 'tlkpDeviceModels'
    DeviceModelKey = db.Column(db.Integer, primary_key=True)
    DeviceManufacturerKey = db.Column(db.Integer, db.ForeignKey('tlkpDeviceManufacturer.DeviceManufacturerKey'), nullable=False)
    DeviceModelName = db.Column(db.String, nullable=True)
    DeviceCount = db.Column(db.Integer, nullable=True)
    DeviceModelCreateTS = db.Column(db.DateTime, nullable=True)
    donations = db.relationship('TrackerDonorDevices', backref='device', lazy=True)

class DeviceManufacturer(db.Model):
    __tablename__ = 'tlkpDeviceManufacturer'
    DeviceManufacturerKey = db.Column(db.Integer, primary_key=True)
    DeviceManufacturerName = db.Column(db.String, nullable=True)
    DeviceManufacturerCreateTS = db.Column(db.DateTime, nullable=True)

# Schema definitions
class OrganizationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Organization

class OrganizationProgramSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OrganizationProgram

class CommunicationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Communication

class CommunicationTypeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CommunicationType

class StateSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = State

class TrackerDonorsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TrackerDonors

class TrackerDonorDevicesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TrackerDonorDevices

class DeviceModelsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DeviceModels

class DeviceManufacturerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DeviceManufacturer
