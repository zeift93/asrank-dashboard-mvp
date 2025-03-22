from flask import Blueprint, send_file, request
import pandas as pd
from io import BytesIO
from app.models import db
from sqlalchemy import text

export_bp = Blueprint('export', __name__)

@export_bp.route('/raw-cone', methods=['GET'])
def export_raw_cone():
    asn = request.args.get('asn')
    date = request.args.get('date')
    sql = text("""
        SELECT ROW_NUMBER() OVER() AS Number,
               date_id AS Date,
               asn AS ASN,
               caida_cone_asns AS Customer_Cone,
               caida_cone_prefixes AS Prefix_Count,
               caida_cone_addresses AS Address_Count
        FROM fact_asrank_snapshots
        WHERE asn=:asn AND date_id=:date
    """)
    df = pd.read_sql(sql, db.session.bind, params={'asn': asn, 'date': date})
    buf = BytesIO()
    df.to_excel(buf, index=False, sheet_name="Raw CAIDA Cone")
    buf.seek(0)
    return send_file(buf,
                     download_name=f"asn_{asn}_raw_cone_{date}.xlsx",
                     as_attachment=True)

@export_bp.route('/cone-analysis', methods=['GET'])
def export_cone_analysis():
    asn = request.args.get('asn')
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    sql = text("""
        SELECT ROW_NUMBER() OVER(ORDER BY change_date) AS Number,
               change_date AS Date,
               change_type AS Relationship,
               customer_asn AS 'Cust ASN',
               lost_org AS 'Customer Name',
               lost_cust_cone AS 'Customer Cone',
               new_provider_asn AS 'Competitor ASN'
        FROM fact_cone_change
        WHERE requestor_asn=:asn
          AND change_date BETWEEN :start AND :end
        ORDER BY change_date
    """)
    df = pd.read_sql(sql, db.session.bind, params={'asn': asn, 'start': start, 'end': end})
    buf = BytesIO()
    df.to_excel(buf, index=False, sheet_name="Cone Analysis")
    buf.seek(0)
    return send_file(buf,
                     download_name=f"asn_{asn}_cone_analysis_{start}_to_{end}.xlsx",
                     as_attachment=True)
