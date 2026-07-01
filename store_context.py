"""
store_context.py — NovaBuy fake store data: products, policies, and the AI system prompt.

This is the "knowledge base" injected into every AI conversation as a system prompt,
grounding responses in NovaBuy's specific products and policies.
"""

# ── Product Catalog ───────────────────────────────────────────────────────────
PRODUCTS: list[dict] = [
    {
        "id": "SKU-001",
        "name": "SoundWave Pro Earbuds",
        "price": 79.99,
        "category": "Audio",
        "in_stock": True,
        "description": "True wireless earbuds with active noise cancellation, 30-hour battery life, IPX5 water resistance, and premium sound quality.",
    },
    {
        "id": "SKU-002",
        "name": "UltraSlim Phone Case (iPhone 15)",
        "price": 19.99,
        "category": "Accessories",
        "in_stock": True,
        "description": "Military-grade drop protection in a 0.8mm slim profile. Available in Midnight Black, Pearl White, and Ocean Blue.",
    },
    {
        "id": "SKU-003",
        "name": "ProHub 7-in-1 USB-C Hub",
        "price": 54.99,
        "category": "Connectivity",
        "in_stock": True,
        "description": "7 ports: 4K HDMI, 3x USB-A 3.0, SD card reader, USB-C PD 100W pass-through, and 3.5mm audio jack.",
    },
    {
        "id": "SKU-004",
        "name": "ErgoPro Laptop Stand",
        "price": 44.99,
        "category": "Ergonomics",
        "in_stock": False,
        "description": "Aluminum adjustable laptop stand, 6 height levels, foldable design, supports up to 15kg. Currently out of stock — back in 2 weeks.",
    },
    {
        "id": "SKU-005",
        "name": "ClearView 4K Webcam",
        "price": 89.99,
        "category": "Video",
        "in_stock": True,
        "description": "4K 30fps webcam with built-in ring light, auto-focus, dual noise-cancelling microphones, and plug-and-play USB-C.",
    },
    {
        "id": "SKU-006",
        "name": "MagCharge 15W Wireless Pad",
        "price": 29.99,
        "category": "Charging",
        "in_stock": True,
        "description": "15W fast wireless charging pad compatible with Qi devices. Includes 2m braided cable and 20W adapter.",
    },
    {
        "id": "SKU-007",
        "name": "KeyMaster Mechanical Keyboard",
        "price": 119.99,
        "category": "Peripherals",
        "in_stock": True,
        "description": "TKL mechanical keyboard with Red switches, RGB per-key backlighting, aluminum frame, and dual USB-C/Bluetooth connectivity.",
    },
    {
        "id": "SKU-008",
        "name": "TrackPad Pro Mouse",
        "price": 49.99,
        "category": "Peripherals",
        "in_stock": True,
        "description": "Ergonomic wireless mouse with 4000 DPI, 6 programmable buttons, 60-hour battery, and silent clicks.",
    },
    {
        "id": "SKU-009",
        "name": "PowerBank 20000 Ultra",
        "price": 59.99,
        "category": "Charging",
        "in_stock": True,
        "description": "20,000mAh power bank with 65W USB-C PD output, 2x USB-A 18W, LED display, and airline-approved.",
    },
    {
        "id": "SKU-010",
        "name": 'ScreenGuard Pro (MacBook 14")',
        "price": 24.99,
        "category": "Accessories",
        "in_stock": True,
        "description": "Anti-glare tempered glass screen protector with blue-light filtering. Includes alignment frame for bubble-free installation.",
    },
]

