const puppeteer = require("puppeteer");
const fs = require("fs");

//aysnc
(async() => {
    //await promise
    const browser = await puppeteer.launch({headless: true}) //headless mode

    const page = await browser.newPage();

    // console.log(process.argv[2]);
    webpage = process.argv[2];

    split_webpage = webpage.split(".")

    domain_name = split_webpage[1]

    console.log(domain_name)

    save_path = domain_name + 'trace.json';

    //start tracing
    await page.tracing.start({path: save_path});

    //start gathering js code coverage
    // await Promise.all([page.coverage.startJSCoverage()]);

    await page.goto(webpage);
    await page.waitForSelector('title'); //wait for title

    //stop tracing
    await page.tracing.stop();

    await browser.close();
})();