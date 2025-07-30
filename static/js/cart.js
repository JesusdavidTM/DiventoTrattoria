// Variables globales
const cartIcon = document.getElementById('cart-icon');
const cartSidebar = document.getElementById('cart-sidebar');
const closeCartBtn = document.getElementById('close-cart');
const cartCountEl = document.getElementById('cart-count');
const cartItemsEl = document.getElementById('cart-items');
const cartTotalEl = document.getElementById('cart-total');
const checkoutBtn = document.getElementById('checkout-btn');

let cart = {};

// Toggle carrito
cartIcon.addEventListener('click', () => cartSidebar.classList.toggle('visible'));
closeCartBtn.addEventListener('click', () => cartSidebar.classList.remove('visible'));

// Añadir al carrito
document.querySelectorAll('.add-to-cart').forEach(btn => {
  btn.addEventListener('click', () => {
    const id = btn.dataset.id;
    cart[id] = (cart[id] || 0) + 1;
    updateCartUI();
  });
});

// Actualiza cuenta y detalle en sidebar
enableRetries
function updateCartUI() {
  cartCountEl.textContent = Object.values(cart).reduce((a,b)=>a+b,0);
  // Llamamos API para detalles
  fetch('/api/cart', {
    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({cart})
  })
  .then(r=>r.json())
  .then(data => {
    // Renderizamos lista
    cartItemsEl.innerHTML = data.items.map(i=>
      `<li>${i.qty} × ${i.name} <strong>$${i.subtotal.toFixed(2)}</strong></li>`
    ).join('');
    cartTotalEl.textContent = data.total.toFixed(2);
  });
}

// Checkout simulado\checkout
checkoutBtn.addEventListener('click', () => {
  alert('Total a pagar: $' + cartTotalEl.textContent);
});

document.getElementById('place-order').addEventListener('click', () => {
  // recoge name, phone, address + cart...
  // hace fetch('/checkout', { ... })
});
