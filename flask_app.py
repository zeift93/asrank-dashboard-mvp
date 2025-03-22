import json, logging, traceback
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, request, jsonify, send_file
import mysql.connector
import pandas as pd
from io import BytesIO

from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

def compute_provider_quantities(requestor_asn, lost_asn, lost_month):
    current_snapshot = lost_month.strftime("%Y-%m-%d")
    baseline_snapshot = (lost_month - relativedelta(months=3)).replace(day=1).strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM as_relationships
        WHERE customer_asn=%s AND relationship_type='provider' AND snapshot_date=%s
    """, (lost_asn, current_snapshot))
    provider_qty = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM as_relationships
        WHERE customer_asn=%s AND relationship_type='provider' AND snapshot_date=%s
    """, (lost_asn, baseline_snapshot))
    baseline_qty = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return provider_qty, provider_qty - baseline_qty

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/as/<asn>', methods=['GET'])
def get_as_data(asn):
    snapshot_date = request.args.get('snapshot_date')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if snapshot_date:
        sql = "SELECT * FROM as_data WHERE asn=%s AND snapshot_date=%s"
        cursor.execute(sql, (asn, snapshot_date))
    else:
        sql = "SELECT * FROM as_data WHERE asn=%s ORDER BY snapshot_date DESC LIMIT 1"
        cursor.execute(sql, (asn,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(result or {}), (200 if result else 404)

@app.route('/api/historical', methods=['GET'])
def historical_data():
    asn = request.args.get('asn')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT snapshot_date, as_rank, cone_asn_count, customer_degree, transit_degree, peer_degree
        FROM as_data
        WHERE asn=%s AND snapshot_date BETWEEN %s AND %s
        ORDER BY snapshot_date
    """
    cursor.execute(sql, (asn, start_date, end_date))
    rows = cursor.fetchall()
    # Provider quantity fix: count upstream providers (customer_asn)
    cursor.execute("""
        SELECT snapshot_date, COUNT(*) AS provider_count
        FROM as_relationships
        WHERE customer_asn=%s AND relationship_type='provider'
          AND snapshot_date BETWEEN %s AND %s
        GROUP BY snapshot_date
    """, (asn, start_date, end_date))
    provider_counts = {r[0].isoformat(): r[1] for r in cursor.fetchall()}
    for row in rows:
        row['provider_quantity'] = provider_counts.get(row['snapshot_date'].isoformat(), 0)
    cursor.close()
    conn.close()
    return jsonify(rows)

@app.route('/api/competitor_analysis', methods=['GET'])
def competitor_analysis():
    requestor_asn = request.args.get('requestor_asn')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, requestor_asn, lost_asn, lost_month, lost_org, lost_cust_cone
        FROM lost_customers
        WHERE requestor_asn=%s AND lost_month BETWEEN %s AND %s
        ORDER BY lost_month
    """, (requestor_asn, start_date, end_date))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        lost_date = row['lost_month']
        provider_qty, new_provider_qty = compute_provider_quantities(
            requestor_asn, row['lost_asn'], lost_date
        )
        result.append({
            **row,
            'provider_quantity': provider_qty,
            'new_provider_quantity': new_provider_qty
        })
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/export/cone-analysis')
def export_cone_analysis():
    asn = request.args.get('asn')
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    conn = get_db_connection()
    df = pd.read_sql("""
        SELECT ROW_NUMBER() OVER (ORDER BY change_date) AS No,
               lost_asn AS 'Cust ASN', lost_org AS 'Customer Name',
               lost_cust_cone AS 'Customer Cone', provider_quantity AS 'Provider Qty',
               new_provider_quantity AS 'New Provider Qty'
        FROM lost_customers
        WHERE requestor_asn=%s AND lost_month BETWEEN %s AND %s
    """, conn, params=(asn, start, end))
    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    conn.close()
    return send_file(buf, download_name=f"asn_{asn}_cone_analysis.xlsx", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
