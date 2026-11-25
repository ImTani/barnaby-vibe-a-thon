/* The other eight tabs Martin keeps open: plausible 2009-ish pages from FICTIONAL services (no real brands or
 * logos). Each function returns one .page element's HTML, sized for one browser viewport (~1060x516 logical px).
 * The nine-tab beat is Theo's last week, Thursday 19 November 2026, at night. Customer names and texts come from
 * the real seed (shop-data.js); everything else here is set dressing. */
(function (G) {
  'use strict';
  const D = G.SHOP, I = G.ICONS;
  const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const ukDate = iso => iso.slice(0, 10).split('-').reverse().join('/');

  // little product drawings for the trade counter
  const PROD = {
    pads: `<svg width="58" height="40" viewBox="0 0 58 40"><rect x="6" y="8" width="20" height="24" rx="6" fill="#59606a" stroke="#2b3036"/><rect x="10" y="12" width="12" height="16" rx="4" fill="#9a8f80"/><rect x="32" y="8" width="20" height="24" rx="6" fill="#59606a" stroke="#2b3036"/><rect x="36" y="12" width="12" height="16" rx="4" fill="#9a8f80"/><circle cx="16" cy="6" r="2" fill="#aeb6bf"/><circle cx="42" cy="6" r="2" fill="#aeb6bf"/></svg>`,
    rotor: `<svg width="44" height="44" viewBox="0 0 44 44"><circle cx="22" cy="22" r="19" fill="#d5dade" stroke="#6b737c"/><circle cx="22" cy="22" r="12" fill="#fff" stroke="#6b737c"/>${[0, 1, 2, 3, 4, 5].map(i => { const a = i / 6 * Math.PI * 2; return `<circle cx="${(22 + Math.cos(a) * 15.5).toFixed(1)}" cy="${(22 + Math.sin(a) * 15.5).toFixed(1)}" r="1.8" fill="#8f979f"/>`; }).join('')}<circle cx="22" cy="22" r="5" fill="#8f979f"/></svg>`,
    cable: `<svg width="50" height="40" viewBox="0 0 50 40"><path d="M6 30 C6 6 44 6 44 20 C44 32 14 32 14 20 C14 12 36 12 36 20" fill="none" stroke="#2b3036" stroke-width="3"/><path d="M36 20 L46 34" stroke="#aeb6bf" stroke-width="1.6"/></svg>`,
    bottle: `<svg width="30" height="44" viewBox="0 0 30 44"><rect x="11" y="2" width="8" height="6" fill="#c33"/><path d="M8 10 h14 l3 6 v24 a2 2 0 0 1 -2 2 h-16 a2 2 0 0 1 -2 -2 v-24z" fill="#f2f4f6" stroke="#6b737c"/><rect x="7" y="20" width="16" height="12" fill="#2f6fb6"/></svg>`,
    blocks: `<svg width="56" height="34" viewBox="0 0 56 34"><rect x="4" y="10" width="22" height="10" rx="3" fill="#222"/><rect x="30" y="10" width="22" height="10" rx="3" fill="#222"/><path d="M15 20v6M41 20v6" stroke="#aeb6bf" stroke-width="2.4"/></svg>`,
    hose: `<svg width="50" height="40" viewBox="0 0 50 40"><path d="M4 34 C10 4 40 36 46 6" fill="none" stroke="#1d1f22" stroke-width="3.4"/><rect x="42" y="2" width="7" height="6" fill="#b8bfc6"/></svg>`,
  };

  function supplier() {
    const P = [
      ['pads', 'Disc brake pads, resin compound (pair)', '6.50', 'out', 'OUT OF STOCK - due 26/11'],
      ['pads', 'Disc brake pads, sintered (pair)', '7.95', 'in', 'In stock'],
      ['blocks', 'V-brake blocks 70mm (pair)', '3.20', 'in', 'In stock'],
      ['rotor', 'Disc rotor 160mm 6-bolt', '14.50', 'low', 'Low stock (3)'],
      ['cable', 'Brake cable + outer kit', '5.75', 'in', 'In stock'],
      ['hose', 'Hydraulic hose kit 2m', '11.40', 'in', 'In stock'],
      ['bottle', 'DOT 5.1 brake fluid 500ml', '8.00', 'in', 'In stock'],
      ['bottle', 'Mineral brake oil 100ml', '6.10', 'out', 'OUT OF STOCK'],
    ];
    return `<div class="page sup">
      <div class="top"><div class="logo">NORTHGATE<b>&#9679;</b><small>cycle supply &middot; TRADE COUNTER</small></div>
        <div class="acct">Account: <b>SPOKES &amp; SPROCKETS (HAR014)</b><br>Basket: 0 items &middot; <u>Log out</u></div></div>
      <div class="menu"><a>Home</a><a class="on">Brakes</a><a>Drivetrain</a><a>Wheels</a><a>Tyres &amp; Tubes</a><a>Workshop</a><a>Clearance!</a><a>My account</a></div>
      <div class="body">
        <div class="side"><h4>Brakes</h4>Disc pads<br>Rim brake blocks<br>Rotors<br>Cables &amp; hose<br>Fluids &amp; bleed kits<br>Levers<br><h4 style="margin-top:8px">Quick order</h4>Code: <span class="inp"></span><br><span class="mini-btn">Add</span></div>
        <div class="grid"><div class="crumb">Home &raquo; Brakes &raquo; All &nbsp; <span class="inp wide">Search trade catalogue...</span> &nbsp; 1&ndash;8 of 64</div>
          ${P.map(([pic, name, pr, st, stt]) => `<div class="prod"><div class="ph">${PROD[pic]}</div><b>${name}</b><div class="pr">&pound;${pr} <small>ex VAT</small></div><div class="st ${st}">${stt}</div><div class="btn ${st === 'out' ? 'dis' : ''}">${st === 'out' ? 'Notify me' : 'Add to basket'}</div></div>`).join('')}
        </div>
      </div></div>`;
  }

  /* What Theo left in the box on Thursday night: a booking text for Sofia's job 4475 (full service, due Tue 24/11),
   * never sent. Her "ready to collect" text is Barnaby's, on Monday afternoon. The count is the draft's own length. */
  const DRAFT = 'Hi Sofia, your Giant Defy is booked in for a full service, ready Tues 24th. Spokes & Sprockets';

  /* Older texts from the SMS box's own log (not in the back office), merged with the shop's by date, newest first.
   * Jana's fork service was booked for Mon 23 Nov (job 4488; her bike is one of Monday's hand-backs). */
  const OLDER_TEXTS = [
    { sent_at: '2026-11-12 10:12', customer: 'Jana Novak', message: 'Hi Jana, fork service booked in for Mon 23rd. Spokes & Sprockets' },
    { sent_at: '2026-10-02 16:40', customer: 'Arthur Pemberton', message: 'Hi Arthur, the parts for the Raleigh are still on order, sorry! S&S' },
  ];

  function sms() {
    const log = [...D.texts, ...OLDER_TEXTS].sort((a, b) => (a.sent_at < b.sent_at ? 1 : -1))
      .map(t => `<div class="msg"><i>${esc(t.sent_at.slice(0, 16))}</i><b>${esc(t.customer)}</b><br>${esc(t.message)}</div>`).join('');
    return `<div class="page sms">
      <div class="top"><span class="logo">SMS<b>box</b></span><small>business texting from your PC &middot; since 2006</small><span class="cred">Credits: 14</span></div>
      <div class="body">
        <div class="compose">
          <div class="warn">${I.ICO.warn(14)} Your credits are running low. <u>Buy 500 more for &pound;29</u></div>
          <label>To (mobile number)</label><div class="in">07700 900110</div>
          <label>From</label><div class="in">SpokesSprk</div>
          <label>Message</label><div class="ta">${esc(DRAFT)}<span class="caret"></span></div>
          <div class="cnt">${DRAFT.length} / 160 characters (1 text)</div>
          <div class="send">Send</div>
        </div>
        <div class="log"><h4>Sent messages</h4>${log}</div>
      </div></div>`;
  }

  function xls() {
    const cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K'];
    const R = [
      [['WORKLOAD  (theo - update every monday!!)', 'h big', 6]],
      [['week commencing:'], ['03/08/2026', 'r stale'], [''], [''], ['', ''], ['<- not updated since august (sorry uncle M)', 'note', 5]],
      [],
      [['Mechanic', 'h'], ['Mon', 'h c'], ['Tue', 'h c'], ['Wed', 'h c'], ['Thu', 'h c'], ['Fri', 'h c'], ['Sat', 'h c'], ['TOTAL', 'h c'], ['hrs/wk', 'h c'], ['spare', 'h c']],
      [['Dev'], ['6', 'r'], ['other shop', 'c grey'], ['7.5', 'r'], ['4', 'r'], ['3', 'r'], ['', 'r'], ['#REF!', 'err sel'], ['20', 'r'], ['#REF!', 'err']],
      [['Ravi'], ['4.5', 'r'], ['6', 'r'], ['3', 'r'], ['2.5', 'r'], ['2', 'r'], ['1.5', 'r'], ['19.5', 'r'], ['30', 'r'], ['10.5', 'r']],
      [['Saturday lad'], ['', 'r'], ['', 'r'], ['', 'r'], ['', 'r'], ['', 'r'], ['4', 'r'], ['4', 'r'], ['6', 'r'], ['2', 'r']],
      [],
      [['NB Dev at the other shop TUESDAYS', 'note', 4]],
      [['DONT SORT COLUMN A it breaks the totals', 'note red', 4]],
      [['wheel builds = 6hrs front, 5.5 rear (ask Dev)', 'note', 4]],
      [], [], [], [], [], [],
    ];
    const head = `<tr><th class="rn"></th>${cols.map(c => `<th class="${c === 'H' ? 'csel' : ''}">${c}</th>`).join('')}</tr>`;
    const body = R.map((row, ri) => {
      let cells = '', used = 0;
      for (const [txt, cls = '', span = 1] of row) { cells += `<td class="${cls}"${span > 1 ? ` colspan="${span}"` : ''}>${txt}</td>`; used += span; }
      for (; used < cols.length; used++) cells += '<td></td>';
      return `<tr><th class="rn ${ri === 4 ? 'rsel' : ''}">${ri + 1}</th>${cells}</tr>`;
    }).join('');
    return `<div class="page xls">
      <div class="menu">${['File', 'Edit', 'View', 'Insert', 'Format', 'Tools', 'Data', 'Window', 'Help'].map(m => `<span>${m}</span>`).join('')}</div>
      <div class="rib">${['B', 'I', 'U'].map(b => `<span class="tb"><b>${b}</b></span>`).join('')}<span class="sep"></span><span class="tb">&#931;</span><span class="tb">%</span><span class="tb">.00</span><span class="sep"></span><span class="sel">Arial</span><span class="sel sm">10</span><span class="sep"></span><span class="tb fill"></span><span class="tb fontc">A</span></div>
      <div class="fx"><span class="nm">H5</span><span class="fxi">fx</span><span class="f">=SUM(B5:G5)+#REF!</span></div>
      <table>${head}${body}</table>
      <div class="sheets"><span class="on">this week</span><span>OLD (dont use)</span><span>Sheet3</span></div></div>`;
  }

  function invoices() {
    const rows = D.invoices.map(i => {
      const days = Math.round((Date.parse('2026-11-19') - Date.parse(i.created.slice(0, 10))) / 864e5);
      return `<tr><td><u>INV-${String(i.id).padStart(4, '0')}</u></td><td>${esc(i.customer)}</td><td>${ukDate(i.created)}</td><td class="r">&pound;${(+i.amount).toFixed(2)}</td><td><span class="pill ${days > 30 ? 'od' : 'due'}">${days > 30 ? `Overdue ${days} days` : 'Due'}</span></td><td><u>Send reminder</u></td></tr>`;
    }).join('');
    return `<div class="page inv">
      <div class="top"><span class="logo">ledger<b>book</b> <small>online accounts</small></span><span class="who">Spokes &amp; Sprockets &middot; <u>Settings</u> &middot; <u>Sign out</u></span></div>
      <div class="trial">Your free trial ended <b>412 days ago</b>. Some features are read-only. <u>Upgrade now</u></div>
      <div class="body">
        <div class="side"><div>Dashboard</div><div class="on">Sales invoices</div><div>Quotes</div><div>Bills</div><div>Bank</div><div>VAT return</div><div>Contacts</div><div>Reports</div></div>
        <div class="main"><h3>Sales invoices <span class="tabsx"><span>All</span><span class="on">Unpaid (${D.invoices.length})</span><span>Paid</span><span>Drafts</span></span></h3>
          <div class="btnrow"><span class="btn">+ New invoice</span><span class="btn g">Import from back office&hellip;</span><span class="muted">(Theo said he'd sort this)</span></div>
          <table><tr><th>Number</th><th>Customer</th><th>Date</th><th class="r">Amount</th><th>Status</th><th></th></tr>${rows}</table>
          <div class="sum">Total unpaid: <b>&pound;${D.invoices.reduce((a, i) => a + +i.amount, 0).toFixed(2)}</b></div>
        </div>
      </div></div>`;
  }

  /** Theo's older parts list (2008, before the back office had a Parts page), still the one everyone opens. */
  function partsList() {
    const rows = D.parts.map((p, i) => `<tr bgcolor="${i % 2 ? '#ffffff' : '#ffffcc'}"><td>${esc(p.sku)}</td><td>${esc(p.name)}</td><td align="center">${esc(p.supplier)}</td><td align="right">&pound;${(+p.unit_cost).toFixed(2)}</td><td align="center">${['drawer 3', 'drawer 7', 'shelf B', 'drawer 1', 'drawer 4', 'drawer 4', 'drawer 2', 'shelf A', 'drawer 6', 'cupboard', 'drawer 6', 'shelf B'][i]}</td></tr>`).join('');
    return `<div class="page plist">
      <center>
        <h1>${I.spanner(30)} PARTS LIST ${I.spanner(30)}</h1>
        <p class="sub"><b>Spokes &amp; Sprockets</b> &mdash; where everything lives &mdash; <font color="#cc0000"><b>last updated 14/06/2010</b></font></p>
        <p class="old"><blink>!! the stock numbers are in the BACK OFFICE now, this is just where things are kept !!</blink> - T</p>
        <table border="1" cellpadding="3" cellspacing="0" width="780"><tr bgcolor="#000080"><th>code</th><th>part</th><th>who from</th><th>cost</th><th>where</th></tr>${rows}</table>
        <p class="ft"><a>back to home</a> | <a>email theo</a> | made with notepad and a lot of tea</p>
      </center></div>`;
  }

  function email() {
    const M = [
      [1, 'Theo Hartley', 'README for whoever looks after it next', 'Thu 21:12', true, true],
      [1, 'SMS box', 'Low credit warning: 14 credits left', 'Thu 18:30', false, false],
      [0, 'Northgate Cycle Supply', 'Your order NG-88213 has been dispatched', 'Thu 15:02', false, false],
      [1, 'Anika Banerjee', 'brakes squeaking again :( can you fit me in?', 'Thu 11:47', false, false],
      [0, 'Madison Trade Sales', 'Your November statement is ready', 'Wed 09:20', false, false],
      [0, 'Rachel Okafor', 'Re: rims for the wheel build', 'Wed 08:05', false, false],
      [1, 'Carol Hartley', "Sunday lunch? + Theo's leaving do!!", 'Tue 19:41', false, true],
      [0, 'Harbour & County Bank', 'Important changes to your online banking', 'Tue 07:00', false, false],
      [0, 'Dev', "can't do tues this week, other shop", 'Mon 22:16', false, false],
      [0, 'Jana Novak', 'Fork service - is Monday still ok?', 'Mon 13:31', false, false],
      [0, 'Ravi', 'van MOT reminder', '15/11', false, false],
      [0, 'Northgate Cycle Supply', 'WINTER CLEARANCE - up to 40% off!!', '14/11', false, false],
    ];
    return `<div class="page mailp">
      <div class="top"><span class="logo">${I.mail(22)} Shop mail</span><span class="sb">Search mail...</span><span class="who">shop@spokesandsprockets.co.uk &middot; <u>Options</u> &middot; <u>Sign out</u></span></div>
      <div class="body">
        <div class="side"><div class="new">New message</div><div class="f on">Inbox (4)</div><div class="f">Drafts (2)</div><div class="f">Sent</div><div class="f">Junk (213)</div><div class="f">Deleted</div><div class="f sm">Folders</div><div class="f sub">suppliers</div><div class="f sub">customers</div><div class="f sub">THEO - SYSTEM STUFF</div></div>
        <div class="list"><div class="tools"><u>Delete</u> &nbsp; <u>Junk</u> &nbsp; <u>Reply</u> &nbsp; <u>Forward</u> &nbsp; <u>Move to &#9662;</u><span style="float:right">1&ndash;12 of 1,904</span></div>
          ${M.map(([u, fr, su, dt, sel, flag]) => `<div class="row ${u ? 'u' : ''} ${sel ? 'sel' : ''}"><span class="fl">${flag ? '&#9873;' : ''}</span><span class="fr">${esc(fr)}</span><span class="su">${esc(su)}</span><span class="dt">${dt}</span></div>`).join('')}
        </div>
      </div></div>`;
  }

  function bank() {
    return `<div class="page bank">
      <div class="top"><div class="logo">Harbour &amp; County<small>BUSINESS ONLINE BANKING</small></div><div class="out">${I.ICO.lock(14)} Secure area &middot; <u>Help</u> &middot; <u>Contact us</u></div></div>
      <div class="body">
        <div class="card login"><h4>You have been logged out</h4>
          <div class="timeout">${I.ICO.warn(16)}<span>For your security you were logged out after <b>10 minutes</b> without activity. Please log in again.</span></div>
          <label>Customer number</label><div class="in">&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;2087</div>
          <label>Please enter the <b>2nd</b>, <b>4th</b> and <b>7th</b> characters of your passcode</label>
          <div class="passcode"><span class="dd">&#9662;</span><span class="dd">&#9662;</span><span class="dd">&#9662;</span></div>
          <label>Card reader code (press <b>RESPOND</b> on your card reader)</label><div class="in short"></div>
          <div class="go">Log in &raquo;</div>
        </div>
        <div class="card side"><h4>Did you know?</h4><p>We will <b>never</b> ask for your full passcode by email or on the phone.</p><p>New: pay up to 25 suppliers at once with <u>Bulk Payments</u>.</p><p class="muted">Opening hours: Mon&ndash;Fri 8am&ndash;6pm, Sat 9am&ndash;12pm.</p></div>
      </div></div>`;
  }

  function calendar() {
    const days = [['Mon', 16], ['Tue', 17], ['Wed', 18], ['Thu', 19], ['Fri', 20], ['Sat', 21]], today = 19;
    const H0 = 8, H1 = 19, ROW = 34;
    const EV = [  // day, start hour, duration h, colour, text
      [16, 9, 1, 'b', 'Madison rep (Steve) - new catalogue'],
      [16, 13, 1, 'g', 'Bank - ring re: card machine'],
      [18, 18, 1, 'b', 'bins out!!'],
      [17, 8.5, 1.5, 'o', 'Rachel O. - drop off rims'],
      [18, 10, 1, 'g', 'Northgate delivery am'],
      [18, 16, 1, 'p', 'Theo - show uncle M the backup (AGAIN)'],
      [19, 9, 1, 'b', 'Anika - brakes?'],
      [19, 14, 2, 'p', 'Theo: write README for whoever looks after it next'],
      [20, 17, 1, 'o', 'leaving drinks @ the Bell 5pm!!'],
      [21, 10, 2, 'g', 'Kids bike check (free)'],
    ];
    const allday = { 17: ['g', 'Dev at Market St shop'], 20: ['r', "THEO'S LAST DAY :("] };
    const hours = [];
    for (let hh = H0; hh < H1; hh++) hours.push(hh);
    return `<div class="page calp">
      <div class="top"><span class="logo">${I.FAV.cal(18)} Calendar</span><span class="today">Today</span><span class="nav">&#9664; &#9654;</span><span class="rng">16 &ndash; 21 November 2026</span>
        <span class="views"><span>Day</span><span class="on">Week</span><span>Month</span></span></div>
      <div class="cal">
        <div class="hdr"><span class="tmh"></span>${days.map(([d, n]) => `<span class="hd ${n === today ? 'td' : ''}">${d} ${n}/11</span>`).join('')}</div>
        <div class="alld"><span class="tmh">all day</span>${days.map(([, n]) => `<span class="ad">${allday[n] ? `<span class="ev ${allday[n][0]}">${allday[n][1]}</span>` : ''}</span>`).join('')}</div>
        <div class="grid"><div class="tms">${hours.map(hh => `<div class="tm">${hh}:00</div>`).join('')}</div>
          ${days.map(([, n]) => `<div class="col ${n === today ? 'td' : ''}">${hours.map(() => '<div class="hr"></div>').join('')}
            ${EV.filter(e => e[0] === n).map(([, s, d, c, t]) => `<div class="ev ${c}" style="top:${(s - H0) * ROW + 1}px;height:${d * ROW - 3}px">${s % 1 ? `${Math.floor(s)}:${String(Math.round(s % 1 * 60)).padStart(2, '0')}` : `${s}:00`} ${t}</div>`).join('')}</div>`).join('')}
        </div>
      </div></div>`;
  }

  G.TABPAGES = { supplier, sms, xls, invoices, parts: partsList, email, bank, cal: calendar };
})(window);
