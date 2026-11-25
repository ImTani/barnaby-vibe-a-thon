"""ui/skins/app.css after the finish review: no capsules, a wider inspector with a header edge, soft scroll edges,
one moving indicator while he works, folded technical names, a separated toolbar subtitle, decisions as loud as the
words around them at compact widths."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'ui/skins/app.css'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:90], s.count(old))
    s = s.replace(old, new)


rep("--side: clamp(340px, 23vw, 440px);", "--side: clamp(380px, 26vw, 440px);")

# toolbar: title, then a separated subtitle
rep(""".sys-chip span { color: var(--ink-3); }""",
""".sys-chip span { color: var(--ink-3); }
.sys-chip span::before { content: "\\00B7"; margin-right: 8px; color: var(--line-strong); }""")
# one moving indicator while he works: the line in the conversation. The toolbar and the step hold still.
rep("""body.s-thinking .status .dot, body.s-speaking .status .dot {
  display: block; width: 14px; height: 14px; border-radius: 50%; border: 2px solid var(--hair); border-top-color: var(--ink-2);
  animation: spin .9s linear infinite;
}""",
"""body.s-thinking .status .dot, body.s-speaking .status .dot { display: block; width: 8px; height: 8px; border-radius: 50%; background: var(--ink-3); }""")
rep(""".tr.step.doing .mark .ico { animation: spin .9s linear infinite; }\n""", "")

# soft scroll edges: content passing under the toolbar or the composer fades rather than being cut
rep(""".convo::after { content: ""; flex: none; height: 20px; }""",
""".convo::after { content: ""; flex: none; height: 20px; }
.convo {
  -webkit-mask-image: linear-gradient(to bottom, transparent 0, #000 16px, #000 calc(100% - 16px), transparent 100%);
  mask-image: linear-gradient(to bottom, transparent 0, #000 16px, #000 calc(100% - 16px), transparent 100%);
}""")
rep("""  position: sticky; bottom: 0; z-index: 2;""", """  position: sticky; bottom: 16px; z-index: 2;""")

# the inspector's heading keeps an edge, and earlier steps wrap to two lines rather than cut a word
rep(""".trace .panel-head { display: flex; align-items: center; justify-content: space-between; padding: 18px 20px 8px; }""",
""".trace .panel-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px 12px; margin-bottom: 8px; border-bottom: 1px solid var(--hair); }""")
rep(""".tr.step.past .say { font-size: var(--t-small); color: var(--ink-2); font-weight: 400; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }""",
""".tr.step.past .say { font-size: var(--t-small); color: var(--ink-2); font-weight: 400; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }""")

# abilities: state words, never capsules; technical names on request
rep(""".ab .today { align-self: start; padding: 0 8px; border-radius: 999px; background: var(--brass-tint); color: var(--brass-ink); font-weight: 600; }""",
""".ab .today { color: var(--brass-ink); font-weight: 600; }
.map .use .ico { color: var(--ok); }""")
rep(""".ab .tech { grid-column: 2 / -1; grid-row: 2;""", """.ab .tech { display: none; grid-column: 2 / -1; grid-row: 2;""")
rep(""".ab.shut .what {""",
"""#map.show-tech .ab .tech { display: block; }
.tech-toggle {
  margin-top: 10px; padding: 4px 2px; border: 0; background: none; font: 600 var(--t-meta)/1.4 var(--ui); color: var(--ink-2);
  text-decoration: underline; text-decoration-color: var(--line-strong); text-underline-offset: 3px;
}
.tech-toggle:hover { color: var(--ink); text-decoration-color: var(--ink-3); }
.ab.shut .what {""")
rep(""".map .use .ico { color: var(--ink-2); }\n""", "")

# compact widths: the decision is never quieter than the words above it
rep("""body.overlay .card .title { padding-top: 4px; font-size: var(--t-body); }""",
"""body.overlay .card .title { padding-top: 2px; font-size: var(--t-answer); }""")
rep("""  .card .title { padding-top: 4px; font-size: var(--t-body); }""",
"""  .card .title { padding-top: 2px; font-size: var(--t-answer); }
  .brand span { display: none; }""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', p)
