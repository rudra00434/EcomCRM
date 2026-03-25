import json
import os
import re
from datetime import date
from typing import Any

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone

from .models import Customer, Product, Tag, order


SESSION_KEY = "ask_to_ai_history"
MAX_HISTORY_MESSAGES = 8
MAX_CONTEXT_DOCS = 6
DEFAULT_EXTRACT_MODEL = os.getenv("GROQ_EXTRACT_MODEL", "openai/gpt-oss-20b")
DEFAULT_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "openai/gpt-oss-20b")


STATIC_SITE_DOCS = [
    {
        "title": "Dashboard",
        "url_name": "home",
        "tags": ["overview", "dashboard", "metrics", "navigation"],
        "content": (
            "The dashboard is the command center of EcomCRM. It shows total customers, total orders, pending orders, "
            "delivered orders, out for delivery orders, recent customer activity, recent order activity, and charts "
            "based on live order status and orders per day data."
        ),
    },
    {
        "title": "Customers",
        "url_name": "customer_list",
        "tags": ["customers", "profiles", "crm", "navigation"],
        "content": (
            "The customer section lets users browse customer profiles, open customer detail pages, edit customer data, "
            "delete customers, and place orders for a specific customer. Individual customer pages show contact details, "
            "location data, order history, and order filters."
        ),
    },
    {
        "title": "Products",
        "url_name": "product",
        "tags": ["products", "inventory", "catalog", "navigation"],
        "content": (
            "The product section manages the catalog. Users can add products, update products, delete products, review "
            "product images, view pricing, categories, descriptions, and assigned tags."
        ),
    },
    {
        "title": "Orders",
        "url_name": "order_list",
        "tags": ["orders", "fulfillment", "delivery", "navigation"],
        "content": (
            "The order section tracks the order lifecycle. Users can create new orders, edit order status, cancel orders, "
            "review linked customer information, and see order progress across Pending, Out for delivery, and Delivered."
        ),
    },
    {
        "title": "Tags",
        "url_name": "tag_list",
        "tags": ["tags", "taxonomy", "catalog", "navigation"],
        "content": (
            "The tags section manages product taxonomy. Users can view tags, import tags from CSV, and use tags to "
            "organize products."
        ),
    },
    {
        "title": "Analytics",
        "url_name": "analytics",
        "tags": ["analytics", "charts", "metrics", "navigation"],
        "content": (
            "The analytics page provides charts for order status volume, status distribution, daily order trends, "
            "and order counts per day using real order records from the database."
        ),
    },
    {
        "title": "Revenue",
        "url_name": "revenue",
        "tags": ["revenue", "finance", "analytics", "navigation"],
        "content": (
            "The revenue page calculates per day revenue from delivered orders, average daily revenue, projected annual "
            "revenue, pipeline revenue from pending and out for delivery orders, and a best revenue day view."
        ),
    },
    {
        "title": "About",
        "url_name": "about",
        "tags": ["about", "company", "navigation"],
        "content": (
            "The about page explains what EcomCRM does, the product philosophy, and the core pillars of customer memory, "
            "operational control, and revenue visibility."
        ),
    },
    {
        "title": "Contact",
        "url_name": "contact",
        "tags": ["contact", "support", "navigation"],
        "content": (
            "The contact page shares support information including phone, email, location, support hours, and when "
            "to reach out for help."
        ),
    },
    {
        "title": "Media Storage",
        "url_name": "product",
        "tags": ["media", "cloudinary", "images", "storage"],
        "content": (
            "Customer and product images use Cloudinary-backed media storage when Cloudinary environment variables are "
            "configured. Existing local media has been migrated to Cloudinary-compatible storage paths."
        ),
    },
]


def get_ask_ai_page_context() -> dict[str, Any]:
    return {
        "ai_history": get_chat_history(None),
        "groq_available": is_groq_ready(),
        "chat_model": os.getenv("GROQ_CHAT_MODEL", DEFAULT_CHAT_MODEL),
        "suggested_prompts": [
            "What can I do from the dashboard?",
            "How is revenue calculated on this website?",
            "Tell me about customer and order management here.",
            "Where do product images get stored?",
        ],
        "assistant_capabilities": [
            "Explains how each page of the website works",
            "Uses live database signals like customers, orders, statuses, and revenue",
            "Can point you to the right page or route for a task",
            "Uses grounded retrieval before answering",
        ],
    }


def get_chat_history(session) -> list[dict[str, Any]]:
    if session is None:
        return []
    history = session.get(SESSION_KEY, [])
    return history if isinstance(history, list) else []


def save_chat_history(session, history: list[dict[str, Any]]) -> None:
    if session is None:
        return
    trimmed = history[-MAX_HISTORY_MESSAGES:]
    session[SESSION_KEY] = trimmed
    session.modified = True


