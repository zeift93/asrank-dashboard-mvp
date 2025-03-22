from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ASN(db.Model):
    __tablename__ = 'dim_asn'
    asn = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    org_name = db.Column(db.String(255))
    country_iso = db.Column(db.String(2))

class DateDim(db.Model):
    __tablename__ = 'dim_date'
    date_id = db.Column(db.Date, primary_key=True)

class ASRankSnapshot(db.Model):
    __tablename__ = 'fact_asrank_snapshots'
    asn = db.Column(db.Integer, db.ForeignKey('dim_asn.asn'), primary_key=True)
    date_id = db.Column(db.Date, db.ForeignKey('dim_date.date_id'), primary_key=True)
    caida_rank = db.Column(db.Integer, nullable=False)
    caida_cone_asns = db.Column(db.Integer, nullable=False)
    caida_cone_prefixes = db.Column(db.Integer)
    caida_cone_addresses = db.Column(db.BigInteger)
    local_cone_asns = db.Column(db.Integer)

class ETLJob(db.Model):
    __tablename__ = 'etl_jobs'
    job_id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.Enum('cone','asrank','radb','ripe','bgpview','cables'), nullable=False)
    asn = db.Column(db.Integer, db.ForeignKey('dim_asn.asn'), nullable=False)
    date_id = db.Column(db.Date, db.ForeignKey('dim_date.date_id'), nullable=False)
    status = db.Column(db.Enum('pending','running','complete','error'), default='pending')
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    error_msg = db.Column(db.Text)

# Add other models similarly following the schema DDL
