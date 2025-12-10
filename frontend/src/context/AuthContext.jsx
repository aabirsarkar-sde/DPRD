import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";

const AuthContext = createContext();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem("token"));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            // Set default header for future requests
            axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
            // In a real app, you might validate the token with a /me endpoint here
            // For now, we'll assume if token exists, user is logged in (simplified)
            setUser({ email: "user@example.com" }); // Placeholder until we have a /me endpoint or decode token
        } else {
            delete axios.defaults.headers.common["Authorization"];
            setUser(null);
        }
        setLoading(false);
    }, [token]);

    const login = async (email, password) => {
        try {
            const formData = new FormData();
            formData.append("username", email);
            formData.append("password", password);

            const response = await axios.post(`${API}/auth/login`, formData);
            const { access_token } = response.data;

            setToken(access_token);
            localStorage.setItem("token", access_token);
            toast.success("Logged in successfully");
            return true;
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Login failed");
            return false;
        }
    };

    const signup = async (email, password) => {
        try {
            const response = await axios.post(`${API}/auth/signup`, { email, password });
            const { access_token } = response.data;

            setToken(access_token);
            localStorage.setItem("token", access_token);
            toast.success("Account created successfully");
            return true;
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Signup failed");
            return false;
        }
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem("token");
        delete axios.defaults.headers.common["Authorization"];
        toast.success("Logged out");
    };

    return (
        <AuthContext.Provider value={{ user, token, login, signup, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
