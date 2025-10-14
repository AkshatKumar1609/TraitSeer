import { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const aboutRef = useRef(null);
  const gameRef = useRef(null);
  const contactRef = useRef(null);
  const footerRef = useRef(null);

  const [node, setNode] = useState(null);
  const [answers, setAnswers] = useState([]);

  useEffect(() => { startGame(); }, []);

  const startGame = () => {
    // fetch("/start")
    fetch("start")
      .then((res) => res.json())
      .then((data) => setNode(data))
      .catch((err) => console.error("Error fetching start node:", err));
  };

  const handleAnswer = (answer) => {
    if (!node || node.guess) return;

    // record player choices
    setAnswers((prev) => [
      ...prev,
      {
        question: node.question ?? `Is ${node.feature} ≤ ${node.threshold}?`,
        answer: answer === "yes" ? "Yes" : "No",
      },
    ]);

    const nextNodeId =
      answer === "yes" ? node.yes ?? node.right : node.no ?? node.left;

    // fetch(`http://127.0.0.1:8000/question/${nextNodeId}`)
    fetch(`question/${nextNodeId}`)
      .then((res) => res.json())
      .then((data) => setNode(data));
  };

  const scrollTo = (ref) => ref.current.scrollIntoView({ behavior: "smooth" });

  const resetGame = () => {
    setNode(null);
    setAnswers([]);
    fetch("start")
      .then((res) => res.json())
      .then((data) => {
        setNode(data);
        setTimeout(() => scrollTo(gameRef), 200);
      });
  };

  if (!node) return <h2 className="loading">Loading...</h2>;

  return (
    <div className="app">
      {/* ---------- HEADER ---------- */}
      <nav className="navbar improved-header">
        <div className="nav-left">
          <img src="/icon.png" alt="logo" className="header-logo" />
          <span className="brand-name">
            Trait<span>Seer</span>
          </span>
        </div>

        <ul className="nav-links improved-links">
          <li onClick={() => scrollTo(aboutRef)}>Home</li>
          <li onClick={() => scrollTo(gameRef)}>Guess</li>
          <li onClick={() => scrollTo(contactRef)}>Contact Us</li>
        </ul>
      </nav>

      {/* ---------- ABOUT ---------- */}
      <section
        ref={aboutRef}
        className="page about"
        style={{ backgroundImage: `url(/background.jpg)` }}
      >
        <div className="about-content">
          <h1>Discover Which Anime Character You’re Thinking Of with TraitSeer!</h1>
          <p>
            Think of any anime character — answer a few Yes/No questions and let{" "}
            <strong>TraitSeer</strong> use its ML‑powered decision tree to uncover
            who you have in mind.
          </p>
          <button className="cta-btn" onClick={() => scrollTo(gameRef)}>
            Start Guessing
          </button>
        </div>
      </section>

      {/* ---------- GAME ---------- */}
      <section ref={gameRef} className="page game">
        <div className="game-container">
          <h2 className="game-title">Answer the Questions</h2>
          <div className="game-card">
            {node.guess ? (
              <div className="character-result">
                <div className="result-details">
                  <h4 className="subheader">TraitSeer Thinks...</h4>
                  <h2 className="character-name">{node.guess}</h2>
                  <p className="character-desc">
                    {`${node.guess} is a beloved anime character, known for their 
                    courage, loyalty, and the spark that makes anime unforgettable.`}
                  </p>

                  {answers.length > 0 && (
                    <div className="answers-summary">
                      <h4>Your Answers</h4>
                      <ul>
                        {answers.map((item, index) => (
                          <li key={index}>
                            <strong>Q:</strong> {item.question}{" "}
                            <span
                              className={item.answer === "Yes" ? "yes" : "no"}
                            >
                              → {item.answer}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="character-actions">
                    <button className="recalc-btn" onClick={resetGame}>
                      Recalculate / Try Again
                    </button>
                    <button
                      className="learn-btn"
                      onClick={() =>
                        window.open(
                          `https://myanimelist.net/search/all?q=${encodeURIComponent(
                            node.guess
                          )}`,
                          "_blank"
                        )
                      }
                    >
                      Learn More About {node.guess} →
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <>
                <div className="game-question">
                  <h3>
                    {node.question ?? `Is ${node.feature} ≤ ${node.threshold}?`}
                  </h3>
                </div>

                <div className="game-actions">
                  <button
                    className="yes-modern"
                    onClick={() => handleAnswer("yes")}
                  >
                    {node.right_label ?? "Yes"}
                  </button>
                  <button
                    className="no-modern"
                    onClick={() => handleAnswer("no")}
                  >
                    {node.left_label ?? "No"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ---------- CONTACT ---------- */}
      <section ref={contactRef} className="page contact">
        <div className="contact-container">
          <div className="contact-left">
            <div className="contact-icon-wrapper">
              <img src="/icon.png" alt="icon" className="contact-icon" />
            </div>
            <h2>Contact TraitSeer</h2>
            <p>
              Have questions, feedback, or ideas for TraitSeer? Get in touch —
              we’d love to hear from you!
            </p>
            <p>
              📧{" "}
              <a href="mailto:support@traitseer.app">support@traitseer.app</a>
            </p>
            <small>We usually respond within 24 hours.</small>
          </div>

          <form className="contact-right">
            <div className="form-row">
              <input type="text" placeholder="Name" required />
              <input type="email" placeholder="Email" required />
            </div>
            <input type="text" placeholder="Subject" />
            <textarea placeholder="Your message..."></textarea>
            <button className="send-btn" type="submit">
              Send Message
            </button>
          </form>
        </div>
      </section>

      {/* ---------- FOOTER ---------- */}
      <footer ref={footerRef} className="footer">
        <div className="footer-inner">
          <p className="footer-text">
            🧠 Built with <strong>Machine Learning (Decision Tree)</strong> by
            the TraitSeer Team.
          </p>
          <p className="footer-sub">
            © {new Date().getFullYear()} TraitSeer. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;