from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Doctor, Appointment
from forms import DoctorForm
from functools import wraps

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
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_doctors=total_doctors,
                         total_appointments=total_appointments,
                         pending_appointments=pending_appointments,
                         confirmed_appointments=confirmed_appointments,
                         completed_appointments=completed_appointments,
                         cancelled_appointments=cancelled_appointments,
                         recent_appointments=recent_appointments)


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
            specialization=form.specialization.data
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
        db.session.commit()
        
        flash(f'Doctor {doctor.name} updated successfully!', 'success')
        return redirect(url_for('admin.doctors'))
    
    # Pre-fill form
    elif request.method == 'GET':
        form.name.data = doctor.name
        form.specialization.data = doctor.specialization
    
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
    
    appointment.status = status
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
