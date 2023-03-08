from datetime import datetime


def format_ideas(ideas):
    """
    Receives a list of idea json objects
    and turns them into list of dicts
    """
    response = []
    for idea in ideas:
        i_dict = idea.dict()
        response.append(i_dict)
    return response

def format_reminders(reminders):
    """ 
    Receives a list of reminder json objects
    and turns them into list of dicts 
    """
    response = []
    for reminder in reminders:
        rem_dict = reminder.dict()
        rem_dict['time'] = datetime.fromtimestamp(rem_dict['time'])
        print("REMINDER: ",rem_dict['user'])
        response.append(rem_dict)

    return response

def format_timers(timers):
    
    response = []
    for timer in timers:
        timer_dict = timer.dict()

        timer_dict['time'] = datetime.fromtimestamp(timer_dict['time'])
        response.append(timer_dict)

    return response

