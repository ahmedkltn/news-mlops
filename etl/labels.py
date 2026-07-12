import logging
from etl.llm import complete

logger = logging.getLogger(__name__)


def label_topics(topic_keywords: dict[int, list[str]]) -> dict[int, str]:
    labels_out = {}
    for tid, keywords in topic_keywords.items():
        kw = ", ".join(keywords[:8])
        try:
            text = complete(
                user=(
                    f"Ces mots-clés décrivent un thème d'actualité tunisienne : {kw}. "
                    f"Donne un titre de thème court (2-4 mots), en français, sans ponctuation finale."
                ),
                max_tokens=24,
            )
            labels_out[tid] = text or f"Topic {tid}"
        except Exception as e:
            logger.warning(f"Label failed for topic {tid}: {e}")
            labels_out[tid] = f"Topic {tid}"
    return labels_out
