from flask import Blueprint, request, jsonify
from app.models import ASRankSnapshot, FactRankPrediction
from datetime import datetime

rank_bp = Blueprint('rank', __name__)

@rank_bp.route('/<int:asn>/rank')
def get_rank(asn):
    date = request.args.get('date')
    rec = ASRankSnapshot.query.filter_by(asn=asn, date_id=datetime.fromisoformat(date).date()).first()
    if not rec:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "asn": asn,
        "date": rec.date_id.isoformat(),
        "caida_rank": rec.caida_rank,
        "local_cone_asns": rec.local_cone_asns
    })

@rank_bp.route('/<int:asn>/rank/history')
def rank_history(asn):
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    query = ASRankSnapshot.query.filter(ASRankSnapshot.asn==asn)
    if start:
        query = query.filter(ASRankSnapshot.date_id >= datetime.fromisoformat(start).date())
    if end:
        query = query.filter(ASRankSnapshot.date_id <= datetime.fromisoformat(end).date())
    snapshots = query.order_by(ASRankSnapshot.date_id).all()
    return jsonify([{
        "date": s.date_id.isoformat(),
        "caida_rank": s.caida_rank,
        "local_cone_asns": s.local_cone_asns
    } for s in snapshots])

@rank_bp.route('/<int:asn>/rank-forecast')
def rank_forecast(asn):
    date = request.args.get('date')
    pred = FactRankPrediction.query.filter_by(asn=asn, date_id=datetime.fromisoformat(date).date()).first()
    if not pred:
        return jsonify({"error": "No forecast available"}), 404
    return jsonify({
        "asn": asn,
        "date": pred.date_id.isoformat(),
        "predicted_rank": pred.predicted_rank,
        "confidence": float(pred.confidence)
    })
