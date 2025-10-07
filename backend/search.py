import joblib
from sklearn.tree import _tree

loaded = joblib.load("model.pkl")

if isinstance(loaded, tuple):
    clf, feature_names = loaded
else:
    clf = loaded
    feature_names = [f"feature_{i}" for i in range(clf.n_features_in_)]

target_names = [str(c) for c in clf.classes_]

tree = clf.tree_

def find_character_path(model, feature_names, target_names, character_name):
    tree_ = model.tree_
    paths = []

    def recurse(node, path):
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_names[tree_.feature[node]]
            threshold = tree_.threshold[node]

            recurse(tree_.children_left[node], path + [(name, "<=", threshold)])
            recurse(tree_.children_right[node], path + [(name, ">", threshold)])
        else:
            values = tree_.value[node][0]
            for class_index, count in enumerate(values):
                if count > 0 and target_names[class_index] == character_name:
                    paths.append(path)


    recurse(0, [])
    return paths

def print_paths_human_readable(paths):
    for idx, path in enumerate(paths):
        print(f"Path {idx+1}:")
        for feature, cond, threshold in path:
            if cond == "<=":
                print(f"  - Is {feature} NO?")
            else:
                print(f"  - Is {feature} YES?")

character_to_find = "Kakashi HATAKE"
paths = find_character_path(clf, feature_names, target_names, character_to_find)
if paths:
    print_paths_human_readable(paths)
else:
    print(f"No path found for {character_to_find}.")
