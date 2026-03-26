import { Builder, Browser } from "selenium-webdriver";
import firefox from "selenium-webdriver/firefox";
import { backOff } from "exponential-backoff";
import { logger } from "../utils/logger";

export async function extractWebpageContent(url: string): Promise<string[]> {
  try {
    const response = await backOff(async () => {
      return await extractWebpageContentWorker(url);
    }, {
      numOfAttempts: 10,
      startingDelay: 500,
      timeMultiple: 2,
      jitter: "full",
      maxDelay: 50000,
    });
    return response;
  } catch (err: any) {
    logger.error(`Failed out of retry loop for URL "${url}", returning placeholder to pipeline`);
    return ["API EXCEPTION"];
  }
}

async function extractWebpageContentWorker(url: string): Promise<string[]> {
  let driver;
  try {
    const options = new firefox.Options();
    options.addArguments("--headless");
    driver = await new Builder()
      .forBrowser(Browser.FIREFOX)
      .setFirefoxOptions(options)
      .build();
  } catch (err: any) {
    const desc = `Failed to launch Firefox driver: ${err.message}`;
    logger.error(desc);
    throw new Error(desc);
  }

  try {
    try {
      await driver.get(url);
    } catch (err: any) {
      const desc = `Failed to navigate to URL "${url}": ${err.message}`;
      logger.error(desc);
      throw new Error(desc);
    }

    try {
      await driver.wait(async () => {
        return await driver.executeScript(
          "return document.readyState === 'complete'"
        );
      }, 5000);
    } catch (err: any) {
      logger.error(`Page load timed out for "${url}", attempting to read partial content: ${err.message}`);
      // do not throw, attempt to read
    }

    let readableText: string;
    try {
      readableText = await driver.executeScript(
        "return document.body.innerText;"
      ) as string;
    } catch (err: any) {
      const desc = `Failed to extract page text from "${url}": ${err.message}`;
      logger.error(desc);
      throw new Error(desc);
    }

    const filteredLines = readableText
      .split(/\r?\n/)
      .map(line => line.trim())
      .filter(line => line.split(/\s+/).length > 1);

    if (filteredLines.length === 0) {
      const desc = `No content extracted from "${url}"`;
      logger.error(desc);
      throw new Error(desc);
    }

    return filteredLines;
  } finally {
    try {
      await driver.quit();
    } catch (err: any) {
      logger.error(`Failed to quit Firefox driver cleanly: ${err.message}`);
    }
  }
}

// console.log(await extractWebpageContent("https://www.bbc.co.uk/news/live/c74wd01egvyt"))
// console.log(await extractWebpageContent("https://badcertificate.int.jeynes.uk/"))