"""Explicit session-only device authentication; no token files or shared cache."""
import openeo


def connect_session(display):
    connection = openeo.connect('https://openeo.dataspace.copernicus.eu', default_timeout=30)
    connection.authenticate_oidc_device(
        store_refresh_token=False, max_poll_time=300, display=display,
    )
    return connection


def reconnect_job(run, connection):
    """Resume polling the existing job after a new login, without resubmitting it."""
    if run is not None and run.job is not None:
        run.job = connection.job(run.job.job_id)
