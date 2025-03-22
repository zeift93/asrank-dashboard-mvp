from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app.models import db
from datetime import datetime

competitor_bp = Blueprint('competitor', __name__)

@competitor_bp.route('/analysis', methods=['GET'])
def competitor_analysis():
    """
    Returns lost customer events for the requestor ASN within a given date range.
    This is a basic example — you can enhance it further to calculate competitor data.
    """
    requestor_asn = request.args.get('requestor_asn')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not requestor_asn or not start_date or not end_date:
        return jsonify({"error": "requestor_asn, start_date, and end_date are required"}), 400

    sql = text("""
        SELECT id, requestor_asn, lost_asn AS lost_customer_asn, lost_month AS event_date,
               lost_org AS customer_org, lost_cust_cone AS customer_cone
        FROM lost_customers
        WHERE requestor_asn = :asn
          AND lost_month BETWEEN :start_date AND :end_date
        ORDER BY lost_month
    """)
    result = db.session.execute(sql, {'asn': requestor_asn, 'start_date': start_date, 'end_date': end_date})
    rows = [dict(row) for row in result]
    return jsonify(rows)
