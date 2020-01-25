import {Builder, By, WebDriver, until} from "selenium-webdriver";
import {Deserializer} from "ts-jsonapi";
import * as fs from "fs";
import * as path from "path";
import {URL, URLSearchParams} from "url";

const PATREON_USERNAME = process.env["PATREON_USERNAME"]!;
const PATREON_PASSWORD = process.env["PATREON_PASSWORD"]!;

const FUNC_FETCH = fs.readFileSync(
  path.join(__dirname, "../../../webdriver/fetch.js")
).toString("utf-8");


export interface CallOptions {
  include?: string[];
  fields?: { [key: string]: string[] };
  sort?: string[];
  filter?: { [key: string]: string|string[]|boolean|number };
}

interface FetchError {
  error: string;
}

interface FetchSuccess {
  status: number;
  statusText: string;
  body: string;
}

type FetchResult = FetchSuccess | FetchError;

export class PatreonClient {
  private browser: WebDriver;
  private ser = new Deserializer();

  constructor() {
    this.browser = new Builder()
      .forBrowser("firefox")
      .build()
    ;
  }

  async login() {
    await this.browser.get("https://www.patreon.com/login");

    await this.browser.findElement(By.id("email")).sendKeys(PATREON_USERNAME);
    await this.browser.findElement(By.id("password")).sendKeys(PATREON_PASSWORD);
    await this.browser.findElement(By.css("button[type=submit]")).click();

    await this.browser.wait(until.urlIs("https://www.patreon.com/home"));
  }

  async call(
    path: string,
    options: CallOptions = {},
  ) {
    const params = new URLSearchParams({
      "json-api-use-default-includes": "false",
      "json-api-version": "1.0",
    });

    if (options.include) {
      params.set("include", options.include.join(","));
    }

    if (options.fields) {
      for (const [type, fields] of Object.entries(options.fields)) {
        params.set(`fields[${type}]`, fields.join(","));
      }
    }

    if (options.sort) {
      params.set("sort", options.sort.join(","));
    }

    if (options.filter) {
      for (const [key, value] of Object.entries(options.filter)) {
        if (Array.isArray(value)) {
          params.set(`filter[${key}]`, value.join(","));
        } else {
          params.set(`filter[${key}]`, "" + value);
        }
      }
    }

    const url = new URL(path, "https://www.patreon.com/api/");
    url.search = params.toString();

    console.log("calling", url.toString())

    const result = await this.browser.executeAsyncScript(FUNC_FETCH, url.toString()) as FetchResult;

    if ("error" in result) {
      throw new Error("API call failed: " + result.error);
    }

    if (result.status < 200 || result.status >= 300) {
      throw new Error(`API call returned ${result.status} ${result.statusText}`);
    }

    return this.ser.deserialize(JSON.parse(result.body));
  }

  async close() {
    await this.browser.quit();
  }
}
