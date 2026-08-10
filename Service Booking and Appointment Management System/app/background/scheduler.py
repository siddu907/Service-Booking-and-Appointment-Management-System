from apscheduler.schedulers.background import BackgroundScheduler

from app.background.reminder_tasks import send_upcoming_reminders

scheduler = BackgroundScheduler()
scheduler.add_job(send_upcoming_reminders, "interval", minutes=2)
