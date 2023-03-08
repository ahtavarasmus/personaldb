from flask import (Blueprint,session,flash,redirect,url_for,request,render_template)
from redis_om.model import NotFoundError
from .models import Idea,Reminder
from . import tz
from datetime import datetime

editing = Blueprint("editing",__name__,template_folder='templates')

@editing.route("/edit-idea-<pk>", methods=['POST','GET'])
def edit_idea(pk):
    user = session.get('user',default=dict())
    if not user:
        flash('login required')
        return redirect(url_for('.routes.home'))

    idea = Idea.find(Idea.pk == pk).first()
    cur_idea = idea.dict()
    if request.method == 'POST':
        new_idea = request.form.get('idea')
        if new_idea == "":
            Idea.delete(pk)
            flash("Idea deleted")
        else:
            print("NEW IDEA: ",new_idea)
            idea.message = new_idea
            idea.save()
            flash("Idea edited")
        return redirect(url_for('.routes.home'))
    print("HEREeeeeeeee")

    return render_template('edit_idea.html',
                           user=user,
                           cur_idea=cur_idea)


@editing.route("/edit-reminder-<pk>", methods=['POST','GET'])
def edit_reminder(pk):
    user = session.get('user',default=dict())
    if not user:
        flash("login required")
        return redirect(url_for('.routes.home'))

    try: 
        reminder = Reminder.find(Reminder.pk == pk).first()
    except NotFoundError:
        flash("reminder not found")
        return redirect(url_for('.routes.home'))

    rem_message_str = reminder.dict()['message']

    if request.method == 'POST':
        if 'time' in request.form:
            time = request.form.get('time')
            try:
                time_obj = datetime.strptime(str(time),
                    "%d/%m/%y %H:%M").replace(tzinfo=tz)
            except ValueError as e:
                print(e)
                flash("Date format not right")
                return render_template('edit_reminder.html',
                                       reminder_pk=pk)
            epoch_time = int(round(time_obj.timestamp()))
            reminder.time = epoch_time
            reminder.save()
            flash("Time changed")
        elif 'msg' in request.form:
            msg = request.form.get('msg')
            if msg == "":
                Reminder.delete(pk)
                flash("Reminder Deleted")
            else: 
                reminder.message = msg
                reminder.save()
                flash("Message changed")

        return redirect(url_for('.routes.home'))
    return render_template('edit_reminder.html',
                           user=user,
                           message=rem_message_str,
                           reminder_pk=pk
                           )


