#!/usr/bin/env python
import traceback
from datetime import datetime
from app import create_app
from app.models import db, ETLJob
from app.etl.caida import load_caida_data  # Your CAIDA ETL function
from app.etl.cone_compute import compute_cone  # Your cone compute function

app = create_app()
app.app_context().push()  # Required for standalone script

def run_pending_jobs():
    pending_jobs = ETLJob.query.filter_by(status='pending').all()
    for job in pending_jobs:
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.session.commit()
        try:
            if job.job_type == 'asrank':
                # Trigger CAIDA data load and bottom-up cone compute
                load_caida_data(job.asn, job.date_id.isoformat())
                compute_cone(job.asn, job.date_id)
            # Future support for additional job types (e.g. radb, ripe, bgpview, cables) can be added here.
            job.status = 'complete'
        except Exception as e:
            job.status = 'error'
            job.error_msg = str(e)
            traceback.print_exc()
        finally:
            job.finished_at = datetime.utcnow()
            db.session.commit()

if __name__ == '__main__':
    run_pending_jobs()
