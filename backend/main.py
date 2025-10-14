import os
import re
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sklearn.tree import _tree

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model + feature names
loaded = joblib.load('backend/model.pkl')
if isinstance(loaded, tuple):
    clf, feature_names = loaded
else:
    clf = loaded
    feature_names = [f"feature_{i}" for i in range(clf.n_features_in_)]

tree = clf.tree_

#Formatting helpers

EPS = 1e-6

def _format_number(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(n - round(n)) < EPS:
        return str(int(round(n)))
    return f"{n:.2f}".rstrip("0").rstrip(".")

def _humanize(text: str) -> str:
    if not text:
        return ""
    s = str(text)
    s = re.sub(r"[.\-]+", " ", s)
    s = s.replace("/", " / ")  
    s = re.sub(r"[_]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()

def _capitalize_q(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    s = s[0].upper() + s[1:]
    if not re.search(r"[?.!]$", s):
        s += "?"
    return s

def _strip_bool_prefix(s: str) -> str:
    # remove leading is/has/have to make a possessive phrase nicer
    return re.sub(r"^(is|has|have)\s+", "", s, flags=re.I).strip()

def _possessive_phrase(feature_h: str) -> str:
    f = _strip_bool_prefix(feature_h)
    return f"the character's {f}"

def _is_boolean_threshold(threshold) -> bool:
    try:
        t = float(threshold)
    except (TypeError, ValueError):
        return False
    return (0.0 <= t <= 1.0) and (abs(t - 0.5) < 1e-3 or abs(t - 0.0) < 1e-9 or abs(t - 1.0) < 1e-9)

def _split_base_value(raw_feature: str):
    """
    Try to split one-hot names like:
      - hair_color_blond -> ("hair color", "blond")
      - gender_male -> ("gender", "male")
      - is_male -> (None, "male")
      - hair:blond / hair==blond -> ("hair", "blond")
    Returns (base or None, value or None)
    """
    name = str(raw_feature)
    # Direct separators
    for sep in ("==", "=", ":", "__"):
        if sep in name:
            base, val = name.split(sep, 1)
            base_h = _humanize(base)
            val_h = _humanize(val)
            return (base_h or None), (val_h or None)

    tokens = name.split("_")
    if len(tokens) >= 3:
        base = " ".join(tokens[:-1])
        val = tokens[-1]
        return _humanize(base), _humanize(val)
    if len(tokens) == 2:
        first, second = tokens[0].lower(), tokens[1]
        if first in ("gender", "sex", "hair", "eye", "haircolor", "haircolour", "eyecolor"):
            return _humanize(tokens[0]), _humanize(tokens[1])
        if first in ("is", "has", "have"):
            return None, _humanize(tokens[1])
    return None, None

def _make_boolean_question(feature_name: str) -> str:
    base, val = _split_base_value(feature_name)
    if val:
        if (base or "") in ("gender", "sex"):
            q = f"is the character {val}"
        elif base:
            q = f"is the character's {base} {val}"
        else:
            q = f"is the character {val}"
        return _capitalize_q(q)

    feat_h = _humanize(feature_name)
    if feat_h.startswith("is "):
        return _capitalize_q(f"is the character {feat_h[3:]}")
    if feat_h.startswith("has "):
        return _capitalize_q(f"does the character have {feat_h[4:]}")
    if feat_h.startswith("have "):
        return _capitalize_q(f"does the character have {feat_h[5:]}")
    return _capitalize_q(f"is the character {feat_h}")

def _make_numeric_question(feature_name: str, threshold) -> str:
    feat_h = _humanize(feature_name)
    subj = _possessive_phrase(feat_h)
    thr = _format_number(threshold)
    return _capitalize_q(f"is {subj} ≤ {thr}")

#  TREE EXPORT 

def build_node(node_id: int):
    if node_id < 0 or node_id >= tree.node_count:
        raise HTTPException(status_code=404, detail=f"node_id {node_id} out of range (0..{tree.node_count - 1})")

    # Non-leaf
    if tree.feature[node_id] != _tree.TREE_UNDEFINED:
        feature_index = int(tree.feature[node_id])
        feature_name = feature_names[feature_index]
        threshold = float(tree.threshold[node_id])
        left_child = int(tree.children_left[node_id])
        right_child = int(tree.children_right[node_id])

        if _is_boolean_threshold(threshold):
            # Boolean / one-hot: left (<= 0.5) -> No, right (> 0.5) -> Yes
            question_text = _make_boolean_question(feature_name)
            yes_next = right_child
            no_next = left_child
        else:
            # Numeric: left (<= threshold) -> Yes, right (>) -> No
            question_text = _make_numeric_question(feature_name, threshold)
            yes_next = left_child
            no_next = right_child

        return {
            "id": int(node_id),
            "feature": feature_name,
            "threshold": threshold,
            "question": question_text,
            # Keep children for compatibility/debug
            "left": left_child,
            "right": right_child,
            # Explicit yes/no mapping for the frontend
            "yes": yes_next,
            "no": no_next,
            # Clean, consistent button labels
            "left_label": "No",
            "right_label": "Yes",
        }

    # Leaf node
    values = tree.value[node_id].ravel()
    class_index = int(values.argmax())
    guess = clf.classes_[class_index]
    return {"id": int(node_id), "guess": str(guess)}

#  API ENDPOINTS 
@app.get("/question/{node_id}")
def get_question(node_id: int):
    return build_node(node_id)

@app.get("/start")
def start():
    return build_node(0)

frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend/build")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        return FileResponse(os.path.join(frontend_dir, "index.html"))