def clear_chat_history(session) -> None:
    if session is None:
        return
    session.pop(SESSION_KEY, None)
    session.modified = True


def is_groq_ready() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


def generate_ai_chat_response(user_message: str, session_history: list[dict[str, Any]]) -> dict[str, Any]:
    cleaned_message = (user_message or "").strip()
    if not cleaned_message:
        return {
            "reply": "Ask a question about the website and I will help you with the right page, feature, or live business context.",
            "sources": [],
            "used_groq": False,
        }

    extracted_features = extract_query_features(cleaned_message, session_history)
    documents = retrieve_relevant_documents(cleaned_message, extracted_features)
    sources = [
        {"title": document["title"], "url": document["url"]}
        for document in documents[:4]
        if document.get("url")
    ]

    try:
        if is_groq_ready():
            reply = build_groq_answer(cleaned_message, session_history, extracted_features, documents)
            return {"reply": reply, "sources": sources, "used_groq": True}
    except Exception:
        # Fall back to a deterministic grounded summary if the Groq API is unavailable.
        pass

    return {
        "reply": build_grounded_fallback_answer(cleaned_message, extracted_features, documents),
        "sources": sources,
        "used_groq": False,
    }


def extract_query_features(user_message: str, session_history: list[dict[str, Any]]) -> dict[str, Any]:
    if not is_groq_ready():
        return fallback_feature_extraction(user_message)

    try:
        from groq import Groq

        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        schema = {
            "type": "object",
            "properties": {
                "user_goal": {"type": "string"},
                "topics": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "overview",
                            "customers",
                            "products",
                            "orders",
                            "analytics",
                            "revenue",
                            "tags",
                            "media",
                            "about",
                            "contact",
                            "navigation",
                            "support",
                            "metrics",
                        ],
                    },
                },
                "wants_steps": {"type": "boolean"},
                "wants_counts": {"type": "boolean"},
                "wants_recent": {"type": "boolean"},
                "entity_name": {"type": ["string", "null"]},
                "response_style": {
                    "type": "string",
                    "enum": ["concise", "detailed", "instructional"],
                },
            },
            "required": [
                "user_goal",
                "topics",
                "wants_steps",
                "wants_counts",
                "wants_recent",
                "entity_name",
                "response_style",
            ],
            "additionalProperties": False,
        }

        history_summary = "\n".join(
            f"{item.get('role', 'user')}: {item.get('content', '')}"
            for item in session_history[-4:]
        ) or "No previous conversation."

        response = client.chat.completions.create(
            model=os.getenv("GROQ_EXTRACT_MODEL", DEFAULT_EXTRACT_MODEL),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract website-assistant intent from user questions about EcomCRM. "
                        "Return only the structured schema output."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Conversation history:\n{history_summary}\n\n"
                        f"Current user message:\n{user_message}"
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "website_query_features",
                    "strict": True,
                    "schema": schema,
                },
            },
        )
        return json.loads(response.choices[0].message.content or "{}")
    except Exception:
        return fallback_feature_extraction(user_message)


def fallback_feature_extraction(user_message: str) -> dict[str, Any]:
    lowered = user_message.lower()
    topics = []
    topic_map = {
        "customer": "customers",
        "profile": "customers",
        "product": "products",
        "inventory": "products",
        "order": "orders",
        "delivery": "orders",
        "analytics": "analytics",
        "chart": "analytics",
        "revenue": "revenue",
        "money": "revenue",
        "tag": "tags",
        "image": "media",
        "media": "media",
        "cloudinary": "media",
        "about": "about",
        "contact": "contact",
        "navigate": "navigation",
        "where": "navigation",
        "dashboard": "overview",
        "overview": "overview",
        "support": "support",
        "count": "metrics",
        "total": "metrics",
    }
    for keyword, topic in topic_map.items():
        if keyword in lowered and topic not in topics:
            topics.append(topic)

    if not topics:
        topics = ["overview"]

    wants_steps = any(word in lowered for word in ["how", "steps", "where", "navigate", "use"])
    wants_counts = any(word in lowered for word in ["count", "total", "how many", "number"])
    wants_recent = any(word in lowered for word in ["recent", "latest", "current", "today"])

    entity_name = None
    quoted_names = re.findall(r'"([^"]+)"|\'([^\']+)\'', user_message)
    if quoted_names:
        first_match = quoted_names[0]
        entity_name = first_match[0] or first_match[1]

    return {
        "user_goal": user_message[:200],
        "topics": topics,
        "wants_steps": wants_steps,
        "wants_counts": wants_counts,
        "wants_recent": wants_recent,
        "entity_name": entity_name,
        "response_style": "instructional" if wants_steps else "concise",
    }


