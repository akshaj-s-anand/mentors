let currentVisibleIndex = 0;
const text = [
    document.getElementById('text1'),
    document.getElementById('text2'),
    document.getElementById('text3'),
];

setInterval(() => {
    // Hide the current text
    text[currentVisibleIndex].style.display = 'none';
    // Calculate the next index
    currentVisibleIndex = (currentVisibleIndex + 1) % text.length;
    // Show the next text
    text[currentVisibleIndex].style.display = 'block';
}, 3000); // Change text every 3 seconds


const texts = [
    "Explore unfamiliar territory, embrace diverse cultures, and discover opportunities that ignite your creativity.",
    "Promote local community engagement by enabling people to work within their own nearby areas."
];

let currentTextIndex = 0;

function swapText() {
    const textElement = document.getElementById('text');
    textElement.classList.add('hidden');

    setTimeout(() => {
        currentTextIndex = (currentTextIndex + 1) % texts.length;
        textElement.textContent = texts[currentTextIndex];
        textElement.classList.remove('hidden');
    }, 1000); // matches the transition duration
}

setInterval(swapText, 3000); // swap text every 3 seconds

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.col-md-6[data-link]').forEach(div => {
        div.addEventListener('click', () => {
            window.location.href = div.getAttribute('data-link');
        });
    });
});