# ── Store Policies ─────────────────────────────────────────────────────────────
POLICIES: str = """
SHIPPING POLICY:
- Standard shipping: 3-5 business days. FREE on orders over $50, otherwise $5.99.
- Express shipping: 1-2 business days for $12.99.
- Same-day delivery: Available in select cities for orders placed before 12pm for $19.99.
- International shipping: Available to 40+ countries, 7-14 business days, calculated at checkout.
- Orders are processed within 1 business day. A tracking number is emailed once shipped.

RETURN POLICY:
- 30-day hassle-free returns from date of delivery.
- Items must be in original condition and packaging.
- Electronics must be unopened/unused for a full refund; opened electronics qualify for exchange or store credit only.
- To start a return: email support@novabuy.store with your order ID and reason.
- Refunds processed within 5-7 business days after receiving the item.
- Return shipping is FREE for defective items; customer pays $4.99 for change-of-mind returns.

PAYMENT METHODS:
- Visa, Mastercard, American Express, Discover.
- PayPal, Apple Pay, Google Pay.
- Shop Pay (buy now, pay later in 4 interest-free installments).
- All transactions secured with 256-bit SSL encryption.

CUSTOMER SUPPORT:
- Email: support@novabuy.store
- Live chat: novabuy.store (during support hours)
- Support hours: Monday-Friday, 9am-6pm EST
- Response time: Within 4 hours during business hours

ORDER CANCELLATIONS:
- Orders can be cancelled within 1 hour of placement for a full refund.
- After 1 hour, if not yet shipped, contact support and we will try our best.
- Once shipped, the return policy applies.

WARRANTY:
- All NovaBuy products include a 12-month manufacturer warranty against defects.
- Extended warranty plans (2 or 3 years) available at checkout.
"""


# ── Product Catalog as formatted string ───────────────────────────────────────
def _build_product_list() -> str:
    lines = []
    for p in PRODUCTS:
        stock = "In Stock" if p["in_stock"] else "Out of Stock"
        lines.append(
            f"- {p['name']} | ID: {p['id']} | ${p['price']:.2f} | {stock}\n"
            f"  {p['description']}"
        )
    return "\n".join(lines)


import re


def detect_language(text: str) -> str:
    lowered = text.lower()
    if re.search(r"[\u0400-\u04ff]", text):
        return "Russian"
    if re.search(r"[\u0600-\u06ff]", text):
        return "Arabic"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "Chinese"
    if re.search(r"[\u3040-\u30ff]", text):
        return "Japanese"
    if re.search(r"[\u0900-\u097f]", text):
        return "Hindi"
    if any(token in lowered for token in ["hola", "gracias", "por favor", "pedido", "devolución"]):
        return "Spanish"
    if any(token in lowered for token in ["bonjour", "merci", "commande", "retour"]):
        return "French"
    if any(token in lowered for token in ["hallo", "danke", "bestellung", "rückgabe"]):
        return "German"
    if any(token in lowered for token in ["olá", "obrigado", "pedido", "devolução"]):
        return "Portuguese"
    return "English"


def build_system_prompt(
    *,
    preferred_language: str | None = None,
    user_name: str | None = None,
    extra_context: str | None = None,
) -> str:
    language_line = (
        f"- Reply in {preferred_language} and mirror the user's language naturally."
        if preferred_language
        else "- Reply in the same language the user used."
    )
    name_line = f"- The user's name is {user_name}." if user_name else ""
    context_line = f"\n\nEXTRA CONTEXT:\n{extra_context}" if extra_context else ""
    return f"""You are Genie, a friendly and knowledgeable customer support assistant for NovaBuy — a premium online electronics and accessories store. You work as part of the SupportGenie bot.

YOUR PERSONALITY:
- Warm, helpful, and professional
- Concise but thorough — don't over-explain unless asked
- Use light emoji usage: tasteful and contextual, not excessive
- Format responses clearly; use bullet points for lists

YOUR KNOWLEDGE BASE:

=== PRODUCT CATALOG ===
{_build_product_list()}

=== STORE POLICIES ===
{POLICIES}

YOUR RULES:
1. Only answer questions related to NovaBuy, its products, orders, and policies.
2. If asked about a specific order, ask for their Order ID (format: NB-XXXXX). You cannot look them up yourself — the system will handle that separately.
3. If you are genuinely unsure, say so honestly and suggest the human support option.
4. Never invent product specs, prices, or policies beyond what is listed above.
5. If a topic is completely unrelated to NovaBuy (e.g., general knowledge, other stores), politely decline and offer to connect them with support.
6. Keep responses concise — ideally under 200 words for Telegram readability.
7. Always format prices with a $ sign and 2 decimal places.
8. {language_line}
{name_line}

ESCALATION (recommend "Talk to Human" for these):
- Billing disputes or unexpected charges
- Account security or hacking concerns
- Legal complaints
- Customer expressing high frustration after multiple failed attempts
{context_line}
"""


# ── System Prompt ──────────────────────────────────────────────
SYSTEM_PROMPT: str = build_system_prompt()
