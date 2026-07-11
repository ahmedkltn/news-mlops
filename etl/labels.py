import logging
logger = logging.getLogger(__name__)

_client_singleton = None
def _client():
    global _client_singleton
    if _client_singleton is None:
        import anthropic
        _client_singleton = anthropic.Anthropic()
    return _client_singleton

def label_topics(topic_keywords: dict[int, list[str]]) -> dict[int, str]:
    client = _client()
    labels_out = {}
    for tid, keywords in topic_keywords.items():
        kw = ", ".join(keywords[:8])
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=24,
                messages=[{"role": "user", "content":
                    f"Ces mots-clés décrivent un thème d'actualité tunisienne : {kw}. "
                    f"Donne un titre de thème court (2-4 mots), en français, sans ponctuation finale."}],
            )
            labels_out[tid] = next(
                (b.text.strip() for b in msg.content if b.type == "text"), f"Topic {tid}")
        except Exception as e:
            logger.warning(f"Label failed for topic {tid}: {e}")
            labels_out[tid] = f"Topic {tid}"
    return labels_out
