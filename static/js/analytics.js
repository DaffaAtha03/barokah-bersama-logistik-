/* Google Analytics 4 — hanya dimuat bila "ga4_id" diisi di Pengaturan Situs. */
(function () {
  var tag = document.currentScript;
  var id = tag && tag.getAttribute('data-ga');
  if (!id) return;
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', id, { anonymize_ip: true });
})();
