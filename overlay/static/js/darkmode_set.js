// Description: Sets the darkmode class to the body if the user has darkmode enabled.
window.onload = () => {
    setInterval(() => {
        const darkmode = localStorage.getItem("darkmode") == "true";
        console.log(darkmode);
        darkmode ? document.body.classList.add("darkmode") : document.body.classList.remove("darkmode");
    }, 100);
}