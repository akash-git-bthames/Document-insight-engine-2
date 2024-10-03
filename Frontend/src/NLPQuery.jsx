// NLPQuery.jsx
import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import Analise from "./Analiser";
import { convertLength } from "@mui/material/styles/cssUtils";

const NLPQuery = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [typingEffect, setTypingEffect] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showAnaliser, setShowAnaliser] = useState(false);
  const [emptyQuery,setEmptyQuery]=useState(false);
  const responseContainerRef = useRef(null); // Ref to track the response container

  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  };

  const handleQuerySubmit = async () => {
    setEmptyQuery(false);
    setShowAnaliser(true);
    setTypingEffect("");
    if (query.length==0) {
      
       setEmptyQuery(true);
      
      return;
    }

    try {
      const res = await axios.get("http://65.2.86.51:8000/query", {
        params: { query },
      });
      setResponse(res.data.response);
      
      // Reset typing effect
      setShowAnaliser(false);
      setIsTyping(true); // Start typing effect
    } catch (error) {
      console.error("Error fetching response:", error);
      setResponse("Failed to retrieve response");
    }
  };

  useEffect(() => {
    if (isTyping && response) {
      let index = -1;
      const interval = setInterval(() => {
        setTypingEffect((prev) => { 
          return prev + response[index]});
        index++;
        if (index === response.length-1) {
          clearInterval(interval);
          setIsTyping(false); // Stop typing once done
        }
      },30);
      return () => clearInterval(interval);
    }
  }, [isTyping, response]);

  useEffect(() => {
    // Automatically scroll to the bottom when the typing effect is updating
    if (responseContainerRef.current) {
      responseContainerRef.current.scrollTop = responseContainerRef.current.scrollHeight;
    }
  }, [typingEffect]);

  return (
    <div>
      <h1 className="text-lg font-bold text-white">
        Ask Any Question related to document
      </h1>
      <textarea
        className="input h-40 w-[50vw] p-4 rounded-lg border-2 border-white"
        value={query}
        onChange={handleQueryChange}
        placeholder="Ask a question..."
        rows="4"
        cols="50"
      />

      <div className="flex justify-end">
        <button
          className="bg-white text-red-600 px-6 py-2 rounded-lg shadow-md hover:bg-red-500 hover:text-white transition-colors"
          onClick={handleQuerySubmit}
        >
          Submit
        </button>
      </div>
      <div className="mt-4">
        {/* Response container */}
        <div
          className="response-container bg-gray-800 w-[50vw] text-white p-4 rounded-lg overflow-y-auto"
          style={{ minHeight: "10rem", maxHeight: "20rem" }} // Limit the height to enable scrolling
          ref={responseContainerRef}
        >
          {typingEffect ? (
            <p>
              <strong>Response : </strong>{" "}
              <span className="typing-effect">{typingEffect}</span>
            </p>
          ) : (
            showAnaliser && (
              <div className="flex justify-center">
                {emptyQuery?<strong>Pleae Enter the Question</strong>:<Analise />}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};

export default NLPQuery;
