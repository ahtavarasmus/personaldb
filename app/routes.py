from flask import Blueprint, render_template
from flask_login import login_required, current_user
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from . import twilio_client,celery_app,tz
from datetime import datetime, timedelta
from .messaging import *
import json


routes = Blueprint('routes',__name__,template_folder='templates')

@routes.route("/", methods=['POST','GET'])
def home():
    return render_template('home.html',user=current_user)

    
