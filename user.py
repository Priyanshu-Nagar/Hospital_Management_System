from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Doctor, Appointment
from forms import AppointmentForm
from datetime import datetime
from functools import wraps

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
    # Get user's appointments
    appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.desc()).all()
    
    # Count appointments by status
    total_appointments = len(appointments)
    pending_count = len([apt for apt in appointments if apt.status == 'pending'])
    confirmed_count = len([apt for apt in appointments if apt.status == 'confirmed'])
    completed_count = len([apt for apt in appointments if apt.status == 'completed'])
    
    # Get upcoming appointments
    upcoming = [apt for apt in appointments if apt.date >= datetime.now() and apt.status != 'cancelled'][:5]
    
    return render_template('user/dashboard.html',
                         total_appointments=total_appointments,
                         pending_count=pending_count,
                         confirmed_count=confirmed_count,
                         completed_count=completed_count,
                         upcoming=upcoming)


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
    """View all available doctors"""
    all_doctors = Doctor.query.all()
    return render_template('user/doctors.html', doctors=all_doctors)


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
        
        # Create new appointment
        appointment = Appointment(
            user_id=current_user.id,
            doctor_id=form.doctor_id.data,
            date=form.date.data,
            status='pending'
        )
        
        db.session.add(appointment)
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
    
    flash('Appointment cancelled successfully.', 'info')
    return redirect(url_for('user.appointments'))
