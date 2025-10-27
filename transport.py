from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app.models.models import db, Route, Vehicle, Schedule, Booking
from datetime import datetime, timedelta
import random
import string

transport_bp = Blueprint('transport', __name__, url_prefix='/transport')

def generate_booking_reference():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Dashboard with stats
@transport_bp.route('/')
@login_required
def dashboard():
    routes = Route.query.all()
    vehicles = Vehicle.query.all()
    recent_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_time.desc()).limit(5).all()
    stats = {
        'total_routes': Route.query.count(),
        'total_vehicles': Vehicle.query.count(),
        'total_bookings': Booking.query.count(),
        'my_bookings': Booking.query.filter_by(user_id=current_user.id).count(),
        'available_vehicles': Vehicle.query.filter_by(status="Available").count()
    }
    return render_template(
        'transport/dashboard.html',
        routes=routes,
        vehicles=vehicles,
        recent_bookings=recent_bookings,
        stats=stats
    )

# List all routes
@transport_bp.route('/routes')
@login_required
def routes():
    routes = Route.query.all()
    return render_template('transport/routes.html', routes=routes)

# Route search
@transport_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search_routes():
    routes = []
    if request.method == 'POST':
        source = request.form.get('source', '').strip()
        destination = request.form.get('destination', '').strip()
        if source and destination:
            routes = Route.query.filter(
                Route.source.ilike(f'%{source}%'),
                Route.destination.ilike(f'%{destination}%')
            ).all()
            if not routes:
                flash(f'No routes found from {source} to {destination}')
        else:
            flash('Please enter both source and destination')
    return render_template('transport/search.html', routes=routes)

# Timetable for a route
@transport_bp.route('/schedule/<int:route_id>')
@login_required
def view_schedule(route_id):
    route = Route.query.get_or_404(route_id)
    schedules = Schedule.query.filter_by(route_id=route_id, status='Scheduled').order_by(Schedule.departure_time).all()
    return render_template('transport/schedule.html', route=route, schedules=schedules)

# Book a ticket
@transport_bp.route('/book/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def book_ticket(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if request.method == 'POST':
        seats = int(request.form.get('seats', 1))
        if seats <= 0:
            flash('Invalid number of seats')
            return redirect(url_for('transport.book_ticket', schedule_id=schedule_id))
        if seats > schedule.available_seats:
            flash(f'Only {schedule.available_seats} seats available')
            return redirect(url_for('transport.book_ticket', schedule_id=schedule_id))
        total_fare = schedule.route.fare * seats
        booking = Booking(
            user_id=current_user.id,
            schedule_id=schedule_id,
            seats_booked=seats,
            total_fare=total_fare,
            status='Confirmed',
            booking_reference=generate_booking_reference()
        )
        schedule.available_seats -= seats
        db.session.add(booking)
        db.session.commit()
        flash(f'Ticket booked successfully! Reference: {booking.booking_reference}')
        return redirect(url_for('transport.booking_details', booking_id=booking.id))
    return render_template('transport/book.html', schedule=schedule)

# Booking details
@transport_bp.route('/booking/<int:booking_id>')
@login_required
def booking_details(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    return render_template('transport/booking_details.html', booking=booking)

# My Bookings
@transport_bp.route('/my-bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_time.desc()).all()
    return render_template('transport/my_bookings.html', bookings=bookings)

# Cancel Booking
@transport_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    if booking.status == 'Cancelled':
        flash('Booking is already cancelled')
        return redirect(url_for('transport.my_bookings'))
    booking.status = 'Cancelled'
    schedule = Schedule.query.get(booking.schedule_id)
    schedule.available_seats += booking.seats_booked
    db.session.commit()
    flash('Booking cancelled successfully')
    return redirect(url_for('transport.my_bookings'))

################ Admin Only Below ################

@transport_bp.route('/admin/add-route', methods=['GET', 'POST'])
@login_required
def add_route():
    if request.method == 'POST':
        route = Route(
            route_name=request.form['route_name'],
            source=request.form['source'],
            destination=request.form['destination'],
            distance=float(request.form['distance']),
            duration=int(request.form['duration']),
            fare=float(request.form['fare'])
        )
        db.session.add(route)
        db.session.commit()
        flash('Route added successfully')
        return redirect(url_for('transport.routes'))
    return render_template('transport/add_route.html')

@transport_bp.route('/admin/add-vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if request.method == 'POST':
        vehicle = Vehicle(
            vehicle_number=request.form['vehicle_number'],
            vehicle_type=request.form['vehicle_type'],
            capacity=int(request.form['capacity']),
            status='Available'
        )
        db.session.add(vehicle)
        db.session.commit()
        flash('Vehicle added successfully')
        return redirect(url_for('transport.dashboard'))
    return render_template('transport/add_vehicle.html')

@transport_bp.route('/admin/add-schedule', methods=['GET', 'POST'])
@login_required
def add_schedule():
    if request.method == 'POST':
        departure_time = datetime.strptime(request.form['departure_time'], '%Y-%m-%dT%H:%M')
        route = Route.query.get(request.form['route_id'])
        vehicle = Vehicle.query.get(request.form['vehicle_id'])
        arrival_time = departure_time + timedelta(minutes=route.duration)
        schedule = Schedule(
            vehicle_id=vehicle.id,
            route_id=route.id,
            departure_time=departure_time,
            arrival_time=arrival_time,
            available_seats=vehicle.capacity,
            status='Scheduled'
        )
        db.session.add(schedule)
        db.session.commit()
        flash('Schedule added successfully')
        return redirect(url_for('transport.dashboard'))
    vehicles = Vehicle.query.filter_by(status='Available').all()
    routes = Route.query.all()
    return render_template('transport/add_schedule.html', vehicles=vehicles, routes=routes)
@transport_bp.route('/pay/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def pay_booking(booking_id):
    booking = Booking.query.filter_by(id=booking_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        # Simulate a payment success for demo
        booking.status = "Paid"
        db.session.commit()
        flash("Payment successful! Booking confirmed.", "success")
        return redirect(url_for('transport.booking_details', booking_id=booking_id))
    return render_template('transport/payment.html', booking=booking)