def retrieve_relevant_documents(user_message: str, features: dict[str, Any]) -> list[dict[str, Any]]:
    documents = build_static_documents() + build_dynamic_documents(features)
    query_tokens = tokenize(user_message)
    requested_topics = set(features.get("topics", []))
    entity_name = (features.get("entity_name") or "").lower().strip()

    scored_documents = []
    for document in documents:
        score = 0
        document_tokens = document["tokens"]
        score += len(query_tokens.intersection(document_tokens)) * 2
        score += len(requested_topics.intersection(set(document.get("tags", [])))) * 4

        title_tokens = tokenize(document["title"])
        score += len(query_tokens.intersection(title_tokens)) * 3

        if entity_name and entity_name in document["content"].lower():
            score += 6

        if features.get("wants_counts") and "metrics" in document.get("tags", []):
            score += 4

        if features.get("wants_recent") and "recent" in document.get("tags", []):
            score += 4

        if score > 0:
            scored_documents.append((score, document))

    scored_documents.sort(key=lambda item: item[0], reverse=True)
    top_documents = [document for _, document in scored_documents[:MAX_CONTEXT_DOCS]]

    if not top_documents:
        top_documents = documents[:MAX_CONTEXT_DOCS]

    return top_documents


def build_static_documents() -> list[dict[str, Any]]:
    documents = []
    for item in STATIC_SITE_DOCS:
        url = reverse(item["url_name"])
        content = f"{item['title']} page at {url}. {item['content']}"
        documents.append(
            {
                "title": item["title"],
                "url": url,
                "tags": item["tags"],
                "content": content,
                "tokens": tokenize(content + " " + " ".join(item["tags"])),
            }
        )
    return documents


def build_dynamic_documents(features: dict[str, Any]) -> list[dict[str, Any]]:
    documents = []

    orders = order.objects.select_related("customer", "product")
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()
    total_orders = orders.count()
    delivered = orders.filter(status="Delivered").count()
    pending = orders.filter(status="Pending").count()
    out_for_delivery = orders.filter(status="Out for delivery").count()

    documents.append(
        make_document(
            "Live Platform Metrics",
            reverse("home"),
            ["overview", "metrics", "dashboard"],
            (
                f"The website currently has {total_customers} customers, {total_products} products, and {total_orders} "
                f"orders. Order status counts are {delivered} delivered, {pending} pending, and {out_for_delivery} "
                f"out for delivery."
            ),
        )
    )

    today = timezone.localdate()
    delivered_orders = orders.filter(
        status="Delivered",
        product__price__isnull=False,
        date_created__year=today.year,
    )
    daily_revenue = (
        delivered_orders.annotate(date=TruncDate("date_created"))
        .values("date")
        .annotate(revenue=Sum("product__price"), orders=Count("id"))
        .order_by("-date")[:5]
    )
    ytd_revenue = float(delivered_orders.aggregate(total=Sum("product__price"))["total"] or 0)
    pipeline_revenue = float(
        orders.filter(status__in=["Pending", "Out for delivery"], product__price__isnull=False).aggregate(
            total=Sum("product__price")
        )["total"]
        or 0
    )
    revenue_rows = ", ".join(
        f"{row['date']}: Rs. {float(row['revenue'] or 0):.2f} from {row['orders']} delivered orders"
        for row in daily_revenue
    ) or "No delivered revenue rows are available yet."

    documents.append(
        make_document(
            "Live Revenue Snapshot",
            reverse("revenue"),
            ["revenue", "metrics"],
            (
                f"Year-to-date delivered revenue for {today.year} is Rs. {ytd_revenue:.2f}. Pending pipeline revenue "
                f"is Rs. {pipeline_revenue:.2f}. Recent revenue rows: {revenue_rows}"
            ),
        )
    )

    recent_orders = list(orders.order_by("-date_created")[:5])
    if recent_orders:
        recent_order_text = "; ".join(
            f"Order #{item.id} for {item.product.name} by {item.customer.name} is {item.status}."
            for item in recent_orders
        )
        documents.append(
            make_document(
                "Recent Orders",
                reverse("order_list"),
                ["orders", "recent", "metrics"],
                recent_order_text,
            )
        )

    recent_customers = list(Customer.objects.order_by("-date_created")[:5])
    if recent_customers:
        customer_text = "; ".join(
            f"{item.name} ({item.email}, {item.phone})"
            for item in recent_customers
        )
        documents.append(
            make_document(
                "Recent Customers",
                reverse("customer_list"),
                ["customers", "recent", "metrics"],
                f"Recent customers in the website are: {customer_text}.",
            )
        )

    recent_products = list(Product.objects.order_by("-date_created")[:5])
    if recent_products:
        product_text = "; ".join(
            f"{item.name} in category {item.category} priced at Rs. {float(item.price or 0):.2f}"
            for item in recent_products
        )
        documents.append(
            make_document(
                "Recent Products",
                reverse("product"),
                ["products", "recent", "metrics"],
                f"Recent products in the catalog are: {product_text}.",
            )
        )

    all_tags = list(Tag.objects.order_by("name").values_list("name", flat=True)[:12])
    if all_tags:
        documents.append(
            make_document(
                "Current Tags",
                reverse("tag_list"),
                ["tags", "metrics"],
                f"The current product tags include: {', '.join(all_tags)}.",
            )
        )

    entity_name = (features.get("entity_name") or "").strip()
    if entity_name:
        documents.extend(build_entity_documents(entity_name))

    return documents


