from flask import Blueprint, request, jsonify
from app.models import db, RankAlert, AlertHistory

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/', methods=['POST'])
def create_alert():
    data = request.get_json()
    asn = data.get('asn')
    threshold = data.get('threshold_rank')
    direction = data.get('direction')
    if not (asn and threshold is not None and direction in ('above','below')):
        return jsonify(error="asn, threshold_rank, and direction required"), 400
    alert = RankAlert(asn=asn, threshold_rank=threshold, direction=direction)
    db.session.add(alert)
    db.session.commit()
    return jsonify(alert_id=alert.alert_id), 201

@alerts_bp.route('/<int:asn>', methods=['GET'])
def list_alerts(asn):
    alerts = RankAlert.query.filter_by(asn=asn).all()
    return jsonify([{
        "alert_id": a.alert_id,
        "threshold_rank": a.threshold_rank,
        "direction": a.direction,
        "enabled": a.enabled
    } for a in alerts])

@alerts_bp.route('/history/<int:alert_id>', methods=['GET'])
def alert_history(alert_id):
    entries = AlertHistory.query.filter_by(alert_id=alert_id).order_by(AlertHistory.triggered_at.desc()).all()
    return jsonify([{
        "triggered_at": e.triggered_at.isoformat(),
        "old_rank": e.old_rank,
        "new_rank": e.new_rank
    } for e in entries])
