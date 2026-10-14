/* CV. Barokah Bersama Logistik — interaksi situs (tanpa framework). */
(function () {
  'use strict';

  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  /* ---------- Header: bayangan saat scroll ---------- */
  var header = $('[data-header]');
  function onScroll() {
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 8);
  }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ---------- Menu mobile ---------- */
  var toggle = $('[data-nav-toggle]');
  var nav = $('[data-nav]');
  function setMenu(open) {
    if (!toggle || !nav) return;
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Tutup menu' : 'Buka menu');
  }
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      setMenu(toggle.getAttribute('aria-expanded') !== 'true');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setMenu(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setMenu(false);
    });
    window.matchMedia('(min-width: 961px)').addEventListener('change', function () { setMenu(false); });
  }

  /* ---------- Animasi muncul saat di-scroll ---------- */
  var reveals = $$('.reveal');
  if (reveals.length) {
    var show = function (el) { el.classList.add('is-in'); };
    if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) { show(entry.target); io.unobserve(entry.target); }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
      reveals.forEach(function (el) { io.observe(el); });
      // Jaring pengaman: pastikan konten tidak pernah tersembunyi.
      setTimeout(function () { reveals.forEach(show); }, 4000);
    } else {
      reveals.forEach(show);
    }
  }

  /* ---------- Filter portofolio ---------- */
  var filters = $('[data-filters]');
  if (filters) {
    var items = $$('.portfolio-item');
    filters.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-filter]');
      if (!btn) return;
      var f = btn.getAttribute('data-filter');
      $$('[data-filter]', filters).forEach(function (b) {
        var on = b === btn;
        b.classList.toggle('is-active', on);
        b.setAttribute('aria-pressed', String(on));
      });
      items.forEach(function (it) {
        var match = f === '*' || it.getAttribute('data-category') === f;
        it.hidden = !match;
        if (match) it.classList.add('is-in');
      });
    });
  }

  /* ---------- Lightbox ---------- */
  var box = $('[data-lightbox]');
  if (box && typeof box.showModal === 'function') {
    var boxImg = $('[data-lightbox-img]', box);
    var boxCap = $('[data-lightbox-caption]', box);
    document.addEventListener('click', function (e) {
      var trigger = e.target.closest('[data-full]');
      if (!trigger) return;
      var src = trigger.getAttribute('data-full');
      if (!src) return;
      boxImg.src = src;
      boxImg.alt = trigger.getAttribute('data-alt') || '';
      boxCap.textContent = trigger.getAttribute('data-alt') || '';
      box.showModal();
    });
    box.addEventListener('click', function (e) {
      // klik di luar gambar atau pada tombol tutup
      if (e.target === box || e.target.closest('[data-lightbox-close]')) box.close();
    });
    box.addEventListener('close', function () { boxImg.removeAttribute('src'); });
  }

  /* ---------- Formulir penawaran ---------- */
  var form = $('#lead-form');
  if (!form) return;

  var statusEl = $('[data-status]', form);
  var submitBtn = $('[data-submit]', form);
  var waBtn = $('[data-wa-send]', form);
  var waNumber = form.getAttribute('data-wa') || '';
  var hasKey = form.getAttribute('data-has-key') === 'yes';
  var thanksUrl = form.getAttribute('data-thanks') || '/';

  function setStatus(text, kind) {
    statusEl.textContent = text || '';
    statusEl.className = 'form-status' + (kind ? ' is-' + kind : '');
  }

  // Isi pilihan dari tautan, mis. /kontak/?layanan=Kurir&armada=CDE
  (function prefill() {
    var params = new URLSearchParams(window.location.search);
    ['layanan', 'armada'].forEach(function (name) {
      var val = params.get(name);
      var select = form.elements[name];
      if (!val || !select) return;
      Array.prototype.forEach.call(select.options, function (opt) {
        if (opt.value.toLowerCase() === val.toLowerCase()) select.value = opt.value;
      });
    });
  })();

  function fieldOf(input) { return input.closest('.field'); }
  function showError(input, message) {
    var field = fieldOf(input);
    if (!field) return;
    field.classList.add('has-error');
    var err = $('.field-error', field);
    if (!err) {
      err = document.createElement('p');
      err.className = 'field-error';
      err.id = input.id + '-error';
      field.appendChild(err);
      input.setAttribute('aria-describedby', err.id);
    }
    err.textContent = message;
    input.setAttribute('aria-invalid', 'true');
  }
  function clearError(input) {
    var field = fieldOf(input);
    if (!field) return;
    field.classList.remove('has-error');
    input.removeAttribute('aria-invalid');
  }
  form.addEventListener('input', function (e) { if (e.target.matches('input, textarea, select')) clearError(e.target); });

  function validate(requirePhone) {
    var ok = true, firstBad = null;
    var nama = form.elements.nama, tel = form.elements.telepon, msg = form.elements.message, email = form.elements.email;
    [nama, tel, msg, email].forEach(clearError);

    function bad(input, text) { showError(input, text); ok = false; if (!firstBad) firstBad = input; }

    if (!nama.value.trim()) bad(nama, 'Nama wajib diisi.');
    var digits = tel.value.replace(/\D/g, '');
    if (requirePhone && digits.length < 8) bad(tel, 'Masukkan nomor telepon/WhatsApp yang valid.');
    if (!msg.value.trim()) bad(msg, 'Tuliskan kebutuhan Anda.');
    if (email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) bad(email, 'Format email belum benar.');

    if (firstBad) firstBad.focus();
    return ok;
  }

  function summary() {
    var v = function (n) { return (form.elements[n] && form.elements[n].value || '').trim(); };
    var lines = ['Halo CV. Barokah Bersama Logistik, saya ingin meminta penawaran.', ''];
    var rows = [
      ['Nama', v('nama')], ['Perusahaan', v('perusahaan')], ['Telepon/WA', v('telepon')], ['Email', v('email')],
      ['Layanan', v('layanan')], ['Armada', v('armada')], ['Asal', v('asal')], ['Tujuan', v('tujuan')],
      ['Barang', v('barang')]
    ];
    rows.forEach(function (r) { if (r[1]) lines.push(r[0] + ': ' + r[1]); });
    lines.push('', v('message'));
    return lines.join('\n');
  }

  function openWhatsApp() {
    var url = 'https://wa.me/' + waNumber + '?text=' + encodeURIComponent(summary());
    window.open(url, '_blank', 'noopener');
  }

  waBtn.addEventListener('click', function () {
    if (!validate(false)) return;
    setStatus('Membuka WhatsApp…', 'ok');
    openWhatsApp();
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    setStatus('', '');
    if (!validate(true)) return;

    // Honeypot terisi => kemungkinan bot; pura-pura sukses.
    if (form.elements.botcheck && form.elements.botcheck.checked) { window.location.assign(thanksUrl); return; }

    if (!hasKey) {
      setStatus('Pengiriman email belum diaktifkan. Kami arahkan ke WhatsApp.', 'ok');
      openWhatsApp();
      return;
    }

    var data = {};
    new FormData(form).forEach(function (value, key) { if (key !== 'redirect' && key !== 'botcheck') data[key] = value; });
    data.name = data.nama;
    data.message = summary();

    submitBtn.disabled = true;
    var original = submitBtn.textContent;
    submitBtn.textContent = 'Mengirim…';

    var ctrl = 'AbortController' in window ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 20000) : null;

    fetch(form.action, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(data),
      signal: ctrl ? ctrl.signal : undefined
    })
      .then(function (res) { return res.json().then(function (j) { return { ok: res.ok, json: j }; }); })
      .then(function (r) {
        if (r.ok && r.json && r.json.success) {
          window.location.assign(thanksUrl);
        } else {
          throw new Error((r.json && r.json.message) || 'Gagal mengirim');
        }
      })
      .catch(function () {
        setStatus('Maaf, formulir belum berhasil terkirim. Silakan coba lagi atau kirim lewat WhatsApp.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = original;
      })
      .then(function () { if (timer) clearTimeout(timer); });
  });
})();
