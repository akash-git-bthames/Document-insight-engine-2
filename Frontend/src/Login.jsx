import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const Login = ({ setAuthToken }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const params = new URLSearchParams();
      params.append("username", email); // Assuming 'email' is used as 'username'
      params.append("password", password);

      const response = await axios.post("http://65.2.86.51:8000/token", params, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      const token = response.data.access_token; // Adjusted to match your backend response
      setAuthToken(token);
      localStorage.setItem("authToken", token); // Store token in localStorage for session management
    } catch (error) {
      setError("Login failed. Please check your credentials.");
    }
  };

  const registerHandler = () => {
    navigate("/register");
  };

  return (
    <div className="h-full w-[50rem] bg-slate-200 rounded-lg shadow-lg shadow-slate-800 m-auto mt-16 flex flex-col  items-center justify-evenly p-10">
      <h1 className="text-3xl font-bold text-[rgb(61,106,255)]">Login</h1>
      <div className="flex flex-col gap-10">
        <input
          placeholder="Email"
          type="email"
          class="input"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          placeholder="Password"
          type="password"
          class="input"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      <button onClick={handleLogin}>Login</button>

      <p className="hover:cursor-pointer" onClick={registerHandler}>
        Not a user? Register Here!
      </p>

      {error && <p className="text-red-700">{error}</p>}
    </div>
  );
};

export default Login;
