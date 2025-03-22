-- Day0_create_schema.sql — Complete Dashboard Schema

-- Legacy Tables
CREATE TABLE peeringdb_networks (
  asn INT PRIMARY KEY,
  network_name VARCHAR(255),
  network_type VARCHAR(255),
  peering_policy VARCHAR(255),
  ixp_count INT,
  facility_count INT,
  traffic_category VARCHAR(255),
  geo_regions VARCHAR(255),
  last_update TIMESTAMP
);

CREATE TABLE peeringdb_ix (
  ix_id INT AUTO_INCREMENT PRIMARY KEY,
  asn INT NOT NULL,
  name VARCHAR(255),
  ipaddr4 VARCHAR(45),
  port_size VARCHAR(64),
  discovered_date DATE,
  FOREIGN KEY(asn) REFERENCES peeringdb_networks(asn)
);

CREATE TABLE peeringdb_fac (
  fac_id INT AUTO_INCREMENT PRIMARY KEY,
  asn INT NOT NULL,
  name VARCHAR(255),
  city VARCHAR(100),
  country CHAR(2),
  discovered_date DATE,
  FOREIGN KEY(asn) REFERENCES peeringdb_networks(asn)
);

CREATE TABLE as_data (
  asn INT NOT NULL,
  snapshot_date DATE NOT NULL,
  as_rank INT,
  cone_asn_count INT,
  customer_degree INT,
  transit_degree INT,
  peer_degree INT,
  PRIMARY KEY(asn,snapshot_date)
);

CREATE TABLE as_relationships (
  provider_asn INT NOT NULL,
  customer_asn INT NOT NULL,
  relationship_type ENUM('provider','customer','peer') NOT NULL,
  snapshot_date DATE NOT NULL,
  PRIMARY KEY(provider_asn,customer_asn,snapshot_date)
);

CREATE TABLE lost_customers (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  requestor_asn INT NOT NULL,
  lost_asn INT NOT NULL,
  lost_month DATE NOT NULL,
  lost_org VARCHAR(255),
  lost_cust_cone INT
);

CREATE TABLE etl_metadata (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  process_name VARCHAR(255),
  status VARCHAR(50),
  details TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension Tables
CREATE TABLE dim_asn (asn INT PRIMARY KEY, name VARCHAR(255), org_name VARCHAR(255), country_iso CHAR(2));
CREATE TABLE dim_date (date_id DATE PRIMARY KEY);
CREATE TABLE dim_country (iso CHAR(2) PRIMARY KEY, name VARCHAR(255), continent VARCHAR(50));
CREATE TABLE dim_ixp (ixp_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), city VARCHAR(100), country_iso CHAR(2), FOREIGN KEY(country_iso) REFERENCES dim_country(iso));
CREATE TABLE dim_facility (fac_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), city VARCHAR(100), country_iso CHAR(2), FOREIGN KEY(country_iso) REFERENCES dim_country(iso));
CREATE TABLE dim_submarine_cable (cable_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), owner VARCHAR(255));
CREATE TABLE dim_prefix (prefix VARCHAR(50) PRIMARY KEY, origin_asn INT, last_updated DATE, FOREIGN KEY(origin_asn) REFERENCES dim_asn(asn));

-- Fact Tables
CREATE TABLE fact_asrank_snapshots (
  asn INT NOT NULL, date_id DATE NOT NULL, caida_rank INT NOT NULL,
  caida_cone_asns INT NOT NULL, caida_cone_prefixes INT, caida_cone_addresses BIGINT,
  local_cone_asns INT, PRIMARY KEY(asn,date_id),
  FOREIGN KEY(asn) REFERENCES dim_asn(asn), FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
) PARTITION BY RANGE (YEAR(date_id));

CREATE TABLE fact_cone_change (
  id BIGINT AUTO_INCREMENT PRIMARY KEY, requestor_asn INT NOT NULL, customer_asn INT NOT NULL,
  change_date DATE NOT NULL, change_type ENUM('added','removed') NOT NULL, new_provider_asn INT NULL,
  FOREIGN KEY(requestor_asn) REFERENCES dim_asn(asn), FOREIGN KEY(customer_asn) REFERENCES dim_asn(asn),
  FOREIGN KEY(new_provider_asn) REFERENCES dim_asn(asn)
);

