import {Builder, By, WebDriver} from "selenium-webdriver";
import * as dotenv from "dotenv";

dotenv.config();
const PATREON_USERNAME = process.env["PATREON_USERNAME"]!;
const PATREON_PASSWORD = process.env["PATREON_PASSWORD"]!;

async function loadPatreon(browser: WebDriver) {
  await browser.get("https://www.patreon.com/login");

  await browser.findElement(By.id("email")).sendKeys(PATREON_USERNAME);
  await browser.findElement(By.id("password")).sendKeys(PATREON_PASSWORD);
  await browser.findElement(By.css("button[type=submit]")).click();

  await browser.sleep(2 * 60 * 1000);
}

(async () => {
  const browser = await new Builder()
    .forBrowser("firefox")
    .build()
  ;
  try {
    await loadPatreon(browser);
  } finally {
    browser.quit();
  }
})().catch((err) => {
  console.error(err);
});
