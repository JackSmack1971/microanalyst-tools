export const analyzeToken = async (token) => {
    const response = await fetch(`/api/analyze/${token}`);
    if (!response.ok) {
        throw new Error('Analysis failed');
    }
    return response.json();
};