CREATE TABLE fact_competitor_metrics (
  id BIGINT AUTO_INCREMENT PRIMARY KEY, asn INT NOT NULL, competitor_asn INT NOT NULL,
  date_id DATE NOT NULL, competitor_cone_asns INT, competitor_rank INT,
  UNIQUE(asn,competitor_asn,date_id), FOREIGN KEY(asn) REFERENCES dim_asn(asn),
  FOREIGN KEY(competitor_asn) REFERENCES dim_asn(asn), FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
) PARTITION BY RANGE (YEAR(date_id));

CREATE TABLE fact_rank_predictions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY, asn INT NOT NULL, date_id DATE NOT NULL,
  predicted_rank INT NOT NULL, confidence DECIMAL(5,4),
  UNIQUE(asn,date_id), FOREIGN KEY(asn) REFERENCES dim_asn(asn), FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
) PARTITION BY RANGE (YEAR(date_id));

CREATE TABLE fact_irr_routes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY, asn INT NOT NULL, prefix VARCHAR(50) NOT NULL,
  source ENUM('RADB','ARIN','RIPE','APNIC'), registered_date DATE,
  UNIQUE(asn,prefix,source), FOREIGN KEY(asn) REFERENCES dim_asn(asn),
  FOREIGN KEY(prefix) REFERENCES dim_prefix(prefix)
) PARTITION BY RANGE (YEAR(registered_date));

CREATE TABLE fact_prefix_visibility (
  id BIGINT AUTO_INCREMENT PRIMARY KEY, prefix VARCHAR(50) NOT NULL, date_id DATE NOT NULL,
  announced_asn INT NOT NULL, UNIQUE(prefix,date_id,announced_asn),
  FOREIGN KEY(prefix) REFERENCES dim_prefix(prefix), FOREIGN KEY(date_id) REFERENCES dim_date(date_id),
  FOREIGN KEY(announced_asn) REFERENCES dim_asn(asn)
) PARTITION BY RANGE (YEAR(date_id));

CREATE TABLE fact_bgp_metrics (
  id BIGINT AUTO_INCREMENT PRIMARY KEY, asn INT NOT NULL, date_id DATE NOT NULL,
  prefix_count INT, peer_count INT, provider_count INT,
  UNIQUE(asn,date_id), FOREIGN KEY(asn) REFERENCES dim_asn(asn),
  FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
) PARTITION BY RANGE (YEAR(date_id));

CREATE TABLE fact_cable_presence (
  id BIGINT AUTO_INCREMENT PRIMARY KEY, asn INT NOT NULL, cable_id INT NOT NULL, date_id DATE NOT NULL,
  UNIQUE(asn,cable_id,date_id), FOREIGN KEY(asn) REFERENCES dim_asn(asn),
  FOREIGN KEY(cable_id) REFERENCES dim_submarine_cable(cable_id), FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);

-- ETL JOB QUEUE
CREATE TABLE etl_jobs (
  job_id INT AUTO_INCREMENT PRIMARY KEY, job_type ENUM('cone','asrank','radb','ripe','bgpview','cables') NOT NULL,
  asn INT NOT NULL, date_id DATE NOT NULL, status ENUM('pending','running','complete','error') DEFAULT 'pending',
  started_at DATETIME, finished_at DATETIME, error_msg TEXT,
  UNIQUE(asn,date_id,job_type), FOREIGN KEY(asn) REFERENCES dim_asn(asn), FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);

-- Alerts
CREATE TABLE rank_alerts (
  alert_id INT AUTO_INCREMENT PRIMARY KEY, asn INT NOT NULL,
  threshold_rank INT NOT NULL, direction ENUM('above','below'), enabled BOOLEAN DEFAULT TRUE,
  FOREIGN KEY(asn) REFERENCES dim_asn(asn)
);

CREATE TABLE alert_history (
  history_id BIGINT AUTO_INCREMENT PRIMARY KEY, alert_id INT NOT NULL, triggered_at DATETIME NOT NULL,
  old_rank INT, new_rank INT, FOREIGN KEY(alert_id) REFERENCES rank_alerts(alert_id)
);

-- ML Metadata
CREATE TABLE ml_models (
  model_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), version VARCHAR(32), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ml_predictions (
  prediction_id BIGINT AUTO_INCREMENT PRIMARY KEY, model_id INT NOT NULL, asn INT NOT NULL,
  date_id DATE NOT NULL, prediction JSON, UNIQUE(model_id,asn,date_id),
  FOREIGN KEY(model_id) REFERENCES ml_models(model_id), FOREIGN KEY(asn) REFERENCES dim_asn(asn), FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);
