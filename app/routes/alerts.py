from flask import Blueprint, request, jsonify
from app.models import db
from datetime import datetime

alerts_bp = Blueprint('alerts', __name__)

# Example model classes (if not already defined in models.py)
# from app.models import RankAlert, AlertHistory

@alerts_bp.route('/', methods=['POST'])
def create_alert():
    data = request.get_json() or {}
    asn = data.get('asn')
    threshold = data.get('threshold_rank')
    direction = data.get('direction')
    if not asn or threshold is None or not direction:
        return jsonify({"error": "asn, threshold_rank, and direction are required"}), 400
    # Assume RankAlert is defined in your models as:
    # class RankAlert(db.Model):
    #    alert_id = db.Column(db.Integer, primary_key=True)
    #    asn = db.Column(db.Integer, db.ForeignKey('dim_asn.asn'), nullable=False)
    #    threshold_rank = db.Column(db.Integer, nullable=False)
    #    direction = db.Column(db.Enum('above','below'), nullable=False)
    #    enabled = db.Column(db.Boolean, default=True)
    alert = RankAlert(asn=asn, threshold_rank=threshold, direction=direction)
    db.session.add(alert)
    db.session.commit()
    return jsonify({"alert_id": alert.alert_id}), 201

@alerts_bp.route('/history', methods=['GET'])
def get_alert_history():
    asn = request.args.get('asn')
    if not asn:
        return jsonify({"error": "asn is required"}), 400
    alerts = AlertHistory.query.filter_by(asn=asn).order_by(AlertHistory.triggered_at.desc()).all()
    history = [{
        "alert_id": alert.alert_id,
        "triggered_at": alert.triggered_at.isoformat(),
        "old_rank": alert.old_rank,
        "new_rank": alert.new_rank
    } for alert in alerts]
    return jsonify(history)
