"""
Step 3 — Run BERTopic clustering on all articles that have embeddings.

Usage:
    python -m scripts.cluster
    python -m scripts.cluster --min-cluster-size 5
"""
import argparse
import logging
from etl.cluster import run_clustering

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(min_cluster_size: int = 3):
    logger.info("=== CLUSTER: running BERTopic ===")
    result = run_clustering(min_cluster_size=min_cluster_size)
    logger.info(f"=== CLUSTER done: {result} ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-cluster-size", type=int, default=3)
    args = parser.parse_args()
    main(min_cluster_size=args.min_cluster_size)