def build_entity_documents(entity_name: str) -> list[dict[str, Any]]:
    lowered = entity_name.lower()
    documents = []

    customer_matches = Customer.objects.filter(name__icontains=lowered)[:3]
    for customer in customer_matches:
        documents.append(
            make_document(
                f"Customer Match: {customer.name}",
                reverse("customer", kwargs={"pk": customer.id}),
                ["customers", "navigation", "metrics"],
                (
                    f"Customer {customer.name} has email {customer.email}, phone {customer.phone}, and profile page "
                    f"at {reverse('customer', kwargs={'pk': customer.id})}."
                ),
            )
        )

    product_matches = Product.objects.filter(name__icontains=lowered)[:3]
    for product in product_matches:
        documents.append(
            make_document(
                f"Product Match: {product.name}",
                reverse("product"),
                ["products", "metrics"],
                (
                    f"Product {product.name} is in category {product.category}, priced at Rs. {float(product.price or 0):.2f}, "
                    f"and appears in the product catalog page."
                ),
            )
        )

    return documents


def make_document(title: str, url: str, tags: list[str], content: str) -> dict[str, Any]:
    return {
        "title": title,
        "url": url,
        "tags": tags,
        "content": content,
        "tokens": tokenize(f"{title} {content} {' '.join(tags)}"),
    }


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def format_context_documents(documents: list[dict[str, Any]]) -> str:
    lines = []
    for index, document in enumerate(documents, start=1):
        lines.append(
            f"{index}. {document['title']} ({document['url']})\n"
            f"Tags: {', '.join(document['tags'])}\n"
            f"Details: {document['content']}"
        )
    return "\n\n".join(lines)


def build_groq_answer(
    user_message: str,
    session_history: list[dict[str, Any]],
    extracted_features: dict[str, Any],
    documents: list[dict[str, Any]],
) -> str:
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    context_block = format_context_documents(documents)
    history_messages = [
        {
            "role": item.get("role", "user"),
            "content": item.get("content", ""),
        }
        for item in session_history[-4:]
        if item.get("content")
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "You are the Ask to AI assistant for EcomCRM. Answer only with information that is supported by the "
                "provided website context and live website data. If the context is incomplete, say that clearly instead "
                "of inventing details. Mention the relevant page names and routes when useful. Keep answers practical, "
                "accurate, and grounded in the supplied context."
            ),
        },
        {
            "role": "system",
            "content": f"Query feature extraction:\n{json.dumps(extracted_features, ensure_ascii=True)}",
        },
        {
            "role": "system",
            "content": f"Website context:\n{context_block}",
        },
    ]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model=os.getenv("GROQ_CHAT_MODEL", DEFAULT_CHAT_MODEL),
        messages=messages,
    )
    return (completion.choices[0].message.content or "").strip()


def build_grounded_fallback_answer(
    user_message: str,
    extracted_features: dict[str, Any],
    documents: list[dict[str, Any]],
) -> str:
    if not documents:
        return (
            "I could not find grounded website context for that question yet. Try asking about dashboard, customers, "
            "orders, products, analytics, revenue, tags, about, or contact."
        )

    lead_document = documents[0]
    related_routes = ", ".join(document["url"] for document in documents[:3] if document.get("url"))
    related_titles = ", ".join(document["title"] for document in documents[:3])

    intro = (
        "Groq AI is not configured yet, so I used the website knowledge and live database context available locally."
    )
    if is_groq_ready():
        intro = "I used grounded website context to answer your question."

    detail = lead_document["content"]
    if extracted_features.get("wants_steps"):
        detail += f" Relevant pages to check next: {related_routes}."
    elif related_titles:
        detail += f" The most relevant website areas are: {related_titles}."

    return f"{intro}\n\n{detail}"
