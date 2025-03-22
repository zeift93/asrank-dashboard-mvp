from app.models import db, ASRankSnapshot
import networkx as nx

def compute_cone(asn: int, date_obj):
    # Build directed graph of c2p relationships for this date
    rels = db.session.execute(
        "SELECT provider_asn, customer_asn FROM as_relationships WHERE snapshot_date=%s",
        (date_obj,)
    ).fetchall()
    G = nx.DiGraph()
    G.add_edges_from([(r[1], r[0]) for r in rels])  # customer→provider

    cone = {node:1 for node in G.nodes() if G.out_degree(node)==0}
    for node in reversed(list(nx.topological_sort(G))):
        cone[node] = 1 + sum(cone.get(child,0) for child in G.successors(node))

    local_size = cone.get(asn, 1)
    snapshot = ASRankSnapshot.query.filter_by(asn=asn, date_id=date_obj).first()
    if snapshot:
        snapshot.local_cone_asns = local_size
        db.session.commit()
    else:
        raise RuntimeError(f"No ASRankSnapshot found for ASN {asn} on {date_obj}")
