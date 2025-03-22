from flask import Blueprint, request, jsonify
from app.models import ETLJob, db
from datetime import date

etl_bp = Blueprint('etl', __name__)

@etl_bp.route('/trigger', methods=['POST'])
def trigger_etl():
    data = request.get_json() or {}
    asn = data.get('asn')
    date_str = data.get('date')
    if not asn or not date_str:
        return jsonify({"error": "asn and date required"}), 400
    job = ETLJob(
        job_type='asrank',
        asn=int(asn),
        date_id=date.fromisoformat(date_str)
    )
    db.session.add(job)
    db.session.commit()
    return jsonify({"job_id": job.job_id}), 202

@etl_bp.route('/status', methods=['GET'])
def etl_status():
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"error": "job_id required"}), 400
    job = ETLJob.query.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    return jsonify({
        "job_id": job.job_id,
        "status": job.status,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "error_msg": job.error_msg
    })
