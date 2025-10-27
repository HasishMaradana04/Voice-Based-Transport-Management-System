# app/routes/main.py

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models.models import Route, Schedule, Booking, VoiceCommand
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    total_bookings = Booking.query.filter_by(user_id=current_user.id).count()
    active_bookings = Booking.query.filter_by(user_id=current_user.id, status='Confirmed').count()
    voice_commands_count = VoiceCommand.query.filter_by(user_id=current_user.id).count()
    recent_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_time.desc()).limit(5).all()
    recent_commands = VoiceCommand.query.filter_by(user_id=current_user.id).order_by(VoiceCommand.timestamp.desc()).limit(5).all()
    available_routes = Route.query.limit(6).all()
    stats = {
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'voice_commands': voice_commands_count,
        'routes_available': Route.query.count()
    }
    return render_template('dashboard.html',
                           stats=stats,
                           recent_bookings=recent_bookings,
                           recent_commands=recent_commands,
                           available_routes=available_routes)

@main_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    seven_days_ago = datetime.now() - timedelta(days=7)
    daily_bookings = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        bookings_count = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.booking_time >= day_start,
            Booking.booking_time <= day_end
        ).count()
        daily_bookings.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': bookings_count
        })
    voice_stats = {
        'total': VoiceCommand.query.filter_by(user_id=current_user.id).count(),
        'today': VoiceCommand.query.filter(
            VoiceCommand.user_id == current_user.id,
            VoiceCommand.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
    }
    return jsonify({
        'daily_bookings': daily_bookings,
        'voice_stats': voice_stats
    })
