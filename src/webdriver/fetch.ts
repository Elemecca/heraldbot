// this file is wrapped in an anonymous function when called
declare const arguments: [any, any];

(function (
  url: string,
  callback: (result: any) => void,
) {
  "use strict";
  (async () => {
    const response = await fetch(url, {
      cache: "no-cache",
      credentials: "include",
    });

    callback({
      status: response.status,
      statusText: response.statusText,
      body: await response.text(),
    });
  })().catch((error) => {
    callback({
      error: error.toString(),
    });
  });
})(...arguments);
