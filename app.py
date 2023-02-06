from flask import Flask, request
from pydantic import ValidationError
import json
from reminder import Reminder

app = Flask(__name__)

# reminder's time obj can be created with this: 
# dt = datetime.strptime("7/2/23 0:20","%d/%m/%y %H:%M")
@app.route("/reminder/new",methods=['POST'])
def create_reminder():
    try:
        print(request.json)
        new_reminder = Reminder(**request.json)
        new_reminder.save()
        return new_reminder.pk

    except ValidationError as e:
        print(e)
        return "Wasn't able to create reminder.",400

@app.route("/",methods=['GET','POST'])
def home():
    return "moi"


