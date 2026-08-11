(() => {
  document.addEventListener("click", (event) => {
    const link = event.target.closest("[data-recommended-event]");
    if (!link || typeof window.gtag !== "function") return;

    window.gtag("event", link.dataset.recommendedEvent, {
      tool_slug: link.dataset.toolSlug,
      card_position: link.dataset.cardPosition || "detail_page",
      language: link.dataset.language,
      destination_type: link.dataset.destinationType,
      cta_location: link.dataset.ctaLocation,
      is_sponsored: link.dataset.isSponsored || "unknown",
    });
  });
})();
