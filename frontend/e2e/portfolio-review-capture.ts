import { expect, type Page, type TestInfo } from "@playwright/test";
import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";

async function noOverflow(page: Page) {
  expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
}

async function reviewedLayout(page: Page, _state: string, width: number) {
  await page.evaluate("document.fonts.ready");
  const headings = page.locator("h1");
  await expect(headings).toHaveCount(1);
  const actions = page.getByRole("button").filter({
    hasText:
      /^(Keep portfolio|Delete portfolio|Remove(?: portfolio)?|Check deletion result|Review latest portfolio)$/,
  });
  const boxes = [];
  for (const action of await actions.all()) {
    if (!(await action.isVisible())) continue;
    const box = await action.boundingBox();
    if (!box) continue;
    expect(box.width).toBeGreaterThanOrEqual(44);
    expect(box.height).toBeGreaterThanOrEqual(44);
    boxes.push(box);
  }
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i],
        b = boxes[j];
      const vertical = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
      const horizontal = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
      if (vertical > 0)
        expect(Math.max(a.x, b.x) - Math.min(a.x + a.width, b.x + b.width)).toBeGreaterThanOrEqual(
          7.5,
        );
      if (horizontal > 0)
        expect(
          Math.max(a.y, b.y) - Math.min(a.y + a.height, b.y + b.height),
        ).toBeGreaterThanOrEqual(7.5);
    }
  }
  return { viewport: width, action_count: boxes.length, h1_count: 1, no_horizontal_overflow: true };
}

