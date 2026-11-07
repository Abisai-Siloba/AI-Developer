async function summarize() {
    const btn = document.getElementById("submit-btn");
    const output = document.getElementById("output");

    // show loading state
    btn.disabled = true;
    btn.textContent = "Summarizing...";
    output.textContent = "";
    
    try {
        const response = await fetch("/summarize", { /*...*/ });
        if (!response.ok) throw new Error("Server error");
        const data = await response.json();
        output.textContent = data.summary;
    } catch (error) {
        output.textContent = "Error summarizing text. Try again later.";

    } finally {
        btn.disabled = false;
        btn.textContent = "Sumarize";
    }
}
