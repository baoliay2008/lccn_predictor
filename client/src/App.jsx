import { useState, useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import Navbar from "./components/Navbar";
import PredictedContest from "./pages/Predicted/PredictedContests";
import PredictedRecords from "./pages/Predicted/PredictedRecords";
import Footer from "./components/Footer";

function App() {
  const initializeDataTheme = () =>
    JSON.parse(localStorage.getItem("dataTheme")) ?? "light";
  const [dataTheme, setDataTheme] = useState(initializeDataTheme());
  useEffect(() => {
    localStorage.setItem("dataTheme", JSON.stringify(dataTheme));
  }, [dataTheme]);

  // useEffect(() => {
  //   document.title = "Home";
  // }, []);

  return (
    <div data-theme={dataTheme}>
      <BrowserRouter>
        <Navbar dataTheme={dataTheme} setDataTheme={setDataTheme} />
        <div className="container mx-auto">
          <div className="grid h-20 card bg-base-300 rounded-box place-items-center">
            <p>🤞 Leetcode contest rating predictor 👀</p>
            <a
              className="grey-text text-lighten-3"
              target="_blank"
              rel="noreferrer noopener"
              href="https://github.com/baoliay2008/lccn_predictor"
            >
              <img
                src="https://img.shields.io/github/stars/baoliay2008/lccn_predictor?style=social"
                alt="Stars"
              />
            </a>
          </div>
          <div className="divider"></div>
          <Routes>
            <Route path="/" element={<PredictedContest />} />
            <Route
              path="/predicted/:titleSlug"
              element={<PredictedRecords />}
            />
          </Routes>
        </div>
        <div className="divider"></div>
        <Footer className="fixed bottom-0 left-0 w-full" />
      </BrowserRouter>
    </div>
  );
}

export default App;
