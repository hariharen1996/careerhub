from django import template
from django.utils.timesince import timesince 
from datetime import datetime
import pytz 

register = template.Library()


@register.filter
def posted_time_ago(value):
    if isinstance(value,str):
        value = datetime.strptime(value,'%Y-%m-%d %H-%M-%S')
    
    if value.tzinfo is None:
        value = pytz.utc.localize(value)
    
    localtimezone = pytz.timezone('Asia/kolkata')
    localtime = value.astimezone(localtimezone)
    time = timesince(localtime)
    split_time = time.split()
    if 'hour' in time:
        split_time = split_time[:-2]

    return ' '.join(split_time).strip(",") 