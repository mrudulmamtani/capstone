import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { DemoRoleProvider } from "./components/DemoRoleProvider.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <DemoRoleProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </DemoRoleProvider>
  </React.StrictMode>
);
