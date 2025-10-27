# app/__init__.py

from flask import Flask, render_template
from flask_login import LoginManager
from app.models.models import db, User
from app.routes.auth import auth_bp
from app.routes.transport import transport_bp
from app.routes.voice import voice_bp
import os

def create_sample_data():
    from app.models.models import Route, Vehicle, Schedule
    from datetime import datetime, timedelta

    if Route.query.count() > 0 or Vehicle.query.count() > 0:
        print("Sample data already exists. Skipping creation.")
        return

    routes = [
        Route(route_name='Visakhapatnam to Hyderabad', source='Visakhapatnam', destination='Hyderabad',
              distance=600, duration=480, fare=500),
        Route(route_name='Hyderabad to Vijayawada', source='Hyderabad', destination='Vijayawada',
              distance=275, duration=240, fare=300),
        Route(route_name='Vijayawada to Chennai', source='Vijayawada', destination='Chennai',
              distance=430, duration=360, fare=400),
        Route(route_name='Visakhapatnam to Vijayawada', source='Visakhapatnam', destination='Vijayawada',
              distance=350, duration=300, fare=350),
    ]
    vehicles = [
        Vehicle(vehicle_number='AP39Z1234', vehicle_type='Bus', capacity=40, status='Available'),
        Vehicle(vehicle_number='AP39Z5678', vehicle_type='Bus', capacity=50, status='Available'),
        Vehicle(vehicle_number='AP39Z9012', vehicle_type='Mini Bus', capacity=25, status='Available'),
        Vehicle(vehicle_number='AP39Z3456', vehicle_type='Bus', capacity=45, status='Available'),
    ]
    for route in routes:
        db.session.add(route)
    for vehicle in vehicles:
        db.session.add(vehicle)
    db.session.commit()

    schedules = []
    base_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    for i, route in enumerate(routes):
        for j, vehicle in enumerate(vehicles):
            if i == j:
                departure_times = [
                    base_time + timedelta(hours=0),
                    base_time + timedelta(hours=6),
                    base_time + timedelta(hours=12),
                    base_time + timedelta(days=1, hours=0),
                    base_time + timedelta(days=1, hours=6),
                ]
                for dep_time in departure_times:
                    arrival_time = dep_time + timedelta(minutes=route.duration)
                    schedule = Schedule(
                        vehicle_id=vehicle.id,
                        route_id=route.id,
                        departure_time=dep_time,
                        arrival_time=arrival_time,
                        available_seats=vehicle.capacity,
                        status='Scheduled'
                    )
                    schedules.append(schedule)
    for schedule in schedules:
        db.session.add(schedule)
    db.session.commit()
    print("Sample data created successfully!")

def create_app():
    app = Flask(__name__)

    # Load configuration (may point to your own config module as needed)
    app.config.from_object('config.Config')

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(transport_bp)
    app.register_blueprint(voice_bp)

    # Audio folder setup
    audio_folder = app.config.get('AUDIO_FOLDER', 'static/audio')
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)

    # Database (and sample data) creation
    with app.app_context():
        db.create_all()
        create_sample_data()

    # Modern animated index route
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
