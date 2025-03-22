import requests
from app.models import db, ASRankSnapshot, DimASN, DimDate
from datetime import datetime

CAIDA_GRAPHQL = "https://api.asrank.caida.org/v2/graphql"

def load_caida_data(asn: int, date_str: str):
    query = """
    query($asn:[String!]!, $date:String!) {
      asns(asns:$asn, dateStart:$date, dateEnd:$date) {
        edges { node {
          asn rank date cone { numberAsns numberPrefixes numberAddresses }
        } }
      }
    }
    """
    resp = requests.post(CAIDA_GRAPHQL, json={"query": query, "variables": {"asn":[str(asn)], "date":date_str}})
    resp.raise_for_status()
    node = resp.json()["data"]["asns"]["edges"][0]["node"]

    date_obj = datetime.fromisoformat(node["date"]).date()
    # Ensure dims exist
    DimASN(asn=asn).save_if_not_exists()
    DimDate(date_id=date_obj).save_if_not_exists()

    snapshot = ASRankSnapshot(
        asn=asn, date_id=date_obj,
        caida_rank=node["rank"],
        caida_cone_asns=node["cone"]["numberAsns"],
        caida_cone_prefixes=node["cone"]["numberPrefixes"],
        caida_cone_addresses=node["cone"]["numberAddresses"]
    )
    db.session.merge(snapshot)
    db.session.commit()
