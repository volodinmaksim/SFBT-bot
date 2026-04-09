from collections.abc import Awaitable, Callable
from datetime import datetime

from apscheduler.jobstores.base import JobLookupError

from loader import scheduler


def schedule_user_job(
    *,
    job_id: str,
    run_date: datetime,
    func: Callable[..., Awaitable[None]],
    args: list,
) -> None:
    if run_date.tzinfo is None:
        raise ValueError('run_date must be timezone-aware')

    scheduler.add_job(
        func,
        trigger='date',
        run_date=run_date.astimezone(scheduler.timezone),
        args=args,
        id=job_id,
        replace_existing=True,
        misfire_grace_time=12 * 60 * 60,
        coalesce=True,
        max_instances=1,
    )


def clear_user_story_jobs(*, tg_id: int) -> None:
    job_prefixes = (
        'after_link_yes_delay_1',
        'after_link_yes_delay_2',
        'after_link_yes_day_1',
        'after_link_yes_day_2',
    )

    for prefix in job_prefixes:
        try:
            scheduler.remove_job(job_id=f'{prefix}:{tg_id}')
        except JobLookupError:
            continue
