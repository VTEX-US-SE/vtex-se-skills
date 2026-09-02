# Architecture Decision & Theme Catalog

This is a **memory-jog, not a checklist.** During Phase 1, use this to make sure nothing relevant to the current RFP gets missed — then discard everything that doesn't actually appear in the RFP or architecture note. A B2B distributor opportunity and a bank loyalty marketplace will draw from almost entirely different subsets of this list. Never carry a section forward from a past project just because it existed there.

## Frontend / experience model
- Headless / API-first vs. white-label storefront (FastStore) vs. hybrid-by-phase
- Native mobile strategy (bearer-token API calls vs. WebView)
- Authentication model: BYOIDP token exchange vs. Punchout/delegated access with token-based login
- Design system ownership and constraints

## Account & multi-market architecture
- Single account + subaccounts (Multistores) vs. dedicated accounts per market/region
- Sponsor Account / Edition App governance framework for global baseline + local flexibility
- Trade Policies for currency, language, catalog, pricing, payment, logistics, promotions isolation

## Commerce core
- Catalog data model: Product/SKU Specifications, SKU Attachments, SKU Binding
- Search & discovery: Intelligent Search, semantic search, merchandising rules, personalization
- Pricing: Contextual Price, price tables, rounding rules
- Promotions: Customer Clusters, vtex_segment cookie (campaigns/priceTables), session public namespace

## Checkout & payments
- Payment Provider Protocol (own gateway / local rails / Secure Proxy for PCI scope)
- Gift Card Provider Protocol (external wallets, points, store credit as payment tender)
- Split-tender / mixed-tender orchestration, idempotency, reserve-capture-release lifecycle
- Antifraud Provider Protocol

## Marketplace / multi-seller (only if the opportunity is a marketplace)
- External Seller Protocol
- Native vs. third-party Seller Center / Partner Portal (build vs. buy — reference cases: Americanas/OmniK, Fast Shop/Conecta Lá, Itaú Shop custom build)
- Funding attribution and commission handling (native limits, Custom Order Fields, external commercial layer)
- Delivery Promise, Contextual Price two-tier indexing at scale

## B2B (only if the opportunity is B2B / buyer-side)
- B2B Buyer Portal / Organizations, cost centers, buyer roles and approval workflows
- Punchout for procurement system integration
- Custom pricing / negotiated catalogs per organization

## Content
- Native VTEX CMS vs. customer-owned CMS (AEM, Contentful, etc.) coexistence
- Content governance: branching workflow, approval flows, multi-locale fallback

## Integration & eventing
- Order Hook (push) vs. Feed v3 (pull/batch) vs. VTEX IO Events for sub-order events
- Data Pipeline / batch export for BI and reconciliation
- Correlation/tracing headers for end-to-end observability across the customer's stack

## AI & automation (only if raised by the RFP)
- AI Workspace (catalog, search optimization, promotions, data insights agents)
- Agentic CX / conversational commerce
- VTEX Ads / retail media (only if monetization or advertising is in scope)
- Subscriptions module for recurring commerce

## Infrastructure & compliance
- AWS infrastructure narrative: multi-AZ, auto-scaling, data resilience, network security
- Compliance posture: ISO 27001, SOC 2, PCI-DSS, GDPR/LGPD, region-specific certifications
- Known native boundaries to be transparent about up front: no on-prem hosting, no bring-your-own-key encryption, no product-level commission engine, no mixed-tender payment-split engine, no catalog governance/KYC workflow — these are consistently handled via a customization or third-party layer, never silently ignored.

## Reminder

If a theme above doesn't appear anywhere in the RFP, the architecture note, or the Q&A doc, it does not get a section — including it anyway is exactly the kind of unfocused, checklist-driven drafting this skill is designed to avoid.
