// Example JS for interactivity

// Show alert when Add to Cart button is clicked
document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".btn");

  buttons.forEach(button => {
    button.addEventListener("click", (e) => {
      e.preventDefault();
      alert("Item added to cart!");
    });
  });
});
// Example: Add to cart feature
document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".add-to-cart");

  buttons.forEach(button => {
    button.addEventListener("click", () => {
      const product = button.parentElement.querySelector("h3").textContent;
      alert(`${product} added to cart! 🛒`);
    });
  });
});
function addToCart(productName) {
  alert(productName + " added to cart!");
}

// Toggle Dark Mode
function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
}

// Dark mode CSS (we inject it through toggle)
document.addEventListener("DOMContentLoaded", () => {
  const style = document.createElement("style");
  style.innerHTML = `
    .dark-mode {
      background-color: #222;
      color: #f5f5f5;
    }
    .dark-mode .card {
      background: #333;
      color: #fff;
    }
    .dark-mode .btn {
      background: #f5f5f5;
      color: #222;
    }
  `;
  document.head.appendChild(style);
});
