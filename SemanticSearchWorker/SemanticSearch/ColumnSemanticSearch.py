import numpy as np
<<<<<<< HEAD:BackEnd/ClimateFieldStations/SemanticSearch/ColumnSemanticSearch.py
#from sentence_transformers import SentenceTransformer
from BackEnd.ClimateFieldStations.SemanticSearch.TransformerData import CANONICAL, CANONICAL_META
from BackEnd.ClimateFieldStations.Data.CfSensorObject import CfSensorDataInfo
=======
from sentence_transformers import SentenceTransformer
from SemanticSearch.TransformerData import CANONICAL, CANONICAL_META
>>>>>>> 77bbdec5bf0515c0f63de8fbe2129ca8ab1c20d3:SemanticSearchWorker/SemanticSearch/ColumnSemanticSearch.py

class ColumnSemanticSearch:
    def __init__(self) -> None:
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.label_texts, self.label_to_param = self.build_label_index_with_meta(CANONICAL, CANONICAL_META) # type: ignore
        self.label_emb = np.array(self.model.encode(self.label_texts, normalize_embeddings=True))

    def normalize_token(self, s: str) -> str:
        return s.strip().lower()

    def build_label_index_with_meta(self, CANONICAL: dict, META: dict):
        label_texts = []
        label_to_param = []

        for param, phrases in CANONICAL.items():
            meta = META.get(param, {})
            units = meta.get("units", [])
            aggs = meta.get("aggregations", [])

            aggs_txt = ", ".join(aggs)

            for phrase in phrases:
                base = phrase.strip()

                if len(units) > 0 and len(aggs) > 0:
                    for unit in units:
                        label_texts.append(f"{base} unit {unit} aggregation {aggs_txt}")
                        label_to_param.append(param)

                if len(aggs) > 0:
                    label_texts.append(f"{base} aggregation {aggs_txt}")
                    label_to_param.append(param)

                if len(units) > 0:
                    for unit in units:
                        label_texts.append(f"{base} unit {unit}")
                        label_to_param.append(param)

                label_texts.append(base)
                label_to_param.append(param)
        seen = set()
        dedup_texts = []
        dedup_params = []
        for t, p in zip(label_texts, label_to_param):
            key = (self.normalize_token(t), p)
            if key not in seen:
                seen.add(key)
                dedup_texts.append(t)
                dedup_params.append(p)

        return dedup_texts, dedup_params

    def build_query(self, col_name: str, unit: str | None = None, agg: list | None = None) -> str:
        parts = [col_name]
        if unit: parts.append(f"unit {unit}")
        if agg:
            parts.append("aggregation " + ", ".join(agg))
        return " ".join(parts)
        
    def predict_param_from_text(
        self, 
        text: str,
        top1_thresh: float = 0.62,
        gap_thresh: float = 0.05,
    ):
        q = self.model.encode([text], normalize_embeddings=True)[0]
        sims = self.label_emb @ q

        order = np.argsort(-sims)
        best_idx = int(order[0])
        best_score = float(sims[best_idx])

        second_score = -1
        label_to_param_best = self.label_to_param[best_idx]
        for idx in order[1:]:
            if label_to_param_best == self.label_to_param[idx]:
                continue
            second_score = float(sims[int(order[idx])])
            break
            
        gap = best_score - second_score

        best_param = self.label_to_param[best_idx]
        is_unknown = (best_score < top1_thresh) or (gap < gap_thresh)
        final_param = "unknown" if is_unknown else best_param

        if is_unknown:
            return final_param, 1 - best_score
        return final_param, best_score

    def getPredictedParam(self, sensorDataInfo: dict):
        query  = self.build_query(sensorDataInfo.get("sensor"), sensorDataInfo.get("unit"), sensorDataInfo.get("aggregationsType")) # type: ignore
        return self.predict_param_from_text(query)
