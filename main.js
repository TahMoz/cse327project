const apiUrl = "/api/products";

let state = {
  q: "",
  category: "",
  min_price: "",
  max_price: "",
  sort: "newest",
  page: 1,
  per_page: 12
};

const debounce = (fn, wait=300) => {
  let t;
  return (...args)=> {
    clearTimeout(t);
    t = setTimeout(()=> fn.apply(this, args), wait);
  };
};

function buildQueryParams(params) {
  const esc = encodeURIComponent;
  return Object.keys(params)
    .filter(k => params[k] !== "" && params[k] !== null && params[k] !== undefined)
    .map(k => `${esc(k)}=${esc(params[k])}`)
    .join("&");
}

async function fetchProducts() {
  const params = {
    q: state.q,
    category: state.category,
    min_price: state.min_price || undefined,
    max_price: state.max_price || undefined,
    sort: state.sort,
    page: state.page,
    per_page: state.per_page
  };
  const url = apiUrl + "?" + buildQueryParams(params);
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Network response was not ok");
    const data = await res.json();
    renderProducts(data);
  } catch (err) {
    console.error("Fetch error:", err);
    document.getElementById("product-list").innerHTML = "<p>Error loading products.</p>";
  }
}

function renderProducts(data) {
  const container = document.getElementById("product-list");
  container.innerHTML = "";
  if (data.items.length === 0) {
    container.innerHTML = "<p>No products found.</p>";
  } else {
    data.items.forEach(p => {
      const card = document.createElement("div");
      card.className = "product-card";
      card.innerHTML = `
        <img src="${p.image_url || 'https://via.placeholder.com/400x300?text=No+Image'}" alt="${escapeHtml(p.name)}" />
        <h3>${escapeHtml(p.name)}</h3>
        <div class="price">৳ ${Number(p.price).toFixed(2)}</div>
        <p class="muted">${escapeHtml(p.category || '')}</p>
        <p>${escapeHtml((p.description || '').substring(0,120))}...</p>
      `;
      container.appendChild(card);
    });
  }
  document.getElementById("page-info").innerText = `Page ${data.page} of ${data.pages || 1} (Total: ${data.total})`;
  document.getElementById("prev-page").disabled = data.page <= 1;
  document.getElementById("next-page").disabled = data.page >= (data.pages || 1);
}

function escapeHtml(str) {
  return (str || "").replace(/[&<>"'`=\/]/g, s => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;', '`':'&#96;', '=':'&#61;', '/':'&#47;'
  })[s]);
}

document.addEventListener("DOMContentLoaded", ()=> {
  const searchInput = document.getElementById("global-search");
  const category = document.getElementById("filter-category");
  const minPrice = document.getElementById("min-price");
  const maxPrice = document.getElementById("max-price");
  const sort = document.getElementById("sort");
  const applyBtn = document.getElementById("apply-filters");

  searchInput.addEventListener("input", debounce((e)=>{
    state.q = e.target.value;
    state.page = 1;
    fetchProducts();
  }, 400));

  category.addEventListener("change", ()=> {
    state.category = category.value;
    state.page = 1;
  });

  applyBtn.addEventListener("click", ()=> {
    state.min_price = minPrice.value;
    state.max_price = maxPrice.value;
    state.sort = sort.value;
    state.page = 1;
    fetchProducts();
  });

  document.getElementById("prev-page").addEventListener("click", ()=> {
    if (state.page > 1) {
      state.page--;
      fetchProducts();
    }
  });
  document.getElementById("next-page").addEventListener("click", ()=> {
    state.page++;
    fetchProducts();
  });

  fetchProducts();
});
