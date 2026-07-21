"""
APScheduler setup for all 5 KisanSetu automations.
Import start_scheduler() and shutdown_scheduler() from main.py.
"""
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    from automation.escalation_engine import check_and_escalate_grievances
    from automation.systemic_detector import detect_systemic_issues
    from automation.seasonal_intelligence import generate_seasonal_alerts
    from automation.relief_pipeline import check_pipeline_deadlines
    from automation.officer_scorecard import compute_officer_scores

    _scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    # Automation 1: escalation check every 60 seconds
    _scheduler.add_job(check_and_escalate_grievances, "interval", seconds=60,
                       id="escalation", replace_existing=True)

    # Automation 2: systemic detector every 5 minutes
    _scheduler.add_job(detect_systemic_issues, "interval", minutes=5,
                       id="systemic", replace_existing=True)

    # Automation 3: seasonal alerts daily at 06:00 IST
    _scheduler.add_job(generate_seasonal_alerts, CronTrigger(hour=6, minute=0),
                       id="seasonal", replace_existing=True)

    # Automation 4: pipeline deadline check every 60 seconds
    _scheduler.add_job(check_pipeline_deadlines, "interval", seconds=60,
                       id="pipeline", replace_existing=True)

    # Automation 5: officer scores daily at midnight
    _scheduler.add_job(compute_officer_scores, CronTrigger(hour=0, minute=0),
                       id="scores", replace_existing=True)

    _SCHEDULER_AVAILABLE = True

except ImportError:
    _scheduler = None
    _SCHEDULER_AVAILABLE = False


def start_scheduler():
    if _SCHEDULER_AVAILABLE and _scheduler and not _scheduler.running:
        _scheduler.start()


def shutdown_scheduler():
    if _SCHEDULER_AVAILABLE and _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
