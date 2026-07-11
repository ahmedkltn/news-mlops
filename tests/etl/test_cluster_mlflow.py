from etl import cluster

def test_log_clustering_metrics_called(monkeypatch):
    calls = {}
    class FakeMlflow:
        def set_tracking_uri(self, u): ...
        def set_experiment(self, n): ...
        def start_run(self):
            class Ctx:
                def __enter__(s): return s
                def __exit__(s, *a): return False
            return Ctx()
        def log_params(self, p): calls["params"] = p
        def log_metrics(self, m): calls["metrics"] = m
        def log_artifacts(self, path): calls["artifacts"] = path
    monkeypatch.setattr(cluster, "mlflow", FakeMlflow(), raising=False)
    cluster.log_clustering_run(n_topics=5, outlier_pct=0.2, min_cluster_size=3)
    assert calls["metrics"]["n_topics"] == 5
    assert calls["params"]["embed_model"] == "intfloat/multilingual-e5-small"
