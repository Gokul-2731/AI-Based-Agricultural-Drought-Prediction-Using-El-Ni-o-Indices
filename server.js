const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const files = new Map([
  ["/", ["index.html", "text/html"]],
  ["/index.html", ["index.html", "text/html"]],
  ["/styles.css", ["styles.css", "text/css"]],
  ["/script.js", ["script.js", "text/javascript"]],
  ["/forecast.js", ["forecast.js", "text/javascript"]],
]);

const server = http.createServer((request, response) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    response.writeHead(405, { Allow: "GET, HEAD" });
    response.end("Method not allowed");
    return;
  }

  const pathname = (request.url ?? "/").split("?")[0];
  const file = files.get(pathname);

  if (!file) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
    return;
  }

  const [fileName, contentType] = file;
  fs.readFile(path.join(__dirname, fileName), (error, content) => {
    if (error) {
      console.error(`Could not read ${fileName}:`, error);
      response.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Internal server error");
      return;
    }

    response.writeHead(200, {
      "Content-Type": `${contentType}; charset=utf-8`,
      "X-Content-Type-Options": "nosniff",
    });
    response.end(request.method === "HEAD" ? undefined : content);
  });
});

server.listen(3000, () => {
  console.log("Fieldwatch is available at http://localhost:3000");
});

server.on("error", (error) => {
  console.error("Could not start Fieldwatch:", error);
  process.exitCode = 1;
});
