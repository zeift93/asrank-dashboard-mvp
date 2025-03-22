#!/usr/bin/env python3
import traceback
from datetime import datetime
from app import create_app
from app.models import db, ETLJob, ASRankSnapshot, RankAlert, AlertHistory
from app.etl.caida import load_caida_data
from app.etl.cone_compute import compute_cone

app = create_app()
app.app_context().push()

def run_pending_jobs():
    pending_jobs = ETLJob.query.filter_by(status='pending').all()
    for job in pending_jobs:
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.session.commit()
        try:
            if job.job_type == 'asrank':
                # 1️⃣ Fetch CAIDA snapshot and compute local cone
                load_caida_data(job.asn, job.date_id.isoformat())
                compute_cone(job.asn, job.date_id)

                # 2️⃣ Trigger any rank alerts
                snapshot = ASRankSnapshot.query.get((job.asn, job.date_id))
                for alert in RankAlert.query.filter_by(asn=job.asn, enabled=True):
                    triggered = False
                    if alert.direction == 'above' and snapshot.caida_rank < alert.threshold_rank:
                        triggered = True
                    if alert.direction == 'below' and snapshot.caida_rank > alert.threshold_rank:
                        triggered = True
                    if triggered:
                        db.session.add(AlertHistory(
                            alert_id=alert.alert_id,
                            triggered_at=datetime.utcnow(),
                            old_rank=None,
                            new_rank=snapshot.caida_rank
                        ))
                db.session.commit()

            # TODO: handle other job_types (radb, ripe, bgpview, cables)

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
