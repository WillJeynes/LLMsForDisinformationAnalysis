import { Builder, Browser } from "selenium-webdriver";
import firefox from "selenium-webdriver/firefox";

export async function extractWebpageContent(url: string) : Promise<string[]>{
    const options = new firefox.Options();
    options.addArguments("--headless");

    let driver = await new Builder().forBrowser(Browser.FIREFOX).setFirefoxOptions(options).build()
    try {
        await driver.get(url)
        await driver.wait(async () => {
            return await driver.executeScript(
                "return document.readyState === 'complete'"
            );
        }, 5000);

        const readableText = await driver.executeScript(
            "return document.body.innerText;"
        ) as string;

        const filteredLines = readableText
            .split(/\r?\n/)
            .map(line => line.trim())
            .filter(line => line.split(/\s+/).length > 1); 
        
        return filteredLines;
    } finally {
        await driver.quit()
    }
}

//TODO: Extract, rank snippets

//console.log(await extractWebpageContent("https://www.bbc.co.uk/news/live/c74wd01egvyt"))