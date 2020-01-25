import {Builder, By, WebDriver, until} from "selenium-webdriver";
import * as dotenv from "dotenv";
import * as fs from "fs";
import * as path from "path";
import {URL, URLSearchParams} from "url";

dotenv.config();
const PATREON_USERNAME = process.env["PATREON_USERNAME"]!;
const PATREON_PASSWORD = process.env["PATREON_PASSWORD"]!;

const FUNC_FETCH = fs.readFileSync(
  path.join(__dirname, "../webdriver/fetch.js")
).toString("utf-8");

async function pollStream(browser: WebDriver) {
  const url = new URL("https://www.patreon.com/api/posts");
  url.search = new URLSearchParams({
    "include": "user",
    "fields[post]": [
      "title",
      "published_at",
      "current_user_can_view",
      "content",
      "image",
      "url",
    ].join(","),
    "fields[user]": [
      "full_name",
      "image_url",
      "url",
    ].join(","),
    "sort": "-published_at",
    "filter[campaign_id]": "88541",
    "filter[is_draft]": "false",
    "filter[contains_exclusive_posts]": "true",
    "json-api-use-default-includes": "false",
    "json-api-version": "1.0",
  }).toString();

  console.log(url.toString());

  const result = await browser.executeAsyncScript(FUNC_FETCH, url.toString());
  console.log(result);
}

async function loadPatreon(browser: WebDriver) {
  await browser.get("https://www.patreon.com/login");

  await browser.findElement(By.id("email")).sendKeys(PATREON_USERNAME);
  await browser.findElement(By.id("password")).sendKeys(PATREON_PASSWORD);
  await browser.findElement(By.css("button[type=submit]")).click();

  await browser.wait(until.urlIs("https://www.patreon.com/home"));

  await pollStream(browser);

  //await browser.sleep(2 * 60 * 1000);
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
