/* Theo's back office as it renders in the shop PC's browser. Markup mirrors the REAL templates
 * (systems/spokes-and-sprockets/templates/*.html) and the data is the real seed (shop-data.js, generated).
 * Additions for the film (the spinning sprocket, the under-construction sign, the 88x31 buttons, the digit counter)
 * are marked "+film"; they're the 2009-teenager personality the real app's CSS comment already has.
 *
 *   G.SITE.html()            -> the whole site, every page, built once
 *   G.SITE.bind(el).render(s) -> shows s.page as of s.date (Thursday 19, Monday 23 or Tuesday 24 Nov: the Jobs page
 *                                and the banner date follow the day); applies s.reports ('soon' | 'built'), s.po, s.poHl,
 *                                s.reassign, s.handedBack (Monday afternoon's hand-backs: 0-4 bikes marked ready), s.marquee */
(function (G) {
  'use strict';
  const D = G.SHOP;
  const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const f1 = x => (+x).toFixed(1), f2 = x => (+x).toFixed(2);
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

  /** +film: the classic "under construction" GIF, redrawn: a yellow road sign with a little digger, black chevrons. */
  function underConstruction(s = 44) {
    return `<svg class="uc-svg" width="${s}" height="${s}" viewBox="0 0 44 44">
      <path d="M22 1.5 L42.5 22 L22 42.5 L1.5 22Z" fill="#ffcc00" stroke="#111" stroke-width="2.2" stroke-linejoin="round"/>
      <path d="M22 5 L39 22 L22 39 L5 22Z" fill="none" stroke="#111" stroke-width=".8"/>
      <circle cx="18.5" cy="13.4" r="2.2" fill="#111"/>
      <path d="M18 16 L16.6 23.6 L13 30 M16.8 22.6 L20.6 29.8 M17.6 18.2 L22.4 21.6 L25.8 19.8" fill="none" stroke="#111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M25 19.4 L30.6 29.4" stroke="#111" stroke-width="1.4" stroke-linecap="round"/><path d="M29.2 28.6 L33.4 27.4 L32.8 31.2z" fill="#111"/>
      <path d="M24.5 32.8 C26.5 29.6 31 29.4 33.6 32.8z" fill="#111"/></svg>`;
  }
  /** +film: a sprocket "gif" for the banner (Theo's logo, as a 2009 animated gif would have it). */
  const bannerSprocket = () => G.ICONS.sprocket(40, { steel: ['#fff6cf', '#ffd94a', '#c99a10', '#ffe680'], stroke: '#5a3e00' });

  const NAV = [['jobs', 'Jobs'], ['customers', 'Customers'], ['parts', 'Parts'], ['po', 'Purchase Orders'], ['mechanics', 'Mechanics'], ['invoices', 'Invoices'], ['reports', 'Reports (coming soon!!)']];

  /** Theo's Jobs page for one day. v: Monday's data (D) or another day's (D.days[date]); live: Monday's page, whose
   * counters and hand-backs follow the state (the other days are as the shop printed them on that day). */
  function jobsPage(v, live) {
    const st = v.stats, tag = k => live ? ` data-stat="${k}"` : '';
    const rows = v.jobs.map(j => {
      const late = j.due_date < v.today && j.status !== 'ready';
      const sc = j.status === 'ready' ? 'status-ready' : j.status === 'waiting on parts' ? 'status-waiting' : '';
      return `<tr data-job="${j.job_id}"><td>${j.job_id}</td><td class="mech">${esc(j.mechanic || '-')}</td><td>${esc(j.work)}</td><td>${esc(j.customer)}</td><td>${esc(j.bike || '')}</td><td>${f1(j.estimate_hours)}</td><td class="${late ? 'late' : ''}">${j.due_date}</td><td class="status ${sc}">${esc(j.status)}</td></tr>`;
    }).join('');
    const texts = v.texts.map(t => `<tr><td>${esc(t.sent_at)}</td><td>${esc(t.customer)}</td><td>${esc(t.message)}</td></tr>`).join('');
    return `<div class="box stats">
        <span${tag('open_jobs')}><b>Open jobs:</b> ${st.open_jobs}</span>
        <span${tag('due_today')}><b>Due today:</b> ${st.due_today}</span>
        <span${tag('ready_to_collect')}><b>Ready to collect:</b> ${st.ready_to_collect}</span>
        <span><b>Parts low:</b> <span class="${st.low_stock_parts ? 'low' : ''}">${st.low_stock_parts}</span></span>
        <span${tag('unpaid_invoices')}><b>Unpaid invoices:</b> ${st.unpaid_invoices}</span>
      </div>
      <h2>Open repair jobs &ndash; week of ${v.week_start}</h2>
      <table class="grid jobs"><tr><th>Job #</th><th>Mechanic</th><th>Work</th><th>Customer</th><th>Bike</th><th>Hrs</th><th>Due</th><th>Status</th></tr>${rows}</table>
      <h3>Last texts sent</h3>
      <table class="grid"><tr><th>When</th><th>To</th><th>Message</th></tr>${texts || '<tr><td colspan="3"><i>no texts yet</i></td></tr>'}</table>`;
  }

  function poPage() {
    const p = D.new_po;
    const rows = D.purchase_orders.map(o => `<tr><td>${o.id}</td><td>${esc(o.part)}</td><td>${o.quantity}</td><td>${esc(o.supplier)}</td><td class="status ${o.status === 'ordered' ? 'status-waiting' : ''}">${esc(o.status)}</td><td>${esc(o.created)}</td></tr>`).join('');
    return `<h2>Purchase orders</h2>
      <table class="grid po"><tr><th>PO #</th><th>Part</th><th>Qty</th><th>Supplier</th><th>Status</th><th>Created</th></tr>
      <tr class="po-new"><td>${p.id}</td><td>${esc(p.part)}</td><td>${p.quantity}</td><td>${esc(p.supplier)}</td><td class="status status-waiting">${p.status}</td><td>${p.created}</td></tr>
      ${rows}</table>`;
  }

  function partsPage() {
    const rows = D.parts.map(p => `<tr><td>${p.id}</td><td>${esc(p.sku)}</td><td>${esc(p.name)}</td><td class="${p.stock <= p.reorder_level ? 'low' : 'ok'}">${p.stock}</td><td>${p.reorder_level}</td><td>${esc(p.supplier)}</td><td>&pound;${f2(p.unit_cost)}</td></tr>`).join('');
    return `<h2>Parts &amp; stock</h2>
      <div class="box">Red = at or below reorder level. To order more go to <a>Purchase Orders</a> (ring the supplier first!!)</div>
      <table class="grid"><tr><th>#</th><th>SKU</th><th>Part</th><th>In stock</th><th>Reorder at</th><th>Supplier</th><th>Unit cost</th></tr>${rows}</table>`;
  }

  function mechanicsPage() {
    const rows = D.mechanics.map(m => `<tr><td>${m.id}</td><td>${esc(m.name)}</td><td>${Math.round(m.weekly_capacity_hours)}</td><td>${esc(m.started)}</td></tr>`).join('');
    return `<h2>Mechanics</h2><table class="grid"><tr><th>#</th><th>Name</th><th>Hours per week</th><th>Started</th></tr>${rows}</table>
      <p class="box">TODO (Theo, 2012): show how busy everyone is this week. need to add up the job hours somehow</p>`;
  }

  function reportsSoon() {
    const st = D.stats, tk = D.takings;
    return `<h2>Reports</h2>
      <p class="soon-big">Coming soon!! <span class="blink">&#9733;</span> <span class="uc">${underConstruction(40)}</span></p>
      <p>Theo is working on loads of reports (mechanic workload, best customers, lapsed customers...). For now:</p>
      <div class="box stats">
        <span><b>Taken today:</b> &pound;${f2(tk.total)} (${tk.invoices} invoices)</span>
        <span data-stat="open_jobs"><b>Open jobs:</b> ${st.open_jobs}</span>
        <span data-stat="ready_to_collect"><b>Ready to collect:</b> ${st.ready_to_collect}</span>
      </div>
      <p class="updated">last updated: march 2011</p>`;
  }

  /** The room Theo never built: Barnaby's workload report, written in Theo's own house style (his classes, his grid). */
  function reportsBuilt() {
    const W = D.workload, st = D.stats, tk = D.takings;
    const max = Math.max(...W.mechanics.map(m => Math.max(m.workload_hours, m.weekly_capacity_hours)));
    const rows = W.mechanics.map(m => {
      const over = m.overloaded, pctCap = m.weekly_capacity_hours / max * 100, pctLoad = m.workload_hours / max * 100;
      return `<tr><td><b>${esc(m.name)}</b></td><td>${m.job_count}</td><td class="${over ? 'late' : ''}">${f1(m.workload_hours)}</td><td>${Math.round(m.weekly_capacity_hours)}</td>
        <td class="${over ? 'late' : 'ok'}">${m.spare_hours > 0 ? '+' : ''}${f1(m.spare_hours)}</td>
        <td class="barcell"><div class="wbar"><i class="cap" style="width:${pctCap.toFixed(1)}%"></i><i class="load ${over ? 'over' : ''}" style="width:${pctLoad.toFixed(1)}%"></i></div></td>
        <td class="${over ? 'late' : 'ok'}">${over ? 'overloaded!' : m.workload_hours === 0 ? 'free' : 'ok'}</td></tr>`;
    }).join('');
    return `<h2>Reports</h2>
      <h3 class="first">Mechanic workload &ndash; week of ${W.week_start} to ${W.week_end}</h3>
      <table class="grid workload"><tr><th>Mechanic</th><th>Jobs</th><th>Booked hrs</th><th>Hours per week</th><th>Spare</th><th class="barh">booked vs. hours per week</th><th></th></tr>${rows}</table>
      <p class="note">Booked hours = the estimates of jobs due this week (Mon&ndash;Sat) that aren't ready or collected yet, same as Theo's notes.</p>
      <div class="box stats today">
        <span><b>Taken today:</b> &pound;${f2(tk.total)} (${tk.invoices} invoices)</span>
        <span data-stat="open_jobs"><b>Open jobs:</b> ${st.open_jobs}</span>
        <span data-stat="ready_to_collect"><b>Ready to collect:</b> ${st.ready_to_collect}</span>
      </div>
      <p class="updated">workload report added ${D.today.split('-').reverse().join('/')} by Barnaby &middot; approved by Martin</p>`;
  }

  function html() {
    const nav = NAV.map(([p, label]) => `<a data-p="${p}"${p === 'reports' ? ' class="soon"' : ''}>${label}</a>`).join('');
    const digits = '004127'.split('').map(c => `<i>${c}</i>`).join('');
    return `<div class="page site"><div class="s-page">
      <div class="s-banner"><h1>Spokes &amp; Sprockets</h1><div class="sub">A Hartley family workshop &middot; est. 1987</div><div class="logo">${bannerSprocket()}</div><div class="date"></div></div>
      <div class="marquee"><span>*** SPRING TUNE-UP SPECIAL: full service just &pound;49.99!! *** Wheel builds done in house *** Ask about our loyalty card ***</span></div>
      <div class="s-nav">${nav}</div>
      <div class="s-content">
        <div class="sp" data-p="jobs" data-day="${D.today}">${jobsPage(D, true)}</div>
        ${Object.keys(D.days).map(d => `<div class="sp" data-p="jobs" data-day="${d}">${jobsPage(D.days[d], false)}</div>`).join('')}
        <div class="sp" data-p="po">${poPage()}</div>
        <div class="sp" data-p="parts">${partsPage()}</div>
        <div class="sp" data-p="mechanics">${mechanicsPage()}</div>
        <div class="sp" data-p="reports-soon">${reportsSoon()}</div>
        <div class="sp" data-p="reports-built">${reportsBuilt()}</div>
      </div>
      <div class="s-foot"><span>Best viewed in IE7 at 1024&times;768 &middot; &copy; 2009 Theo H. &middot; <a>webmaster</a> &middot; <a>sign my guestbook!</a></span><span class="visits">You are visitor No. <span class="ctr">${digits}</span></span></div>
      <div class="badges">
        <span class="b88 a"><span>SPOKES &amp;<br><b>SPROCKETS</b></span></span>
        <span class="b88 b"><span>theo h.<br>webmaster</span></span>
        <span class="b88 c"><span>best viewed at<br><b>1024x768</b></span></span>
        <span class="b88 d"><span>UNDER CONSTRUCTION</span></span>
        <span class="b88 e"><span>NO FRAMES<br>NO POPUPS!!</span></span>
        <span class="b88 f">${G.ICONS.sprocket(20, { teeth: 12 })}<span>BIKE<br>POWERED</span></span>
      </div>
    </div></div>`;
  }

  function bind(root) {
    const q = s => root.querySelector(s), qa = s => [...root.querySelectorAll(s)];
    const nav = qa('.s-nav a'), pages = qa('.sp'), reportsLink = q('.s-nav a[data-p="reports"]');
    const poRow = q('tr.po-new'), marq = q('.marquee span'), dateEl = q('.s-banner .date');
    const mon = q(`.sp[data-p="jobs"][data-day="${D.today}"]`);            // Monday's Jobs page: the one the state animates
    const moved = D.reassigned.jobs.map(id => mon.querySelector(`tr[data-job="${id}"]`)).filter(Boolean);
    const HB = D.handed_back, statEls = qa('[data-stat]');
    const handed = HB.jobs.map(id => ({ td: mon.querySelector(`tr[data-job="${id}"] td.status`), was: D.jobs.find(j => j.job_id === id).status }));
    // the day the shop's pages are printed for: the latest one we have on or before the state's date
    const DAYS = [D.today, ...Object.keys(D.days)].sort();
    const dayOf = date => DAYS.filter(d => d <= date).pop() || DAYS[0];
    const statusClass = st => st === 'ready' ? 'status-ready' : st === 'waiting on parts' ? 'status-waiting' : '';
    return {
      render(s) {
        const built = s.reports === 'built';
        const want = s.page === 'reports' ? (built ? 'reports-built' : 'reports-soon') : s.page;
        const day = dayOf(s.date || D.today);
        pages.forEach(p => { p.style.display = p.dataset.p === want && (!p.dataset.day || p.dataset.day === day) ? '' : 'none'; });
        dateEl.textContent = day;
        nav.forEach(a => a.classList.toggle('on', a.dataset.p === s.page));
        reportsLink.textContent = built ? 'Reports' : 'Reports (coming soon!!)';
        reportsLink.classList.toggle('soon', !built);
        // the new purchase order row
        const po = clamp(s.po);
        poRow.style.display = po > 0 ? '' : 'none';
        poRow.style.opacity = Math.min(1, po * 1.5);
        poRow.querySelectorAll('td').forEach(td => { td.style.position = 'relative'; td.style.top = `${((1 - po) * -10).toFixed(2)}px`; });
        poRow.classList.toggle('fresh', clamp(s.poHl) > .02);
        poRow.style.setProperty('--hl', clamp(s.poHl));
        // Dev -> Priya
        const r = clamp(s.reassign), hl = r > 0 ? clamp(1 - Math.abs(r - .5) * 2.2) : 0;
        moved.forEach(tr => {
          tr.querySelector('.mech').textContent = r >= .5 ? D.reassigned.to : 'Dev';
          tr.classList.toggle('fresh', hl > .02);
          tr.style.setProperty('--hl', hl);
        });
        // Monday afternoon: the first n bikes handed back are 'ready', and Theo's counters are the shop's own after them
        const n = Math.round(clamp(s.handedBack || 0, 0, HB.jobs.length));
        handed.forEach(({ td, was }, i) => {
          const st = i < n ? HB.status : was;
          td.textContent = st;
          td.className = `status ${statusClass(st)}`.trim();
        });
        const stats = n ? HB.stats[n - 1] : D.stats;
        statEls.forEach(el => { el.lastChild.nodeValue = ` ${stats[el.dataset.stat]}`; });
        // marquee: starts ~a third of the way in, as if it has been scrolling
        const span = 1740, text = 760;   // the page is 980 wide; the text is ~760
        marq.style.left = `${((150 - (s.marquee || 0) + text) % span + span) % span - text}px`;
      },
    };
  }

  G.SITE = { html, bind, underConstruction };
})(window);
