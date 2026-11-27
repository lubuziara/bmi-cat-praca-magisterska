const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'msedge', args: ['--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1200, height: 1050 }, timezoneId: 'Europe/Warsaw' });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('http://localhost:8000/**', async route => {
    const response = await route.fetch({ url: route.request().url().replace('localhost:8000', '127.0.0.1:8002') });
    await route.fulfill({ response });
  });
  async function button(name) { await page.getByRole('button', { name, exact: true }).click(); await page.waitForTimeout(300); }
  async function field(name, value) {
    await page.getByRole('textbox', { name, exact: true }).click(); await page.waitForTimeout(200);
    await page.keyboard.press('Control+A'); await page.keyboard.insertText(value);
    await page.waitForTimeout(200); await page.keyboard.press('Tab'); await page.waitForTimeout(100);
  }
  async function menu(name) {
    await button('Otwórz menu nawigacyjne');
    await page.getByText(name, { exact: true }).click();
    await page.waitForTimeout(500);
  }
  async function back() { await button('Wstecz'); }
  async function chooseScan() {
    const promise = page.waitForEvent('filechooser');
    await button('Wybierz zdjęcie');
    await (await promise).setFiles('work/health-preview/scan.png');
    await page.getByRole('button', { name: 'Akceptuję — zapisz PDF', exact: true }).waitFor();
  }
  try {
    await page.goto('http://localhost:5173/?health=1');
    await page.getByRole('button', { name: 'Enable accessibility' }).dispatchEvent('click');
    await field('E-mail', 'health-preview@example.com');
    await field('Hasło', 'Haslo bardzo dlugie!');
    await button('Zaloguj się');
    await page.getByRole('button', { name: 'Powiadomienia', exact: true }).waitFor();
    const avatar = await (await page.locator('iframe').elementHandle()).contentFrame();
    console.log('Avatar URL:', avatar.url(), 'src:', await page.locator('iframe').getAttribute('src'));
    await page.waitForTimeout(4000);
    console.log('Avatar state:', await page.locator('iframe').evaluate(el => ({ready:el.contentWindow.catViewer?.ready, url:el.contentWindow.location.href, text:el.contentDocument.body.innerText})));
    await page.screenshot({ path: 'outputs/bmi-cat/panel-menu-desktop.png' });
    await menu('Kalendarz');
    await button('Dodaj wydarzenie');
    await field('Nazwa wizyty', 'Wizyta kontrolna');
    await field('Notatka (opcjonalnie)', 'Syntetyczna notatka do testu');
    await button('Zapisz wydarzenie');
    await page.getByRole('button', { name: /^Wizyta kontrolna/ }).first().waitFor();
    await back();
    await menu('Kalkulator BMI');
    await field('Obwód klatki piersiowej (cm)', '40');
    await field('Odcinek tylnej nogi (cm)', '16');
    await button('Oblicz i zapisz w kalendarzu');
    await page.getByText('Szacowany udział tkanki tłuszczowej (FBMI)', { exact: false }).waitFor();
    await field('Obwód klatki piersiowej (cm)', '39');
    await button('Oblicz i zapisz w kalendarzu');
    await page.screenshot({ path: 'outputs/bmi-cat/kalkulator-bmi.png' });
    await back();
    await menu('Dokumentacja medyczna');
    await chooseScan();
    await page.screenshot({ path: 'outputs/bmi-cat/dokument-podglad.png' });
    await button('Odrzuć zdjęcie');
    await chooseScan();
    await field('Tytuł dokumentu', 'Testowy dokument weterynaryjny');
    await button('Akceptuję — zapisz PDF');
    await page.getByRole('button', { name: /^Testowy dokument weterynaryjny/ }).last().waitFor();
    await page.getByRole('button', { name: /^Testowy dokument weterynaryjny/ }).last().click();
    const pendingDownload = page.waitForEvent('download');
    await button('Pobierz PDF');
    const download = await pendingDownload;
    await download.saveAs('work/health-preview/browser-download.pdf');
    if (!fs.readFileSync('work/health-preview/browser-download.pdf').subarray(0, 4).equals(Buffer.from('%PDF'))) throw Error('Invalid PDF');
    await back();
    await back();
    await menu('Kalendarz');
    await page.screenshot({ path: 'outputs/bmi-cat/kalendarz-desktop.png' });
    await page.getByRole('button', { name: /^Testowy dokument weterynaryjny/ }).last().click();
    await button('Usuń dokument');
    await button('Usuń');
    await page.getByRole('heading', { name: 'Kalendarz', exact: true }).waitFor();
    await page.waitForTimeout(300);
    await page.getByText('Spokojny dzień.', { exact: false }).count();
    if (await page.getByRole('button', { name: /^Testowy dokument weterynaryjny/ }).last().count()) throw Error('Deleted document remains in calendar');
    await back();
    await menu('Ustawienia');
    await field('Imię', 'Anna');
    await field('Imię kota', 'Luna');
    await field('Dzienny cel kalorii (kcal)', '240');
    await button('Zapisz ustawienia');
    await back();
    await page.setViewportSize({ width: 390, height: 1000 });
    await page.screenshot({ path: 'outputs/bmi-cat/panel-menu-mobile.png' });
    await button('Otwórz menu nawigacyjne');
    await page.screenshot({ path: 'outputs/bmi-cat/menu-mobile.png' });
    console.log('PASS: login, menu, vet visit, BMI update, scan rejection/acceptance, PDF download, calendar document open/delete, settings and mobile layout.');
    console.log('Page errors:', errors);
  } catch (e) {
    console.log(await page.locator('body').ariaSnapshot());
    await page.screenshot({ path: 'work/health-failure.png' });
    throw e;
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
