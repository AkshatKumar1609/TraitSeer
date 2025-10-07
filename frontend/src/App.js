import { useState, useEffect } from "react";

function App() {
  const [node, setNode] = useState(null);

  // Start game
  useEffect(() => {
    // fetch("http://127.0.0.1:8000/start")
    fetch("start")
      .then(res => res.json())
      .then(data => setNode(data));
  }, []);

  const handleAnswer = (answer) => {
    if (!node || node.guess) return;
    const nextNodeId = answer === "yes" ? (node.yes ?? node.right) : (node.no ?? node.left);

    // fetch(`http://127.0.0.1:8000/question/${nextNodeId}`)
    fetch(`question/${nextNodeId}`)
      .then(res => res.json())
      .then(data => setNode(data));
  };

  if (!node) return <h2>Loading...</h2>;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white shadow-lg rounded-2xl p-6 w-96 text-center">
        {node.guess ? (
          <h2 className="text-xl font-bold">I guess... {node.guess}!</h2>
        ) : (
          <>
            <h2 className="text-lg mb-4">{node.question ?? `Is ${node.feature} \u2264 ${node.threshold} ?`}</h2>
            <div className="flex gap-4 justify-center">
              <button
                className="px-4 py-2 bg-green-500 text-white rounded-lg"
                onClick={() => handleAnswer("yes")}
              >
                {node.right_label ?? "Yes"}
              </button>
              <button
                className="px-4 py-2 bg-red-500 text-white rounded-lg"
                onClick={() => handleAnswer("no")}
              >
                {node.left_label ?? "No"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
