import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";

const Signup = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const { signup } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        const success = await signup(email, password);
        if (success) {
            navigate("/");
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center px-4">
            <div className="max-w-md w-full space-y-8 p-8 border border-[#1f1f23] rounded-xl bg-[#111113]">
                <div className="text-center">
                    <h2 className="text-3xl font-bold text-[#fafafa]">Create an account</h2>
                    <p className="mt-2 text-[#a1a1aa]">Start generating PRDs today</p>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="email" className="sr-only">Email address</label>
                            <Input
                                id="email"
                                name="email"
                                type="email"
                                required
                                placeholder="Email address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="bg-[#18181b] border-[#27272a] text-[#fafafa]"
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="sr-only">Password</label>
                            <Input
                                id="password"
                                name="password"
                                type="password"
                                required
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="bg-[#18181b] border-[#27272a] text-[#fafafa]"
                            />
                        </div>
                    </div>

                    <Button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-[#fafafa] text-[#0a0a0b] hover:bg-[#e4e4e7]"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        Sign up
                    </Button>
                </form>
                <div className="text-center text-sm">
                    <span className="text-[#71717a]">Already have an account? </span>
                    <Link to="/login" className="font-medium text-[#fafafa] hover:underline">
                        Sign in
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default Signup;