/** Freeze only the actual public DOM/styles/fonts; no cookies, storage or scripts. */
export async function capturePhase14(page: Page, info: TestInfo, state: string, width: number) {
  await noOverflow(page);
  const layout: Record<string, unknown> = await reviewedLayout(page, state, width);
  const name = `phase14-${state}-${width}`;
  const destination = process.env.BIRJA_PHASE14_REVIEW_DIR ?? process.env.BIRJA_PHASE12_REVIEW_DIR;
  const path = (suffix: string) =>
    destination ? `${destination}/${name}.${suffix}` : info.outputPath(`${name}.${suffix}`);
  await page.screenshot({ path: path("png"), fullPage: true });
  let css = await page.evaluate<string>(
    "Array.from(document.styleSheets).flatMap(s=>Array.from(s.cssRules,r=>r.cssText)).join('\\n')",
  );
  for (const match of [...css.matchAll(/url\((["']?)([^)"']+)\1\)/g)]) {
    if (match[2].startsWith("data:")) continue;
    const url = new URL(match[2], page.url());
    expect(url.origin).toBe(new URL(page.url()).origin);
    expect(url.pathname).toMatch(/\.(woff2?|ttf|otf)$/);
    const response = await page.request.get(url.href);
    expect(response.ok()).toBe(true);
    css = css.replaceAll(
      match[0],
      `url("data:font/woff2;base64,${(await response.body()).toString("base64")}")`,
    );
  }
  const browser = page.context().browser()!;
  const render = () =>
    page.evaluate<string>(`(styles => {
    const d=document.cloneNode(true);
    d.querySelectorAll('script,link,style,iframe').forEach(n=>n.remove());
    for(const tag of ['input','textarea','select']) {
      const live=document.querySelectorAll(tag);
      d.querySelectorAll(tag).forEach((n,i)=>{
        if(tag==='textarea')n.textContent=live[i].value;
        else if(tag==='select')n.querySelectorAll('option').forEach(o=>o.toggleAttribute('selected',o.value===live[i].value));
        else n.setAttribute('value',live[i].value);
        n.setAttribute('readonly','');
      });
    }
    d.querySelectorAll('form').forEach(n=>{const v=d.createElement('div');v.className=n.className;v.replaceChildren(...n.childNodes);n.replaceWith(v);});
    d.querySelectorAll('a').forEach(n=>n.setAttribute('href','#'));
    d.querySelectorAll('button').forEach(n=>n.setAttribute('type','button'));
    d.querySelectorAll('*').forEach(n=>Array.from(n.attributes).filter(a=>a.name.startsWith('on')).forEach(a=>n.removeAttribute(a.name)));
    const s=d.createElement('style');s.textContent=styles;d.head.append(s);
    const c=d.createElement('meta');c.httpEquiv='Content-Security-Policy';c.content="default-src 'none';style-src 'unsafe-inline';font-src data:;img-src data:;base-uri 'none';form-action 'none'";d.head.prepend(c);
    return '<!doctype html>\\n'+d.documentElement.outerHTML;
  })(${JSON.stringify(css)})`);
  let rendered = await render();
  if (width >= 768) {
    const viewport = page.viewportSize()!;
    const responsiveTable = (await page.getByRole("table").count()) > 0;
    await page.setViewportSize({ width: Math.floor(width / 2), height: 480 });
    await expect.poll(() => page.evaluate("matchMedia('(min-width: 768px)').matches")).toBe(false);
    // Wait for the actual React conditional table-to-card render as well as CSS.
    if (responsiveTable) await expect(page.getByRole("table")).toHaveCount(0);
    await noOverflow(page);
    layout.reflow = await reviewedLayout(page, state, Math.floor(width / 2));
    const narrow = await render();
    await page.screenshot({ path: path("reflow.png"), fullPage: true });
    await page.setViewportSize(viewport);
    rendered = await page.evaluate<string>(`(([wide,narrow])=>{
      const parser=new DOMParser(),d=parser.parseFromString(wide,'text/html');
      const small=parser.parseFromString(narrow,'text/html');
      function variant(doc,mode){
        const wrapper=d.createElement('div');wrapper.setAttribute('data-review-mode',mode);
        const ids=new Map();
        doc.body.querySelectorAll('[id]').forEach(n=>{const old=n.id; n.id=mode+'-'+old;ids.set(old,n.id);});
        doc.body.querySelectorAll('*').forEach(n=>{
          for(const attribute of ['for','aria-describedby','aria-labelledby','aria-controls']){
            const value=n.getAttribute(attribute);if(value)n.setAttribute(attribute,value.split(' ').map(v=>ids.get(v)||v).join(' '));
          }
        });
        wrapper.replaceChildren(...doc.body.childNodes);return wrapper;
      }
      const large=variant(d,'wide'),compact=variant(small,'narrow');
      d.body.replaceChildren(large,compact);
      const style=d.createElement('style');style.textContent='[data-review-mode="narrow"]{display:none}@media(max-width:767px){[data-review-mode="wide"]{display:none}[data-review-mode="narrow"]{display:block}}';d.head.append(style);
      return '<!doctype html>\\n'+d.documentElement.outerHTML;
    })(${JSON.stringify([rendered, narrow])})`);
  }
  const metadata = {
    phase: 14,
    state,
    width,
    browser: browser.browserType().name(),
    version: browser.version(),
    synthetic: true,
    source: process.env.BIRJA_PHASE14_SOURCE ?? process.env.BIRJA_PHASE12_SOURCE,
    native_200_percent_verified: false,
    owner_accepted: false,
    layout,
    artifacts: {
      html: name + ".html",
      png: name + ".png",
      trace: name + ".trace.json",
      ...(width >= 768 ? { reflow_png: name + ".reflow.png" } : {}),
    },
    scope: createHash("sha256")
      .update(JSON.stringify(await (await page.request.get("/api/v2/me")).json()))
      .digest("hex"),
    trace: await page.evaluate<Array<{ path: string; start: number; duration: number }>>(
      `performance.getEntriesByType('resource').map(e=>({path:new URL(e.name).pathname,start:e.startTime,duration:e.duration}))`,
    ),
  };
  const html = rendered.replace(
    "</head>",
    `<meta name="birja-evidence" content="${JSON.stringify(metadata).replaceAll('"', "&quot;")}"></head>`,
  );
  expect(html).not.toMatch(/<script|<form|\s(?:src|href|action)=["']https?:/);
  expect(html).not.toContain("bj_access");
  await writeFile(path("html"), html, { flag: "wx" });
}
