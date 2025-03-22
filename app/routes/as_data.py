from flask import Blueprint, request, jsonify
from app.models import ASRankSnapshot
from app.models import db
from datetime import datetime

as_data_bp = Blueprint('as_data', __name__)

@as_data_bp.route('/<int:asn>', methods=['GET'])
def get_as_data(asn):
    date_str = request.args.get('snapshot_date')
    query = ASRankSnapshot.query.filter_by(asn=asn)
    if date_str:
        try:
            date_obj = datetime.fromisoformat(date_str).date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
        query = query.filter_by(date_id=date_obj)
    else:
        query = query.order_by(ASRankSnapshot.date_id.desc()).limit(1)
    record = query.first()
    if not record:
        return jsonify({"error": "No data found"}), 404
    return jsonify({
        "asn": record.asn,
        "date": record.date_id.isoformat(),
        "caida_rank": record.caida_rank,
        "caida_cone_asns": record.caida_cone_asns,
        "caida_cone_prefixes": record.caida_cone_prefixes,
        "caida_cone_addresses": record.caida_cone_addresses,
        "local_cone_asns": record.local_cone_asns
    })

@as_data_bp.route('/<int:asn>/history', methods=['GET'])
def get_as_history(asn):
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    query = ASRankSnapshot.query.filter_by(asn=asn)
    if start:
        query = query.filter(ASRankSnapshot.date_id >= datetime.fromisoformat(start).date())
    if end:
        query = query.filter(ASRankSnapshot.date_id <= datetime.fromisoformat(end).date())
    snapshots = query.order_by(ASRankSnapshot.date_id.asc()).all()
    return jsonify([{
        "date": s.date_id.isoformat(),
        "caida_rank": s.caida_rank,
        "caida_cone_asns": s.caida_cone_asns,
        "local_cone_asns": s.local_cone_asns
    } for s in snapshots])
