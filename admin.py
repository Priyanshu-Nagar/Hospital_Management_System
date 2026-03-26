from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Doctor, Appointment, Announcement, ActivityLog
from forms import DoctorForm, AnnouncementForm

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to ensure only admin can access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Get statistics
    total_users = User.query.filter_by(role='user').count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()
    
    # Appointments by status
    pending_appointments = Appointment.query.filter_by(status='pending').count()
    confirmed_appointments = Appointment.query.filter_by(status='confirmed').count()
    completed_appointments = Appointment.query.filter_by(status='completed').count()
    cancelled_appointments = Appointment.query.filter_by(status='cancelled').count()
    
    # Recent appointments
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    
    # Chart Data: Appointments per day (last 7 days)
    today = datetime.now().date()
    appointments_per_day = []
    day_labels = []
    
    for i in range(6, -1, -1):  # Last 7 days
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        count = Appointment.query.filter(
            Appointment.created_at >= day_start,
            Appointment.created_at <= day_end
        ).count()
        
        appointments_per_day.append(count)
        day_labels.append(day.strftime('%a, %b %d'))
    
    # Recent activity logs
    recent_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_doctors=total_doctors,
                         total_appointments=total_appointments,
                         pending_appointments=pending_appointments,
                         confirmed_appointments=confirmed_appointments,
                         completed_appointments=completed_appointments,
                         cancelled_appointments=cancelled_appointments,
                         recent_appointments=recent_appointments,
                         appointments_per_day=appointments_per_day,
                         day_labels=day_labels,
                         recent_logs=recent_logs)


@admin_bp.route('/doctors')
@login_required
@admin_required
def doctors():
    """View all doctors"""
    all_doctors = Doctor.query.all()
    return render_template('admin/doctors.html', doctors=all_doctors)


@admin_bp.route('/add-doctor', methods=['GET', 'POST'])
@login_required
@admin_required
def add_doctor():
    """Add new doctor"""
    form = DoctorForm()
    
    if form.validate_on_submit():
        doctor = Doctor(
            name=form.name.data,
            specialization=form.specialization.data,
            available_days=form.available_days.data if form.available_days.data else None,
            available_time=form.available_time.data if form.available_time.data else None
        )
        db.session.add(doctor)
        db.session.commit()
        
        flash(f'Doctor {doctor.name} added successfully!', 'success')
        return redirect(url_for('admin.doctors'))
    
    return render_template('admin/add_doctor.html', form=form)


@admin_bp.route('/edit-doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(doctor_id):
    """Edit doctor details"""
    doctor = Doctor.query.get_or_404(doctor_id)
    form = DoctorForm()
    
    if form.validate_on_submit():
        doctor.name = form.name.data
        doctor.specialization = form.specialization.data
        doctor.available_days = form.available_days.data if form.available_days.data else None
        doctor.available_time = form.available_time.data if form.available_time.data else None
        db.session.commit()
        
        flash(f'Doctor {doctor.name} updated successfully!', 'success')
        return redirect(url_for('admin.doctors'))
    
    # Pre-fill form
    elif request.method == 'GET':
        form.name.data = doctor.name
        form.specialization.data = doctor.specialization
        form.available_days.data = doctor.available_days
        form.available_time.data = doctor.available_time
    
    return render_template('admin/edit_doctor.html', form=form, doctor=doctor)


@admin_bp.route('/delete-doctor/<int:doctor_id>')
@login_required
@admin_required
def delete_doctor(doctor_id):
    """Delete doctor"""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Check if doctor has appointments
    if doctor.appointments:
        flash(f'Cannot delete {doctor.name}. Doctor has existing appointments.', 'danger')
        return redirect(url_for('admin.doctors'))
    
    db.session.delete(doctor)
    db.session.commit()
    
    flash(f'Doctor {doctor.name} deleted successfully!', 'info')
    return redirect(url_for('admin.doctors'))


@admin_bp.route('/patients')
@login_required
@admin_required
def patients():
    """View all patients"""
    all_patients = User.query.filter_by(role='user').all()
    return render_template('admin/patients.html', patients=all_patients)


@admin_bp.route('/delete-patient/<int:patient_id>')
@login_required
@admin_required
def delete_patient(patient_id):
    """Delete patient"""
    patient = User.query.get_or_404(patient_id)
    
    # Don't allow deleting admin
    if patient.is_admin:
        flash('Cannot delete admin user.', 'danger')
        return redirect(url_for('admin.patients'))
    
    db.session.delete(patient)
    db.session.commit()
    
    flash(f'Patient {patient.name} deleted successfully!', 'info')
    return redirect(url_for('admin.patients'))


@admin_bp.route('/appointments')
@login_required
@admin_required
def appointments():
    """View all appointments"""
    all_appointments = Appointment.query.order_by(Appointment.date.desc()).all()
    return render_template('admin/appointments.html', appointments=all_appointments)


@admin_bp.route('/update-appointment-status/<int:appointment_id>/<status>')
@login_required
@admin_required
def update_appointment_status(appointment_id, status):
    """Update appointment status"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Validate status
    valid_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
    if status not in valid_statuses:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.appointments'))
    
    old_status = appointment.status
    appointment.status = status
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action=f'Admin updated appointment #{appointment.id} (Patient: {appointment.patient.name}) from {old_status} to {status}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Appointment #{appointment.id} status updated to {status}.', 'success')
    return redirect(url_for('admin.appointments'))


@admin_bp.route('/delete-appointment/<int:appointment_id>')
@login_required
@admin_required
def delete_appointment(appointment_id):
    """Delete appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    db.session.delete(appointment)
    db.session.commit()
    
    flash(f'Appointment #{appointment.id} deleted successfully!', 'info')
    return redirect(url_for('admin.appointments'))

@admin_bp.route('/announcements')
@login_required
@admin_required
def announcements():
    """View all announcements"""
    from forms import AnnouncementForm  # Make sure this import is at the top of the file
    
    form = AnnouncementForm()  # Create form instance
    all_announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    
    return render_template('admin/announcements.html', 
                         announcements=all_announcements,
                         form=form)  # Pass form to template


@admin_bp.route('/add-announcement', methods=['GET', 'POST'])
@login_required
@admin_required
def add_announcement():
    """Create new announcement"""
    form = AnnouncementForm()
    
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            message=form.message.data
        )
        db.session.add(announcement)
        db.session.commit()
        
        flash('Announcement posted successfully!', 'success')
        return redirect(url_for('admin.announcements'))
    
    return render_template('admin/add_announcement.html', form=form)


@admin_bp.route('/delete-announcement/<int:announcement_id>')
@login_required
@admin_required
def delete_announcement(announcement_id):
    """Delete announcement"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    db.session.delete(announcement)
    db.session.commit()
    
    flash(f'Announcement "{announcement.title}" deleted successfully!', 'info')
    return redirect(url_for('admin.announcements'))


@admin_bp.route('/activity-logs')
@login_required
@admin_required
def activity_logs():
    """View all activity logs"""
    from datetime import datetime
    
    # Get all logs, ordered by most recent first
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    
    # Calculate statistics
    registration_count = sum(1 for log in logs if 'registered' in log.action)
    booking_count = sum(1 for log in logs if 'booked' in log.action)
    cancellation_count = sum(1 for log in logs if 'cancelled' in log.action)
    admin_update_count = sum(1 for log in logs if 'Admin updated' in log.action)
    
    return render_template('admin/activity_logs.html', 
                         logs=logs, 
                         now=datetime.now(),
                         registration_count=registration_count,
                         booking_count=booking_count,
                         cancellation_count=cancellation_count,
                         admin_update_count=admin_update_count)
