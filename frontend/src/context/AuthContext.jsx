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
        const fetchUser = async () => {
            if (token) {
                axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
                try {
                    const response = await axios.get(`${API}/auth/me`);
                    setUser(response.data);
                } catch (error) {
                    console.error("Failed to fetch user:", error);
                    // Token might be expired, clear it
                    localStorage.removeItem("token");
                    setToken(null);
                    setUser(null);
                }
            } else {
                delete axios.defaults.headers.common["Authorization"];
                setUser(null);
            }
            setLoading(false);
        };
        fetchUser();
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

            // Explicitly set header and fetch user immediately to ensure state is ready before navigation
            axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
            const userResponse = await axios.get(`${API}/auth/me`);
            setUser(userResponse.data);

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
