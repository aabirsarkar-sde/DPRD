const config = {
    BACKEND_URL: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
    API_PREFIX: '/api',
    get API_URL() {
        return `${this.BACKEND_URL}${this.API_PREFIX}`;
    }
};

export default config;
