import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sklearn.tree import _tree

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# loaded = joblib.load('model.pkl')
loaded = joblib.load('backend/model.pkl')
if isinstance(loaded, tuple):
    clf, feature_names = loaded
else:
    clf = loaded
    feature_names = [f"feature_{i}" for i in range(clf.n_features_in_)]

tree = clf.tree_

# ---------- TREE EXPORT ----------
def build_node(node_id: int):
    if node_id < 0 or node_id >= tree.node_count:
        return {"error": f"node_id {node_id} out of range (0..{tree.node_count - 1})"}

    if tree.feature[node_id] != _tree.TREE_UNDEFINED:
        feature_index = int(tree.feature[node_id])
        feature_name = feature_names[feature_index]
        threshold = float(tree.threshold[node_id])

        # Simple yes/no for boolean-like features
        if 0.0 <= threshold <= 1.0 and abs(threshold - 0.5) < 0.01:
            qname = feature_name
            if qname.lower().startswith("is "):
                qname = qname[3:]
            elif qname.lower().startswith("is_"):
                qname = qname[3:]
            question_text = f"Is {qname}?"
            left_label, right_label = "No", "Yes"
        else:
            question_text = f"{feature_name} \u2264 {threshold} ?"
            left_label = f"{feature_name} \u2264 {threshold}"
            right_label = f"{feature_name} > {threshold}"

        return {
            "id": int(node_id),
            "feature": feature_name,
            "threshold": threshold,
            "question": question_text,
            "left_label": left_label,
            "right_label": right_label,
            "left": int(tree.children_left[node_id]),
            "right": int(tree.children_right[node_id]),
            "yes": int(tree.children_right[node_id]) if right_label.lower() == "yes" else int(tree.children_left[node_id]),
            "no": int(tree.children_left[node_id]) if right_label.lower() == "yes" else int(tree.children_right[node_id]),
        }

    # Leaf node
    values = tree.value[node_id].ravel()
    class_index = int(values.argmax())
    guess = clf.classes_[class_index]

    return {"id": int(node_id), "guess": str(guess)}

# ---------- API ENDPOINTS ----------
@app.get("/question/{node_id}")
def get_question(node_id: int):
    return build_node(node_id)

@app.get("/start")
def start():
    return build_node(0)
