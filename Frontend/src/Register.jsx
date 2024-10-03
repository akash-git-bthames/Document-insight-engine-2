import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const Register = ({ setAuthToken }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      const response = await axios.post("http://65.2.86.51:8000/signup", { email, password, username});
      navigate("/");
    } catch (error) {
      setError("Login failed. Please check your credentials.");
    }
  };

  const loginHandler = () => {
    navigate("/")
  }

  return (
    <div className="h-[80vh] w-[35vw] bg-slate-200 rounded-lg shadow-lg shadow-slate-800 m-auto mt-16 flex flex-col  items-center justify-evenly p-10">
      <h1 className="text-3xl font-bold text-[rgb(61,106,255)]">Register</h1>
      <div className="flex flex-col gap-10">
        <input
          placeholder="Username"
          type="text"
          className="input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          placeholder="Email"
          type="email"
          className="input"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          placeholder="Password"
          type="password"
          className="input"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      <button onClick={handleRegister}>Sign Up</button>

      <p className="hover:cursor-pointer" onClick={loginHandler}>Already a User? Login here!</p>

      {error && <p className="text-red-700">{error}</p>}
    </div>
  );
};

export default Register;
