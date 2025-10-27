# app/routes/voice.py

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import speech_recognition as sr
import pyttsx3
import threading
from datetime import datetime
from app.models.models import db, VoiceCommand, Route, Schedule

voice_bp = Blueprint('voice', __name__, url_prefix='/voice')

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)

    def listen_for_command(self, timeout=5):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            command = self.recognizer.recognize_google(audio).lower()
            return command
        except sr.WaitTimeoutError:
            return "Timeout: No speech detected"
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Speech recognition error: {e}"

    def speak_response(self, text):
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def process_transport_query(self, command):
        response = ""
        # Basic NLP for demo
        if "route" in command or "bus" in command or "train" in command:
            if "from" in command and "to" in command:
                try:
                    parts = command.split("from")[1].split("to")
                    source = parts[0].strip().title()
                    destination = parts[1].strip().title()
                except:
                    source, destination = "", ""
                routes = Route.query.filter(
                    Route.source.contains(source),
                    Route.destination.contains(destination)
                ).all()
                if routes:
                    response = f"Found {len(routes)} routes from {source} to {destination}. "
                    for route in routes[:3]:
                        response += f"Route {route.route_name}, Distance: {route.distance} km, Duration: {route.duration} min, Fare: {route.fare} ₹. "
                else:
                    response = f"No routes found from {source} to {destination}"
            else:
                response = "Please specify source and destination using 'from' and 'to'"
        elif "schedule" in command or "time" in command:
            schedules = Schedule.query.filter_by(status='Scheduled').limit(3).all()
            if schedules:
                response = f"Found {len(schedules)} upcoming schedules. "
                for schedule in schedules:
                    response += f"Vehicle {schedule.vehicle.vehicle_number} departing at {schedule.departure_time.strftime('%H:%M')} from {schedule.route.source} to {schedule.route.destination}. "
            else:
                response = "No schedules available"
        elif "book" in command or "ticket" in command:
            response = "To book a ticket, please specify the route and preferred time. You can say 'book ticket from Mumbai to Delhi at 10 AM'"
        elif "help" in command:
            response = ("I can help with routes, schedules, and booking tickets. "
                        "Try saying 'route from Mumbai to Delhi', 'show schedule', or 'book ticket'.")
        else:
            response = ("I didn't understand that command. Please try asking about routes, schedules, or booking tickets.")
        return response

voice_assistant = VoiceAssistant()

@voice_bp.route('/')
@login_required
def voice_interface():
    return render_template('voice/interface.html')

@voice_bp.route('/listen', methods=['POST'])
@login_required
def listen_command():
    try:
        start_time = datetime.now()
        command = voice_assistant.listen_for_command()
        processing_time = (datetime.now() - start_time).total_seconds()
        if command.startswith("Timeout") or command.startswith("Could not") or command.startswith("Speech recognition"):
            return jsonify({
                'success': False,
                'error': command,
                'processing_time': processing_time
            })
        response = voice_assistant.process_transport_query(command)
        voice_command = VoiceCommand(
            user_id=current_user.id,
            command_text=command,
            response_text=response,
            processing_time=processing_time
        )
        db.session.add(voice_command)
        db.session.commit()
        return jsonify({
            'success': True,
            'command': command,
            'response': response,
            'processing_time': processing_time
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@voice_bp.route('/speak', methods=['POST'])
@login_required
def speak_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        if text:
            threading.Thread(target=voice_assistant.speak_response, args=(text,), daemon=True).start()
            return jsonify({'success': True, 'message': 'Speaking...'})
        return jsonify({'success': False, 'error': 'No text provided'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@voice_bp.route('/history')
@login_required
def command_history():
    commands = VoiceCommand.query.filter_by(user_id=current_user.id).order_by(VoiceCommand.timestamp.desc()).limit(50).all()
    return render_template('voice/history.html', commands=commands)

@voice_bp.route('/test')
@login_required
def test_voice():
    return render_template('voice/test.html')
