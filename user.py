from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Doctor, Appointment
from forms import AppointmentForm
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename
import os
from models import db, Doctor, Appointment, MedicalRecord
from models import db, Doctor, Appointment, MedicalRecord, ActivityLog


def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

user_bp = Blueprint('user', __name__)


def user_required(f):
    """Decorator to ensure only regular users can access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_admin:
            flash('Access denied. Admin cannot access user pages.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    """User dashboard showing appointment summary"""
    from models import Announcement
    
    # Get user's appointments
    appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.desc()).all()
    
    # Count appointments by status
    total_appointments = len(appointments)
    pending_count = len([apt for apt in appointments if apt.status == 'pending'])
    confirmed_count = len([apt for apt in appointments if apt.status == 'confirmed'])
    completed_count = len([apt for apt in appointments if apt.status == 'completed'])
    
    # Get upcoming appointments
    upcoming = [apt for apt in appointments if apt.date >= datetime.now() and apt.status != 'cancelled'][:5]
    
    # Get recent announcements (last 5)
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    
    return render_template('user/dashboard.html',
                         total_appointments=total_appointments,
                         pending_count=pending_count,
                         confirmed_count=confirmed_count,
                         completed_count=completed_count,
                         upcoming=upcoming,
                         announcements=announcements)


@user_bp.route('/profile')
@login_required
@user_required
def profile():
    """View user profile"""
    return render_template('user/profile.html')


@user_bp.route('/doctors')
@login_required
@user_required
def doctors():
    """View all available doctors with search"""
    # Get search query from URL parameters
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        # Search by name or specialization (case-insensitive)
        all_doctors = Doctor.query.filter(
            db.or_(
                Doctor.name.ilike(f'%{search_query}%'),
                Doctor.specialization.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        # Show all doctors if no search query
        all_doctors = Doctor.query.all()
    
    return render_template('user/doctors.html', doctors=all_doctors, search_query=search_query)


@user_bp.route('/book-appointment', methods=['GET', 'POST'])
@login_required
@user_required
def book_appointment():
    """Book a new appointment"""
    form = AppointmentForm()
    
    # Populate doctor choices
    form.doctor_id.choices = [(d.id, f"{d.name} - {d.specialization}") for d in Doctor.query.all()]
    
    if form.validate_on_submit():
        # Check if appointment date is in the future
        if form.date.data < datetime.now():
            flash('Please select a future date and time.', 'danger')
            return render_template('user/book_appointment.html', form=form)
        
        # Get doctor info
        doctor = Doctor.query.get(form.doctor_id.data)
        
        # Create new appointment
        appointment = Appointment(
            user_id=current_user.id,
            doctor_id=form.doctor_id.data,
            date=form.date.data,
            status='pending'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action=f'Appointment booked with {doctor.name} ({doctor.specialization}) on {form.date.data.strftime("%d %b %Y, %I:%M %p")}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Appointment booked successfully! Wait for confirmation.', 'success')
        return redirect(url_for('user.appointments'))
    
    return render_template('user/book_appointment.html', form=form)


@user_bp.route('/appointments')
@login_required
@user_required
def appointments():
    """View all user appointments"""
    # Get all appointments for current user
    user_appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.desc()).all()
    
    return render_template('user/appointments.html', appointments=user_appointments)


@user_bp.route('/cancel-appointment/<int:appointment_id>')
@login_required
@user_required
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if appointment belongs to current user
    if appointment.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('user.appointments'))
    
    # Check if appointment can be cancelled
    if appointment.status in ['completed', 'cancelled']:
        flash(f'Cannot cancel {appointment.status} appointment.', 'warning')
        return redirect(url_for('user.appointments'))
    
    # Cancel appointment
    appointment.status = 'cancelled'
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action=f'Appointment #{appointment.id} with {appointment.doctor.name} cancelled by user'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Appointment cancelled successfully.', 'info')
    return redirect(url_for('user.appointments'))
@user_bp.route('/appointment-slip/<int:appointment_id>')
@login_required
@user_required
def appointment_slip(appointment_id):
    """View appointment slip"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if appointment belongs to current user
    if appointment.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('user.appointments'))
    
    return render_template('user/appointment_slip.html', appointment=appointment)

@user_bp.route('/medical-records')
@login_required
@user_required
def medical_records():
    """View user's medical records"""
    records = MedicalRecord.query.filter_by(user_id=current_user.id).order_by(MedicalRecord.upload_date.desc()).all()
    return render_template('user/medical_records.html', records=records)


@user_bp.route('/upload-medical-record', methods=['POST'])
@login_required
@user_required
def upload_medical_record():
    """Upload medical record"""
    # Check if file is in request
    if 'medical_file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('user.medical_records'))
    
    file = request.files['medical_file']
    
    # Check if file is empty
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('user.medical_records'))
    
    # Check file type
    if not allowed_file(file.filename):
        flash('Invalid file type. Only PDF, PNG, JPG, JPEG are allowed.', 'danger')
        return redirect(url_for('user.medical_records'))
    
    # Secure filename and add timestamp to avoid conflicts
    from datetime import datetime
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{current_user.id}_{timestamp}_{filename}"
    
    # Save file
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    # Get file extension
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    # Save record to database
    record = MedicalRecord(
        user_id=current_user.id,
        file_name=filename,
        file_path=unique_filename,
        file_type=file_extension
    )
    db.session.add(record)
    db.session.commit()
    
    flash(f'Medical record "{filename}" uploaded successfully!', 'success')
    return redirect(url_for('user.medical_records'))


@user_bp.route('/delete-medical-record/<int:record_id>')
@login_required
@user_required
def delete_medical_record(record_id):
    """Delete medical record"""
    record = MedicalRecord.query.get_or_404(record_id)
    
    # Check if record belongs to current user
    if record.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('user.medical_records'))
    
    # Delete file from filesystem
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, record.file_path)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    db.session.delete(record)
    db.session.commit()
    
    flash(f'Medical record "{record.file_name}" deleted successfully!', 'info')
    return redirect(url_for('user.medical_records'))


@user_bp.route('/download-medical-record/<int:record_id>')
@login_required
@user_required
def download_medical_record(record_id):
    """Download medical record"""
    from flask import send_from_directory
    
    record = MedicalRecord.query.get_or_404(record_id)
    
    # Check if record belongs to current user
    if record.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('user.medical_records'))
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, record.file_path, as_attachment=True, download_name=record.file_name)
